import asyncio
import datetime
import importlib
import json
import logging
from typing import Any, Optional, TextIO, TypedDict

import click
import confuse
import dateutil.tz

from .. import git
from ..main import pass_config
from ..parser.base import Parser

logger = logging.getLogger(__name__)


class ParsedCommit(TypedDict, total=False):
    commit: git.Commit
    parsed: Any


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


async def async_main(
    config: confuse.Configuration,
    *,
    input: TextIO,
    output: TextIO,
    include_unparsed: Optional[bool],
) -> None:
    if include_unparsed is not None:
        config.set_args({"parser.include-unparsed": include_unparsed}, dots=True)

    try:
        await async_main_impl(config, input=input, output=output)
    finally:
        input.close()
        output.close()


async def async_main_impl(config: confuse.Configuration, *, input: TextIO, output: TextIO) -> None:
    def _json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.astimezone(dateutil.tz.UTC).isoformat()

        raise TypeError("Type %s not serializable" % type(obj))

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
        parsed: Any = parser.parse(commit)

        if not config["parser"]["include-unparsed"].get(bool) and not parsed:
            continue

        data: ParsedCommit = {"commit": commit}
        if parsed:
            data["parsed"] = parsed

        line = json.dumps(data, default=_json_serial)
        await loop.run_in_executor(None, output.writelines, [line, "\n"])
