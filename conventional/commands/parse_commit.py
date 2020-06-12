import asyncio
import datetime
import importlib
import json
import logging
from typing import Any, Optional, TextIO, TypedDict

import click
import confuse
import dateutil.tz

from .. import git, util
from ..main import pass_config
from ..parser.base import Parser

logger = logging.getLogger(__name__)


class Change(TypedDict, total=False):
    source: git.Commit
    data: Any


@click.command()
@click.option(
    "--input",
    type=click.File("r"),
    default="-",
    help="A file to read commits from. If `-`, commits will be read from stdin.",
)
@click.option(
    "--output",
    type=click.File("w"),
    default="-",
    help="A file to write parsed commits to. If `-`, parsed commits will be written to stdout.",
)
@click.option(
    "--include-unparsed/--no-include-unparsed",
    is_flag=True,
    default=None,
    help="If set, commits which fail to be parsed will be returned.",
)
@pass_config
def main(config: confuse.Configuration, **kwargs):
    asyncio.run(async_main(config, **kwargs))


async def async_main(config: confuse.Configuration, **kwargs) -> None:
    await async_main_impl(config, **kwargs)


async def async_main_impl(
    config: confuse.Configuration, *, input: TextIO, output: TextIO, include_unparsed: bool
) -> None:
    def _load_parser(config: confuse.Configuration) -> Parser[Any]:
        parser_config = config["parser"]
        module = parser_config["module"].get(str)
        name = parser_config["name"].get(str)
        custom_config = parser_config["config"]

        return getattr(importlib.import_module(module), name)(custom_config)

    parser = _load_parser(config)
    loop = asyncio.get_event_loop()

    while True:
        input_line = await loop.run_in_executor(None, input.readline)

        if not input_line:
            break

        commit: git.Commit = git.create_commit(**json.loads(input_line))
        data: Any = parser.parse(commit)

        if not include_unparsed and not data:
            continue

        change: Change = {"source": commit}
        if data:
            change["data"] = data

        line = json.dumps(change, default=util.json_defaults)
        await loop.run_in_executor(None, output.writelines, [line, "\n"])
