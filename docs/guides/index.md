# Guides

Practical how-to guides for common development tasks in litestar-pydotorg.

## Overview

These guides are task-oriented and help you accomplish specific goals. They assume you have completed the [Getting Started](../getting-started/index.md) setup and have a basic understanding of the project.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Development
:link: development
:link-type: doc

Code standards, workflows, and development best practices.
:::

:::{grid-item-card} Feature Flags
:link: feature-flags
:link-type: doc

Configure and use feature flags for conditional functionality.
:::

:::{grid-item-card} API Usage
:link: api-usage
:link-type: doc

Work with the REST API, authentication, and rate limiting.
:::

:::{grid-item-card} Testing
:link: testing
:link-type: doc

Write and run tests for your code.
:::
::::

## Guide Categories

### Development Workflow

- [Development Guide](development.md) - Code standards, commit conventions, and workflows
- [Testing Guide](testing.md) - Unit, integration, and E2E testing
- [Debugging Guide](debugging.md) - Debug your code effectively

### API & Authentication

- [API Usage Guide](api-usage.md) - REST API usage and client SDKs
- [Authentication Guide](authentication.md) - JWT, sessions, and OAuth

### Configuration

- [Feature Flags](feature-flags.md) - Conditional functionality
- [Environment Configuration](configuration.md) - Environment variables and settings

### Deployment

- [Deployment Guide](deployment.md) - Production deployment strategies
- [Docker Guide](docker.md) - Container-based development and deployment

```{toctree}
:maxdepth: 2
:hidden:

development
feature-flags
api-usage
authentication
testing
debugging
configuration
deployment
docker
```
