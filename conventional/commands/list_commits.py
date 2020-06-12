import asyncio
import contextlib
import datetime
import io
import json
import logging
import os
from typing import List, Optional, TextIO

import click
import confuse
import dateutil.tz

from .. import git, util
from ..main import pass_config
from . import parse_commit

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--output",
    type=click.File("w"),
    default="-",
    help="A file to write commits to. If `-`, commits will be written to stdout.",
)
@click.option("--from", "from_rev")
@click.option("--from-last-tag", is_flag=True)
@click.option("--to", "to_rev", default="HEAD")
@click.option("--reverse", is_flag=True)
@click.option("--parse", is_flag=True, help="If set, commits will be parsed with `parse-commit`.")
@click.option(
    "--include-unparsed/--no-include-unparsed",
    is_flag=True,
    default=None,
    help="If set, commits which fail to be parsed will be returned. See `parse-commit`.",
)
@pass_config
def main(config: confuse.Configuration, **kwargs):
    asyncio.run(async_main(config, **kwargs))


async def async_main(config: confuse.Configuration, **kwargs) -> None:
    await async_main_impl(config, **kwargs)


async def async_main_impl(
    config: confuse.Configuration,
    *,
    output: TextIO,
    parse: bool,
    include_unparsed: Optional[bool],
    **kwargs,
) -> None:

    if include_unparsed and not parse:
        logger.warning("--include-unparsed is ignored without --parse")

    if not parse:
        await list_commits(config, output=output, **kwargs)
        return

    async def _list_commits(fd: int) -> None:
        async with util.AsyncFileObject(os.fdopen(fd, "w")) as list_output:
            await list_commits(config, output=list_output, **kwargs)

    async def _parse_commit(fd: int) -> None:
        async with util.AsyncFileObject(os.fdopen(fd)) as parse_input:
            await parse_commit.async_main(
                config, input=parse_input, output=output, include_unparsed=include_unparsed
            )

    read_fd, write_fd = os.pipe()
    list_task = _list_commits(write_fd)
    parse_task = _parse_commit(read_fd)

    await asyncio.gather(list_task, parse_task)


async def list_commits(
    config: confuse.Configuration,
    *,
    output: TextIO,
    from_rev: Optional[str],
    from_last_tag: bool,
    to_rev: str,
    reverse: bool,
) -> None:
    if from_last_tag:
        if from_rev is not None:
            logger.warning("--from-last-tag is ignored when combined with --from")
        else:
            excluded = config["tags"]["exclude"].get(confuse.StrSeq())
            try:
                tag_filter = config["tags"]["filter"].get(str)
            except confuse.NotFoundError:
                tag_filter = None

            tags = await git.get_tags(pattern=tag_filter, sort="creatordate", reverse=True)
            from_rev = next(tag["name"] for tag in tags if tag["name"] not in excluded)

    loop = asyncio.get_event_loop()
    async for commit in git.get_commits(start=from_rev, end=to_rev, reverse=reverse):
        line = json.dumps(commit, default=util.json_defaults)
        await loop.run_in_executor(None, output.writelines, [line, "\n"])
