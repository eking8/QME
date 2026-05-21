"""
fritz.errors
~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
# Right now, I'm going to tie in our normal exceptions with click.
# this shouldn't affect too much? I don't love it, but the priority for
# me is showing readable errors.
import click


class FritzError(click.ClickException):
    """Generic Exception class for Fritz Errors."""

    def __init__(self, message, status_code=None):
        """
        Args:
            message (str): Error message
            status_code (Optional[int]): Status Code of response.
        """
        super().__init__(message)
        self._message = message
        self.status_code = status_code

    def __str__(self):
        return self._message or "<empty message>"

    def __repr__(self):
        cls_name = self.__class__.__name__

        return "{cls_name}(message={msg} status_code={status_code})".format(
            cls_name=cls_name, msg=self._message, status_code=self.status_code
        )


class FritzNotInitializedError(FritzError):
    """Error when Python SDK not initialized."""

    def __init__(self):
        message = (
            "`fritz.configure` not called.  Please call "
            "`fritz.configure` with your API Key and Project ID."
        )
        super().__init__(message)


class MissingFritzConfigError(FritzError):
    """Missing Fritz configuration file."""

    def __init__(self, path):
        message = """

No Fritz Configuration file exists at {path}

Please create a file at {path} with the follinwg contents.
[default]
api_key = <api_key>
project_id = <project_id>

This is easy with the Fritz CLI:

$ fritz config --api-key <api_key> --project-id <project_id>
        """
        super().__init__(message.format(path=path))


class InvalidFritzConfigError(FritzError):
    """Error when Fritz config contains invalid options."""

    def __init__(self, path):
        message = """
        Fritz configuration file at {path} contains invalid options

        Please check your Fritz configuration file at ~/.fritz.

        To update the config, run:

        $ fritz config udpate
        """
        super().__init__(message.format(path=path))


class ConnectionError(FritzError):
    """Could not not connect to server."""

    def __init__(self, path):
        message = (
            "Error connecting to path {path}. "
            "Please check your connection and try again."
        )
        super().__init__(message.format(path=path))


class ArgumentRequiredError(FritzError):
    """Argument required"""

    def __init__(self, id_name):
        message = "{id_name} argument required."
        super().__init__(message.format(id_name=id_name))


class MissingProjectFileError(FritzError):
    """Could not find expected file."""

    def __init__(self, file_name):
        message = """
        Project missing {file_name}.

        Check to make sure project root is pointing to directory containing
        your mobile app code.
        """.format(
            file_name=file_name
        )

        super().__init__(message)
