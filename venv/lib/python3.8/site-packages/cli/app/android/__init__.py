"""
This module contains the code for setting up an Android app.
"""
import fritz
from cli.app.android.android_config import AndroidConfig
from cli.app.android import android_snippets


def code_snippets(app_config: AndroidConfig, app: fritz.App):
    """Load all code snippets.

    Args:
        app_config: Android config
        app: App to connect Android project to.

    Returns: List of code snippets.
    """
    snippets = [
        android_snippets.FritzCustomModelServiceSnippet,
        android_snippets.InternetPermissionsSnippet,
        android_snippets.ImportFritzSnippet,
        android_snippets.ConfigureFritzSnippet,
        android_snippets.AddBuildDependencies,
        android_snippets.AddProjectBuildDependencies,
        android_snippets.AddRenderscript,
    ]
    return [snippet(app_config, app) for snippet in snippets]
