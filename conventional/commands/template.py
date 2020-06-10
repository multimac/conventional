import asyncio
import contextlib
import datetime
import fnmatch
import json
import logging
from typing import Any, AsyncIterable, Dict, List, Optional, TextIO, Tuple, cast

import click
import confuse
import dateutil.tz
import jinja2

from .. import git, util
from ..main import pass_config
from . import list_commits
from .parse_commit import ParsedCommit

logger = logging.getLogger(__name__)

DEFAULT = object()


@click.command()
@click.option("--input", type=click.File("r"), default=None)
@click.option("--output", type=click.File("w"), default="-")
@click.option("--tag-filter", type=str)
@click.option(
    "--include-unparsed/--no-include-unparsed",
    is_flag=True,
    default=None,
    help="If set, commits which fail to be parsed will be returned. See `parse-commit`.",
)
@pass_config
def main(config: confuse.Configuration, **kwargs):
    asyncio.run(async_main(config, **kwargs))


async def async_main(
    config: confuse.Configuration, *, input: Optional[TextIO], output: TextIO, **kwargs
) -> None:
    try:
        await async_main_impl(config, input=input, output=output, **kwargs)
    finally:
        if input is not None:
            input.close()

        output.close()


async def async_main_impl(
    config: confuse.Configuration,
    *,
    input: Optional[TextIO],
    output: TextIO,
    include_unparsed: bool,
    tag_filter: str,
) -> None:
    def _read_config(view, default=DEFAULT, typ=str):
        try:
            return view.get(typ)
        except confuse.NotFoundError:
            if default is DEFAULT:
                raise

            return default

    loop = asyncio.get_event_loop()

    tasks: List[asyncio.Task] = []
    if input is None:
        list_input, list_output = util.create_pipe_streams()
        list_task = list_commits.async_main(
            config,
            output=list_output,
            include_unparsed=include_unparsed,
            parse=True,
            from_rev=None,
            to_rev="HEAD",
        )

        logger.debug("Scheduling list-commits task")
        tasks.append(asyncio.create_task(list_task))
        input = list_input

    gathered_tasks = asyncio.gather(*tasks)
    try:
        versioned_commits: List[
            Tuple[Optional[git.Tag], Dict[Optional[str], List[ParsedCommit]]]
        ] = []

        commits: Dict[Optional[str], List[ParsedCommit]] = {}
        versioned_commits.append((None, commits))

        while True:
            input_line = await loop.run_in_executor(None, input.readline)

            if not input_line:
                break

            data = json.loads(input_line)
            commit = cast(ParsedCommit, data)

            if commit["commit"]["tags"]:
                tags = commit["commit"]["tags"]
                if tag_filter:
                    tags = [tag for tag in tags if fnmatch.fnmatch(tag["name"], tag_filter)]

                if tags:
                    tag = sorted(tags, key=lambda tag: tag["name"])[0]

                    logger.debug(f"Found version, {tag['name']}")
                    if commits:
                        logger.debug(f"({len(commits)} commits in previous version)")

                    commits = {}
                    versioned_commits.append((tag, commits))

            typ = commit["parsed"]["subject"]["type"] if "parsed" in commit else None

            if typ not in commits:
                commits[typ] = []

            commits[typ].append(commit)

        logger.debug(f"{len(versioned_commits)} versions found")

        environment = jinja2.Environment(
            loader=jinja2.PackageLoader(config["template"]["package"].get(str)),
            extensions=["jinja2.ext.loopcontrols"],
        )

        environment.filters["read_config"] = _read_config

        template = environment.get_template(config["template"]["name"].get(str))
        stream = template.stream(
            versions=versioned_commits, config=config["template"]["config"], confuse=confuse
        )
        stream.dump(output)
    except:
        gathered_tasks.cancel()
        raise
    finally:
        input.close()

        with contextlib.suppress(asyncio.CancelledError):
            await gathered_tasks
