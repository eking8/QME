"""
fritz.api_resources.model_version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
import os
import time
import logging
import json
import math
import requests

import fritz
import fritz.utils
import fritz.errors
from fritz.api_resources.fritz_object import FritzObject
from fritz.api_client import FritzClient

_logger = logging.getLogger(__name__)


def _convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    to_raise = int(math.floor(math.log(size_bytes, 1024)))
    power = math.pow(1024, to_raise)
    size = round(size_bytes / power, 2)
    return "%s %s" % (size, size_name[to_raise])


class ModelVersion(FritzObject):
    """ModelVersion  """

    OBJECT_NAME = "ModelVersion"

    def summary(self):
        """Print summary of object."""
        details = [
            ("Model Size", self.model_size),
            ("Filename", self.provided_filename),
            ("Version", self.version_number),
            ("Metadata", json.dumps(self.metadata, indent=2)),
            ("Loss", self.loss),
        ]
        return self._summary(self.provided_filename, details)

    @property
    def model_size(self):
        """Convert model bytes to human readable string."""
        return _convert_size(self.model_bytes)

    @property
    def loss(self):
        """Training loss if in metadata."""
        metadata = self.metadata or {}
        return metadata.get("loss")

    # pylint: disable=duplicate-code,too-many-arguments
    @classmethod
    def create(
        cls,
        api_key=None,
        project_id=None,
        model_id=None,
        snapshot_id=None,
        filename=None,
        feature_type=None,
        use_existing_model_on_duplicate_name=False,
        data=None,
        set_active=None,
        metadata=None,
    ):
        """Create a new ModelVersion, uploading file to Fritz.

        Args:
            api_key (Optional[str]): API Key. Optional if `fritz.configure`
                was called.
            project_id (Optional[str]): Project ID. Optional if
                `fritz.configure` was called with project_id.
            model_id (str): optional Model ID.
            snapshot_id (str): If snapshot_id set, will attach version to
                given snapshot.
            filename (str): Name of model version filename.
            feature_type (feature_type.FeatureType): The feature type of
                the model. e.g. FeatureType.POSE_ESTIMATION
            use_existing_model_on_duplicate_name (bool): If true, the model
                version will be attached a model with the same name and format
                in the project if one is found.
            data (io.BytesIO): Model data to upload
            set_active (bool): If True, model will be set as the active version
               in Fritz. If it is True, any devices runninng this model will
               download the latest version.
            metadata (dict): Dictionary of metadata.

        Returns:
            Tuple[ModelVersion, ModelSnapshot, Model]
        """
        if not fritz.api_key and not api_key:
            raise fritz.errors.FritzNotInitializedError()

        if model_id:
            url = "/model/{model_id}/version".format(model_id=model_id)
        else:
            url = "/model/version"

        client = FritzClient(api_key or fritz.api_key)
        response = client.post(
            url,
            params={
                "project_uid": project_id or fritz.project_id,
                "snapshot_uid": snapshot_id,
                "model_uid": model_id,
                "feature_type": feature_type.value if feature_type else None,
                "use_existing_model_on_duplicate_name": (
                    use_existing_model_on_duplicate_name
                ),
            },
            data={
                "set_active": set_active,
                "metadata_json": json.dumps(metadata or {}),
            },
            files={"file": (filename, data)},
        )
        converted = {
            key: fritz.utils.convert_to_fritz_object(value)
            for key, value in response.items()
        }
        return converted["version"], converted["snapshot"], converted["model"]

    @classmethod
    def get(cls, version_id=None, api_key=None):
        """Get version by version_id

        Args:
            version_id: Version ID
            api_key (str): Optional API Key to use.

        Returns: ModelVersion
        """
        if not version_id:
            raise fritz.errors.ArgumentRequiredError("version_id")

        url = "/model/version/{version_id}".format(version_id=version_id)

        response = cls.client_get(url, api_key=api_key)
        return fritz.utils.convert_to_fritz_object(response)

    @classmethod
    def list(cls, model_id, api_key=None):
        """Get all model versions for model_id

        Args:
            model_id: Model ID
            api_key (str): Optional API Key to use.

        Returns: List[ModelVersion]
        """
        url = "/model/" + model_id + "/version"
        response = cls.client_get(url, api_key=api_key)
        return [
            fritz.utils.convert_to_fritz_object(version)
            for version in response["versions"]
        ]

    def benchmark(self, api_key=None, wait_seconds=5, attempts=5):
        """Get model grade report, waiting if it does not yet exist.

        Args:
            api_key (str): Optional API Key
            wait_seconds (int): Number of seconds to wait between each
                request.
            attempts (int): Number of attempts to make.

        Returns: ModelGradeReport if it exists
        """

        try:
            return fritz.ModelGradeReport.get(api_key=api_key, version_id=self.id)
        except fritz.errors.FritzError as err:
            if err.status_code != 404:
                raise err
            _logger.info("Grader report not found, trying again")
            attempts -= 1
            if attempts < 0:
                raise err

            time.sleep(wait_seconds)

            return self.benchmark(
                api_key=api_key, wait_seconds=wait_seconds, attempts=attempts
            )

    def download(self, download_dir=None):
        """Download Model version.

        Args:
            download_dir (str): optional directory to download model in.

        Returns: str path of downloaded model.
        """
        response = requests.get(self.s3_path, allow_redirects=True)
        path = os.path.join(download_dir or ".", self.provided_filename)
        with open(path, "wb") as f:
            f.write(response.content)
        return path
