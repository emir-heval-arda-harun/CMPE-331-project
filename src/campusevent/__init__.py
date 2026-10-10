"""CampusEvent: a social sports-matching platform for university students.

This package currently contains only the skeleton (boilerplate) of the
system. Every service method raises ``NotImplementedError`` so that the
requirement tests under ``tests/`` fail until the features are implemented.
"""

from campusevent.app import CampusEventApp, create_app

__all__ = ["CampusEventApp", "create_app"]
