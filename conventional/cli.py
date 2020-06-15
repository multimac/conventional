import asyncio
import enum
import logging
import pathlib
from typing import List

import confuse
import typer

from .commands import group as main
from .util.typer import ColorFormatter, TyperHandler

handler = TyperHandler()
handler.formatter = ColorFormatter()

logger = logging.getLogger()
logging.basicConfig(handlers=[handler], force=True)

# Importing aiocache results in a warning being logged. Temporarily disable it
# until it has been imported.
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
    config_file: List[pathlib.Path] = typer.Option(
        None,
        exists=True,
        dir_okay=False,
        help="A file to read configuration values from. May be specified multiple times to combine configuration values from multiple files.",
    ),
    verbosity: Verbosity = typer.Option(
        Verbosity.info, case_sensitive=False, help="Set the verbosity of the logging."
    ),
) -> None:
    """
    Conventional - An extensible command-line tool for parsing and processing structured commits.
    """

    import aiocache
    from .util.config import find_project_configuration_file

    logging.getLogger().setLevel(getattr(logging, verbosity))

    # Reset aiocache log level since aiocache has now been imported and unnecessary
    # warning has been avioded.
    logging.getLogger("aiocache").setLevel(logging.NOTSET)

    config = confuse.Configuration("Conventional", "conventional")

    project_config_file = asyncio.run(find_project_configuration_file())
    if project_config_file is not None:
        logger.debug(f"Loading configuration file, {project_config_file.as_posix()}")
        config.set_file(project_config_file)

    for filename in config_file:
        logger.debug(f"Loading configuration file, {filename.as_posix()}")
        config.set_file(filename)

    ctx.obj = config


if __name__ == "__main__":
    main()
