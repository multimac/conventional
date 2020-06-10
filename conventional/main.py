import importlib
import io
import logging
import pathlib
from typing import Optional

import click
import click_log
import confuse

logger = logging.getLogger()
click_log.basic_config(logger)

pass_config = click.make_pass_decorator(confuse.Configuration)
plugin_module = "commands"


class PluggableCli(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []

        path = pathlib.Path(__file__).parent.joinpath(plugin_module)
        for child in path.iterdir():
            if child.suffix == ".py" and child.stem != "__init__":
                rv.append(child.stem.replace("_", "-"))

        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = importlib.import_module(
            ".".join(["conventional", plugin_module, name.replace("-", "_")])
        )
        return ns.main


@click.command(cls=PluggableCli)
@click_log.simple_verbosity_option(logger)
@click.option("--config-file", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def main(ctx: click.Context, config_file: Optional[click.Path]) -> None:
    """
    This commandline program provides a series of commands for validating and
    updating stacks in CloudFormation. The config file specified via '--config'
    details where to find the template and other information required to validate
    no unknown changes have been made.

    Examples:
    List the stacks that should be deployed within an environment.

    \b
    main.py -c "cloudformation-config.yml" -g "development" info list-stacks

    Validate a stack against it's template in source control and detect
    and resources which have drifted from their expected state.

    \b
    main.py -c "cloudformation-config.yml" -g "development" stacks validate detect-drift

    Update a stack and watch the list of events, exiting with an exit code 1 if
    the update fails.

    \b
    main.py -c "cloudformation-config.yml" -g "development" stacks update --ami ami-01234567890123456 get-events --exit-code
    """

    config = confuse.Configuration("Conventional", "conventional")

    if config_file is not None:
        config.set_file(config_file)

    ctx.obj = config


if __name__ == "__main__":
    main()
