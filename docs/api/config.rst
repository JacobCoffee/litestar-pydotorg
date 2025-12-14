Configuration
=============

Application configuration and settings management.

.. module:: pydotorg.config

Module Contents
---------------

.. automodule:: pydotorg.config
   :members:
   :undoc-members:
   :show-inheritance:

Configuration Classes
---------------------

The application uses Pydantic settings for configuration management:

- **AppConfig** - Main application settings
- **DatabaseConfig** - Database connection settings
- **RedisConfig** - Redis connection settings
- **AuthConfig** - Authentication settings
- **EmailConfig** - Email sending settings

Environment Variables
---------------------

Configuration is loaded from environment variables and ``.env`` files.
See the project's ``.env.example`` for available settings.
