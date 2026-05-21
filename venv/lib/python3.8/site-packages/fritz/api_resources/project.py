"""
fritz.api_resources.project
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""

import fritz
from fritz.api_resources import fritz_object


class Project(fritz_object.FritzObject):
    """Fritz Project object."""

    OBJECT_NAME = "Project"

    def summary(self):
        """Print summary of object."""
        details = [("Created At", self.created_date)]
        return self._summary(self.name, details)

    @classmethod
    def get(cls, project_id=None, api_key=None):
        """Get project by id

        Args:
            project_id (str): ID of proejct
            api_key (str): Optional API Key to use.

        Returns: Project
        """
        project_id = project_id or fritz.project_id
        url = "/project/{project_id}".format(project_id=project_id)
        response = cls.client_get(url, api_key=api_key)
        return fritz.utils.convert_to_fritz_object(response)

    @classmethod
    def list(cls, api_key=None):
        """Get project by id

        Args:
            api_key (str): Optional API Key to use.

        Returns: Project
        """
        url = "/project"
        response = cls.client_get(url, api_key=api_key)

        return [
            fritz.utils.convert_to_fritz_object(project)
            for project in response["projects"]
        ]
