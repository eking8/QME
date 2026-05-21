"""
cli.app.ios.ios_helpers
"""

from typing import Optional
import plistlib
import pathlib
import os
from pbxproj import XcodeProject
import fritz
from cli import print_utils


def read_plist(plist_path):
    """Read plist file.

    Args:
        plist_path (str): Path to plist.

    Returns: Dict if exists and is readable, None if error encountered.
    """
    try:
        # TODO: Replace with non-deprecated method.
        # pylint: disable=deprecated-method
        plist = plistlib.readPlist(str(plist_path))
        return plist
    # pylint: disable=broad-except
    except (plistlib.InvalidFileException, Exception):
        print_utils.warn("{plist_path} does not exist".format(plist_path=plist_path))
        return None


def find_fritz_api_key(fritz_info_path: pathlib.Path) -> Optional[str]:
    """Find API key from Fritz-Info.plist file.

    Args:
        fritz_info_path: Path to Fritz-Info.plist file.

    Returns: App API Key if it exists.
    """
    plist = read_plist(fritz_info_path) or {}
    if "apiKey" in plist:
        return plist["apiKey"]

    return None


def get_app_name(xcodeproj_path: pathlib.Path) -> Optional[str]:
    """Get app name from xcodeproj path.

    Args:
        xcodeproj_path: Path to xcodeproj folder.

    Returns: App Name if found.
    """
    cmd = (
        "xcodebuild  -project {xcodeproj} -showBuildSettings | grep PRODUCT_NAME | "
        'grep -Fv "FULL_PRODUCT_NAME"'
    )
    cmd = cmd.format(xcodeproj=str(xcodeproj_path))
    product_name_line = os.popen(cmd).read()

    if not product_name_line:
        return None

    return product_name_line.split("=")[1].strip()


def get_bundle_id(xcodeproj_path: pathlib.Path) -> Optional[str]:
    """Get bundle ID form xcodeproj.

    Args:
        xcodeproj_path: Path to xcodeproj folder.

    Returns: Bundle ID if found.
    """
    cmd = (
        "xcodebuild -project {xcodeproj} -showBuildSettings | "
        "grep PRODUCT_BUNDLE_IDENTIFIER"
    )
    cmd = cmd.format(xcodeproj=str(xcodeproj_path))
    product_bundle_line = os.popen(cmd).read()
    if not product_bundle_line:
        return None

    return product_bundle_line.split("=")[1].strip()


def create_fritz_info(path: pathlib.Path, app: fritz.App):
    """Create Fritz-Info.plist file at path.

    Args:
        path: Fritz-Info.plist path.
        app: App.
    """
    data = {
        "namespace": "production",
        "apiUrl": fritz.api_base.replace("client", "sdk"),
        "apiKey": app.api_key,
    }
    # TODO: Replace with non-deprecated method.
    # pylint: disable=deprecated-method
    plistlib.writePlist(data, str(path))


def add_path_to_xcodeproj(
    project: XcodeProject, relative_path: pathlib.Path
) -> XcodeProject:
    """Adds path to xcode project file.

    Args:
        project: Project to update.
        relative_path: Relative path from root of project.

    Returns: Updated Xcode project.
    """
    parent_name = relative_path.parent.name
    if not parent_name:
        project.add_file(str(relative_path))
        return project

    groups = project.get_groups_by_name(parent_name)
    if not groups:
        project.add_file(str(relative_path))
        return project

    project.add_file(str(relative_path), parent=groups[0])
    return project


def remove_file_in_xcodeproj(project: XcodeProject, filename: str) -> XcodeProject:
    """Removes file from Xcode Project.

    Args:
        project: Project to modify.
        filename: Name of file to remove.

    Returns: Modified project.

    """
    files = project.get_files_by_name(filename)

    for file in files:
        # The remove_file_by_id function doesn't quite work, here are some
        # modifications to successfully remove the file.
        project.remove_file_by_id(file.get_id())

        for group in project.objects.get_objects_in_section(u"PBXGroup"):
            if file.get_id() in group.children:
                group.remove_child(file)

        for build_file in project.objects.get_objects_in_section(u"PBXBuildFile"):
            if build_file.fileRef == file.get_id():
                del project.objects[build_file.get_id()]

        for build_file in project.objects.get_objects_in_section("PBXFileReference"):
            if build_file.get_id() == file.get_id():
                del project.objects[build_file.get_id()]

    return project
