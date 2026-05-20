"""Hosted-agent manifest validation helpers.

The validator is intentionally data-oriented: it checks a small public sample
schema without depending on Azure SDKs or requiring credentials.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast


@dataclass(frozen=True, slots=True)
class ManifestIssue:
    """Validation issue found in a hosted-agent manifest."""

    path: str
    message: str
    level: Literal["error", "warning"] = "error"


@dataclass(frozen=True, slots=True)
class ManifestValidationResult:
    """Validation result for a hosted-agent manifest."""

    issues: tuple[ManifestIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Return true when no error-level issues were found."""

        return all(issue.level != "error" for issue in self.issues)


def load_hosted_agent_manifest(path: str | Path) -> Mapping[str, object]:
    """Load a YAML hosted-agent manifest when PyYAML is installed."""

    manifest_path = Path(path)
    try:
        yaml_module = importlib.import_module("yaml")
    except ImportError as import_error:
        raise RuntimeError(
            "Install the manifest extra to load YAML files: "
            "python -m pip install -e .[manifest]"
        ) from import_error

    safe_load_value = vars(yaml_module).get("safe_load")
    if not callable(safe_load_value):
        raise RuntimeError("PyYAML safe_load is unavailable.")
    safe_load = cast(Callable[[str], object], safe_load_value)
    loaded_manifest = safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(loaded_manifest, Mapping):
        raise ValueError("Hosted-agent manifest must be a mapping.")

    return _mapping(loaded_manifest) or {}


def validate_hosted_agent_manifest(
    manifest: Mapping[str, object]
) -> ManifestValidationResult:
    """Validate hosted-agent deployment facts encoded in the sample manifest."""

    issues: list[ManifestIssue] = []
    issues.extend(scan_public_safety(manifest))

    container = _required_mapping(manifest, "container", issues)
    protocols = _required_mapping(manifest, "protocols", issues)
    identity = _required_mapping(manifest, "identity", issues)
    registries = _required_mapping(manifest, "registries", issues)

    if container is not None:
        _validate_container(container, issues)
    if protocols is not None:
        _validate_protocols(protocols, issues)
    if identity is not None:
        _validate_identity(identity, issues)
    if registries is not None:
        _validate_registry(registries, issues)

    return ManifestValidationResult(issues=tuple(issues))


def scan_public_safety(manifest: Mapping[str, object]) -> tuple[ManifestIssue, ...]:
    """Scan a manifest for values that should not appear in public samples."""

    issues: list[ManifestIssue] = []
    for path, value in _walk_mapping(manifest):
        lowered_path = path.lower()
        if any(marker in lowered_path for marker in _SENSITIVE_KEY_MARKERS):
            issues.append(
                ManifestIssue(
                    path=path,
                    message="Public sample must not include this key.",
                )
            )
        if isinstance(value, str) and _looks_sensitive_value(value):
            issues.append(
                ManifestIssue(
                    path=path,
                    message="Public sample must use placeholders, not private values.",
                )
            )
    return tuple(issues)


def _validate_container(
    container: Mapping[str, object], issues: list[ManifestIssue]
) -> None:
    platform = container.get("platform")
    if platform != "linux/amd64":
        issues.append(
            ManifestIssue(
                path="container.platform",
                message="Hosted-agent images must target linux/amd64.",
            )
        )

    tag = container.get("tag")
    if not isinstance(tag, str) or not tag.strip():
        issues.append(
            ManifestIssue(path="container.tag", message="Container tag is required.")
        )
    elif tag == "latest":
        issues.append(
            ManifestIssue(
                path="container.tag",
                message="Use a unique immutable tag; do not deploy latest.",
            )
        )


