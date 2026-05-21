"""
fritz.api_resources.model_snapshot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
import logging

import fritz
from fritz.api_resources.fritz_object import FritzObject

# pylint: disable=invalid-name
_logger = logging.getLogger(__name__)


class ModelSnapshot(FritzObject):
    """A collection of models built from the same training model. """

    OBJECT_NAME = "ModelSnapshot"

    # pylint: disable=duplicate-code
    @classmethod
    def create(
        cls,
        api_key=None,
        project_id=None,
        keras_model=None,
        converters=None,
        model_ids=None,
        filename=None,
        set_active=None,
        metadata=None,
        feature_type=None,
    ):
        """Create new ModelSnapshot from a Keras model.

        Calling create will run all provided converters on `keras_model`
        and upload them to the API. All models will be bundled into
        the same ModelSnapshot

        Args:
            api_key (Optional[str]): API Key. Optional if `fritz.configure`
                was called.
            project_id (Optional[str]): Project ID. Optional if
                `fritz.configure` was called with project_id.
            keras_model (keras.models.Model): Keras Model.
            converters (Dict[frameworks.ModelFramework,(keras.model.Model) ->
                Any]): Dictionary mapping model framework to conversion
                function.
            model_ids (Dict[`frameworks.ModelFramework`,str]): Dictionary
                mapping model framework to model ids.  If model_id not set
                for a given platform, a new model will be created.
            filename (str): Name of Keras model output filename.
            set_active (bool): If True, model will be set as the active version
               in Fritz. If it is True, any devices runninng this model will
               download the latest version.
            metadata (dict): Dictionary of metadata.
            feature_type (feature_type.FeatureType): the feature type of the
                model.

        Returns: Tuple[fritz.ModelSnapshot, List[fritz.ModelVersion],
            List[fritz.Model]]
        """
        keras_file = fritz.frameworks.KerasFile(keras_model)
        model_ids = model_ids or {}
        versions = []
        models = []

        keras_model_id = model_ids.get(fritz.frameworks.KERAS)
        version, snapshot, model = fritz.ModelVersion.create(
            api_key=api_key,
            project_id=project_id,
            filename=filename,
            data=keras_file.to_bytes(),
            model_id=keras_model_id,
            set_active=set_active,
            metadata=metadata,
            feature_type=feature_type,
        )
        versions.append(version)
        models.append(model)

        for framework, converter in converters.items():
            _logger.info("Converting %s model", framework.name)

            try:
                converted_model = converter(keras_model)
            except Exception:  # pylint: disable=broad-except
                _logger.exception(
                    "Failed to convert model for framework {framework}".format(
                        framework=framework
                    )
                )
                continue
            framework_file = framework.to_file(converted_model)

            version, snapshot, _ = fritz.ModelVersion.create(
                api_key=api_key,
                project_id=project_id,
                model_id=model_ids.get(framework),
                snapshot_id=snapshot.id,
                filename=framework.as_framework_filename(filename),
                data=framework_file.to_bytes(),
                set_active=set_active,
                metadata=metadata,
                feature_type=feature_type,
            )
            versions.append(version)

        return snapshot, versions, models
