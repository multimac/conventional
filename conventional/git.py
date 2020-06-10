import asyncio
import datetime
import io
import logging
import pathlib
from asyncio import IncompleteReadError, LimitOverrunError, StreamReader
from typing import AsyncIterable, BinaryIO, Dict, Iterable, List, Optional, TypedDict, cast

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


def get_commit_format() -> Iterable[str]:
    return ["%H", "%h", "%s", "%b", "%aN", "%aE", "%cI"]


def get_tag_format() -> Iterable[str]:
    return [
        "%(refname:lstrip=2)",
        "%(if)%(*objectname)%(then)%(*objectname)%(else)%(objectname)%(end)",
        "%(if)%(*objectname)%(then)%(subject)%(end)",
        "%(if)%(*objectname)%(then)%(body)%(end)",
    ]


def create_commit(
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


def create_tag(name: str, object_name: str, subject: str, body: str) -> "Tag":
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


async def is_git_repository(path: pathlib.PurePath = None) -> bool:
    args = [
        "git",
        "rev-parse",
        "--is-inside-work-tree",
    ]

    logger.debug(f"Running command: {args}")
    if path is not None:
        logger.debug(f"  in {path.as_posix()}")

    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL, cwd=path
    )

    await proc.communicate()
    return proc.returncode == 0


async def get_commits(
    *,
    start: str = None,
    end: str = "HEAD",
    path: pathlib.PurePath = None,
) -> AsyncIterable[Commit]:
    """Get the commits between start and end."""

    if not await is_git_repository(path):
        logger.warning("Not a git repository.")
        return

    tags: Dict[str, List[Tag]] = {}
    async for tag in get_tags(path=path):
        name = tag["object_name"]
        if name not in tags:
            tags[name] = []

        tags[name].append(tag)

    fmt = "%x00".join([*get_commit_format(), delimiter])

    args = ["git", "log", f"--pretty=format:{fmt}"]

    if start:
        args.append(f"{start}..{end}")
    else:
        args.append(end)

    logger.debug(f"Running command: {args}")
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, cwd=path
    )

    assert proc.stdout

    counter = 0
    async for commit_data in _process_delimited_stream(proc.stdout, delimiter):
        commit_fields = commit_data[:-1].split("\x00")
        commit = create_commit(*commit_fields)

        counter += 1
        if commit["rev"] in tags:
            commit["tags"] = tags[commit["rev"]]

        yield commit

    logger.debug(f"Read {counter} commits from repository")

    await asyncio.gather(proc.wait())


async def get_tags(*, path: pathlib.PurePath = None, pattern: str = None) -> AsyncIterable[Tag]:
    """ Gets all tags in the repository. """

    if not await is_git_repository(path):
        logger.warning("Not a git repository.")
        return

    fmt = "%00".join([*get_tag_format(), delimiter])
    args = ["git", "tag", "--list", f"--format={fmt}"]

    if pattern is not None:
        args.append(pattern)

    logger.debug(f"Running command: {args}")
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, cwd=path
    )

    if proc.stdout:
        counter = 0
        async for tag_data in _process_delimited_stream(proc.stdout, delimiter):
            tag_fields = tag_data[:-1].split("\x00")
            tag = create_tag(*tag_fields)

            counter += 1
            yield tag

        logger.debug(f"Read {counter} tags from repository")

    await proc.wait()
