"""
Fritz is a library to simplify your mobile machine learning workflow.

usage:
   >>> import fritz
   >>> fritz.configure(api_key="<api_key>", project_id="<project_id>")
   >>> version = fritz.ModelVersion.get("<model_version_id>")
   >>> benchmark = version.benchmark()
   >>> benchmark.summary()
       ------------------------
       Fritz Model Grade Report
       ------------------------
       Core ML Compatible:              True
       Predicted Runtime (iPhone X):    31.4 ms (31.9 fps)
       Total MFLOPS:                    686.90
       Total Parameters:                1,258,580


:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
# pylint: disable=invalid-name
from fritz.api_resources import *  # noqa

from fritz import frameworks  # noqa


# Configuration Variables
api_key = None
project_id = None
api_base = "https://api.fritz.ai/client/v1"


def configure(**kwargs):
    """Sets Fritz configuration variables.

    If no variables are passed, the function will attempt to load configuration
    variables from a ~/.fritz file.

    To configure this file, run `fritz config` from the command line.

    Args:
        api_key (str): Client API Key used to authenticate requests to Fritz.
        project_id (str): Project ID to store models in.
        api_base (str): Base URL of Fritz API
    """
    # pylint: disable=global-statement
    global api_key, project_id, api_base
    if not kwargs:
        # If no kwargs are passed, attempt to initialize from ~/.fritz file.
        from fritz import configuration

        configuration.init_config()
        return

    api_key = kwargs.get("api_key") or api_key
    project_id = kwargs.get("project_id") or project_id
    api_base = kwargs.get("api_base") or api_base


def reset_configuration():
    """Resets Fritz configuration variables."""
    # pylint: disable=global-statement
    global api_key, project_id, api_base
    api_key = None
    project_id = None
    api_base = None
