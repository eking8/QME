"""
This module contains the code for setting up an Android app.
"""
import fritz
from cli.app.ios.ios_config import IOSConfig
from cli.app.ios import ios_snippets


def code_snippets(app_config: IOSConfig, app: fritz.App):
    """Load all code snippets.

    Args:
        app_config: iOS config
        app: App to connect Android project to.

    Returns: List of code snippets.
    """
    snippets = [
        ios_snippets.CreateFritzInfo,
        ios_snippets.FritzInfoXcodeProject,
        ios_snippets.FritzInfoAPIKeyUpdater,
        ios_snippets.AddFritzImport,
        ios_snippets.AddFritzConfigure,
        ios_snippets.AddPodfile,
        ios_snippets.AddFritzToPodfile,
    ]
    return [snippet(app_config, app) for snippet in snippets]
