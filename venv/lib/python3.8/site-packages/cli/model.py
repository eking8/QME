"""
fritz.api_resources.model_version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
import os
import click
from termcolor import colored

import fritz
from fritz import feature_type
from cli import print_utils
from cli import click_utils


# A decorator to pass the model to the current command.
# pylint: disable=invalid-name
pass_model = click_utils.make_pass_decorator(fritz.Model, required=True)
pass_model_optional = click_utils.make_pass_decorator(fritz.Model, required=False)


@click.command()
@click.option("--project-id", help="Restrict results to Project ID")
@click.option("--all-projects", help="List models from all projects", is_flag=True)
@click.option(
    "--include-archived", help="Include archived models in list", is_flag=True
)
@click.option(
    "--feature-type",
    type=click.Choice([feature.value for feature in feature_type.FeatureType]),
    help="Feature type to filter on.",
)
@click.option(
    "--framework",
    type=click.Choice(
        [framework.name for framework in fritz.frameworks.all_frameworks()]
    ),
    help="Model framework to filter on.",
)
@click.option(
    "--include-archived", help="Include archived models in list", is_flag=True
)
def models(
    project_id=None,
    all_projects=False,
    feature_type=None,
    include_archived=False,
    framework=None,
):
    """List all models."""
    row_format = [
        ("name", "{name:%s}", "Model Name"),
        ("feature_type", "{feature_type:%s}", "Feature Type"),
        ("framework", "{framework:%s}", "Framework"),
        ("version", "{version:%s}", "Active Version"),
        ("created", "{created:%s}", "Created"),
        ("updated", "{updated:%s}", "Updated"),
        ("model_id", "{model_id:%s}", "Model ID"),
    ]
    rows = []

    models = fritz.Model.list(project_id=project_id, all_projects=all_projects)
    if not include_archived:
        models = [model for model in models if not model.archived_at]

    if feature_type:
        models = [model for model in models if model.feature_type == feature_type]
    if framework:
        models = [model for model in models if model.framework.name == framework]
    if all_projects:
        project_message = "all projects."
    else:
        project = fritz.Project.get(project_id or fritz.project_id)
        project_message = project.name + " project."

    print_utils.notice(
        "\n{num_models} models in {project_message}\n".format(
            num_models=len(models), project_message=project_message
        )
    )

    for model in models:

        row = {
            "name": model.name,
            "framework": model.framework.name,
            "feature_type": model.feature_type or "--",
            "version": model.active_version,
            "created": model.created_date,
            "updated": model.updated_date,
            "model_id": model.id,
        }
        rows.append(row)

    rows.sort(key=lambda x: x["updated"], reverse=True)
    print_utils.formatted_table(row_format, rows)


@click.group(
    cls=click_utils.OptionalArgumentGroup,
    invoke_without_command=True,
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
)
@click.argument("model_id", required=False)
@click.pass_context
def model(ctx, model_id):
    """Commands for working with Fritz Models."""
    model = None
    if model_id:
        model = fritz.Model.get(model_id=model_id)
        ctx.obj = model

    if model and not ctx.invoked_subcommand:
        ctx.invoke(details)
        click.echo(ctx.command.get_help(ctx))
        return

    if not model and not ctx.invoked_subcommand:
        click.echo(ctx.command.get_help(ctx))
        return


@model.command()
@click.option("--description", help="Updated model description")
@click.option("--active-version", type=int, help="Active model version.")
@click.option("--name", help="Name of model")
@click.option(
    "--is-global", help="If true, all projects and accounts can access model."
)
@click.option("--archive", type=bool, help="If true, model will be archived")
@click.option(
    "--feature-type",
    type=click.Choice([feature.value for feature in feature_type.FeatureType]),
    help="Feature type for model.",
)
@pass_model
def update(model, **updates):
    """Update model.

    Args:
        updates: Dict of updates.
    """
    updates = {key: value for key, value in updates.items() if value is not None}
    if not updates:
        print_utils.warn("\nNo updates, aborting.\n")
        return

    model = model.update(**updates)
    print_utils.message(model.summary())


@model.command()
@click.option(
    "--version",
    type=int,
    help="Specific version number. If not specified, uses latest",
)
@pass_model
@click.argument("output-dir", required=False)
def download(model, output_dir=None, version=None):
    """Download model version.

    Args:
        model_id: Model ID
        version_number: Optional version to download,
            defaults to active_version.
        output_dir: Optional directory for model download.
    """
    version, downloaded_path = model.download(
        version_number=version, output_dir=output_dir
    )
    if not version:
        print_utils.warn("\nDid not find model version for version" + str(version))

    print_utils.ack(
        (
            "Successfully downloaded {model_name} - {version} " "to {downloaded_path}"
        ).format(
            model_name=model.name,
            version=version.version_number,
            downloaded_path=downloaded_path,
        )
    )


@model.command()
@click.option("--deploy", is_flag=True, flag_value=True)
@click.option("--api-key", help="Fritz API Key")
@click.option("--project-id", help="Fritz Project ID")
@click.option(
    "--skip-model-init",
    is_flag=True,
    help="Do not initialize model, just upload bytes.",
)
@click.option(
    "--use-existing-model-on-duplicate-name",
    is_flag=True,
    help=(
        "Creates a new version of an existing model if there is already a "
        "model in the project with the same name and format."
    ),
)
@click.argument("path")
@pass_model_optional
def upload(
    model,
    path,
    deploy=False,
    api_key=None,
    project_id=None,
    skip_model_init=False,
    use_existing_model_on_duplicate_name=False,
):

    """Upload model version to Fritz API.

    Args:
        path: Path to model file.
        model_id: Model ID of existing model.
        deploy: If True, will deploy newly uploaded model.
    """
    filename = os.path.basename(path)
    model_file = fritz.frameworks.build_framework_file(
        path,
        # Skipping initalization of the model.  Loading the class (say
        # from Keras) fails a handful of times with custom operations.
        skip_model_cls_init=True,
    )
    model_id = model.id if model else None
    version, snapshot, fritz_model = fritz.ModelVersion.create(
        filename=filename,
        data=model_file.to_bytes(),
        model_id=model_id,
        set_active=deploy,
        api_key=api_key,
        project_id=project_id,
        use_existing_model_on_duplicate_name=(use_existing_model_on_duplicate_name),
    )

    print_utils.message(fritz_model.summary())
    print_utils.message(version.summary())

    return version, snapshot, model


@model.command()
@click.option("--version-id", help="Existing model version.")
@click.option("--api-key", help="Fritz API Key")
@click.argument("path", required=False)
@click.pass_context
def benchmark(ctx, version_id=None, path=None, api_key=None):
    """Get model grader report for a model version or Keras file.

    Args:
        version_id: Optional ModelVersion ID.
        path: Optional Path to model
    """
    if not version_id and not path:
        print(colored("Version ID or path to model required.", "yellow"))
        return
    if not version_id:
        version, _, _ = ctx.invoke(upload, path=path, skip_model_init=False)
    else:
        version = fritz.ModelVersion.get(version_id, api_key=api_key)

    report = version.benchmark()
    report.summary()


@model.command()
@pass_model
@click.pass_context
def details(ctx, model):
    """Get details about specific model.

    Args:
        id: Model ID to query.
    """
    click.echo("")
    print_utils.message(model.summary())
    click.echo("")
    ctx.forward(versions)


@model.command()
@pass_model
def versions(model):
    """List Model Versions for a specific model_id."""
    versions = fritz.ModelVersion.list(model.id)
    versions_name = print_utils.make_plural(len(versions), "version")
    print_utils.notice(
        "\n{num_versions} model {versions_name} in {model_name}\n".format(
            num_versions=len(versions),
            versions_name=versions_name,
            model_name=model.name,
        )
    )

    row_format = [
        ("filename", "{filename:%s}", "Provided Filename"),
        ("version", "{version:%s}", "Version"),
        ("created", "{created:%s}", "Created"),
        ("model_size", "{model_size:>%s}", "Model Size"),
        ("version_id", "{version_id:%s}", "Version ID"),
        ("loss", "{loss:%s.4}", "Loss"),
    ]
    rows = []

    for version in versions:
        row = {
            "filename": version.provided_filename,
            "version": version.version_number,
            "created": version.created_date,
            "model_size": version.model_size,
            "version_id": version.id,
            "loss": version.loss or "",
        }
        rows.append(row)

    rows.sort(key=lambda x: x["version"], reverse=True)
    print_utils.formatted_table(row_format, rows)


@model.group(invoke_without_command=True)
@click.argument("version_id")
@pass_model
@click.pass_context
def version(ctx, model, version_id):
    """Commands related to specific versions of a model."""
    version = fritz.ModelVersion.get(version_id=version_id)
    ctx.obj = version

    if version and not ctx.invoked_subcommand:
        ctx.invoke(version_details)
        click.echo("")
        click.echo(ctx.command.get_help(ctx))


@version.command("details")
@click.pass_context
def version_details(ctx):
    """Get Details for a specific Model Version.

    Args:
        version_id: Version ID to query.
    """
    print_utils.message(ctx.obj.summary())
