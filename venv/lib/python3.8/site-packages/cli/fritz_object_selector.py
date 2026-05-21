"""
cli.fritz_object_selector

Functions to select a single fritz object from a click prompt.
"""
from typing import List, Optional
import click
import fritz
from cli import print_utils


def _row_chooser_prompt(rows, row_format, include_none=False):

    row_format = [("index", "{index:%s}", "Index")] + row_format

    new_objects = []

    # Giving option to not choose an item in the list
    if include_none:
        row = {key: "----" for key, _, _ in row_format}
        row["index"] = "[0]"
        # Setting the field of the first object as the value None
        row[row_format[1][0]] = "None"
        new_objects.append(row)

    for i, obj in enumerate(rows):
        object_with_index = dict(**obj)
        object_with_index["index"] = "[" + str(i + 1) + "]"
        new_objects.append(object_with_index)

    print_utils.formatted_table(row_format, new_objects)
    options = click.IntRange(min=0 if include_none else 1, max=len(new_objects))
    index = click.prompt("Select an index", type=options)
    if not index:
        return None

    return index - 1


def choose_app(
    apps: List[fritz.App], include_none: bool = False
) -> Optional[fritz.App]:
    """Prints app table to choose a single app from.

    Args:
        apps: Apps
        include_none: If True, includes option to not select app.

    Returns: Selected app
    """
    row_format = [
        ("name", "{name:%s}", "App Name"),
        ("apk_id", "{apk_id:%s}", "APK ID"),
        ("created", "{created:%s}", "Created"),
        ("project", "{project:%s}", "Project"),
    ]
    apps.sort(key=lambda x: x.created_at, reverse=True)
    projects = {}
    rows = []
    for app in apps:
        if app.project_id not in projects:
            projects[app.project_id] = fritz.Project.get(project_id=app.project_id)
        row = {
            "name": app.app_name,
            "apk_id": app.apk_id,
            "platform": app.platform,
            "created": app.created_date,
            "project": projects[app.project_id].name,
        }
        rows.append(row)

    index = _row_chooser_prompt(rows, row_format, include_none=include_none)

    if index is None:
        return None

    return apps[index]


def choose_model(
    models: List[fritz.Model], include_none: bool = False
) -> Optional[fritz.Model]:
    """Prints model table to choose a single model from.

    Args:
        models: Models
        include_none: If True, includes option to not select model.

    Returns: Selected model
    """
    row_format = [
        ("name", "{name:%s}", "Name"),
        ("model_format", "{model_format:%s}", "Format"),
        ("created", "{created:%s}", "Created"),
        ("updated", "{updated:%s}", "Updated"),
        ("active_version", "{active_version:%s}", "Active Version"),
    ]
    models.sort(key=lambda x: x.updated_at, reverse=True)
    rows = []
    for model in models:
        row = {
            "name": model.name,
            "model_format": model.model_format,
            "created": model.created_date,
            "updated": model.updated_date,
            "active_version": model.active_version,
        }
        rows.append(row)

    index = _row_chooser_prompt(rows, row_format, include_none=include_none)

    if index is None:
        return None

    return models[index]


def choose_project(
    projects: List[fritz.Project], include_none: bool = False
) -> Optional[fritz.Project]:
    """Prints project table and prompts choice of one.

    Args:
        projects: Projects
        include_none: If True, includes option to not select project.

    Returns: Selected project
    """
    row_format = [
        ("name", "{name:%s}", "Project Name"),
        ("created", "{created:%s}", "Created"),
        ("project_id", "{project_id:%s}", "Project ID"),
    ]
    rows = []

    projects.sort(key=lambda x: x.created_at, reverse=True)

    for project in projects:
        row = {
            "name": project.name,
            "created": project.created_date,
            "project_id": project.id,
        }
        rows.append(row)

    index = _row_chooser_prompt(rows, row_format, include_none=include_none)
    if index is None:
        return None

    return projects[index]
