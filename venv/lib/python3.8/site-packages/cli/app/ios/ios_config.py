"""
cli.app.android.android_config

Android Configuration.
"""

from typing import Optional
import pathlib
from fritz import errors

from cli.app.ios import ios_helpers


def _find_xcodeproj_path(root: pathlib.Path) -> pathlib.Path:
    paths = root.rglob("**/*.xcodeproj")
    return next(paths, None)


def _find_app_delegate_path(root: pathlib.Path) -> pathlib.Path:
    paths = root.rglob("AppDelegate.swift")
    return next(paths, None)


def _find_fritz_info_path(root: pathlib.Path) -> Optional[pathlib.Path]:
    paths = root.rglob("Fritz-Info.plist")
    return next(paths, None)


def _find_podfile_path(root: pathlib.Path) -> Optional[pathlib.Path]:
    paths = root.rglob("Podfile")
    return next(paths, None)


class IOSConfig(object):
    """Configuration of IOS app project."""

    def __init__(
        self,
        root: pathlib.Path,
        app_delegate_path=None,
        xcodeproj_path=None,
        fritz_info_path=None,
        podfile_path=None,
    ):
        self.root = root
        self._xcodeproj_path = xcodeproj_path
        self._app_delegate_path = app_delegate_path
        self._fritz_info_path = fritz_info_path
        self._podfile_path = podfile_path

        # Loading the app name and bundle name is expensive.
        # allow this to be loaded once on init.
        self._app_name = ios_helpers.get_app_name(self.xcodeproj_path)
        self._package_name = ios_helpers.get_bundle_id(self.xcodeproj_path)

    @property
    def platform(self):
        """Platform of app."""
        return "ios"

    @property
    def app_name(self) -> Optional[str]:
        """App Name. """
        return self._app_name

    @property
    def package_name(self) -> Optional[str]:
        """Returns APK ID for project."""
        return self._package_name

    @property
    def app_delegate_path(self) -> Optional[pathlib.Path]:
        """Path to AppDelegate."""
        return self._app_delegate_path

    @property
    def default_podfile_path(self) -> pathlib.Path:
        """Default path to Podfile."""
        return self.root / "Podfile"

    @property
    def default_fritz_info_path(self) -> pathlib.Path:
        """Gets path to info file by searching common directory structures."""
        supporting_files_folder = self.root.rglob("Supporting Files/")
        for folder in supporting_files_folder:
            # only want to look at directories.
            if not folder.is_dir():
                continue

            # Do not want to use the supporting files folder from a pod.
            if "Pods" in str(folder):
                continue

            return folder / "Fritz-Info.plist"

        # Many default apps are created with application code inside of a
        # folder with the same name as the app name.  If that exists, use
        # that folder.
        if (self.root / self.app_name).exists():
            return self.root / self.app_name / "Fritz-Info.plist"

        return self.root / "Fritz-Info.plist"

    @property
    def fritz_info_path(self) -> Optional[pathlib.Path]:
        """Fritz info path path."""
        return self._fritz_info_path

    @fritz_info_path.setter
    def fritz_info_path(self, value):
        """Fritz info path path."""
        self._fritz_info_path = value

    @property
    def podfile_path(self) -> Optional[pathlib.Path]:
        """Podfile path."""
        return self._podfile_path

    @podfile_path.setter
    def podfile_path(self, value):
        """Podfile path."""
        self._podfile_path = value

    @property
    def xcodeproj_path(self) -> Optional[pathlib.Path]:
        """Path to xcodeproj."""
        return self._xcodeproj_path

    @property
    def fritz_api_key(self) -> Optional[pathlib.Path]:
        """Fritz API Key found in app. """
        if not self.fritz_info_path:
            return None

        return ios_helpers.find_fritz_api_key(self.fritz_info_path)

    @classmethod
    def load(cls, root: pathlib.Path):
        """Search root path and initialize config with found files.

        Args:
            root: Root path of Android project.

        Returns: AndroidConfig.
        """
        config = cls(
            root,
            xcodeproj_path=_find_xcodeproj_path(root),
            app_delegate_path=_find_app_delegate_path(root),
            fritz_info_path=_find_fritz_info_path(root),
            podfile_path=_find_podfile_path(root),
        )

        if not config.xcodeproj_path:
            raise errors.MissingProjectFileError(".xcodeproj")

        if not config.app_delegate_path:
            raise errors.MissingProjectFileError("AppDelegate.swift")

        return config

    def summary(self):
        """Summary of iOS App config."""
        return """
App Name:            {app_name}
Bundle ID:           {bundle_id}
Xcode Project Path:  {xcodeproj_path}
AppDelegate Path:    {app_delegate_path}
Fritz-Info path:     {fritz_info_path}
Podfile path:        {podfile_path}
        """.format(
            app_name=self.app_name,
            bundle_id=self.package_name,
            xcodeproj_path=self.xcodeproj_path,
            app_delegate_path=self.app_delegate_path,
            fritz_info_path=self.fritz_info_path,
            podfile_path=self.podfile_path,
        )
