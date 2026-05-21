"""
cli.app.app_setup
~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
from typing import Optional

import pathlib
import click

import fritz
from cli.app import app_files
from cli.app import android
from cli.app import ios
from cli import fritz_object_selector
from cli import print_utils


@click.command()
@click.argument(
    "root", required=False, type=pathlib.Path, default=str(pathlib.Path.cwd())
)
def setup(root):
    """Connecting an existing mobile app to Fritz.

    Args:
        root: root of app directory.
    """
    android_files = list(root.rglob("AndroidManifest.xml"))
    ios_files = list(root.rglob("Info.plist"))
    if android_files and ios_files:
        raise fritz.errors.FritzError(
            "Found iOS and Android projects. Please specify a directory"
            " with only an iOS or Android project"
        )
    if android_files:
        app_config = android.AndroidConfig.load(root)
        platform = "Android"
        build_snippets = android.code_snippets
    elif ios_files:
        platform = "iOS"
        app_config = ios.IOSConfig.load(root)
        build_snippets = ios.code_snippets

    print_utils.ack(
        "Connecting an {platform} app to Fritz.\n".format(platform=platform)
    )
    print_utils.message(
        "Loading {platform} configuration from {root}\n".format(
            platform=platform, root=root
        )
    )
    print_utils.notice("Successfully loaded app configuration")
    print_utils.notice(app_config.summary())

    app = get_fritz_app(app_config)
    code_snippets = build_snippets(app_config, app)

    app_files.update(code_snippets)


def _get_app_from_config(app_config) -> Optional[fritz.App]:
    """Load app from app_config.

    Args:
        app_config: App configuration.

    Returns: App matching current config or None
    """
    apps = fritz.App.list(
        apk_id=app_config.package_name,
        platform=app_config.platform,
        app_api_key=app_config.fritz_api_key,
        all_projects=True,
    )
    if not apps:
        return None

    if len(apps) > 1:
        print_utils.warn("Found more than one app, taking first")

    return apps[0]


def _choose_app_from_matching_apk_id(app_config) -> Optional[fritz.App]:
    """Choose an app that matches the APK ID from any project.

    When creating an app, the apk may exist in any of your projects. If it does
    this gives you the opportunity to an existing app, rather than creating a
    new one.

    Args:
        app_config: App configuration.
    """
    apps = fritz.App.list(
        apk_id=app_config.package_name, platform=app_config.platform, all_projects=True,
    )

    if not apps:
        return None

    app = fritz_object_selector.choose_app(apps, include_none=True)
    return app


def _configure_app(details: dict) -> dict:
    """Configure values from data needed to create an app.

    Args:
        details: Dict of values to pass to app creation.

    Returns: Updated details.
    """
    project = fritz.Project.get(project_id=details["project_id"])
    summary = {
        "App Name": details["app_name"],
        "APK ID": details["apk_id"],
        "Project Name": project.name,
    }

    lines = []
    max_name = max(len(name) for name, _ in summary.items())
    for name, value in summary.items():
        row_fmt = "  {name:%s}: {value}" % (max_name + 2)
        lines.append(row_fmt.format(name=name, value=value))

    summary = "\n".join(lines)
    print_utils.ack("Your app will be created with the following details:\n")
    print_utils.notice("App Summary")
    print_utils.notice(summary)

    if click.confirm("\nModify App Name or Project?", default=False):
        details["app_name"] = click.prompt(
            "App Name", default=details["app_name"], show_default=True
        )
        projects = fritz.Project.list()

        if len(projects) > 1 and click.confirm(
            "Choose a different project?", default=False
        ):
            project = fritz_object_selector.choose_project(projects)
            details["project_id"] = project.id

        return _configure_app(details)

    return details


def _create_app(app_config) -> fritz.App:
    """Create fritz app from app config.

    Args:
        app_config: App configuration.

    Returns: Created Fritz app.
    """
    project = fritz.Project.get()
    details = {
        "app_name": app_config.app_name,
        "apk_id": app_config.package_name,
        "platform": app_config.platform,
        "project_id": project.id,
    }

    _configure_app(details)

    return fritz.App.create(
        app_name=details["app_name"],
        apk_id=details["apk_id"],
        platform=details["platform"],
        project_id=details["project_id"],
    )


def get_fritz_app(app_config) -> fritz.App:
    """Steps needed to choose the fritz app to connect to project.

    Args:
        app_config: App configuration

    Returns: App that will be used for setup.
    """
    app = None
    if app_config.fritz_api_key:
        app = _get_app_from_config(app_config)

    if not app and app_config.fritz_api_key:
        print_utils.warn(
            "Fritz API Key found, but no app with matching "
            "API Key found connected to your account."
        )

    if not app:
        print_utils.message("Checking for other apps with matching apk id.\n")
        app = _choose_app_from_matching_apk_id(app_config)
        if app:
            return app

    if not app:
        print_utils.ack("\nNo matching apps found.\n")
        app = _create_app(app_config)

    return app
