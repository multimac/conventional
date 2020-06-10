from re import Match
from typing import Any, Dict, Iterable, Union

import confuse
import pytest

from .conventional_commits import ConventionalCommitParser

INVALID_SUBJECT_REGEX = [
    ("spa ce: Type with space"),
    ("type(spa ce): Scope with space"),
    ("type !: Space between type and bang"),
    ("type(scope) !: Space between scope and bang"),
    ("type (scope): Space between type and scope"),
    ("type( scope): Leading space in scope"),
    ("type(scope ): Trailing space in scope"),
    ("type( scope ): Leading and trailing space in scope"),
    ("type:Missing space after colon"),
]

INVALID_FOOTER_REGEX = [
    ("Key : Value"),
    ("Key # Value"),
    ("Key with space: Value"),
    ("Key with space #Value"),
]

VALID_SUBJECT_REGEX = [
    (
        "type: Description",
        {"type": "type", "scope": None, "breaking": None, "message": "Description"},
    ),
    (
        "type!: Breaking Change",
        {"type": "type", "scope": None, "breaking": "!", "message": "Breaking Change"},
    ),
    (
        "type(scope): Scoped Change",
        {"type": "type", "scope": "scope", "breaking": None, "message": "Scoped Change"},
    ),
    (
        "type(scope)!: Scoped Breaking Change",
        {"type": "type", "scope": "scope", "breaking": "!", "message": "Scoped Breaking Change"},
    ),
    (
        "hyp-hen: Hyphenated Type",
        {"type": "hyp-hen", "scope": None, "breaking": None, "message": "Hyphenated Type"},
    ),
    (
        "type(hyp-hen): Hyphenated Scope",
        {"type": "type", "scope": "hyp-hen", "breaking": None, "message": "Hyphenated Scope"},
    ),
]

VALID_BODY_REGEX = [
    ("A body\nwith no footers", {"content": "A body\nwith no footers", "footer": None},),
    ("Footer-Only: True", {"content": None, "footer": "Footer-Only: True",},),
    (
        "A body\n\nAnd a second\nparagraph",
        {"content": "A body\n\nAnd a second\nparagraph", "footer": None},
    ),
    (
        "A body with a footer\n\nFooter: value",
        {"content": "A body with a footer", "footer": "Footer: value"},
    ),
    (
        "A body with a different kind of footer\n\nFooter #Value",
        {"content": "A body with a different kind of footer", "footer": "Footer #Value"},
    ),
    (
        "A body with a breaking change in the footer section\n\nBREAKING CHANGE: A description of the change",
        {
            "content": "A body with a breaking change in the footer section",
            "footer": "BREAKING CHANGE: A description of the change",
        },
    ),
    (
        "A body with a footer\n\nAnd a second paragraph\n\nFooter: value",
        {"content": "A body with a footer\n\nAnd a second paragraph", "footer": "Footer: value",},
    ),
    (
        "A body with multiple footer\n\nOne: value\n\nTwo: value",
        {"content": "A body with multiple footer", "footer": "One: value\n\nTwo: value",},
    ),
    (
        "A body with a multiline footer\n\nOne: value\nand some more",
        {"content": "A body with a multiline footer", "footer": "One: value\nand some more",},
    ),
    # Edge-case tests
    (
        "A body with a single footer that looks like two\n\nOne: value\nTwo: value",
        {
            "content": "A body with a single footer that looks like two",
            "footer": "One: value\nTwo: value",
        },
    ),
    (
        "A body with a footer containing a hyphen\n\nFooter-With-Hyphen: value",
        {
            "content": "A body with a footer containing a hyphen",
            "footer": "Footer-With-Hyphen: value",
        },
    ),
    (
        "A body, but no footer as there is only one newline\nFooter: value",
        {
            "content": "A body, but no footer as there is only one newline\nFooter: value",
            "footer": None,
        },
    ),
    (
        "A body, but no footer as it has an invalid key\n\nFooter : value",
        {
            "content": "A body, but no footer as it has an invalid key\n\nFooter : value",
            "footer": None,
        },
    ),
    (
        "A body, but no footer as it has an invalid key\n\nFooter # value",
        {
            "content": "A body, but no footer as it has an invalid key\n\nFooter # value",
            "footer": None,
        },
    ),
]

