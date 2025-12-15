Domain Modules
==============

Business domain modules implementing the core functionality of Python.org.

Each domain follows a consistent structure:

- **controllers.py** - HTTP route handlers
- **models.py** - SQLAlchemy ORM models
- **schemas.py** - Pydantic schemas for request/response
- **repositories.py** - Data access layer
- **services.py** - Business logic layer
- **dependencies.py** - Litestar dependency injection

.. toctree::
   :maxdepth: 2
   :caption: Domain Modules

   about
   admin
   banners
   blogs
   codesamples
   community
   docs
   downloads
   events
   jobs
   mailing
   minutes
   nominations
   pages
   search
   sponsors
   sqladmin
   successstories
   users
   work_groups
