"""
fritz.utils
~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
import fritz


def _get_object_classes():
    """Get object classes by object name."""
    return {
        fritz.ModelVersion.OBJECT_NAME: fritz.ModelVersion,
        fritz.ModelSnapshot.OBJECT_NAME: fritz.ModelSnapshot,
        fritz.Model.OBJECT_NAME: fritz.Model,
        fritz.App.OBJECT_NAME: fritz.App,
        fritz.Project.OBJECT_NAME: fritz.Project,
        fritz.ModelGradeReport.OBJECT_NAME: fritz.ModelGradeReport,
    }


def convert_to_fritz_object(response_data):
    """Convert response data to a corresponding FritzObject

    Args:
        response_data (dict): Response data from request.

    Returns:
        FritzObject: converted dict into a fritz object.
    """
    if not isinstance(response_data, dict):
        return response_data

    for key in response_data:
        response_data[key] = convert_to_fritz_object(response_data[key])

    object_classes = _get_object_classes()
    if "object_name" in response_data:
        return object_classes[response_data["object_name"]](**response_data)

    return response_data
