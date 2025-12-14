Feature Flags
=============

Feature flag system for controlling feature rollout.

.. module:: pydotorg.core.features

Module Contents
---------------

.. automodule:: pydotorg.core.features
   :members:
   :undoc-members:
   :show-inheritance:

Usage
-----

Feature flags allow you to control feature availability at runtime::

    from pydotorg.core.features import FeatureFlags

    if FeatureFlags.is_enabled("new_download_page"):
        # New feature code
        pass
    else:
        # Legacy code
        pass
