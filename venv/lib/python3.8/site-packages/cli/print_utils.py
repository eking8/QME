"""Helpers for printing in the cli."""
import click


CODE_COLOR = "yellow"
IMPORTANT_COLOR = "green"
ACK_COLOR = "yellow"
ERROR_COLOR = "red"


def code(code):
    """Show a code example."""
    click.echo(click.style(code, fg=CODE_COLOR))


def ack(content):
    """Create acknowledged text after a user action."""
    click.echo(click.style(content, fg=ACK_COLOR))


def message(content):
    """Create acknowledged text after a user action."""
    click.echo(content)


def notice(content):
    """Print notice describing summary of section. """
    click.echo(click.style(content, fg=IMPORTANT_COLOR))


def alert(content):
    """Print alert. """
    click.echo(click.style(content, fg=ERROR_COLOR))


def error(content, fix_content=None):
    """Create an error message with optional content to fix the issue."""
    click.echo(click.style("[ERROR]: " + content, fg=ERROR_COLOR))
    if fix_content:
        click.echo(click.style(fix_content, fg=ERROR_COLOR))


def warn(content, fix_content=None):
    """Create a warning message with optional content to fix the issue."""
    click.echo(click.style("[WARNING]: " + content, fg="yellow"))
    if fix_content:
        click.echo(click.style(fix_content, fg="yellow"))


def title(content):
    """Create a title in the terminal."""
    click.echo(click.style("\n--------------------------", fg=IMPORTANT_COLOR))
    click.echo(click.style(content, fg=IMPORTANT_COLOR))
    click.echo(click.style("--------------------------", fg=IMPORTANT_COLOR))


def field(name, value):
    """Print a field.

    Args:
        name (str): Name of field.
        value (str): Value.
    """
    line = "  {name:20}: {value}".format(name=name, value=value)
    click.echo(click.style(line, fg=IMPORTANT_COLOR))


def header(content):
    """Print header with newline before and dashes after.

    Args:
        content (str): Content of header.
    """
    click.echo("\n" + content)
    click.echo("-" * len(content))


def formatted_table(formats, rows):
    """Print formatted table.

    Args:
        formats (list[tuple]): Tuple of (key, format, header_name)
        rows (List[Dict]): Data rows.
    """
    if not rows:
        return

    format_str = " | ".join(
        column_fmt % max(*[len(str(row[key])) for row in rows], len(header))
        for key, column_fmt, header in formats
    )
    header_values = {key: value for key, _, value in formats}
    header = format_str.format(**header_values)

    click.echo(header)
    click.echo("-" * len(header))

    for row in rows:
        click.echo(format_str.format(**row))

    click.echo("")


def make_plural(count, word):
    """Makes world plural if more than one item.

    Args:
        count (int): count of items.
        word (str): Word.

    Returns: Modified word.
    """
    if count > 1:
        return word + "s"

    return word
