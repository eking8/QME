# pylint: disable=missing-docstring,redefined-outer-name
import enum


class FeatureType(enum.Enum):
    """An enum of feature types.

    Feature types describe the top-level task of a model, e.g. pose estimation.
    Models may be given a specific feature type so that it can be linked
    with other systems such as post-processing.
    """

    IMAGE_SEGMENTATION = "image-segmentation"
    POSE_ESTIMATION = "pose-estimation"
    STYLE_TRANSFER = "style-transfer"
    OBJECT_DETECTION = "object-detection"
    IMAGE_LABELING = "image-labeling"
    SALIENCY = "saliency"
    AUDIO_CLASSIFICATION = "audio-classification"
    GAN = "gan"