VALID_FOOTER_REGEX = [
    ("Key: Value", [{"key": "Key", "value": "Value"}]),
    ("Key #Value", [{"key": "Key", "value": "Value"}]),
    ("BREAKING CHANGE: Value", [{"key": "BREAKING CHANGE", "value": "Value"}]),
    ("Key: Line one\nLine two", [{"key": "Key", "value": "Line one\nLine two"}]),
    ("Key: Line one\nKey # Line two", [{"key": "Key", "value": "Line one\nKey # Line two"}]),
    (
        "Key-One: Value-One\nKey-Two: Value-Two",
        [{"key": "Key-One", "value": "Value-One"}, {"key": "Key-Two", "value": "Value-Two"}],
    ),
    (
        "Key-One: Value-One\nKey-Two: Value-Two",
        [{"key": "Key-One", "value": "Value-One"}, {"key": "Key-Two", "value": "Value-Two"}],
    ),
    (
        "Key-One: Value-One\n\nKey-Two: Value-Two",
        [{"key": "Key-One", "value": "Value-One\n"}, {"key": "Key-Two", "value": "Value-Two"}],
    ),
    (
        "Key-One: Value-One\n\nParagraph two\n\nKey-Two: Value-Two",
        [
            {"key": "Key-One", "value": "Value-One\n\nParagraph two\n"},
            {"key": "Key-Two", "value": "Value-Two"},
        ],
    ),
    # Edge-case tests
    ("Single-Character-Value: A", [{"key": "Single-Character-Value", "value": "A"}]),
]

POST_PROCESS_DATA = [
    ({}, {"metadata": {"breaking": False, "closes": []}}),
    (
        {"subject": {"breaking": "!"}},
        {"subject": {"breaking": "!"}, "metadata": {"breaking": True, "closes": []}},
    ),
    (
        {"subject": {"breaking": None}},
        {"subject": {"breaking": None}, "metadata": {"breaking": False, "closes": []}},
    ),
    (
        {"body": {"footer": {"items": [{"key": "BREAKING CHANGE", "value": "Anything"}]}}},
        {
            "metadata": {"breaking": True, "closes": []},
            "body": {"footer": {"items": [{"key": "BREAKING CHANGE", "value": "Anything"}]}},
        },
    ),
    (
        {
            "body": {
                "footer": {
                    "items": [
                        {"key": "Closes", "value": "A-TICKET"},
                        {"key": "Refs", "value": "B-TICKET"},
                    ]
                }
            }
        },
        {
            "metadata": {"breaking": False, "closes": ["A-TICKET", "B-TICKET"]},
            "body": {
                "footer": {
                    "items": [
                        {"key": "Closes", "value": "A-TICKET"},
                        {"key": "Refs", "value": "B-TICKET"},
                    ]
                }
            },
        },
    ),
]


@pytest.mark.parametrize("text", INVALID_SUBJECT_REGEX)
def test_invalid_subject_regex(text: str) -> None:
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)
    config["parser"]["config"]["types"] = ["type", "hyp-hen"]

    parser = ConventionalCommitParser(config["parser"]["config"])
    actual = parser.get_parsers()["subject"](text)

    assert actual is None


@pytest.mark.parametrize("text", INVALID_FOOTER_REGEX)
def test_invalid_footer_regex(text: str) -> None:
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)
    config["parser"]["config"]["types"] = ["type", "hyp-hen"]

    parser = ConventionalCommitParser(config["parser"]["config"])
    actual = parser.get_parsers()["footer"](text)

    assert isinstance(actual, Iterable)

    actual_data = list(actual)
    assert len(actual_data) == 0


@pytest.mark.parametrize("text, expected", VALID_SUBJECT_REGEX)
def test_valid_subject_regex(text: str, expected: Union[Dict, Iterable[Dict], None]) -> None:
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)
    config["parser"]["config"]["types"] = ["type", "hyp-hen"]

    parser = ConventionalCommitParser(config["parser"]["config"])
    actual = parser.get_parsers()["subject"](text)

    assert isinstance(actual, Match)
    assert actual.groupdict() == expected


@pytest.mark.parametrize("text, expected", VALID_BODY_REGEX)
def test_valid_body_regex(text: str, expected: Union[Dict, Iterable[Dict], None]) -> None:
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)
    config["parser"]["config"]["types"] = ["type", "hyp-hen"]

    parser = ConventionalCommitParser(config["parser"]["config"])
    actual = parser.get_parsers()["body"](text)

    assert isinstance(actual, Match)
    assert actual.groupdict() == expected


@pytest.mark.parametrize("text, expected", VALID_FOOTER_REGEX)
def test_valid_footer_regex(text: str, expected: Union[Dict, Iterable[Dict], None]) -> None:
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)
    config["parser"]["config"]["types"] = ["type", "hyp-hen"]

    parser = ConventionalCommitParser(config["parser"]["config"])
    actual = parser.get_parsers()["footer"](text)

    assert isinstance(actual, Iterable)

    actual_data = [match.groupdict() for match in actual]
    assert actual_data == expected


@pytest.mark.parametrize("data, expected", POST_PROCESS_DATA)
def test_post_process(data: Dict[str, Any], expected: Dict[str, Any]) -> None:
    config = confuse.Configuration("Conventional", "conventional", read=False)
    config.read(user=False)
    config["parser"]["config"]["types"] = ["type", "hyp-hen"]

    parser = ConventionalCommitParser(config["parser"]["config"])

    actual = data.copy()
    parser.post_process(actual)

    assert actual == expected
