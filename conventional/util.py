import asyncio
import asyncio.events
import contextlib
import datetime
import functools
import io
import logging
import os
import pathlib
import subprocess
from typing import Any

import dateutil
import typer
from typer.models import CommandFunctionType


class AsyncFileObject:
    def __init__(self, f):
        self.f = f

    async def __aenter__(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.f.__enter__)

    async def __aexit__(self, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.f.__exit__, *args)


class ColorFormatter(logging.Formatter):
    colors = {
        "error": dict(fg="red"),
        "exception": dict(fg="red"),
        "critical": dict(fg="red"),
        "debug": dict(fg="blue"),
        "warning": dict(fg="yellow"),
    }

    def format(self, record):
        if not record.exc_info:
            level = record.levelname.lower()
            msg = record.getMessage()

            if level in self.colors:
                prefix = typer.style("{}: ".format(level), **self.colors[level])
                msg = "\n".join(prefix + x for x in msg.splitlines())

            return msg
        return logging.Formatter.format(self, record)


class TyperHandler(logging.Handler):
    _use_stderr = True

    def emit(self, record):
        try:
            msg = self.format(record)
            typer.echo(msg, err=self._use_stderr)
        except Exception:
            self.handleError(record)


def async_main(f: CommandFunctionType):
    @functools.wraps(f)
    def callback(*args, **kwargs) -> Any:
        if asyncio.events._get_running_loop() is None:
            return asyncio.run(f(*args, **kwargs))
        return f(*args, **kwargs)

    callback.__annotations__ = f.__annotations__
    return callback


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
