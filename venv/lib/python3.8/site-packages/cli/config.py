"""
cli.config
~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
import configparser
import os
from pathlib import Path
import click

from fritz import configuration
import fritz


_HOME = str(Path.home())
CONFIG_PATH = os.path.join(_HOME, ".fritz")


def update_config(path: str = CONFIG_PATH, **updates):
    """Update Fritz configuration file, creating if it does not exist.

    Args:
        path (str): Path of config file.
        updates (dict): Optional keys to update specified by CLI options.

    Return: ConfigParser
    """
    fritz_config = configuration.load_config_file(path=path)

    if updates:
        try:
            defaults = configuration.get_credentials(fritz_config)
        except configparser.NoSectionError:
            defaults = {}

        changes = []
        for key in ["api_key", "project_id"]:
            if key not in updates:
                continue

            original = defaults.get(key)
            new = updates[key]
            changes.append(
                "{key}: {original} -> {new}".format(key=key, original=original, new=new)
            )

        print("\n".join(["Updating config with provided variables.", *changes]))

        fritz_config = configuration.update_credentials(fritz_config, **updates)
        configuration.write_config_file(fritz_config, path=path)
        return fritz_config

    click.echo(
        """
    Configure the Fritz CLI.
    ------------------------

    This command will add a ~/.fritz configuration file with your API Key
    and default Project ID.

    The API Key is used to authenticate with the Fritz servers, and the
    Project ID is used to determine whcih project to use when creating and
    benchmarking new models.

    To find your API Key and Project ID, log in to Fritz (https://app.fritz.ai)
    and go to the "Training" tab in you project. Enter the listed API Key and
    Project ID in the following prompts:

    """
    )
    api_key = click.prompt("Fritz API Key", type=str)
    project_id = click.prompt("Fritz Project ID", type=str)

    updates = {"api_key": api_key, "project_id": project_id}
    configuration.update_credentials(fritz_config, **updates)
    configuration.write_config_file(fritz_config, path=path)
    return fritz_config


@click.group(invoke_without_command=True)
@click.pass_context
def config(ctx):
    """Fritz configuration settings.

    Args:
        update: Optional flag to update config file.
    """
    if ctx.invoked_subcommand is not None:
        # Don't want to run default flow if specifically trying to update.
        return

    try:
        configuration.init_config()
    except fritz.errors.InvalidFritzConfigError:
        update_config()

    message = "Fritz Configuration"
    print(message)
    print("=" * len(message))
    print("API Key: {api_key}".format(api_key=fritz.api_key))
    print("Project ID: {project_id}".format(project_id=fritz.project_id))


@config.command()
@click.option("--api-key", help="Fritz API Key", default=None)
@click.option("--project-id", help="Fritz Project ID", default=None)
def update(api_key, project_id):
    """Fritz configuration settings.

    Args:
        update: Optional flag to update config file.
    """
    updates = {"api_key": api_key, "project_id": project_id}
    updates = {key: value for key, value in updates.items() if value}
    update_config(**updates)
    fritz.configure()

    message = "Fritz Configuration"
    print(message)
    print("=" * len(message))
    print("API Key: {api_key}".format(api_key=fritz.api_key))
    print("Project ID: {project_id}".format(project_id=fritz.project_id))
