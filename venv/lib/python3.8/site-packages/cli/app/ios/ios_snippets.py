"""
cli.app.ios.ios_snippets

Code Snippets for setting up Fritz with a Swift iOS app.
"""
# pylint: disable=abstract-method

import os
import pathlib

from pbxproj import XcodeProject

from cli.app import code_snippet
from cli.app.ios import ios_helpers
from cli.app import file_manager


class FritzInfoSnippet(code_snippet.CodeSnippet):
    """Base Snippet for Fritz-Info.plist files."""

    def __init__(self, config, app):
        super().__init__(config, app)
        self.path = config.fritz_info_path or config.default_fritz_info_path


class AppDelegateSnippet(code_snippet.CodeSnippet):
    """Base Snippet for AppDelegate.swift files."""

    def __init__(self, config, app):
        super().__init__(config, app)
        self.path = config.app_delegate_path


class CreateFritzInfo(FritzInfoSnippet):
    """Handles create and renaming Fritz-Info.plist file.

    This does not add to the Xcode project, just creates the file.
    """

    @property
    def is_added(self):
        found = next(self.app_config.root.rglob("Fritz-Info.plist"), None)
        return found is not None

    @property
    def is_updated(self):
        if not self.is_added:
            return True

        # If the path specified does not match the one in the project,
        # this will return false.
        return self.path.exists()

    def add(self):
        ios_helpers.create_fritz_info(self.path, self.app)

    def update(self):
        existing = next(self.app_config.root.rglob("Fritz-Info.plist"))
        existing.rename(self.path)


class FritzInfoAPIKeyUpdater(FritzInfoSnippet):
    """Handles updating the API Key if it does not match."""

    @property
    def is_added(self):
        # This will never add an api key... only will update existing ones.
        return True

    @property
    def is_updated(self):
        if not self.is_added:
            return True

        existing_path = next(self.app_config.root.rglob("Fritz-Info.plist"), None)
        if not existing_path:
            return True

        return self.app.api_key == ios_helpers.find_fritz_api_key(existing_path)

    def add(self):
        pass

    def update(self):
        existing_path = next(self.app_config.root.rglob("Fritz-Info.plist"))
        ios_helpers.create_fritz_info(existing_path, self.app)


class FritzInfoXcodeProject(FritzInfoSnippet):
    """Add Fritz Info file to Xcode Project."""

    @property
    def project(self):
        """Xcode Project."""
        project_file = "{xcode_proj_file}/project.pbxproj".format(
            xcode_proj_file=str(self.app_config.xcodeproj_path)
        )
        return XcodeProject.load(project_file)

    @property
    def is_added(self):
        return len(self.project.get_files_by_name("Fritz-Info.plist")) > 0

    @property
    def is_updated(self):
        if not self.is_added:
            return True

        relative_path = self.path.relative_to(self.app_config.root)
        # If there are files matching the path, then file exists in the correct
        # place so no need to move.
        return len(self.project.get_files_by_path(str(relative_path))) > 0

    def add(self):
        relative_path = self.path.relative_to(self.app_config.root)
        project = ios_helpers.add_path_to_xcodeproj(self.project, relative_path)
        project.save()

    def update(self):
        relative_path = self.path.relative_to(self.app_config.root)
        project = ios_helpers.remove_file_in_xcodeproj(self.project, relative_path.name)
        project = ios_helpers.add_path_to_xcodeproj(project, relative_path)
        project.save()


class AddFritzImport(AppDelegateSnippet):
    """Add Fritz import in AppDelegate."""

    @property
    def is_added(self):
        return "import Fritz" in self.path.read_text()

    def add(self):
        text = file_manager.insert_before(
            self.path, "@UIApplicationMain", "import Fritz\n"
        )
        self.path.write_text(text)


class AddFritzConfigure(AppDelegateSnippet):
    """Add Fritz configure call in app-delegate."""

    @property
    def is_added(self):
        return "FritzCore.configure" in self.path.read_text()

    def add(self):
        hint = "didFinishLaunchingWithOptions"
        text = file_manager.insert_in_function_after_hint(
            self.path, hint, "FritzCore.configure()"
        )
        self.path.write_text(text)


class PodfileSnippet(code_snippet.CodeSnippet):
    """Base Snippet for Podfile."""

    def __init__(self, config, app):
        super().__init__(config, app)
        self.path = config.podfile_path or config.default_podfile_path


class AddPodfile(PodfileSnippet):
    """Creates Podfile."""

    @property
    def is_added(self):
        return self.path.exists()

    def add(self):
        os.popen("pod init " + str(self.app_config.xcodeproj_path)).read()
        pod_path = pathlib.Path.cwd() / "Podfile"
        pod_path.rename(self.path)
        self.app_config.podfile_path = self.path


class AddFritzToPodfile(PodfileSnippet):
    """Adds Fritz dependency to Podfile."""

    @property
    def is_added(self):
        if not self.path.exists():
            return False

        return "Fritz" in self.path.read_text()

    def add(self):
        # Line that appears in default podfile.
        fritz_install_line = "  pod 'Fritz'\n"

        text = self.path.read_text()
        target = self.app_config.app_name
        default_target_line = "# Pods for {target}".format(target=target)
        if default_target_line in text:
            text = file_manager.insert_after(
                self.path, default_target_line, fritz_install_line
            )
            self.path.write_text(text)
            return

        pod_target_line = "target '{target}'".format(target=self.app_config.app_name)
        if pod_target_line in text:
            text = file_manager.insert_after(
                self.path, pod_target_line, fritz_install_line
            )
            self.path.write_text(text)
            return

        raise code_snippet.SnippetExecutionError(
            "Could not determine where to insert Fritz pod."
        )
