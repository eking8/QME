"""
cli.project
~~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""

import click
import fritz
from cli import print_utils
from cli import fritz_object_selector
from cli.config import update_config
from cli import click_utils

# pylint: disable=invalid-name
pass_project = click_utils.make_pass_decorator(fritz.Project)


@click.command()
def projects():
    """List all Projects for current account."""
    row_format = [
        ("name", "{name:%s}", "Project Name"),
        ("created", "{created:%s}", "Created"),
        ("project_id", "{project_id:%s}", "Project ID"),
    ]
    rows = []

    projects = fritz.Project.list()
    projects_name = print_utils.make_plural(len(projects), "project")
    print_utils.notice(
        "\n {num_projects} {projects_name}\n".format(
            num_projects=len(projects), projects_name=projects_name
        )
    )

    for project in projects:
        row = {
            "name": project.name,
            "created": project.created_date,
            "project_id": project.id,
        }
        rows.append(row)

    rows.sort(key=lambda x: x["created"], reverse=True)
    print_utils.formatted_table(row_format, rows)


@click.group(
    cls=click_utils.OptionalArgumentGroup,
    invoke_without_command=True,
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
)
@click.argument("project-id", required=False)
@click.pass_context
def project(ctx, project_id=None):
    """Commands for working with Fritz Projects."""

    if project_id:
        ctx.obj = fritz.Project.get(project_id=project_id)

    if ctx.obj and not ctx.invoked_subcommand:
        ctx.invoke(details)
        click.echo("")
        click.echo(ctx.command.get_help(ctx))
        return

    if not ctx.obj and not ctx.invoked_subcommand:
        click.echo(ctx.command.get_help(ctx))
        return


@project.command()
@pass_project
def details(project):
    """Get details of project.

    Args:
        id: Optional Project ID. If not specified, will use project ID
            specified in Fritz Config.
    """
    project.summary()


@project.command()
@click.argument("project_id", required=False)
def set_active(project_id):
    """Set Project ID as the active project in fritz config."""
    if project_id:
        update_config(project_id=project_id)
        return

    projects = fritz.Project.list()
    projects_name = print_utils.make_plural(len(projects), "project")
    print_utils.notice(
        "\n {num_projects} {projects_name}\n".format(
            num_projects=len(projects), projects_name=projects_name
        )
    )
    project = fritz_object_selector.choose_project(projects)
    update_config(project_id=project.id)
