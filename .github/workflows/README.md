# GitHub Actions Workflows

This directory contains the CI/CD workflows for the litestar-pydotorg project.

## Workflows

### ci.yml - Continuous Integration
**Triggers:** Push to main, Pull Requests

The main CI pipeline that runs on every push and PR:

- **Lint**: Runs Ruff linting and format checks + codespell
- **Type Check**: Runs ty type checker on source code
- **Unit Tests**: Fast tests with no external dependencies
- **Integration Tests**: Tests with PostgreSQL and Redis services
- **E2E Tests**: Playwright browser tests
- **Coverage**: Generates test coverage reports and uploads to Codecov
- **Frontend**: Builds Vite assets and TailwindCSS

**Required Checks:** All jobs must pass before merging

**Environment Variables:**
- `CODECOV_TOKEN`: Required for coverage upload (set in repository secrets)

### docker.yml - Docker Build & Publish
**Triggers:** Push to main, PR, Releases

Builds and publishes Docker images:

- **Build**: Multi-platform build (amd64, arm64) with caching
- **Test Image**: Validates Docker image health check (PR only)
- **Security Scan**: Trivy vulnerability scanning
- **Publish Release**: Tags and pushes release images

**Registry:** GitHub Container Registry (ghcr.io)

**Image Tags:**
- `latest` - Latest main branch build
- `main` - Main branch builds
- `pr-<number>` - Pull request builds
- `v*.*.*` - Semantic version tags
- `<branch>-<sha>` - Branch + commit SHA

### docs.yml - Documentation
**Triggers:** Push to main, Pull Requests

Builds and deploys Sphinx documentation:

- **Build**: Generates HTML docs and changelog
- **Link Check**: Validates external links (non-blocking)
- **Deploy**: Deploys to GitHub Pages (main only)

**Deployment:** https://jacobcoffee.github.io/litestar-pydotorg

### codeql.yml - Security Scanning
**Triggers:** Push to main, PR, Weekly schedule (Mondays 6am)

CodeQL security analysis:

- Scans Python and JavaScript code
- Runs security-extended queries
- Results appear in Security tab

### labeler.yml - PR Auto-Labeler
**Triggers:** PR open, sync, reopen

Automatically labels PRs based on changed files:

- `backend` - Python source changes
- `frontend` - JavaScript/CSS/asset changes
- `database` - Migration or DB code changes
- `tests` - Test file changes
- `documentation` - Docs and markdown changes
- `ci` - Workflow or Docker changes
- `dependencies` - Lock file or manifest changes
- `config` - Configuration file changes

### release.yml - Release Automation
**Triggers:** Version tags (v*.*.*)

Automates the release process:

1. **Validate**: Checks tag format and version consistency
2. **Build**: Creates Python distribution packages
3. **Create Release**: Generates GitHub release with changelog
4. **Publish PyPI**: Uploads to PyPI (requires environment approval)

**Tag Format:** `v1.0.0` (semantic versioning)

**Requirements:**
- Tag version must match `pyproject.toml` version
- Requires `pypi` environment with PYPI_TOKEN secret

## Configuration Files

### dependabot.yml
Automated dependency updates:

- Python dependencies (weekly, Mondays 9am)
- GitHub Actions (weekly)
- NPM packages (weekly, ignoring patches)
- Docker base images (weekly)

**PR Labels:** `dependencies`, `python`, `frontend`, `github-actions`, `docker`

### labeler.yml
Configuration for PR auto-labeling based on file patterns.

## Secrets Required

| Secret | Used By | Description |
|--------|---------|-------------|
| `CODECOV_TOKEN` | ci.yml | Upload coverage to Codecov |
| `GITHUB_TOKEN` | All | Automatic token (no setup needed) |
| `PYPI_TOKEN` | release.yml | Publish to PyPI (environment secret) |

## Branch Protection Rules

Recommended settings for `main` branch:

- ✅ Require status checks before merging
  - ✅ Lint (Ruff)
  - ✅ Type Check (ty)
  - ✅ Unit Tests
  - ✅ Integration Tests
  - ✅ Coverage
  - ✅ Frontend Build
- ✅ Require branches to be up to date
- ✅ Require conversation resolution before merging
- ✅ Require linear history
- ⚠️ Do not allow force pushes
- ⚠️ Do not allow deletions

## Caching Strategy

All workflows use aggressive caching to minimize build times:

- **uv dependencies**: Cached via `astral-sh/setup-uv` with `uv.lock` key
- **Docker layers**: GitHub Actions cache (gha) mode
- **Playwright browsers**: Installed per job (considered for separate action)

## Performance Optimizations

- Parallel job execution (lint, type-check, tests run simultaneously)
- Docker multi-platform builds with layer caching
- Frontend build artifact reuse across jobs
- Dependency caching with lock file invalidation
- Service containers for integration/E2E tests

## Development

### Local Testing

Validate workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS

# Test CI workflow
act pull_request -W .github/workflows/ci.yml

# Test specific job
act -j lint -W .github/workflows/ci.yml
```

### Updating Workflows

1. Make changes in a feature branch (never on main)
2. Test locally if possible
3. Create PR - workflows will run automatically
4. Review workflow run logs in PR checks
5. Merge after approval

### Adding New Jobs

When adding new jobs to ci.yml:

1. Add job definition
2. Update `all-checks` job needs list
3. Update branch protection rules
4. Document in this README

## Troubleshooting

### Coverage Upload Fails
- Verify `CODECOV_TOKEN` is set in repository secrets
- Check Codecov service status
- Review codecov.yml configuration

### Docker Build Timeout
- Check Docker Hub rate limits
- Review build cache effectiveness
- Consider splitting multi-stage builds

### Tests Fail in CI but Pass Locally
- Check service container connectivity
- Verify environment variables
- Review database initialization timing
- Check for test isolation issues

### Frontend Build Fails
- Verify Bun installation step
- Check package.json scripts
- Review Node.js version compatibility

## Monitoring

- **Workflow Runs**: Actions tab in GitHub
- **Coverage Trends**: Codecov dashboard
- **Security Alerts**: Security tab > Code scanning
- **Dependency Updates**: Pull Requests from Dependabot

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [UV Documentation](https://docs.astral.sh/uv/)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Codecov Documentation](https://docs.codecov.com/)
