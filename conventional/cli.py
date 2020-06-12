import enum
import logging
import pathlib

import confuse
import typer

from . import util
from .commands import group as main

handler = util.TyperHandler()
handler.formatter = util.ColorFormatter()

logger = logging.getLogger()
logging.basicConfig(handlers=[handler], force=True)

logging.getLogger("aiocache").setLevel(logging.ERROR)


class Verbosity(str, enum.Enum):
    critical = "CRITICAL"
    debug = "DEBUG"
    error = "ERROR"
    fatal = "FATAL"
    info = "INFO"
    warning = "WARNING"


@main.callback()
def init(
    ctx: typer.Context,
    config_file: pathlib.Path = typer.Option(
        None, exists=True, dir_okay=False, help="A file to read configuration values from.",
    ),
    verbosity: Verbosity = typer.Option(
        Verbosity.info, case_sensitive=False, help="Set the verbosity of the logging."
    ),
) -> None:
    """
    Conventional - An extensible command-line tool for parsing and processing structured commits.
    """

    logging.getLogger().setLevel(getattr(logging, verbosity))

    config = confuse.Configuration("Conventional", "conventional")
    if config_file is not None:
        config.set_file(config_file)

    ctx.obj = config


if __name__ == "__main__":
    main()
