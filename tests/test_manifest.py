from __future__ import annotations

from agents_in_azure_playbook.manifest import (
    scan_public_safety,
    validate_hosted_agent_manifest,
)


def _valid_manifest() -> dict[str, object]:
    return {
        "name": "agents-in-azure-playbook-hosted",
        "container": {
            "image": (
                "<registry-name>.azurecr.io/agents-in-azure-playbook/"
                "hosted-agent-fastapi"
            ),
            "tag": "2026-05-20-sample",
            "platform": "linux/amd64",
        },
        "identity": {
            "runtime": "agent-identity",
            "projectManagedIdentityUsedFor": "infrastructure-pull",
        },
        "registries": {
            "acr": {
                "endpointReachability": "public",
                "pullRolePrincipal": "project-managed-identity",
            }
        },
        "protocols": {
            "responses": True,
            "a2a": {
                "incomingPreview": True,
                "version": "0.3",
                "modality": "text",
                "auth": "entra",
            },
        },
    }


def test_validate_hosted_agent_manifest_accepts_public_safe_manifest() -> None:
    result = validate_hosted_agent_manifest(_valid_manifest())

    assert result.is_valid
    assert result.issues == ()


def test_validate_hosted_agent_manifest_rejects_latest_tag() -> None:
    manifest = _valid_manifest()
    container = manifest["container"]
    assert isinstance(container, dict)
    container["tag"] = "latest"

    result = validate_hosted_agent_manifest(manifest)

    assert not result.is_valid
    assert any(issue.path == "container.tag" for issue in result.issues)


def test_validate_hosted_agent_manifest_requires_responses_for_a2a() -> None:
    manifest = _valid_manifest()
    protocols = manifest["protocols"]
    assert isinstance(protocols, dict)
    protocols["responses"] = False

    result = validate_hosted_agent_manifest(manifest)

    assert not result.is_valid
    assert any(issue.path == "protocols.responses" for issue in result.issues)
    assert any(issue.path == "protocols.a2a" for issue in result.issues)


def test_validate_hosted_agent_manifest_rejects_wrong_identity_boundary() -> None:
    manifest = _valid_manifest()
    identity = manifest["identity"]
    assert isinstance(identity, dict)
    identity["runtime"] = "project-managed-identity"

    result = validate_hosted_agent_manifest(manifest)

    assert not result.is_valid
    assert any(issue.path == "identity.runtime" for issue in result.issues)


def test_scan_public_safety_flags_sensitive_values() -> None:
    sensitive_directory_key = "tenant" + "Id"
    private_endpoint = "private" + "link.example.azurecr.io/repo"

    issues = scan_public_safety(
        {
            sensitive_directory_key: "example-directory",
            "container": {"image": private_endpoint},
        }
    )

    assert {issue.path for issue in issues} == {
        sensitive_directory_key,
        "container.image",
    }
