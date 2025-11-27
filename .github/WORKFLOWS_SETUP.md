# GitHub Actions Workflows - Setup Guide

This document provides a quick start guide for the GitHub Actions CI/CD workflows.

## Quick Setup Checklist

### 1. Repository Settings

#### Enable GitHub Actions
- Go to Settings > Actions > General
- Set "Actions permissions" to "Allow all actions and reusable workflows"
- Set "Workflow permissions" to "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"

#### Enable GitHub Pages (for documentation)
- Go to Settings > Pages
- Source: Deploy from a branch
- Branch: `gh-pages` / `root`
- Save

### 2. Required Secrets

Navigate to Settings > Secrets and variables > Actions

#### Repository Secrets

| Secret Name | Required? | Used By | How to Get |
|-------------|-----------|---------|------------|
| `CODECOV_TOKEN` | Optional | ci.yml | Sign up at [codecov.io](https://codecov.io), add repo, copy token |

#### Environment Secrets (for releases)

Create environment: Settings > Environments > New environment

**Environment:** `pypi`
- Protection rules: Require reviewers (recommended)
- Add secret: `PYPI_TOKEN`
  - Get from [PyPI Account Settings](https://pypi.org/manage/account/token/)
  - Scope: "Entire account" or specific to "litestar-pydotorg"

### 3. Branch Protection Rules

Configure for `main` branch: Settings > Branches > Add rule

```yaml
Branch name pattern: main

Settings:
  ✅ Require a pull request before merging
    - Require approvals: 1
    - Dismiss stale reviews
  ✅ Require status checks to pass before merging
    - Require branches to be up to date
    Required checks:
      - Lint (Ruff)
      - Type Check (ty)
      - Unit Tests
      - Integration Tests
      - Test Coverage
      - Frontend Build
      - All Checks Passed
  ✅ Require conversation resolution before merging
  ✅ Require linear history
  ✅ Include administrators
  ⚠️ Do not allow bypassing the above settings
  ⚠️ Do not allow force pushes
  ⚠️ Do not allow deletions
```

### 4. Labels Setup

Create these labels: Settings > Issues > Labels

| Label | Color | Description |
|-------|-------|-------------|
| `backend` | `#0052CC` | Python backend changes |
| `frontend` | `#F1C40F` | JavaScript/CSS/UI changes |
| `database` | `#9B59B6` | Database schema or migrations |
| `tests` | `#2ECC71` | Test file changes |
| `documentation` | `#3498DB` | Documentation updates |
| `ci` | `#E67E22` | CI/CD workflow changes |
| `dependencies` | `#E74C3C` | Dependency updates |
| `config` | `#95A5A6` | Configuration changes |
| `python` | `#3776AB` | Python specific |
| `github-actions` | `#2088FF` | GitHub Actions updates |
| `docker` | `#2496ED` | Docker related changes |

Or use this bulk create script:

```bash
gh label create backend -c 0052CC -d "Python backend changes"
gh label create frontend -c F1C40F -d "JavaScript/CSS/UI changes"
gh label create database -c 9B59B6 -d "Database schema or migrations"
gh label create tests -c 2ECC71 -d "Test file changes"
gh label create documentation -c 3498DB -d "Documentation updates"
gh label create ci -c E67E22 -d "CI/CD workflow changes"
gh label create dependencies -c E74C3C -d "Dependency updates"
gh label create config -c 95A5A6 -d "Configuration changes"
gh label create python -c 3776AB -d "Python specific"
gh label create github-actions -c 2088FF -d "GitHub Actions updates"
gh label create docker -c 2496ED -d "Docker related changes"
```

### 5. Enable Dependabot

Settings > Code security and analysis

- ✅ Dependency graph (should be enabled by default)
- ✅ Dependabot alerts
- ✅ Dependabot security updates
- ✅ Grouped security updates

Dependabot will now:
- Create weekly PRs for dependency updates
- Auto-update GitHub Actions versions
- Update Docker base images
- Manage Python, NPM, and pip dependencies

### 6. CodeQL Setup

Settings > Code security and analysis

- ✅ CodeQL analysis
  - Configure: Default (or Advanced if customization needed)
  - Languages: Python, JavaScript (auto-detected)

The workflow is already configured in `.github/workflows/codeql.yml`

### 7. Verify Workflows

After pushing workflows to main:

```bash
# Check workflow status
gh workflow list

# View workflow runs
gh run list

# Trigger a test run
gh workflow run ci.yml
```

## Testing Before Merge

### Local Validation

1. **Install act** (optional, for local testing):
   ```bash
   brew install act  # macOS
   # or
   curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
   ```

2. **Test workflows locally**:
   ```bash
   # Lint check
   act -j lint -W .github/workflows/ci.yml

   # Type check
   act -j type-check -W .github/workflows/ci.yml
   ```

### Create Test PR

1. Create a feature branch with workflows:
   ```bash
   make worktree NAME=ci-setup
   cd ../.worktrees/litestar-pydotorg/ci-setup

   # Make a trivial change to trigger workflows
   echo "# Test" >> README.md
   git add .github/ README.md
   git commit -m "ci: add GitHub Actions workflows"
   git push -u origin ci-setup
   ```

2. Create PR and observe workflow runs
3. Fix any issues before merging

## First Release

When ready to publish the first release:

1. **Update version in pyproject.toml**:
   ```bash
   # Edit pyproject.toml, set version = "1.0.0"
   git add pyproject.toml
   git commit -m "chore(version): bump to 1.0.0"
   git push
   ```

2. **Create and push tag**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. **Monitor release workflow**:
   - Go to Actions tab
   - Watch "Release" workflow
   - Approve PyPI deployment (if environment protection enabled)

4. **Verify release**:
   - Check GitHub Releases page
   - Verify Docker image: `docker pull ghcr.io/jacobcoffee/litestar-pydotorg:v1.0.0`
   - Check PyPI: https://pypi.org/project/litestar-pydotorg/

## Workflow Monitoring

### Dashboard Access

- **Actions Tab**: See all workflow runs
- **Security Tab > Code scanning**: CodeQL results
- **Security Tab > Dependabot**: Dependency alerts
- **Insights > Dependency graph**: Dependency tree
- **Codecov**: https://app.codecov.io/gh/JacobCoffee/litestar-pydotorg

### Common Issues

#### "Codecov upload failed"
- Add `CODECOV_TOKEN` to repository secrets
- Or remove Codecov step from ci.yml (line 276-282)

#### "Docker rate limit exceeded"
- Authenticate Docker Hub in workflow
- Or use GitHub Container Registry exclusively

#### "PyPI upload failed"
- Check `PYPI_TOKEN` in `pypi` environment
- Verify token has correct scope
- Ensure version hasn't been published before

#### "Tests fail in CI but pass locally"
- Check service container connectivity
- Review environment variables
- Ensure database migrations run
- Check for test isolation issues

## Customization

### Adjust Test Parallelism

In `ci.yml`, enable parallel test execution:

```yaml
- name: Run unit tests
  run: uv run pytest tests/unit -v -n auto  # Add -n auto
```

### Change Python Versions

Update matrix in `ci.yml`:

```yaml
strategy:
  matrix:
    python-version: ["3.13", "3.14"]  # Test multiple versions
```

### Modify Coverage Threshold

In `pyproject.toml`:

```toml
[tool.coverage.report]
fail_under = 75  # Increase to 80, 90, etc.
```

### Disable E2E Tests

Comment out or remove the `test-e2e` job in `ci.yml` if Playwright tests are slow or unstable.

## Maintenance

### Weekly Tasks

- Review Dependabot PRs
- Check failed workflow runs
- Monitor CodeQL security alerts
- Review test coverage trends

### Monthly Tasks

- Update workflow actions versions
- Review and optimize caching strategy
- Audit branch protection rules
- Check Codecov dashboard for trends

## Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [UV Documentation](https://docs.astral.sh/uv/)
- [Workflow README](workflows/README.md)
- [Codecov Setup](https://docs.codecov.com/docs)

## Support

For workflow issues:
1. Check workflow logs in Actions tab
2. Review [Troubleshooting](workflows/README.md#troubleshooting) section
3. Open issue with workflow run URL
