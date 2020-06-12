import asyncio
import contextlib
import datetime
import fnmatch
import json
import logging
import os
from typing import Any, AsyncIterable, Dict, List, Optional, TextIO, Tuple, cast

import click
import confuse
import dateutil.tz
import jinja2

from .. import git, util
from ..main import pass_config
from . import list_commits
from .parse_commit import Change

logger = logging.getLogger(__name__)

DEFAULT = object()


class Version(Dict[Optional[str], List[Change]]):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)

    def has_commits(self):
        return any(self.get_commits())

    def get_commits(self):
        return [commit for commits in self.values() for commit in commits]


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
    config: confuse.Configuration,
    *,
    input: Optional[TextIO],
    output: TextIO,
    tag_filter: Optional[str],
    **kwargs,
) -> None:
    if tag_filter is not None:
        config.set_args({"template.tags.filter": tag_filter}, dots=True)

    await async_main_impl(config, input=input, output=output, **kwargs)


async def async_main_impl(
    config: confuse.Configuration, *, input: Optional[TextIO], output: TextIO, **kwargs,
) -> None:

    if input is not None:
        await template(config, input=input, output=output, **kwargs)
        return

    async def _list_commits(fd: int) -> None:
        async with util.AsyncFileObject(os.fdopen(fd, "w")) as list_output:
            excluded = config["tags"]["exclude"].get(confuse.StrSeq())
            try:
                tag_filter = config["tags"]["filter"].get(str)
            except confuse.NotFoundError:
                tag_filter = None

            to_rev = "HEAD"
            for tag in await git.get_tags(pattern=tag_filter, sort="creatordate", reverse=True):
                if tag["name"] in excluded:
                    continue

                from_rev = tag["name"]
                if to_rev == "HEAD":
                    logger.debug(f"Retrieving commits up until, {from_rev}")
                else:
                    logger.debug(f"Retrieving commits from, {from_rev}, to, {to_rev}")

                await list_commits.async_main(
                    config,
                    output=list_output,
                    parse=True,
                    include_unparsed=True,
                    from_rev=from_rev,
                    from_last_tag=False,
                    to_rev=to_rev,
                    reverse=True,
                )

                to_rev = from_rev

            logger.debug(f"Retrieving remaining commits since {to_rev}")

            await list_commits.async_main(
                config,
                output=list_output,
                parse=True,
                include_unparsed=True,
                from_rev=None,
                from_last_tag=False,
                to_rev=to_rev,
                reverse=True,
            )

    async def _template(fd: int) -> None:
        async with util.AsyncFileObject(os.fdopen(fd, "r")) as template_input:
            await template(config, input=template_input, output=output, **kwargs)

    read_fd, write_fd = os.pipe()
    list_task = _list_commits(write_fd)
    template_task = _template(read_fd)

    await asyncio.gather(list_task, template_task)


async def template(
    config: confuse.Configuration, *, input: TextIO, output: TextIO, include_unparsed: bool,
) -> None:
    def _read_config(view, default=DEFAULT, typ=str):
        try:
            return view.get(typ)
        except confuse.NotFoundError:
            if default is DEFAULT:
                raise

            return default

    loop = asyncio.get_event_loop()

    excluded = config["tags"]["exclude"].get(confuse.StrSeq())
    try:
        tag_filter = config["tags"]["filter"].get(str)
    except confuse.NotFoundError:
        tag_filter = None

    def _ignore_tag(tag: str) -> bool:
        if tag_filter and not fnmatch.fnmatch(tag, tag_filter):
            return True
        if tag in excluded:
            return True
        return False

    versions: List[Tuple[Optional[git.Tag], Version]] = []

    version = next_version = Version()
    while True:
        version = next_version
        input_line = await loop.run_in_executor(None, input.readline)

        if not input_line:
            break

        data = json.loads(input_line)
        change = cast(Change, data)

        if change["source"]["tags"]:
            tags = [tag for tag in change["source"]["tags"] if not _ignore_tag(tag["name"])]

            if tags:
                tag = sorted(tags, key=lambda tag: tag["name"])[0]

                logger.debug(
                    f"Found new version tag, {tag['name']} "
                    f"({len(version.get_commits())} commit(s))"
                )

                versions.append((tag, version))
                next_version = Version()

        if "data" not in change and not include_unparsed:
            continue

        typ = change.get("data", {}).get("subject", {}).get("type")
        if typ not in version:
            version[typ] = []

        version[typ].append(change)

    if version.has_commits():
        logger.debug(f"Found {len(version.get_commits())} unreleased commit(s)")
        versions.append((None, version))

    logger.debug(f"{len(versions)} versions found")

    environment = jinja2.Environment(
        loader=jinja2.PackageLoader(config["template"]["package"].get(str)),
        extensions=["jinja2.ext.loopcontrols"],
    )

    environment.filters["read_config"] = _read_config

    template = environment.get_template(config["template"]["name"].get(str))
    stream = template.stream(
        versions=versions, config=config["template"]["config"], confuse=confuse
    )

    stream.dump(output)
