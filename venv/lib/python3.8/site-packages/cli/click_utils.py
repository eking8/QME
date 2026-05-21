"""
Utilities to help running click commands.

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""

import click
from click import decorators


def make_pass_decorator(object_type, required=True):
    """Finds object of type object_type in ctx and passes as first argument.

    Args:
        object_type: The type of the object to pass.
        required: If set to true, object must be present or an error is thrown.

    Returns: Decorator to find function.
    """

    def decorator(f):
        def new_func(*args, **kwargs):
            ctx = decorators.get_current_context()
            obj = ctx.find_object(object_type)
            if obj is None and required:
                click.echo(ctx.command.get_help(ctx))
                click.echo("")
                raise click.ClickException(
                    "Managed to invoke callback without a "
                    "context object of type %r existing" % object_type.__name__
                )
            return ctx.invoke(f, obj, *args, **kwargs)

        return decorators.update_wrapper(new_func, f)

    return decorator


class OptionalArgumentGroup(click.Group):
    """Group that supports subcommands with optional parent arguments.

    For instance, for the fritz model <model_id> upload <file> command
    the <model_id> command is optional.  Without this group, "upload"
    is treated as the model ID.
    """

    def parse_args(self, ctx, args):
        """Parse args."""
        if not args:
            super().parse_args(ctx, args)
            return

        if args[0] in self.commands:
            if len(args) == 1 or args[1] not in self.commands:
                args.insert(0, "")
        super().parse_args(ctx, args)
