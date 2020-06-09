import asyncio
import contextlib
import datetime
import io
import json
import logging
import os
from typing import List, TextIO

import click
import dateutil.tz

from .. import git, util
from ..parser.conventionalcommits.parser import ConventionalCommitParser
from . import parse_commit

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--output",
    type=click.File("w"),
    default="-",
    help="A file to write commits to. If `-`, commits will be written to stdout.",
)
@click.option("--parse", is_flag=True, help="If set, commits will be parsed with `parse-commit`.")
@click.option(
    "--include-unparsed",
    is_flag=True,
    help="If set, commits which fail to be parsed will be returned. See `parse-commit`.",
)
def main(**kwargs):
    asyncio.run(async_main(**kwargs))


async def async_main(output: TextIO, **kwargs) -> None:
    try:
        await async_main_impl(output=output, **kwargs)
    finally:
        output.close()


async def async_main_impl(output: TextIO, parse: bool, include_unparsed: bool) -> None:
    parser = ConventionalCommitParser()

    def _json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.astimezone(dateutil.tz.UTC).isoformat()

        raise TypeError("Type %s not serializable" % type(obj))

    if include_unparsed and not parse:
        logger.warning("--include-unparsed is ignored without --parse")

    loop = asyncio.get_event_loop()

    tasks: List[asyncio.Task] = []
    if parse:
        parse_input, parse_output = util.create_pipe_streams()
        parse_task = parse_commit.async_main(
            parse_input, output, include_unparsed=include_unparsed
        )

        logger.debug("Scheduling parse-commit task")
        tasks.append(asyncio.create_task(parse_task))
        output = parse_output

    gathered_tasks = asyncio.gather(*tasks)
    try:
        counter = 0

        async for commit in git.get_commits():
            line = json.dumps(commit, default=_json_serial)
            await loop.run_in_executor(None, output.writelines, [line, "\n"])
    except:
        gathered_tasks.cancel()
        raise
    finally:
        output.close()

        with contextlib.suppress(asyncio.CancelledError):
            await gathered_tasks
