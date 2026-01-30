# Releasing paperctl

This document describes how to release a new version of paperctl.

## Release Process

### 1. Update Version Numbers

Update the version in these files:

```bash
# pyproject.toml
version = "X.Y.Z"

# src/paperctl/__init__.py
__version__ = "X.Y.Z"
```

### 2. Update CHANGELOG.md

Move items from `[Unreleased]` to a new version section:

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature

### Changed
- Changed behavior

### Fixed
- Bug fix
```

Update the links at the bottom:

```markdown
[Unreleased]: https://github.com/jwmossmoz/paperctl/compare/vX.Y.Z...HEAD
[X.Y.Z]: https://github.com/jwmossmoz/paperctl/releases/tag/vX.Y.Z
```

### 3. Update uv.lock

Run `uv sync` to update the lockfile with the new version:

```bash
uv sync --all-groups
```

### 4. Commit and Tag

```bash
git add pyproject.toml src/paperctl/__init__.py CHANGELOG.md uv.lock
git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push && git push --tags
```

### 5. Verify Release

GitHub Actions will automatically:
- Build the package
- Publish to PyPI (via trusted publishing)
- Create a GitHub Release

Check:
1. GitHub Actions: https://github.com/jwmossmoz/paperctl/actions
2. PyPI: https://pypi.org/project/paperctl/
3. GitHub Release: https://github.com/jwmossmoz/paperctl/releases

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X): Breaking API changes
- **MINOR** (Y): New features, backward compatible
- **PATCH** (Z): Bug fixes, backward compatible

## Troubleshooting

### Tag Already Exists

```bash
# Delete local tag
git tag -d vX.Y.Z

# Delete remote tag (if pushed)
git push origin :refs/tags/vX.Y.Z
```

### Release Failed

Check the GitHub Actions workflow logs for details:
https://github.com/jwmossmoz/paperctl/actions
