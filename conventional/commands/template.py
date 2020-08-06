import fnmatch
import json
import logging
from typing import Any, AsyncIterable, Dict, List, Optional, TextIO, Tuple, Type, TypedDict, cast

import confuse
import jinja2
import typer

from .. import git
from ..util.confuse import Filename
from . import exceptions

logger = logging.getLogger(__name__)

DEFAULT = object()


class Change(TypedDict):
    source: git.Commit
    data: Optional[Any]


class Version(Dict[Optional[str], List[Change]]):
    def has_commits(self) -> bool:
        return any(self.get_commits())

    def get_commits(self) -> List[Change]:
        return [commit for commits in self.values() for commit in commits]


VersionTuple = Tuple[Optional[git.Tag], Version]


async def cli_main(
    config: confuse.Configuration,
    *,
    input: Optional[TextIO],
    output: TextIO,
    include_unparsed: bool,
    unreleased_version: Optional[str],
) -> None:
    async def _yield_input(stream: TextIO) -> AsyncIterable[Change]:
        for line in stream:
            item = json.loads(line)
            yield cast(Change, item)

    async def _yield_commits() -> AsyncIterable[Change]:
        from .list_commits import main as list_commits
        from .parse_commit import main as parse_commit

        def _yield_commit_range(
            from_rev: Optional[str], to_rev: str
        ) -> AsyncIterable[Change]:
            return parse_commit(
                config,
                input=list_commits(
                    config,
                    from_rev=from_rev,
                    from_last_tag=False,
                    to_rev=to_rev,
                    reverse=True,
                ),
                include_unparsed=True,
            )

        excluded = config["tags"]["exclude"].get(confuse.StrSeq(split=False))
        try:
            tag_filter = config["tags"]["filter"].get(str)
        except confuse.NotFoundError:
            tag_filter = None

        from_rev = None  # type: Optional[str]
        for tag in await git.get_tags(pattern=tag_filter, sort="creatordate"):
            if tag["name"] in excluded:
                continue

            to_rev = tag["name"]
            if from_rev is None:
                logger.debug(f"Retrieving commits up until, {to_rev}")
            else:
                logger.debug(f"Retrieving commits from, {from_rev}, to, {to_rev}")

            async for commit in _yield_commit_range(from_rev, to_rev):
                yield commit

            from_rev = to_rev

        logger.debug(f"Retrieving remaining commits since {from_rev}")
        to_rev = "HEAD"

        async for commit in _yield_commit_range(from_rev, "HEAD"):
            yield commit

    if input is not None:
        commit_stream = _yield_input(input)
    else:
        commit_stream = _yield_commits()

    try:
        template_stream = await main(
            config,
            input=commit_stream,
            include_unparsed=include_unparsed,
            unreleased_version=unreleased_version,
        )
    except exceptions.NoCommitsError:
        logger.error("No commits found!")
        raise typer.Exit(1)
    else:
        template_stream.dump(output)


async def main(
    config: confuse.Configuration,
    *,
    input: AsyncIterable[Change],
    include_unparsed: bool,
    unreleased_version: Optional[str],
) -> jinja2.environment.TemplateStream:
    def _is_unreleased(tag: Optional[git.Tag]) -> bool:
        return tag is None or tag["name"] == unreleased_version

    def _read_config(
        view: confuse.ConfigView, default: Any = DEFAULT, typ: Type = str
    ) -> Any:
        try:
            return view.get(typ)
        except confuse.NotFoundError:
            if default is DEFAULT:
                raise

            return default

    excluded = config["tags"]["exclude"].get(confuse.StrSeq(split=False))
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

    versions: List[VersionTuple] = []

    version = Version()
    async for change in input:
        if change["data"] is not None or include_unparsed:
            data = change["data"] or {}
            typ = data.get("subject", {}).get("type")

            if typ not in version:
                version[typ] = []

            version[typ].append(change)

        if change["source"]["tags"]:
            tags = [
                tag for tag in change["source"]["tags"] if not _ignore_tag(tag["name"])
            ]

            if tags:
                tag = sorted(tags, key=lambda tag: tag["name"])[0]

                logger.debug(
                    f"Found new version tag, {tag['name']} "
                    f"({len(version.get_commits())} commit(s))"
                )

                versions.append((tag, version))
                version = Version()

    if version.has_commits():
        logger.debug(f"Found {len(version.get_commits())} unreleased commit(s)")

        unreleased_tag: Optional[git.Tag] = None
        if unreleased_version is not None:
            logger.debug(
                f"Using {unreleased_version} as the version for unreleased commit(s)"
            )
            unreleased_tag = {
                "name": unreleased_version,
                "object_name": "",
                "subject": "",
                "body": "",
            }

        versions.append((unreleased_tag, version))

    logger.debug(f"{len(versions)} versions found")

    if not any(version.has_commits() for _, version in versions):
        raise exceptions.NoCommitsError()

    # Reverse versions list so that it is in reverse chronological order
    # (ie. most recent release first)
    versions.reverse()

    loaders: List[jinja2.BaseLoader] = []

    for package in config["template"]["package"].get(confuse.StrSeq(split=False)):
        logger.debug(f"Creating package loader for: {package}")
        loaders.append(jinja2.PackageLoader(package))

    for directory in config["template"]["directory"].get(confuse.Sequence(Filename())):
        logger.debug(f"Creating file-system loader for: {directory}")
        loaders.append(jinja2.FileSystemLoader(directory))

    environment = jinja2.Environment(
        loader=jinja2.ChoiceLoader(loaders), extensions=["jinja2.ext.loopcontrols"],
    )

    environment.filters["read_config"] = _read_config
    environment.tests["unreleased"] = _is_unreleased

    template = environment.get_template(config["template"]["name"].get(str))
    template_config = config["template"]["config"]

    return template.stream(versions=versions, config=template_config, confuse=confuse)
