# HACS Setup for Cover Manager

## Problem Statement

Cover Manager is located in `packages/cover-manager/custom_components/cover_manager/`, but HACS expects custom components either:
1. At the repository root: `custom_components/cover_manager/`
2. In a GitHub release zip file with the correct structure

## Solution: Use GitHub Releases

Since this is a monorepo containing multiple components (blueprints + custom components), we use **GitHub releases with zip files** for HACS installation.

### How It Works

1. **Release Tag**: When a tag like `cover-manager-v1.0.0` is pushed, GitHub Actions creates a release
2. **Zip Creation**: The workflow creates `cover_manager.zip` containing:
   ```
   cover_manager.zip
   └── custom_components/
       └── cover_manager/
           ├── __init__.py
           ├── manifest.json
           └── ...
   ```
3. **HACS Download**: HACS downloads the zip from the GitHub release
4. **Installation**: HACS extracts the zip to `<config>/custom_components/cover_manager/`

### Configuration

The `hacs.json` file is configured with:
- `zip_release: true` - Tells HACS to use zip releases
- `filename: cover_manager.zip` - Specifies the zip filename
- `content_in_root: false` - The zip contains `custom_components/` folder

### Creating a Release

To create a new release for Cover Manager:

```bash
# Create and push a tag
git tag cover-manager-v1.0.0
git push origin cover-manager-v1.0.0
```

The GitHub Actions workflow will:
1. Create the zip file with correct structure
2. Create a GitHub release
3. Attach the zip file to the release

### Alternative: Repository Structure

If you want HACS to work directly from the repository (without releases), you would need to:

1. **Option A**: Create a separate repository for Cover Manager
   - Repository: `cover-manager-ha` (or similar)
   - Structure: `custom_components/cover_manager/` at root
   - HACS URL: `https://github.com/chatondearu/cover-manager-ha`

2. **Option B**: Move custom component to repository root
   - Move `packages/cover-manager/custom_components/` to repository root
   - Update all paths and workflows
   - **Not recommended** - breaks monorepo structure

## Current Implementation

✅ **Using GitHub Releases** (recommended for monorepos)
- Maintains clean monorepo structure
- Allows multiple components in one repository
- HACS downloads from releases automatically

## Verification

To verify the release zip structure:

```bash
# After creating a release, download and check
unzip -l cover_manager.zip

# Should show:
# custom_components/cover_manager/__init__.py
# custom_components/cover_manager/manifest.json
# etc.
```

## Troubleshooting

### HACS can't find Cover Manager

1. **Check Release Exists**: Verify a release with tag `cover-manager-v*` exists
2. **Check Zip File**: Verify `cover_manager.zip` is attached to the release
3. **Check Zip Structure**: Unzip and verify `custom_components/cover_manager/` structure
4. **Check hacs.json**: Verify it's in `packages/cover-manager/hacs.json` (HACS will find it in the zip)

### Zip Structure Incorrect

If the zip doesn't have the correct structure, check the workflow:
- The zip should be created from `packages/cover-manager/` directory
- The command should be: `zip -r cover_manager.zip custom_components/cover_manager`
- This creates: `custom_components/cover_manager/...` in the zip

## Best Practices

For monorepos with multiple HACS components:
- Use separate release tags for each component
- Use descriptive zip filenames
- Keep `hacs.json` in each component's directory
- Document the release process
