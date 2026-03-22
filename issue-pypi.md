# Create PyPI Distribution for wiki-cli

## Summary

Create a PyPI distribution for `wiki-cli` to enable easy installation via `pip install wiki-cli` and `pipx install wiki-cli`.

## Motivation

Currently, users must either:

- Clone the repository and install manually
- Use the install script (which clones and installs from git)
- Use `uvx wiki-cli` (requires UV installed)

A PyPI distribution would allow:

```bash
pip install wiki-cli          # Standard installation
pipx install wiki-cli         # Isolated CLI installation
uv pip install wiki-cli        # UV alternative
```

This aligns with how users expect to install Python CLI tools and removes friction for new users.

## Current State

- Package is configured in `pyproject.toml` with proper metadata
- Dependencies: click, httpx, rich, beautifulsoup4
- Entry point: `wiki` command
- Version: Currently managed in `wiki_cli/__version__.py`

## Implementation Steps

1. Create PyPI account (if not already exists)
2. Configure PyPI token in repository secrets (`PYPI_API_TOKEN`)
3. Create GitHub workflow for automated publishing on commits to main
4. Configure workflow to create GitHub releases
5. Add PyPI badge to README.md

## Release Process

The workflow should handle the following automatically:

1. **Version Detection**: Extract version from git tags (e.g., `v0.1.0` or `0.1.0`)
2. **Run Tests**: Verify all tests pass before publishing
3. **Build Package**: Use `uv build` to create distribution
4. **Create GitHub Release**: Tag and create release with release notes
5. **Publish to PyPI**: Upload distribution using trusted publishing (OIDC)

### Example Workflow Structure

```yaml
jobs:
  tests:
    # Run tests on multiple Python versions
    - python: ["3.10", "3.11", "3.12"]

  build:
    needs: [tests]
    steps:
      - uses: actions/checkout@v4
      - run: uv build # Builds dist/
      - upload: dist/ # Upload artifact

  release:
    needs: [build]
    # Creates git tag and GitHub release

  pypi-publish:
    needs: [release]
    # Uses trusted publishing (OIDC)
```

### Key Implementation Details

- **Version Source**: Git tags via `git describe` or similar
- **Trusted Publishing**: Configure PyPI project with GitHub Actions OIDC
- **Release Creation**: Use `softprops/action-gh-release` or `ncipollo/release-action`
- **Artifact Sharing**: Upload `dist/` in build job, download in release/publish jobs

## Acceptance Criteria

- [ ] GitHub workflow exists at `.github/workflows/publish.yml` (or similar)
- [ ] Workflow triggers automatically on commits to `main`
- [ ] Workflow publishes package to PyPI on each release
- [ ] GitHub release is created with appropriate version tag
- [ ] `pip install wiki-cli` successfully installs the package
- [ ] README.md includes PyPI badge

## Verification

After publishing:

- `pip install wiki-cli` installs the package
- `wiki --version` shows version
- CLI works as expected

## References

- [PyPI](https://pypi.org/)
- [Publishing to PyPI](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [uv publish](https://docs.astral.sh/uv/reference/cli/#uv-publish)
- [Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/)
- [PyPI GitHub Action](https://github.com/marketplace/actions/pypi-publish)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)
