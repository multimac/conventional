import asyncio
import importlib
import json
import logging
from typing import Any, TextIO, TypedDict

import confuse

from .. import git, util
from ..parser.base import Parser

logger = logging.getLogger(__name__)


class Change(TypedDict, total=False):
    source: git.Commit
    data: Any


async def main(
    config: confuse.Configuration, *, input: TextIO, output: TextIO, include_unparsed: bool,
) -> None:
    def _load_parser(config: confuse.Configuration) -> Parser[Any]:
        parser_config = config["parser"]
        module = parser_config["module"].get(str)
        name = parser_config["class"].get(str)
        custom_config = parser_config["config"]

        return getattr(importlib.import_module(module), name)(custom_config)

    parser = _load_parser(config)
    loop = asyncio.get_event_loop()

    while True:
        input_line = await loop.run_in_executor(None, input.readline)

        if not input_line:
            break

        commit: git.Commit = git.create_commit(**json.loads(input_line))
        data: Any = parser.parse(commit)

        if not include_unparsed and not data:
            continue

        change: Change = {"source": commit}
        if data:
            change["data"] = data

        line = json.dumps(change, default=util.json_defaults)
        await loop.run_in_executor(None, output.writelines, [line, "\n"])
