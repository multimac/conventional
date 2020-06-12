import re
from typing import Any, Dict, Iterable, Pattern, TypedDict

import confuse

from conventional.parser.base import ParsedItem, Parser, ParserCollection


class Footer(TypedDict):
    key: str
    value: str


class FooterList(ParsedItem):
    items: Iterable[Footer]


class Subject(ParsedItem, total=False):
    type: str
    scope: str
    breaking: str
    message: str


class Body(ParsedItem):
    content: str
    footer: FooterList


class Metadata(TypedDict):
    breaking: bool
    closes: Iterable[str]


class Change(TypedDict):
    subject: Subject
    body: Body

    metadata: Metadata


class ConventionalCommitParser(Parser[Change]):

    _footer_test_regex = "(?:[\w-]+|BREAKING CHANGE)(?:: | #)\w"
    _body_regex = re.compile(
        fr"^(?P<content>(?:(?:(?<!^)\n|(?:^\n*|\n{{2,}})(?!{_footer_test_regex})).+)+)?"
        fr"\n*(?P<footer>{_footer_test_regex}[\w\W]*)?$"
    )

    _footer_regex = re.compile(
        fr"(?:^|\n)(?P<key>([\w-]+|BREAKING CHANGE))(?:: | #)(?P<value>\w(?:.|\n(?!{_footer_test_regex}))*)"
    )

    def _get_subject_regex(self, types: Iterable[str]) -> Pattern:
        return re.compile(
            fr"^(?P<type>({'|'.join(types)}))(?:\((?P<scope>[\w-]+)\))?(?P<breaking>!)?:[ \t]+(?P<message>.+)$"
        )

    def __init__(self, config: confuse.ConfigView) -> None:
        subject_regex = self._get_subject_regex(config["types"].get(confuse.StrSeq()))
        self._parsers: ParserCollection = {
            "subject": lambda text: subject_regex.match(text),
            "body": lambda text: self._body_regex.match(text),
            "footer": lambda text: self._footer_regex.finditer(text),
        }

    def get_parsers(self) -> ParserCollection:
        return self._parsers

    def has_parsed(self, data: Dict[str, Any]) -> bool:
        return bool(data.get("subject", {}).get("type", False))

    def post_process(self, data: Dict[str, Any]) -> None:
        metadata = data.setdefault("metadata", {})
        footers = data.get("body", {}).get("footer", {}).get("items", [])
        subject = data.get("subject", {})

        breaking_change = any(f["key"] == "BREAKING CHANGE" for f in footers)
        metadata["breaking"] = bool(subject.get("breaking")) or breaking_change

        metadata["closes"] = list(f["value"] for f in footers if f["key"] in ("Closes", "Refs"))
