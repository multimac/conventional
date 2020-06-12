import asyncio
import contextlib
import datetime
import io
import os
import pathlib
import subprocess
from typing import Any

import dateutil


class AsyncFileObject:
    def __init__(self, f):
        self.f = f

    async def __aenter__(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.f.__enter__)

    async def __aexit__(self, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.f.__exit__, *args)


def create_commit(path: pathlib.PurePath, message: str) -> None:
    proc = subprocess.run(["git", "commit", "--allow-empty", "-m", message], cwd=path)

    if proc.returncode:
        raise RuntimeError(f"Git command failed with exit code: {proc.returncode}")


def create_tag(path: pathlib.PurePath, name: str, message: str = None) -> None:
    args = ["git", "tag"]
    if message is not None:
        args.extend(["-m", message])

    args.append(name)
    proc = subprocess.run(args, cwd=path)

    if proc.returncode:
        raise RuntimeError(f"Git command failed with exit code: {proc.returncode}")


def json_defaults(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.astimezone(dateutil.tz.UTC).isoformat()

    raise TypeError("Type %s not serializable" % type(obj))
