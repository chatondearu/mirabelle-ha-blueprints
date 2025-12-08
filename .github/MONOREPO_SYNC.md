# Monorepo to Sub-Repository Sync

This document explains how the monorepo automatically syncs HACS integrations to separate sub-repositories.

## Overview

Since HACS requires integrations to be in dedicated repositories (not monorepos), we use GitHub Actions workflows to automatically sync packages from this monorepo to separate sub-repositories.

## Architecture

```
mirabelle-ha-blueprints (monorepo)
├── packages/
│   └── cover-manager/
│       ├── custom_components/
│       ├── hacs.json
│       └── README.md
│
└── .github/workflows/
    └── sync-cover-manager.yml
         │
         └── Syncs to ──> myrabelle-hacs-cover-manager (sub-repository)
                          ├── custom_components/
                          ├── hacs.json
                          └── README.md
```

## Setup Instructions

### 1. Create Sub-Repository

For each HACS integration in `packages/`, create a dedicated GitHub repository:

**Example for Cover Manager:**
- Repository name: `myrabelle-hacs-cover-manager`
- Owner: `chatondearu`
- Visibility: Public (required for HACS)
- Initialize with: README (optional, will be overwritten)

### 2. Create Personal Access Token (PAT)

1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens**
2. Click **Generate new token**
3. Configure:
   - **Token name**: `mirabelle-ha-blueprints-sync`
   - **Expiration**: Choose appropriate duration
   - **Repository access**: Select the sub-repositories (e.g., `myrabelle-hacs-cover-manager`)
4. Under **Repository permissions**, grant:
   - **Contents**: `Read and write`
   - **Metadata**: `Read-only` (automatic)
5. Generate and copy the token

### 3. Add Secret to Monorepo

1. Go to the monorepo: **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add:
   - **Name**: `RELEASE_TOKEN`
   - **Value**: Paste your PAT
4. Click **Add secret**

### 4. Update Workflow Configuration

For each integration, update the sync workflow:

1. Open `.github/workflows/sync-{package-name}.yml`
2. Update the repository name in the checkout step:
   ```yaml
   repository: chatondearu/{sub-repo-name}
   ```
3. Update the paths trigger to match your package:
   ```yaml
   paths:
     - 'packages/{package-name}/**'
   ```

## How It Works

### Trigger

The workflow triggers when:
- Changes are pushed to `main` branch in `packages/{package-name}/**`
- Manual trigger via `workflow_dispatch`

### Process

1. **Checkout monorepo**: Gets the latest code
2. **Prepare package**: Restructures the package for HACS:
   - Moves `custom_components/` to root
   - Copies `hacs.json` to root
   - Copies `README.md` and documentation to root
3. **Checkout sub-repository**: Gets the sub-repo (or initializes if new)
4. **Sync files**: Replaces all files in sub-repo with prepared structure
5. **Commit and push**: Commits changes with `[skip ci]` to avoid loops

### File Structure Transformation

**Monorepo structure:**
```
packages/cover-manager/
├── custom_components/
│   └── cover_manager/
├── hacs.json
└── README.md
```

**Sub-repository structure:**
```
myrabelle-hacs-cover-manager/
├── custom_components/
│   └── cover_manager/
├── hacs.json
└── README.md
```

## Adding New Integrations

To add a new HACS integration:

1. **Create the package** in `packages/{new-package}/`
2. **Create sub-repository** on GitHub
3. **Copy workflow template**:
   ```bash
   cp .github/workflows/sync-cover-manager.yml .github/workflows/sync-{new-package}.yml
   ```
4. **Update workflow**:
   - Change repository name
   - Update paths trigger
   - Update package name in comments
5. **Add PAT permission** for the new sub-repository
6. **Test the workflow** by making a change to the package

## HACS Configuration

Once synced, the sub-repository can be added to HACS:

1. In HACS, go to **Integrations**
2. Click **Custom repositories**
3. Add:
   - **Repository**: `https://github.com/chatondearu/{sub-repo-name}`
   - **Category**: Integration
4. Search for the integration and install

## Benefits

✅ **Clean separation**: Each integration has its own repository  
✅ **HACS compatible**: Direct repository support, no zip files needed  
✅ **Automatic sync**: Changes in monorepo automatically propagate  
✅ **Maintainable**: Single source of truth in monorepo  
✅ **Scalable**: Easy to add new integrations  

## Troubleshooting

### Workflow fails with "Repository not found"

- Ensure the sub-repository exists on GitHub
- Verify the PAT has access to the sub-repository
- Check the repository name in the workflow matches exactly

### Workflow fails with "Permission denied"

- Verify the PAT has `Contents: Read and write` permission
- Ensure the PAT is not expired
- Check the secret name matches: `RELEASE_TOKEN`

### Changes not syncing

- Check if the workflow triggered (GitHub Actions tab)
- Verify the paths in the workflow match your file changes
- Check workflow logs for errors

### Sub-repository has wrong structure

- Ensure the workflow copies files correctly
- Verify `custom_components/` is at the root of sub-repo
- Check that `hacs.json` is at the root

## Best Practices

1. **Use descriptive commit messages** in monorepo (they won't appear in sub-repo)
2. **Test locally** before pushing to ensure structure is correct
3. **Monitor workflows** after major changes
4. **Keep sub-repos in sync** - don't edit them directly
5. **Use tags/releases** in sub-repos for versioning (can be automated)

## Future Enhancements

Potential improvements:
- [ ] Automatic tag creation in sub-repos from monorepo tags
- [ ] Release creation in sub-repos
- [ ] Multi-package sync in single workflow
- [ ] Validation before sync
- [ ] Rollback mechanism
