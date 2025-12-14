Exceptions
==========

Application exception classes and error handling.

.. module:: pydotorg.core.exceptions

Module Contents
---------------

.. automodule:: pydotorg.core.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Exception Hierarchy
-------------------

The exception hierarchy provides structured error handling:

- :class:`ApplicationError` - Base exception for all application errors
- :class:`AuthenticationError` - Authentication failures
- :class:`AuthorizationError` - Authorization/permission failures
- :class:`NotFoundError` - Resource not found errors
- :class:`ValidationError` - Input validation errors
- :class:`ConflictError` - Resource conflict errors
