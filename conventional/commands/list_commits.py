import json
import logging
from typing import Any, AsyncIterable, Optional, TextIO

import confuse

from .. import git
from ..util.io import json_defaults

logger = logging.getLogger(__name__)


async def cli_main(
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

    stream = main(
        config,
        from_rev=from_rev,
        from_last_tag=from_last_tag,
        to_rev=to_rev,
        reverse=reverse,
    )  # type: AsyncIterable[Any]

    if parse:
        from .parse_commit import main as parse_commit

        stream = parse_commit(config, input=stream, include_unparsed=include_unparsed)

    async for item in stream:
        line = json.dumps(item, default=json_defaults)
        output.writelines([line, "\n"])


async def main(
    config: confuse.Configuration,
    *,
    from_rev: Optional[str],
    from_last_tag: bool,
    to_rev: str,
    reverse: bool,
) -> AsyncIterable[git.Commit]:

    if from_last_tag:
        if from_rev is not None:
            logger.warning("--from-last-tag is ignored when combined with --from")
        else:
            excluded = config["tags"]["exclude"].get(confuse.StrSeq(split=False))
            try:
                tag_filter = config["tags"]["filter"].get(str)
            except confuse.NotFoundError:
                tag_filter = None

            tags = await git.get_tags(
                pattern=tag_filter, sort="creatordate", reverse=True
            )
            from_rev = next(tag["name"] for tag in tags if tag["name"] not in excluded)

    async for commit in git.get_commits(start=from_rev, end=to_rev, reverse=reverse):
        yield commit
