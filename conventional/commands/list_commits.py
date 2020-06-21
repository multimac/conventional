import asyncio
import json
import logging
import os
from typing import Optional, TextIO

import confuse

from .. import git
from ..util.io import AsyncFileObject, json_defaults
from . import parse_commit

logger = logging.getLogger(__name__)


async def main(
    config: confuse.Configuration,
    *,
    output: TextIO,
    from_rev: Optional[str],
    from_last_tag: bool,
    to_rev: str,
    reverse: bool,
    parse: bool,
    include_unparsed: bool,
) -> None:

    if include_unparsed and not parse:
        logger.warning("--include-unparsed is ignored without --parse")

    if not parse:
        await list_commits(
            config,
            output=output,
            from_rev=from_rev,
            from_last_tag=from_last_tag,
            to_rev=to_rev,
            reverse=reverse,
        )
        return

    async def _list_commits(fd: int) -> None:
        async with AsyncFileObject(os.fdopen(fd, "w")) as list_output:
            await list_commits(
                config,
                output=list_output,
                from_rev=from_rev,
                from_last_tag=from_last_tag,
                to_rev=to_rev,
                reverse=reverse,
            )

    async def _parse_commit(fd: int) -> None:
        async with AsyncFileObject(os.fdopen(fd)) as parse_input:
            await parse_commit.main(
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
            excluded = config["tags"]["exclude"].get(confuse.StrSeq(split=False))
            try:
                tag_filter = config["tags"]["filter"].get(str)
            except confuse.NotFoundError:
                tag_filter = None

            tags = await git.get_tags(pattern=tag_filter, sort="creatordate", reverse=True)
            from_rev = next(tag["name"] for tag in tags if tag["name"] not in excluded)

    loop = asyncio.get_event_loop()
    async for commit in git.get_commits(start=from_rev, end=to_rev, reverse=reverse):
        line = json.dumps(commit, default=json_defaults)
        await loop.run_in_executor(None, output.writelines, [line, "\n"])
