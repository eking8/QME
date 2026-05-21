"""
cli.app.code_snippet

Base class for CodeSnippets.
"""

from fritz import errors


class CodeSnippet(object):
    """Defines a block of code to update. """

    def __init__(self, app_config, app):
        self.app_config = app_config
        self.app = app

    def __str__(self):
        return self.__class__.__name__

    @property
    def is_added(self):
        """Returns True if code snippet has been added."""
        raise NotImplementedError

    @property
    def is_updated(self):
        """Returns True if added code snippet is up to date."""
        # override if can be updated.
        return True

    def add(self):
        """Add code snippet."""
        raise NotImplementedError

    def update(self):
        """Update existing code snippet."""


class SnippetExecutionError(errors.FritzError):
    """Error executing snippet."""
