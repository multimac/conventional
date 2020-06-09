import asyncio
import datetime
import json
import logging
from typing import Any, TextIO

import click
import dateutil.tz

from .. import git
from ..parser.conventionalcommits.parser import ConventionalCommitParser

logger = logging.getLogger(__name__)


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
    "--include-unparsed",
    is_flag=True,
    help="If set, commits which fail to be parsed will be returned.",
)
def main(**kwargs):
    asyncio.run(async_main(**kwargs))


async def async_main(input: TextIO, output: TextIO, **kwargs) -> None:
    try:
        await async_main_impl(input=input, output=output, **kwargs)
    finally:
        input.close()
        output.close()


async def async_main_impl(input: TextIO, output: TextIO, include_unparsed: bool) -> None:
    parser = ConventionalCommitParser()

    def _json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.astimezone(dateutil.tz.UTC).isoformat()

        raise TypeError("Type %s not serializable" % type(obj))

    loop = asyncio.get_event_loop()

    while True:
        input_line = await loop.run_in_executor(None, input.readline)

        if not input_line:
            break

        commit: git.Commit = git.create_commit(**json.loads(input_line))
        parsed: Any = parser.parse(commit)

        if not include_unparsed and not parsed:
            continue

        data = {"commit": commit}
        if parsed:
            data["parsed"] = parsed

        line = json.dumps(data, default=_json_serial)
        await loop.run_in_executor(None, output.writelines, [line, "\n"])
