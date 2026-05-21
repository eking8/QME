"""Shared methods for app setup."""

import click
import fritz
from cli import print_utils


def pause_confirmation():
    """Pause flow until the user finishes the previous step"""

    click.confirm("\nContinue? Press any key", default="y", show_default=False)


def setup_app_info(app_name, package_name, platform):
    """Create the app automatically

    Args:
        app_name
        package_name
        platform

    Returns:
        the newly created app from the api.
    """

    app_name = click.prompt(
        "Please enter the name of your app", default=app_name, show_default=True,
    )
    while not app_name:
        app_name = click.prompt(
            "Please enter the name of your app", default=app_name, show_default=True,
        )

    package_name = click.prompt(
        "Please enter the package name of your app",
        default=package_name,
        show_default=True,
    )
    while not package_name:
        package_name = click.prompt(
            "Please enter the package name of your app",
            default=package_name,
            show_default=True,
        )
    response = fritz.App.create(
        api_key=fritz.api_key,
        app_name=app_name,
        apk_id=package_name,
        platform=platform,
    )

    print_utils.ack(
        "\n{app_name} ({package_name}) created successfully!".format(
            app_name=app_name, package_name=package_name
        )
    )

    return response
