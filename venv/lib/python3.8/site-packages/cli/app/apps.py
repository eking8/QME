"""
cli.app.apps
~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
import os

import click

import fritz

from cli.app import app_setup
from cli import print_utils
from cli import click_utils

# pylint: disable=invalid-name
pass_app = click_utils.make_pass_decorator(fritz.App)


@click.command()
@click.option("--project-id", help="Restrict results to specific project.")
@click.option("--apk-id", help="Restrict results to APK ID or Bundle ID.")
@click.option("--platform", help="Restrict results to specific platform.")
@click.option("--all-projects", is_flag=True, help="Return results from all projects")
def apps(project_id=None, apk_id=None, platform=None, all_projects=False):
    """List all apps."""
    click.echo("")
    apps = fritz.App.list(
        project_id=project_id,
        apk_id=apk_id,
        platform=platform,
        all_projects=all_projects,
    )
    if all_projects:
        project_message = "all projects."
    else:
        project = fritz.Project.get(project_id or fritz.project_id)
        project_message = "{project_name} project.".format(project_name=project.name)

    apps_name = print_utils.make_plural(len(apps), "app")
    print_utils.notice(
        "{num_apps} {apps_name} in {project_message}\n".format(
            num_apps=len(apps), apps_name=apps_name, project_message=project_message,
        )
    )

    row_format = [
        ("name", "{name:%s}", "App Name"),
        ("apk_id", "{apk_id:%s}", "APK ID"),
        ("platform", "{platform:%s}", "Platform"),
        ("created", "{created:%s}", "Created"),
        ("project_name", "{project_name:%s}", "Project Name"),
        ("api_key", "{api_key:%s}", "API Key"),
        ("app_id", "{app_id:%s}", "App ID"),
    ]
    rows = []
    projects = {}
    for app in apps:
        project = projects.setdefault(
            app.project_id, fritz.Project.get(project_id=app.project_id)
        )
        row = {
            "name": app.app_name,
            "apk_id": app.apk_id,
            "platform": app.platform,
            "created": app.created_date,
            "project_name": project.name,
            "api_key": app.api_key,
            "app_id": app.id,
        }
        rows.append(row)

    rows.sort(key=lambda x: x["created"], reverse=True)
    print_utils.formatted_table(row_format, rows)


@click.group(
    cls=click_utils.OptionalArgumentGroup,
    invoke_without_command=True,
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
)
@click.argument("app-id", required=False)
@click.pass_context
def app(ctx, app_id=None):
    """Commands for working with Fritz Apps.

    Args:
        app_id: App ID to query.
    """

    if app_id:
        ctx.obj = fritz.App.get(app_id=app_id)

    if ctx.obj and not ctx.invoked_subcommand:
        ctx.invoke(details)
        click.echo("")
        click.echo(ctx.command.get_help(ctx))
        return

    if not ctx.obj and not ctx.invoked_subcommand:
        click.echo(ctx.command.get_help(ctx))
        return


app.add_command(app_setup.setup)


@app.command()
@pass_app
def details(app):
    """Get details of a specific app."""
    print_utils.message(app.summary())


@app.group()
def pod():
    """Commands for working with Fritz cocoapods."""


@pod.command()
@click.option("--clean", is_flag=True)
def install(clean):
    """Install the Fritz Cocoapod.

    Args:
        clean (bool): if present, delete cached cocoapods and update the
            repo as well.
    """
    commands = []
    if clean:
        commands.extend(
            [
                "pod repo update --verbose",
                "pod clean --verbose",
                "pod cache clean --all --verbose",
            ]
        )
    commands.append("pod install --verbose")
    for command in commands:
        print(command)
        os.system(command)
