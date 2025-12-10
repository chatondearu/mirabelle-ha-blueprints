# HACS Setup for Cover Manager

## Overview

Cover Manager is part of a monorepo (`mirabelle-ha-blueprints`) but is automatically synced to a dedicated sub-repository (`myrabelle-hacs-cover-manager`) for HACS installation.

## Architecture

```
mirabelle-ha-blueprints (monorepo)
└── packages/cover-manager/
    └── [source code]
         │
         └── Auto-sync via GitHub Actions
              │
              └── myrabelle-hacs-cover-manager (sub-repository for HACS)
                   └── [HACS-ready structure]
```

## How It Works

1. **Development**: All development happens in the monorepo at `packages/cover-manager/`
2. **Auto-Sync**: When changes are pushed to `main`, a GitHub Actions workflow automatically syncs to `myrabelle-hacs-cover-manager`
3. **HACS Installation**: Users install from the dedicated sub-repository

## For Users

### HACS Installation

1. Add custom repository in HACS:
   - **Repository**: `https://github.com/chatondearu/myrabelle-hacs-cover-manager`
   - **Category**: Integration

2. Search for "Cover Manager" and install

3. Configuration
   - No YAML includes are required. The integration manages state internally (impulse switch, no templates/helpers).
   - **Note**: Uses modern `template:` syntax (replacing deprecated `cover: platform: template`).

### Why a Separate Repository?

HACS requires integrations to be in dedicated repositories, not monorepos. The sub-repository is automatically maintained and always in sync with the monorepo.

## For Developers

### Monorepo Structure

The monorepo contains:
```
packages/cover-manager/
├── custom_components/
│   └── cover_manager/
├── hacs.json
├── README.md
└── ...
```

### Sub-Repository Structure

The synced sub-repository has:
```
myrabelle-hacs-cover-manager/
├── custom_components/
│   └── cover_manager/
├── hacs.json
└── README.md
```

### Sync Workflow

The sync workflow (`.github/workflows/sync-cover-manager.yml`) automatically:
1. Detects changes in `packages/cover-manager/`
2. Restructures files for HACS (moves `custom_components/` to root)
3. Pushes to `myrabelle-hacs-cover-manager` repository

### Making Changes

1. **Edit in monorepo**: Make all changes in `packages/cover-manager/`
2. **Commit and push**: Push to `main` branch
3. **Auto-sync**: The workflow automatically syncs to sub-repository
4. **No manual steps**: The sub-repository is read-only from HACS perspective

## Setup (First Time)

If you're setting up the sync for the first time:

1. **Create sub-repository**:
   - Repository name: `myrabelle-hacs-cover-manager`
   - Owner: `chatondearu`
   - Public visibility (required for HACS)

2. **Create PAT** (Personal Access Token):
   - Fine-grained token with `Contents: Read and write` permission
   - Access to `myrabelle-hacs-cover-manager` repository

3. **Add secret to monorepo**:
   - Secret name: `RELEASE_TOKEN`
   - Value: Your PAT

4. **Test the workflow**:
   - Make a small change in `packages/cover-manager/`
   - Push to `main`
   - Verify sync in GitHub Actions

See [MONOREPO_SYNC.md](../../.github/MONOREPO_SYNC.md) for detailed setup instructions.

## Benefits

✅ **HACS Compatible**: Direct repository support, no zip files  
✅ **Automatic Sync**: No manual steps required  
✅ **Single Source of Truth**: All development in monorepo  
✅ **Clean Separation**: Each integration has its own repository  
✅ **Scalable**: Easy to add more integrations  

## Troubleshooting

### Sub-repository not updating

- Check GitHub Actions workflow status
- Verify `RELEASE_TOKEN` secret exists and has correct permissions
- Check workflow logs for errors

### HACS can't find integration

- Verify sub-repository exists: `https://github.com/chatondearu/myrabelle-hacs-cover-manager`
- Check repository is public
- Ensure `hacs.json` is at repository root
- Verify `custom_components/cover_manager/` structure is correct

### Sync workflow fails

- Check PAT permissions (needs `Contents: Read and write`)
- Verify sub-repository name matches workflow configuration
- Check if sub-repository exists on GitHub
