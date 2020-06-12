import io
import json
from typing import Any, List, Optional, Tuple

import confuse
import dateutil
import pytest

from .. import git, util
from ..parser import conventional_commits
from . import parse_commit

pytestmark = pytest.mark.asyncio

COMMITS: List[Tuple[git.Commit, Optional[conventional_commits.Change]]] = [
    (
        {
            "rev": "d216714c3000b3dfa628576335db20e00d70086e",
            "short_rev": "d216714",
            "subject": "An unconventional commit message",
            "body": "",
            "author_name": "Test",
            "author_email": "test@no-one.com",
            "date": dateutil.parser.isoparse("1970-01-01T00:00:00+00:00"),
            "tags": [],
        },
        None,
    ),
    (
        {
            "rev": "0f9f36065f37af3b7452becf67fe259319c07c36",
            "short_rev": "0f9f360",
            "subject": "feat: A Conventional Commits message",
            "body": "With a body that has some footers\n\nFooter-Key: Footer-Value",
            "author_name": "Test",
            "author_email": "test@no-one.com",
            "date": dateutil.parser.isoparse("1970-01-02T00:00:00+00:00"),
            "tags": [],
        },
        {
            "subject": {
                "_raw": "feat: A Conventional Commits message",
                "type": "feat",
                "message": "A Conventional Commits message",
            },
            "body": {
                "_raw": "With a body that has some footers\n\nFooter-Key: Footer-Value",
                "content": "With a body that has some footers",
                "footer": {
                    "_raw": "Footer-Key: Footer-Value",
                    "items": [{"key": "Footer-Key", "value": "Footer-Value"}],
                },
            },
            "metadata": {"breaking": False, "closes": []},
        },
    ),
]


async def test_end_to_end() -> None:
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)

    input_stream = io.TextIOWrapper(io.BytesIO())
    output_stream = io.TextIOWrapper(io.BytesIO())

    expected_data: List[parse_commit.Change] = []
    for commit, data in COMMITS:
        parse_data = json.dumps(commit, default=util.json_defaults)

        expected: parse_commit.Change = {"source": json.loads(parse_data)}
        if data is not None:
            expected["data"] = data

        expected_data.append(expected)
        input_stream.writelines([parse_data, "\n"])
    input_stream.seek(0)

    await parse_commit.async_main(
        config, input=input_stream, output=output_stream, include_unparsed=True
    )

    output_stream.seek(0)
    for actual_data, expected in zip(output_stream, expected_data):
        actual = json.loads(actual_data)

        assert actual == expected