def _validate_protocols(
    protocols: Mapping[str, object], issues: list[ManifestIssue]
) -> None:
    responses_enabled = protocols.get("responses") is True
    if not responses_enabled:
        issues.append(
            ManifestIssue(
                path="protocols.responses",
                message="Responses protocol must be enabled for this sample.",
            )
        )

    a2a = _mapping(protocols.get("a2a"))
    if a2a is None or a2a.get("incomingPreview") is not True:
        return

    if not responses_enabled:
        issues.append(
            ManifestIssue(
                path="protocols.a2a",
                message="Incoming A2A preview requires the Responses protocol.",
            )
        )
    if a2a.get("version") != "0.3":
        issues.append(
            ManifestIssue(
                path="protocols.a2a.version",
                message="Foundry incoming A2A preview currently uses version 0.3.",
            )
        )
    if a2a.get("modality") != "text":
        issues.append(
            ManifestIssue(
                path="protocols.a2a.modality",
                message="Foundry incoming A2A preview is text-only in this sample.",
            )
        )
    if a2a.get("auth") != "entra":
        issues.append(
            ManifestIssue(
                path="protocols.a2a.auth",
                message="Incoming A2A requires Microsoft Entra authentication.",
            )
        )


def _validate_identity(
    identity: Mapping[str, object], issues: list[ManifestIssue]
) -> None:
    if identity.get("runtime") != "agent-identity":
        issues.append(
            ManifestIssue(
                path="identity.runtime",
                message="Runtime access should use the agent identity.",
            )
        )
    if identity.get("projectManagedIdentityUsedFor") != "infrastructure-pull":
        issues.append(
            ManifestIssue(
                path="identity.projectManagedIdentityUsedFor",
                message=(
                    "Project managed identity should be limited to platform "
                    "pull operations."
                ),
            )
        )


def _validate_registry(
    registries: Mapping[str, object], issues: list[ManifestIssue]
) -> None:
    acr = _mapping(registries.get("acr"))
    if acr is None:
        issues.append(
            ManifestIssue(path="registries.acr", message="ACR config required.")
        )
        return

    if acr.get("endpointReachability") != "public":
        issues.append(
            ManifestIssue(
                path="registries.acr.endpointReachability",
                message=(
                    "Hosted agents currently require public ACR endpoint "
                    "reachability."
                ),
            )
        )
    if acr.get("pullRolePrincipal") != "project-managed-identity":
        issues.append(
            ManifestIssue(
                path="registries.acr.pullRolePrincipal",
                message="Project managed identity needs ACR pull permission.",
            )
        )


def _required_mapping(
    manifest: Mapping[str, object], key: str, issues: list[ManifestIssue]
) -> Mapping[str, object] | None:
    value_mapping = _mapping(manifest.get(key))
    if value_mapping is None:
        issues.append(
            ManifestIssue(path=key, message=f"Missing required '{key}' mapping.")
        )
    return value_mapping


def _mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    return {
        str(mapping_key): mapping_value
        for mapping_key, mapping_value in value.items()
        if isinstance(mapping_key, str)
    }


def _walk_mapping(
    manifest: Mapping[str, object], prefix: str = ""
) -> tuple[tuple[str, object], ...]:
    entries: list[tuple[str, object]] = []
    for mapping_key, mapping_value in manifest.items():
        current_path = f"{prefix}.{mapping_key}" if prefix else mapping_key
        entries.append((current_path, mapping_value))
        nested_mapping = _mapping(mapping_value)
        if nested_mapping is not None:
            entries.extend(_walk_mapping(nested_mapping, current_path))
    return tuple(entries)


def _looks_sensitive_value(value: str) -> bool:
    lowered_value = value.lower()
    return any(marker in lowered_value for marker in _SENSITIVE_VALUE_MARKERS)


_SENSITIVE_KEY_MARKERS = (
    "secret",
    "password",
    "subscription",
    "tenant",
    "clientid",
    "objectid",
    "connectionstring",
)

_SENSITIVE_VALUE_MARKERS = (
    "/" + "subscriptions/",
    "account" + "key=",
    "sharedaccess" + "key=",
    "private" + "link.",
)
