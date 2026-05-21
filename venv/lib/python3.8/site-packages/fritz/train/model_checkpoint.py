"""
fritz.keras.model_checkpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This module contains a Keras callback to upload new versions of a
model to Fritz.
"""
import logging
import arrow
import tensorflow as tf

# pylint: disable=no-member
if tf.__version__ >= "2.0.0":
    from tensorflow import keras
else:
    import keras

# pylint: disable=wrong-import-position
import fritz

_logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class FritzSnapshotCallback(keras.callbacks.Callback):
    """Keras callback to create a ModelSnapshot in Fritz.

    Adding this callback will convert and upload mobile-ready models
    during training.
    """
    # pylint: disable=too-many-arguments

    def __init__(
        self,
        api_key=None,
        project_id=None,
        model_ids_by_framework=None,
        converters_by_framework=None,
        output_file_name=None,
        period=10,
        deploy=False,
        metadata=None,
        feature_type=None,
        save_after_seconds=None
    ):
        # pylint: disable=line-too-long
        """Save a Fritz Snapshot to Fritz.

        Args:
            api_key (Optional[str]): Optional API Key.
            project_id (Optional[str]): Optional project id, required if not
                globally set.
            model_ids_by_framework (Dict[frameworks.ModelFramework,str]):
                Dictionary mapping model framework to model ids. If model_id
                not set for a given platform, a new model will be created.
            converters_by_framework (Dict[frameworks.ModelFramework,Callable[[keras.models.Model], Any]]):
                Dictionary mapping model framework to conversion function.
            output_file_name (str): Name of output_file.
            period (int): Interval (number of epochs) between checkpoints.
            deploy (bool): If True will set active version of model to latest
                uploaded model. Default False.
            metadata (dict): Optional dictionary of metadata to include about
                job arguments.
            feature_type (str): the feature type of the model.
            save_after_seconds (int): the number of seconds after which the
                call back should fire and save models
        """
        super().__init__()
        self._api_key = api_key
        self._project_id = project_id
        self._output_file_name = output_file_name
        self._period = period
        self._deploy = deploy
        self._model_ids = model_ids_by_framework or {}
        self._converters = converters_by_framework or {}
        self._job_metadata = metadata or {}
        self._current_epoch = 0
        self._current_logs = {}
        self._feature_type = feature_type
        self._duration = save_after_seconds
        self._start_at = None
        self._has_fired = False

    def add_model_metadata(
        self, logs
    ):  # noqa pylint: disable=unused-argument,no-self-use
        """Adds additional metadata about the model to be stored in Fritz.

        Optionally override this method returning custom information.

        Args:
            logs (dict): Includes values such as `acc` and `loss`.

        Returns: Dict of model metadata.
        """
        return {}

    def _create_fritz_checkpoints(self, epoch, logs=None):
        """Create model snapcshot checkpoints in Fritz.

        Args:
            epoch: the epoch number for the current model
            logs (dict): includes values for accuracy and loss
        """
        _logger.info("Creating ModelSnapshot - epoch %s", epoch)
        metadata = {"epoch": epoch, "keras_model_path": self._output_file_name}
        converted_logs = {}
        import numpy

        for key, value in logs.items():
            if isinstance(value, (numpy.float32, numpy.float64)):
                value = float(value)
            converted_logs[key] = value

        metadata.update(converted_logs or {})
        metadata["job_arguments"] = self._job_metadata
        metadata.update(self.add_model_metadata(logs))
        _, _, models = fritz.ModelSnapshot.create(
            api_key=self._api_key,
            project_id=self._project_id,
            filename=self._output_file_name,
            keras_model=self.model._get_callback_model(),  # pylint: disable=protected-access
            set_active=self._deploy,
            metadata=metadata,
            converters=self._converters,
            model_ids=self._model_ids,
            feature_type=self._feature_type,
        )

        # Update previously unset model_ids with created models.
        for model in models:
            if not self._model_ids.get(model.framework):
                self._model_ids[model.framework] = model.id

    def on_epoch_end(self, epoch, logs=None):
        """Saves model to Fritz on epoch end.

        Args:
            epoch (int): the epoch number
            logs (dict, optional): logs dict
        """
        _logger.info(
            "{num_epochs} - {epoch}".format(
                num_epochs=self.params.get("epochs"), epoch=epoch
            )
        )
        # Update the current epoch even if we aren't saying a model.
        self._current_epoch = epoch
        self._current_logs = logs

        # If this is the last epoch, don't bother saving things because
        # on_train_end will take care of it.
        is_last_epoch = self.params.get("epochs") == (epoch + 1)
        # Adding one so that the very first run does not trigger an upload.
        # If you specify period to be 3, the first upload will be on the 3rd
        # epoch.
        if is_last_epoch or (epoch + 1) % self._period != 0:
            return

        self._create_fritz_checkpoints(epoch, logs)

    def on_train_end(self, logs=None):
        """Saves the model to Fritz on training end."""
        _logger.info("Saving final model checkpoint to Fritz.")
        self._create_fritz_checkpoints(self._current_epoch, self._current_logs)

    def on_train_begin(self, logs=None):
        self._start_at = arrow.utcnow()

    def on_train_batch_end(self, batch, logs=None):
        """Save models if enough time has passed.

        This will only fire once when enough time has passed.

        Args:
            batch: the batch number
            logs: logs dict
        """
        if not self._duration:
            return

        elapsed = (arrow.utcnow() - self._start_at).total_seconds()

        if elapsed > self._duration and not self._has_fired:
            self._create_fritz_checkpoints(self._current_epoch, logs=logs)
            self._has_fired = True
