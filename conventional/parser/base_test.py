import json

import confuse
import pytest

from ..git import create_commit
from .conventional_commits import ConventionalCommitParser

INVALID_COMMITS = [
    (
        create_commit(
            "f7c03766efd3469cbfdd40b3188b90f7354dd461",
            "f7c0376",
            "A commit not matching the conventional commit standard",
            "",
            "mr.x@anonymous.com",
            "Mr. X",
            "1970-01-01",
        )
    )
]

INVALID_PARSER_DATA = [
    (
        "subject",
        "Not a conventional commit subject",
        {"_raw": "Not a conventional commit subject"},
    ),
    ("footer", "There are no footers here", {"_raw": "There are no footers here", "items": []}),
]

VALID_COMMITS = [
    (
        create_commit(
            "f7c03766efd3469cbfdd40b3188b90f7354dd461",
            "f7c0376",
            "feat(somewhere): Test Commit",
            "Some description of the change",
            "mr.x@anonymous.com",
            "Mr. X",
            "1970-01-01",
        ),
        {
            "subject": {
                "_raw": "feat(somewhere): Test Commit",
                "type": "feat",
                "scope": "somewhere",
                "message": "Test Commit",
            },
            "body": {
                "_raw": "Some description of the change",
                "content": "Some description of the change",
            },
            "metadata": {"breaking": False, "closes": []},
        },
    ),
    (
        create_commit(
            "f7c03766efd3469cbfdd40b3188b90f7354dd461",
            "f7c0376",
            "feat(somewhere): Test Commit",
            "Some description of the change\n\nRefs #JIRA-1\nBREAKING CHANGE: Something has changed, be afraid",
            "mr.x@anonymous.com",
            "Mr. X",
            "1970-01-01",
        ),
        {
            "subject": {
                "_raw": "feat(somewhere): Test Commit",
                "type": "feat",
                "scope": "somewhere",
                "message": "Test Commit",
            },
            "body": {
                "_raw": "Some description of the change\n\nRefs #JIRA-1\nBREAKING CHANGE: Something has changed, be afraid",
                "content": "Some description of the change",
                "footer": {
                    "_raw": "Refs #JIRA-1\nBREAKING CHANGE: Something has changed, be afraid",
                    "items": [
                        {"key": "Refs", "value": "JIRA-1"},
                        {"key": "BREAKING CHANGE", "value": "Something has changed, be afraid",},
                    ],
                },
            },
            "metadata": {"breaking": True, "closes": ["JIRA-1"]},
        },
    ),
]

VALID_PARSER_DATA = [
    (
        "subject",
        "feat(scope): Test subject",
        {
            "_raw": "feat(scope): Test subject",
            "type": "feat",
            "scope": "scope",
            "message": "Test subject",
        },
    ),
    (
        "footer",
        "Key: Value\n\nKey-Two: Other Value",
        {
            "_raw": "Key: Value\n\nKey-Two: Other Value",
            "items": [
                {"key": "Key", "value": "Value"},
                {"key": "Key-Two", "value": "Other Value"},
            ],
        },
    ),
]


@pytest.mark.parametrize("method, text, expected", INVALID_PARSER_DATA)
def test_internal_parse_with_invalid_data(method, text, expected):
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)

    parser = ConventionalCommitParser(config["parser"]["config"])

    parser_method = parser.get_parsers()[method]
    change = parser._parse(parser_method, text)

    assert change == expected


@pytest.mark.parametrize("method, text, expected", VALID_PARSER_DATA)
def test_internal_parse_with_valid_data(method, text, expected):
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)

    parser = ConventionalCommitParser(config["parser"]["config"])

    parser_method = parser.get_parsers()[method]
    change = parser._parse(parser_method, text)

    assert change == expected


@pytest.mark.parametrize("commit", INVALID_COMMITS)
def test_parser_with_invalid_commit(commit):
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)

    parser = ConventionalCommitParser(config["parser"]["config"])

    change = parser.parse(commit)

    assert change is None


@pytest.mark.parametrize("commit, expected", VALID_COMMITS)
def test_parser_with_valid_commit(commit, expected):
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)

    parser = ConventionalCommitParser(config["parser"]["config"])

    change = parser.parse(commit)

    assert change == expected
