"""
fritz.api_client
~~~~~~~~~~~~~~~~
This module contains the FritzClient for interacting with the Fritz API.
"""
import requests

import fritz
import fritz.errors


class FritzClient(object):
    """Fritz Client to interact with Fritz API."""

    def __init__(self, api_key=None, api_base=None):
        """
        Args:
            api_key (str): Account API Key for Fritz API.
            base_url (str): URL base of Fritz API.
        """
        self._api_key = api_key or fritz.api_key
        self._api_base = api_base or fritz.api_base

    def put(self, url, params=None, data=None, json=None, files=None, headers=None):
        """PUT Request to Fritz API.

        Args:
                url (str): URL to request.
                params (dict): Query parameters
                data (dict): Content
                files (dict): Files to upload
                headers (dict): Headers to add to request.
                json (dict): the json content

            Returns: Dict of response data.
        """
        path = self._api_base + url
        base_headers = {"Authorization": self._api_key}
        base_headers.update(headers or {})
        response = requests.put(
            path,
            params=params,
            data=data,
            json=json,
            files=files,
            headers=base_headers,
        )
        try:
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise fritz.errors.ConnectionError(path)
        except requests.exceptions.RequestException:
            error = response.json()
            raise fritz.errors.FritzError(
                error.get("message"), status_code=response.status_code
            )

        return response.json()

    # Note: Chris - these feel a bit duplicated. Wonder if we can combine this
    # in some way.
    def post(self, url, params=None, data=None, json=None, files=None, headers=None):
        """POST Request to Fritz API.

        Args:
                url (str): URL to request.
                params (dict): Query parameters
                data (dict): Content
                files (dict): Files to upload
                headers (dict): Headers to add to request.
                json (dict): the json content

            Returns: Dict of response data.
        """
        path = self._api_base + url
        base_headers = {"Authorization": self._api_key}
        base_headers.update(headers or {})

        response = requests.post(
            path,
            params=params,
            data=data,
            json=json,
            files=files,
            headers=base_headers,
        )
        try:
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise fritz.errors.ConnectionError(path)
        except requests.exceptions.RequestException:
            error = response.json()
            raise fritz.errors.FritzError(
                error.get("message"), status_code=response.status_code
            )

        return response.json()

    def get(self, url, params=None, headers=None):
        """GET Request to Fritz API.

        Args:
            url (str): URL to request.
            params (dict): Query parameters
            headers (dict): Headers to add to request.

        Returns: Dict of response data.
        """
        path = self._api_base + url
        base_headers = {"Authorization": self._api_key}
        base_headers.update(headers or {})
        try:
            response = requests.get(path, params=params, headers=base_headers)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise fritz.errors.ConnectionError(path)
        except requests.exceptions.RequestException:
            error = response.json()
            raise fritz.errors.FritzError(
                error.get("message"), status_code=response.status_code
            )

        return response.json()
