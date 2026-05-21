"""
fritz.configuration
~~~~~~~~~~~~~~~~~~~

Helps manage fritz configuration.

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""

import os
from pathlib import Path
import configparser

import fritz
import fritz.errors


_HOME = str(Path.home())
CONFIG_PATH_ENV = "FRITZ_CONFIG_PATH"
FRITZ_ENV = "FRITZ_ENV"
API_KEY_ENV = "FRITZ_API_KEY"
PROJECT_ID_ENV = "FRITZ_PROJECT_ID"


if os.environ.get(CONFIG_PATH_ENV):
    CONFIG_PATH = os.environ[CONFIG_PATH_ENV]
else:
    CONFIG_PATH = os.path.join(_HOME, ".fritz")


def init_config(path=CONFIG_PATH):
    """Initializes Fritz configuration, by default checking ~/.fritz.

    If FRITZ_ENV environment variable is set, uses that section in config file.

    Args:
        path (str): Set path to override where config file is initialized from.
    """
    project_id = os.environ.get(PROJECT_ID_ENV)
    api_key = os.environ.get(API_KEY_ENV)

    if project_id and api_key:
        fritz.configure(api_key=api_key, project_id=project_id)
        return

    path = Path(path)
    if not path.exists():
        raise fritz.errors.MissingFritzConfigError(path)
    fritz_config = load_config_file(path=path)

    try:
        env = os.environ.get(FRITZ_ENV, "default")
        defaults = dict(fritz_config.items(env))
        fritz.configure(
            api_key=api_key or defaults["api_key"],
            project_id=project_id or defaults["project_id"],
            api_base=defaults.get("api_base"),
        )
    except (configparser.NoSectionError, KeyError):
        raise fritz.errors.InvalidFritzConfigError(path)


def load_config_file(path=CONFIG_PATH):
    """Loads configuration file from disk.

    Args:
        path (str): Path of config file to load.

    Returns: ConfigParser
    """
    fritz_config = configparser.ConfigParser()
    fritz_config.read(path)
    return fritz_config


def write_config_file(fritz_config, path=CONFIG_PATH):
    """Writes provide configuration file.

    Args:
        fritz_config (ConfigParser): Configuration to save.
        path (str): Path of destination config file.
    """
    fritz_config.write(open(path, "w"))


def get_credentials(fritz_config):
    """Gets credentials from config.

    Args:
        fritz_config (ConfigParser): Fritz Configuration.

    Returns: dict of credentials
    """
    env = os.environ.get("FRITZ_ENV", "default")
    return dict(fritz_config.items(env))


def update_credentials(fritz_config, **updates):
    """Updates Fritz config.

    Args:
        fritz_config (ConfigParser): Fritz Configuration.
        updates (dict): updates

    Returns: ConfigParser
    """
    env = os.environ.get("FRITZ_ENV", "default")
    try:
        defaults = get_credentials(fritz_config)
    except configparser.NoSectionError:
        defaults = {}

    defaults.update(updates)
    fritz_config[env] = defaults

    return fritz_config
