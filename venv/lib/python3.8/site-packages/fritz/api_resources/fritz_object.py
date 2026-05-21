"""
fritz.fritz_object
~~~~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
from typing import Dict
import json
import fritz
from fritz.api_client import FritzClient

# Keys that are accessed with "uid" in data.
UID_KEYS = ["app_id", "model_id", "project_id", "snapshot_id", "version_id"]


class FritzObject(object):
    """An object from the API.

    Subclassed objects are used to define interactions with the API.
    """

    def __init__(self, **kwargs):
        self._data = kwargs

    def __repr__(self):
        identity_parts = [type(self).__name__]

        if isinstance(self.uid, str):
            identity_parts.append("uid=%s" % (self.uid))

        unicode_repr = "<%s> JSON: %s" % (" ".join(identity_parts), str(self))

        return unicode_repr

    def __str__(self):
        return json.dumps(self._data, sort_keys=True, indent=2)

    def __getattr__(self, key):
        if key[0] == "_":
            raise AttributeError(key)

        # We refer to ids externally as "project_id", "model_id", etc, but
        # all underlying data is stored as "project_uid", "model_uid", etc.
        # Enforcing accessing this with id rather than uid.
        split_key = key.split("_")
        if len(split_key) == 2 and split_key[1] == "uid":
            raise AttributeError(key)

        if key in UID_KEYS:
            key = "_".join([split_key[0], "uid"])

        try:
            return self._data[key]
        except KeyError as err:
            raise AttributeError(*err.args)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.__dict__ == other.__dict__

    @property
    def data(self) -> Dict:
        """Underlying data backing object."""
        return self._data

    @property
    def id(self):
        """ID of object.

        Returns: str
        """
        # Note: Internally, IDs are stored as UIDs.  However, externally
        # these are consistently referred to as IDs (i.e. model_id).
        return self.uid

    @property
    def created_date(self):
        """Date when object was created."""
        date, time = self.created_at.split("T")
        return date + " " + time[:5]

    @property
    def updated_date(self):
        """Date when object was created."""
        date, time = self.updated_at.split("T")
        return date + " " + time[:5]

    def _summary(self, object_name, details):
        header_fmt = "{key:>%s}: {value}" % len(self.OBJECT_NAME)
        title = header_fmt.format(key=self.OBJECT_NAME, value=object_name)
        id_row = header_fmt.format(key="ID", value=self.id)
        header_line = "-" * max(len(title), len(id_row))
        lines = [title, id_row, header_line]
        max_name = max(len(name) for name, _ in details)
        for name, value in details:
            row_fmt = "  {name:%s}: {value}" % (max_name + 2)
            lines.append(row_fmt.format(name=name, value=value))

        return "\n".join(lines)

    @staticmethod
    def client_post(url, api_key=None, params=None):
        """Base method to perform POST requests.

        Does not attempt to convert response into object. Implementing classes
        should handle that.

        Args:
            url (str): URL to query.
            api_key (str): Optional Fritz API key.
            params (dict): JSON body to pass to request.

        Returns: dict response if successful.
        """
        if not fritz.api_key and not api_key:
            raise fritz.errors.FritzNotInitializedError()

        client = FritzClient(api_key or fritz.api_key)
        response = client.post(url, json=params)

        return response

    @staticmethod
    def client_put(url, api_key=None, params=None):
        """Base method to perform PUT requests.

        Does not attempt to convert response into object. Implementing classes
        should handle that.

        Args:
            url (str): URL to query.
            api_key (str): Optional Fritz API key.
            params (dict): JSON body to pass to request.

        Returns: dict response if successful.
        """
        if not fritz.api_key and not api_key:
            raise fritz.errors.FritzNotInitializedError()

        client = FritzClient(api_key or fritz.api_key)
        response = client.put(url, json=params)

        return response

    @staticmethod
    def client_get(url, api_key=None, params=None):
        """Base method to perform GET requests.

        Does not attempt to convert response into object. Implementing classes
        should handle that.

        Args:
            url (str): URL to query.
            api_key (str): Optional Fritz API key.
            params (dict): Query parameters to pass to request.

        Returns: dict response if successful.
        """
        if not fritz.api_key and not api_key:
            raise fritz.errors.FritzNotInitializedError()

        client = FritzClient(api_key or fritz.api_key)

        response = client.get(url, params=params)

        return response
