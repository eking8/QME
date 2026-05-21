"""
cli.app.app_files

Methods to help setup Android project with Fritz App.
"""
from typing import List
import click
from cli import print_utils
from cli.app import code_snippet


def update(snippets: List[code_snippet.CodeSnippet]):
    """Update all code snippets to connect to Fritz.

    Args:
        snippets: List of CodeSnippets to update.
    """
    up_to_date = [
        snippet for snippet in snippets if snippet.is_added and snippet.is_updated
    ]
    missing = [snippet for snippet in snippets if not snippet.is_added]
    needs_update = [snippet for snippet in snippets if not snippet.is_updated]

    print_utils.message("Updating code snippets with latest configuration.")

    if up_to_date:
        print_utils.notice("\nThe following snippets are up to date:")
        for snippet in up_to_date:
            print_utils.notice("  - " + str(snippet))

    if needs_update:
        print_utils.notice("\nThe following snippets will be updated:")
        for snippet in needs_update:
            print_utils.ack("  - " + str(snippet))

    if missing:
        print_utils.ack("\nThe following snippets will be added:")
        for snippet in missing:
            print_utils.ack("  - " + str(snippet))
        print_utils.ack("")

    if not click.confirm("Continue updating app files?", default=True):
        return

    errors = []

    for snippet in missing:
        try:
            snippet.add()
            print_utils.notice("Successfully added code in " + str(snippet))
        except code_snippet.SnippetExecutionError as err:
            print_utils.error(str(err))
            errors.append(err)

    for snippet in needs_update:
        try:
            snippet.update()
            print_utils.notice("Successfully added code in " + str(snippet))
        except code_snippet.SnippetExecutionError as err:
            print_utils.error(str(err))
            errors.append(err)

    if errors:
        raise code_snippet.SnippetExecutionError(
            "Some code changes failed to apply properly"
        )
