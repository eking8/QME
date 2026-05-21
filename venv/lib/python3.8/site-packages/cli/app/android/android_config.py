"""
cli.app.android.android_config

Android Configuration.
"""

from typing import Optional
import pathlib
from fritz import errors
from cli.app.android import android_helpers


def _find_android_manifest(root: pathlib.Path) -> pathlib.Path:
    paths = root.rglob("**/src/main/AndroidManifest.xml")
    return next(paths, None)


def _find_app_gradle_path(root: pathlib.Path) -> pathlib.Path:
    paths = root.rglob("build.gradle")
    for path in paths:
        if "com.android.application" in path.read_text():
            return path

    return None


def _find_project_gradle_path(root: pathlib.Path) -> Optional[pathlib.Path]:
    gradle_path = root / "build.gradle"
    if not gradle_path.exists():
        return None
    return gradle_path


class AndroidConfig(object):
    """Configuration of Android app project."""

    def __init__(
        self,
        root: pathlib.Path,
        android_manifest_path=None,
        app_gradle_path=None,
        project_gradle_path=None,
    ):
        self.root = root
        self._android_manifest_path = android_manifest_path
        self._app_gradle_path = app_gradle_path
        self._project_gradle_path = project_gradle_path

    @property
    def platform(self):
        """Platform of app."""
        return "android"

    @property
    def app_name(self) -> Optional[str]:
        """App Name. """
        return android_helpers.find_app_name(self.root, self.android_manifest_path)

    @property
    def package_name(self) -> Optional[str]:
        """Returns APK ID for project."""
        app_id = android_helpers.find_application_id(self.app_gradle_path)
        if app_id:
            return app_id
        return android_helpers.find_package_name(self.android_manifest_path)

    @property
    def android_manifest_path(self) -> Optional[pathlib.Path]:
        """Path to Android manifest."""
        return self._android_manifest_path

    @property
    def app_gradle_path(self) -> Optional[pathlib.Path]:
        """Path to app build.gradle path."""
        return self._app_gradle_path

    @property
    def project_gradle_path(self) -> Optional[pathlib.Path]:
        """Path to project build.gradle path."""
        return self._project_gradle_path

    @property
    def main_activity_path(self) -> Optional[pathlib.Path]:
        """Path to main activity."""
        main_activity_name = android_helpers.find_main_activity(
            self.android_manifest_path
        )
        paths = self.root.rglob("**/" + main_activity_name + ".java")
        return next(paths, None)

    @property
    def fritz_api_key(self) -> Optional[pathlib.Path]:
        """Fritz API Key found in app. """
        return android_helpers.find_fritz_api_key(self.app_gradle_path)

    @classmethod
    def load(cls, root: pathlib.Path):
        """Search root path and initialize config with found files.

        Args:
            root: Root path of Android project.

        Returns: AndroidConfig.
        """
        config = cls(
            root,
            android_manifest_path=_find_android_manifest(root),
            app_gradle_path=_find_app_gradle_path(root),
            project_gradle_path=_find_project_gradle_path(root),
        )

        if not config.android_manifest_path:
            raise errors.MissingProjectFileError("AndroidManifest.xml")

        if not config.app_gradle_path:
            raise errors.MissingProjectFileError("app/build.gradle")

        if not config.project_gradle_path:
            raise errors.MissingProjectFileError("Project build.gradle")

        return config

    def summary(self):
        """Summary of Android config."""
        return """
App Name:            {app_name}
Package Name:        {package_name}
Android Manifest:    {manifest}
App Gradle Path:     {app_gradle}
Project Gradle Path: {project_gradle}
        """.format(
            app_name=self.app_name,
            package_name=self.package_name,
            manifest=self.android_manifest_path,
            app_gradle=self.app_gradle_path,
            project_gradle=self.project_gradle_path,
        )
