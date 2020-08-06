import importlib
import json
import logging
from typing import Any, AsyncIterable, Optional, TextIO, TypedDict, cast

import confuse

from .. import git
from ..parser.base import Parser
from ..util.io import json_defaults

logger = logging.getLogger(__name__)


class ParsedCommit(TypedDict):
    source: git.Commit
    data: Optional[Any]


def load_parser(config: confuse.Configuration) -> Parser[Any]:
    parser_config = config["parser"]
    module = parser_config["module"].get(str)
    name = parser_config["class"].get(str)

    custom_config = parser_config["config"]
    cls = getattr(importlib.import_module(module), name)
    return cast(Parser[Any], cls(custom_config))


async def cli_main(
    config: confuse.Configuration,
    *,
    input: TextIO,
    output: TextIO,
    include_unparsed: bool,
) -> None:
    async def _yield_input() -> AsyncIterable[git.Commit]:
        for line in input:
            item = json.loads(line)
            yield item

    stream = main(config, input=_yield_input(), include_unparsed=include_unparsed)

    async for item in stream:
        line = json.dumps(item, default=json_defaults)
        output.writelines([line, "\n"])


async def main(
    config: confuse.Configuration,
    *,
    input: AsyncIterable[git.Commit],
    include_unparsed: bool,
) -> AsyncIterable[ParsedCommit]:

    parser = load_parser(config)
    async for commit in input:
        data: Any = parser.parse(commit["subject"], commit["body"])

        if not include_unparsed and not data:
            continue

        yield {"source": commit, "data": data}
