# Cookbook

Real-world recipes and patterns for common development tasks in litestar-pydotorg.

## Overview

This cookbook contains practical, copy-paste-ready code examples for implementing common features. Each recipe is self-contained and can be adapted to your specific needs.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Domain Patterns
:link: domain-patterns
:link-type: doc

Create new domains with services, controllers, and models.
:::

:::{grid-item-card} Authentication
:link: authentication-recipes
:link-type: doc

Common authentication patterns and use cases.
:::

:::{grid-item-card} Database
:link: database-recipes
:link-type: doc

Query patterns, transactions, and optimizations.
:::

:::{grid-item-card} Testing
:link: testing-recipes
:link-type: doc

Test fixtures, mocking, and integration testing.
:::
::::

## Recipe Categories

### Domain Development

- [Domain Patterns](domain-patterns.md) - Create new business domains
- [Service Layer](service-patterns.md) - Business logic patterns
- [Controller Patterns](controller-patterns.md) - HTTP endpoint patterns

### Data Access

- [Database Recipes](database-recipes.md) - Query and transaction patterns
- [Caching Recipes](caching-recipes.md) - Redis caching strategies

### Authentication & Authorization

- [Authentication Recipes](authentication-recipes.md) - Auth flows and patterns
- [Authorization Patterns](authorization-patterns.md) - Guard and permission patterns

### Testing

- [Testing Recipes](testing-recipes.md) - Common test patterns

### Background Tasks

- [Task Recipes](task-recipes.md) - Background job patterns

```{toctree}
:maxdepth: 2
:hidden:

domain-patterns
authentication-recipes
database-recipes
testing-recipes
```
