"""
fritz.api_resources.app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
import logging

import fritz
import fritz.utils
import fritz.errors
from fritz.api_resources.fritz_object import FritzObject

_logger = logging.getLogger(__name__)


class App(FritzObject):
    """Resources to manipulate app resources from the CLI."""

    OBJECT_NAME = "Application"

    def summary(self):
        """Print summary of object."""
        details = [
            ("Created At", self.created_date),
            ("APK ID", self.apk_id),
            ("Platform", self.platform),
            ("API Key", self.api_key),
        ]
        return self._summary(self.app_name, details)

    # pylint: disable=duplicate-code
    @classmethod
    def create(
        cls,
        api_key=None,
        project_id=None,
        app_name=None,
        apk_id=None,
        platform=None,
    ):
        """Create a new app.

        Args:
            api_key (str): Fritz API Key
            app_name (str): App Name
            apk_id (str): APK ID
            platform (str): Platform app is created on (ios or android)

        Raises:
            fritz.errors.FritzNotInitializedError

        Returns: App object
        """
        url = "/app"
        params = {
            "project_uid": project_id or fritz.project_id,
            "app_name": app_name,
            "apk_id": apk_id,
            "platform": platform,
        }
        response = cls.client_post(url, api_key=api_key, params=params)
        obj = fritz.utils.convert_to_fritz_object(response)
        return obj

    @classmethod
    def get(cls, api_key=None, app_id=None):
        """Get app.

        Args:
            api_key: Optional API Key to use.
            app_id: ID of app to query.

        Returns: App
        """
        url = "/app/" + app_id
        response = cls.client_get(url, api_key=api_key)
        return fritz.utils.convert_to_fritz_object(response)

    @classmethod
    def list(
        cls,
        api_key=None,
        project_id=None,
        platform=None,
        app_api_key=None,
        apk_id=None,
        all_projects=False,
    ):
        """Get app, restricting results to specified arguments.

        Args:
            api_key: Optional API Key to use.
            project_id: Project ID
            platform: App platform  - either ios or android.
            app_api_key: API Key for app.
            apk_id: APK ID or Bundle ID of apps.
            all_projects: If True and no project_id specified, returns apps
                from all projects. Default False.

        Returns: List[App]
        """
        url = "/app"
        if not project_id and not all_projects:
            project_id = fritz.project_id

        params = {
            "project_uid": project_id,
            "platform": platform,
            "api_key": app_api_key,
            "apk_id": apk_id,
        }
        response = cls.client_get(url, api_key=api_key, params=params)

        return [fritz.utils.convert_to_fritz_object(app) for app in response["apps"]]
