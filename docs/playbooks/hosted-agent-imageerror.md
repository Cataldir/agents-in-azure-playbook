# Playbook: Hosted Agent ImageError Or Container Pull Failure

## Situation

A hosted agent deployment reaches the platform but fails to start because the container image cannot be pulled or started. The visible symptom may be `ImageError`, `AcrPullUnauthorized`, or a container status that never reaches started.

## First Checks

1. Confirm the image uses a linux/amd64 build.
2. Confirm the manifest points to a unique immutable tag, not latest.
3. Confirm the tag exists in the registry.
4. Confirm the registry endpoint is publicly reachable while hosted-agent public ACR reachability is required.
5. Confirm the Foundry project managed identity has pull permission on the registry.
6. Confirm runtime permissions are assigned to the hosted agent identity, not confused with registry pull permissions.

## Diagnostic Commands

Use placeholders only in public notes and issue templates.

```bash
az acr repository show-tags \
  --name <registry-name> \
  --repository <repository-name> \
  --output table
```

```bash
az acr manifest list-metadata \
  --name <repository-name> \
  --registry <registry-name> \
  --output table
```

```bash
az role assignment list \
  --assignee <project-managed-identity-principal-id> \
  --scope <registry-resource-scope> \
  --output table
```

## Likely Causes

- The image was built for the wrong platform.
- The deployment references a tag that was never pushed.
- The deployment references latest, and the platform is resolving a different image than the operator expected.
- The registry has public network access disabled before hosted agents support that pull path.
- The pull role was assigned to the runtime agent identity instead of the project managed identity.
- Runtime roles were assigned to the project managed identity instead of the agent identity, causing later tool or model access failures after the image pull succeeds.

## Recovery

1. Rebuild the image for linux/amd64.
2. Push a new unique tag.
3. Update the hosted-agent manifest or version definition to reference that exact tag.
4. Grant the project managed identity registry pull permission at the narrowest viable registry or repository scope.
5. Redeploy the hosted-agent version.
6. After startup, validate runtime access separately with the agent identity.

## Prevention

Keep image build, tag creation, manifest validation, and role checks in the release checklist. Pull failures are infrastructure problems; tool and model access failures are runtime identity problems. Treat them as separate checks.
