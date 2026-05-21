"""
fritz.frameworks
~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
import io
import os
import tempfile

import onnx
import tensorflow as tf


class ModelFramework(object):
    """Defines a specific model framework"""

    def __init__(self, name, extension, file_cls):
        self.name = name
        self.extension = extension
        self._file_cls = file_cls

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return "ModelFramework(name={name} extension={extension})".format(
            name=self.name, extension=self.extension
        )

    def as_framework_filename(self, filename):
        """Generate filename that representing a model of this framework.

        Args:
            filename (str): filename (i.e. 'mobilenet_v2.h5')

        Returns: str
        """
        file_base = os.path.splitext(os.path.basename(filename))[0]
        return file_base + self.extension

    def to_file(self, model):
        """Build FrameworkFileBase object for Framework.

        Args:
            model: Model

        Returns: FrameworkFileBase
        """
        return self._file_cls(model)

    def build_file(self, path, skip_model_cls_init=False):
        """Build FrameworkFileBase object for a given path.

        Args:
            path: String

        Returns: FrameworkFileBase
        """
        return self._file_cls.build_from_file(
            path, skip_model_cls_init=skip_model_cls_init
        )


class FrameworkFileBase(object):
    """Base class to wrap models for interacting with Fritz."""

    def __init__(self, framework, model, is_byte_representation):
        self.is_byte_representation = is_byte_representation
        self.framework = framework
        self.model = model

    def to_bytes(self):
        """Convert model to bytes.

        Returns: io.BytesIO object
        """
        raise NotImplementedError("Subclass class must implement")

    @classmethod
    def build_from_file(cls, path, skip_model_cls_init=False):
        """Build Framework File from model path.

        Args:
            path (str): Path to file.
            skip_model_cls_init (bool): If True, model is loaded directly
                from file and not instantiated as the Framework type.

        Returns: FrameworkFileBase instance.
        """
        raise NotImplementedError("Subclass class must implement")


class KerasFile(FrameworkFileBase):
    """Wrapper class for Keras model."""

    def __init__(self, model, is_byte_representation=False):
        super().__init__(KERAS, model, is_byte_representation)

    def to_bytes(self):
        if self.is_byte_representation:
            return io.BytesIO(self.model)
        # need to actually get the bytes here.
        tmp_file = tempfile.NamedTemporaryFile(suffix=".h5")
        self.model.save_weights(tmp_file.name)
        tmp_file.seek(0)

        return tmp_file.read()

    @classmethod
    def build_from_file(cls, path, skip_model_cls_init=False):
        """Build Framework File from model path.

        Args:
            path (str): Path to file.
            skip_model_cls_init (bool): If True, model is loaded directly
                from file and not instantiated as the Framework type.

        Returns: KerasFile instance.
        """
        if skip_model_cls_init:
            model = open(path, "rb").read()
            return cls(model, is_byte_representation=True)

        # Keras is imported here so that we don't load keras and tensorflow
        # right away on all fritz imports.
        import keras

        model = keras.models.load_model(path)
        return cls(model)


class CoreMLFile(FrameworkFileBase):
    """Wrapper class for Core ML model."""

    def __init__(self, model, is_byte_representation=False):
        super().__init__(CORE_ML, model, is_byte_representation)

    def to_bytes(self):
        if self.is_byte_representation:
            return io.BytesIO(self.model)

        serialized_spec = self.model.get_spec().SerializeToString()
        return io.BytesIO(serialized_spec)

    @classmethod
    def build_from_file(cls, path, skip_model_cls_init=False):
        """Build Framework File from model path.

        Args:
            path (str): Path to file.
            skip_model_cls_init (bool): If True, model is loaded directly
                from file and not instantiated as the Framework type.

        Returns: CoreMLFile instance.
        """
        if skip_model_cls_init:
            model = open(path, "rb").read()
            return cls(model, is_byte_representation=True)

        # lazy load to prevent loading unless we need it.
        import coremltools

        model = coremltools.models.MLModel(path)
        return cls(model)


class TensorFlowLiteFile(FrameworkFileBase):
    """Wrapper class for TensorFlow Lite model."""

    def __init__(self, model):
        super().__init__(TENSORFLOW_LITE, model, True)

    def to_bytes(self):
        return io.BytesIO(self.model)

    @classmethod
    def build_from_file(cls, path, skip_model_cls_init=False):
        model = open(path, "rb").read()
        return cls(model)


class TensorFlowMobileFile(FrameworkFileBase):
    """Wrapper class for TensorFlow Mobile model."""

    def __init__(self, model):
        super().__init__(TENSORFLOW_MOBILE, model, True)

    def to_bytes(self):
        return io.BytesIO(self.model)

    @classmethod
    def build_from_file(cls, path, skip_model_cls_init=False):
        model = open(path, "rb").read()
        return cls(model)


class SnapMLTensorFlowFile(FrameworkFileBase):
    """Wrapper class for Snap ML model."""

    def __init__(self, model, is_byte_representation=False):
        super().__init__(SNAPML_TF, model, is_byte_representation)

    def to_bytes(self):
        return io.BytesIO(self.model.SerializeToString())

    @classmethod
    def build_from_file(cls, path, skip_model_cls_init=False):
        model = open(path, "rb").read()
        # pylint: disable=no-member
        model = tf.compat.v1.GraphDef.FromString(model)
        return cls(model)


class SnapMLONNXFile(FrameworkFileBase):
    """Wrapper class for Snap ML model."""

    def __init__(self, model, is_byte_representation=False):
        super().__init__(SNAPML_ONNX, model, is_byte_representation)

    def to_bytes(self):
        return io.BytesIO(self.model.SerializeToString())

    @classmethod
    def build_from_file(cls, path, skip_model_cls_init=False):
        model = onnx.load_model(path)
        return cls(model)


TENSORFLOW_LITE = ModelFramework("tflite", ".tflite", TensorFlowLiteFile)
TENSORFLOW_MOBILE = ModelFramework("tfmobile", ".pb", TensorFlowMobileFile)
CORE_ML = ModelFramework("coreml", ".mlmodel", CoreMLFile)
KERAS = ModelFramework("keras", ".h5", KerasFile)
SNAPML_TF = ModelFramework("snapml_tf", ".pb", SnapMLTensorFlowFile)
SNAPML_ONNX = ModelFramework("snapml_onnx", ".onnx", SnapMLONNXFile)


def all_frameworks():
    """List of all supported frameworks.

    Returns: List[ModelFramework]
    """
    return [TENSORFLOW_LITE, CORE_ML, KERAS, SNAPML_TF, SNAPML_ONNX]


def get_from_filename(filename):
    """Gets the corresponding `ModelFramework` from a filename.

    Args:
        filename (str): Filename.

    Returns: Framework if it is supported.
    """
    for framework in all_frameworks():
        if filename.endswith(framework.extension):
            return framework

    return None


def build_framework_file(path, skip_model_cls_init=False):
    """Builds the framework file from path.

    Args:
        path (str): Path.
        skip_model_cls_init (bool): If True, will not load with Framework,
            but just read bytes directly from disk.

    Returns: FrameworkFileBase if it is supported.
    """
    framework = get_from_filename(path)
    if not framework:
        return None

    return framework.build_file(path, skip_model_cls_init=skip_model_cls_init)
