import asyncio
import contextlib
import datetime
import io
import logging
import pathlib
from asyncio import StreamReader
from asyncio.subprocess import Process
from typing import AsyncIterable, AsyncIterator, Dict, Iterable, List, Optional, TypedDict, cast

import aiocache
import dateutil.parser

logger = logging.getLogger(__name__)

delimiter = "----------delimiter----------"


class Tag(TypedDict):
    name: str
    object_name: str

    subject: str
    body: str


class Commit(TypedDict):
    rev: str
    short_rev: str

    subject: str
    body: str

    author_name: str
    author_email: str
    date: datetime.datetime

    tags: Iterable[Tag]


def _get_commit_format() -> Iterable[str]:
    return ["%H", "%h", "%s", "%b", "%aN", "%aE", "%cI"]


def _get_tag_format() -> Iterable[str]:
    return [
        "%(refname:lstrip=2)",
        "%(if)%(*objectname)%(then)%(*objectname)%(else)%(objectname)%(end)",
        "%(if)%(*objectname)%(then)%(subject)%(end)",
        "%(if)%(*objectname)%(then)%(body)%(end)",
    ]


def _create_commit(
    rev: str,
    short_rev: str,
    subject: str,
    body: str,
    author_name: str,
    author_email: str,
    date: str,
    *,
    tags: Iterable[Dict] = None,
) -> "Commit":
    return {
        "rev": rev.strip(),
        "short_rev": short_rev.strip(),
        "subject": subject.strip(),
        "body": body.strip(),
        "author_name": author_name.strip(),
        "author_email": author_email.strip(),
        "date": dateutil.parser.isoparse(date.strip()),
        "tags": list(cast(Tag, tag) for tag in (tags or [])),
    }


def _create_tag(name: str, object_name: str, subject: str, body: str) -> "Tag":
    return {
        "name": name.strip(),
        "object_name": object_name.strip(),
        "subject": subject.strip(),
        "body": body.strip(),
    }


async def _process_delimited_stream(
    stream: asyncio.StreamReader, delimiter: str
) -> AsyncIterable[str]:
    buffer = io.StringIO()

    while True:
        line = (await stream.readline()).decode()

        if not line:
            break

        remaining: Optional[str] = None
        for segment in line.split(delimiter):
            if remaining:
                buffer.write(remaining)

                yield buffer.getvalue()
                buffer = io.StringIO()

            remaining = segment

        if remaining:
            buffer.write(remaining)


@contextlib.asynccontextmanager
async def _run(*args, **kwargs) -> AsyncIterator[Process]:
    logger.debug(f"Running command: {args}")
    if "cwd" in kwargs and kwargs["cwd"] is not None:
        logger.debug(f"  in {kwargs['cwd']}")

    if "stdout" not in kwargs:
        kwargs["stdout"] = asyncio.subprocess.DEVNULL
    if "stderr" not in kwargs:
        kwargs["stderr"] = asyncio.subprocess.DEVNULL

    process = await asyncio.create_subprocess_exec(*args, **kwargs)

    try:
        yield process
    except:
        process.kill()
        raise
    finally:
        await process.wait()
        logger.debug(f"Command exit code: {process.returncode}")


async def create_commit(
    path: pathlib.PurePath, message: str, *, allow_empty: bool = False
) -> None:
    args = ["git", "commit", "-m", message]
    if allow_empty:
        args.append("--allow-empty")

    async with _run(*args, cwd=path):
        pass


async def create_tag(path: pathlib.PurePath, name: str, message: str = None) -> None:
    args = ["git", "tag"]
    if message is not None:
        args.extend(["-m", message])

    args.append(name)

    async with _run(*args, cwd=path):
        pass


@aiocache.cached()
async def is_git_repository(path: pathlib.PurePath = None) -> bool:
    async with _run("git", "rev-parse", "--is-inside-work-tree", cwd=path) as process:
        pass

    return process.returncode == 0


async def get_commits(
    *, start: str = None, end: str = "HEAD", path: pathlib.PurePath = None, reverse: bool = False,
) -> AsyncIterable[Commit]:
    """Get the commits between start and end."""

    if not await is_git_repository(path):
        logger.warning("Not a git repository.")
        return

    tags: Dict[str, List[Tag]] = {}
    for tag in await get_tags(path=path):
        name = tag["object_name"]
        if name not in tags:
            tags[name] = []

        tags[name].append(tag)

    fmt = "%x00".join([*_get_commit_format(), delimiter])
    args = ["git", "log", f"--pretty=format:{fmt}"]

    if reverse:
        args.append("--reverse")

    if start:
        args.append(f"{start}..{end}")
    else:
        args.append(end)

    async with _run(*args, stdout=asyncio.subprocess.PIPE, cwd=path) as process:
        assert process.stdout

        counter = 0
        async for commit_data in _process_delimited_stream(process.stdout, delimiter):
            commit_fields = commit_data[:-1].split("\x00")
            commit = _create_commit(*commit_fields)

            counter += 1
            if commit["rev"] in tags:
                commit["tags"] = tags[commit["rev"]]

            yield commit

        logger.debug(f"Read {counter} commits from repository")


@aiocache.cached()
async def get_tags(
    *, path: pathlib.PurePath = None, pattern: str = None, sort: str = None, reverse: bool = False
) -> Iterable[Tag]:
    """ Gets all tags in the repository. """

    if not await is_git_repository(path):
        logger.warning("Not a git repository.")
        return []

    fmt = "%00".join([*_get_tag_format(), delimiter])
    args = ["git", "tag", "--list", f"--format={fmt}"]

    if sort is not None:
        sort = sort if not reverse else "-" + sort
        args.append(f"--sort={sort}")

    if pattern is not None:
        args.append(pattern)

    async with _run(*args, stdout=asyncio.subprocess.PIPE, cwd=path) as process:
        assert process.stdout

        tags: List[Tag] = []
        async for tag_data in _process_delimited_stream(process.stdout, delimiter):
            tag_fields = tag_data[:-1].split("\x00")
            tag = _create_tag(*tag_fields)

            tags.append(tag)

        logger.debug(f"Read {len(tags)} tags from repository")
        return tags


@aiocache.cached()
async def get_repository_root(path: pathlib.PurePath = None) -> pathlib.Path:
    args = [
        "git",
        "rev-parse",
        "--show-toplevel",
    ]

    async with _run(*args, stdout=asyncio.subprocess.PIPE, cwd=path) as process:
        root, _ = await process.communicate()
        return pathlib.Path(root.decode().strip())
