"""
cli.app.android.android_helpers

Helper methods for parsing various values from Android project.
"""

from typing import Optional
import re
from xml.etree import ElementTree
import pathlib


def _get_app_label(android_manifest_path: pathlib.Path) -> str:
    tree = ElementTree.parse(str(android_manifest_path))
    root = tree.getroot()
    application_node = root.find("application")
    app_label = application_node.get(
        "{http://schemas.android.com/apk/res/android}label"
    )
    return app_label


def _get_app_name_from_strings(root: pathlib.Path, app_label: str) -> Optional[str]:

    label_key = app_label.split("@string/")[1]
    paths = root.rglob("**/src/main/res/values/strings.xml")

    for string_path in paths:
        tree_string = ElementTree.parse(str(string_path))
        root_string = tree_string.getroot()
        string_nodes = root_string.findall("string")

        for string_node in string_nodes:
            if string_node.get("name") == label_key:
                return string_node.text

    return None


def find_app_name(
    root: pathlib.Path, android_manifest_path: pathlib.Path
) -> Optional[str]:
    """Parses app name from a given android manifest file.

    Args:
        root: Root path of project.
        android_manifest_path: Path to AndroidManifest.xml file.

    Returns: App Name if found, None otherwise.
    """
    app_label = _get_app_label(android_manifest_path)
    if "@string/" not in app_label:
        return app_label

    return _get_app_name_from_strings(root, app_label)


def find_package_name(android_manifest_path: pathlib.Path) -> str:
    """Find the name of the package.

    Returns:
        package name
    """
    tree = ElementTree.parse(str(android_manifest_path))
    root = tree.getroot()
    package_name = root.get("package")
    return package_name


def find_application_id(build_path: pathlib.Path) -> str:
    """Find the application id in app/build.gradle.

    Args:
        build_path: the path to build.gradle

    Returns:
        the applicationId
    """
    for line in build_path.open():
        if "applicationId" not in line:
            continue
        matched_items = re.search(r'applicationId "(.+)"', line)
        if matched_items:
            return matched_items.groups(0)[0]

    return None


def find_fritz_api_key(main_activity_path: pathlib.Path) -> str:
    """Find the apk id.

    Returns:
        the apk id.
    """
    for line in main_activity_path.open():
        if "Fritz" not in line:
            continue
        matched_items = re.search(r'Fritz.configure\(this, "(.+)"\);', line)
        if matched_items:
            return matched_items.groups(0)[0]

    return None


def find_main_activity(android_manifest_path: pathlib.Path):
    """Find the 'MainActivity'

    Returns:
        the name of the class
    """
    tree = ElementTree.parse(str(android_manifest_path))
    root = tree.getroot()
    application_node = root.find("application")
    for activity_node in application_node.findall("activity"):
        intent_filter = activity_node.find("intent-filter")
        if intent_filter is None:
            continue
        action_node = intent_filter.find("action")
        if action_node is None:
            continue
        action_name = action_node.get(
            "{http://schemas.android.com/apk/res/android}name"
        )
        if action_name == "android.intent.action.MAIN":
            class_name = activity_node.get(
                "{http://schemas.android.com/apk/res/android}name"
            )
            return class_name.split(".")[-1]

    return None
