import re
from typing import Any, Callable, Dict, Iterable, List, Optional, TypedDict

from conventional.parser.base import ParsedItem, Parser, ParserCollection, ParseResult


class Footer(TypedDict):
    key: str
    value: str


class FooterList(ParsedItem):
    items: Iterable[Footer]


class Subject(ParsedItem):
    type: str
    scope: str
    breaking: bool
    message: str


class Body(ParsedItem):
    content: str
    footer: FooterList


class Change(TypedDict):
    subject: Subject
    body: Body


class ConventionalCommitParser(Parser[Change]):

    _subject_regex = re.compile(
        r"^(?P<type>[\w-]+)(?:\((?P<scope>[\w-]+)\))?(?P<breaking>!)?:[ \t]+(?P<message>.+)$"
    )

    _footer_test_regex = "(?:[\w-]+|BREAKING CHANGE)(?:: | #)\w"
    _body_regex = re.compile(
        fr"^(?P<content>(?:(?:(?<!^)\n|(?:^\n*|\n{{2,}})(?!{_footer_test_regex})).+)+)?"
        fr"\n*(?P<footer>{_footer_test_regex}[\w\W]*)?$"
    )

    _footer_regex = re.compile(
        fr"(?:^|\n)(?P<key>([\w-]+|BREAKING CHANGE))(?:: | #)(?P<value>\w(?:.|\n(?!{_footer_test_regex}))*)"
    )

    def __init__(self) -> None:
        self._parsers: ParserCollection = {
            "subject": self._parse_subject,
            "body": lambda text: self._body_regex.match(text),
            "footer": lambda text: self._footer_regex.finditer(text),
        }

    def _parse_subject(self, text: str) -> ParseResult:
        result = self._subject_regex.match(text)
        return result

    def get_parsers(self) -> ParserCollection:
        return self._parsers

    def has_parsed(self, data: Dict[str, Any]) -> bool:
        return bool(data.get("subject", {}).get("type", False))

    def post_process(self, data: Dict[str, Any]) -> None:
        subject = data.setdefault("subject", {})
        footers = data.get("body", {}).get("footer", {}).get("items", [])

        breaking_change = any(f["key"] == "BREAKING CHANGE" for f in footers)
        subject["breaking"] = bool(subject.get("breaking")) or breaking_change
