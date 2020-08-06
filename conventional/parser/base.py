import abc
from re import Match
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Optional,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

T = TypeVar("T")

ParseResult = Union[Optional[Match], Iterable[Match]]

ParseMethod = Callable[[str], ParseResult]
ParserCollection = Dict[str, ParseMethod]


class ParsedItem(TypedDict):
    _raw: str


class Parser(abc.ABC, Generic[T]):
    def _process_match(self, groups: Dict[str, str]) -> Dict[str, Any]:
        parsers = self.get_parsers()

        results: Dict[str, Any] = {}
        for key, value in groups.items():
            data: Any = value

            if data is not None:
                data = data.strip()

                if key in parsers:
                    data = self._parse(parsers[key], data)

                results[key] = data

        return results

    def _parse(self, parser: ParseMethod, text: str) -> Dict[str, Any]:
        parser_result = parser(text)
        result = {"_raw": text}

        if not parser_result:
            return result

        def _process(match: Match) -> Dict[str, Any]:
            return self._process_match(match.groupdict())

        if not isinstance(parser_result, Iterable):
            return {**result, **_process(parser_result)}
        else:
            return {**result, "items": [_process(match) for match in parser_result]}

    @abc.abstractmethod
    def get_parsers(self) -> ParserCollection:
        raise NotImplementedError()

    def has_parsed(self, data: Dict[str, Any]) -> bool:
        return True

    def post_process(self, data: Dict[str, Any]) -> None:
        pass

    def parse(self, subject: str, body: str = None) -> Optional[T]:
        parsers = self.get_parsers()

        data: Any = {}
        if body is not None and "body" in parsers:
            data = {**data, **self._process_match({"body": body})}

        if "subject" in parsers:
            data = {**data, **self._process_match({"subject": subject})}

        if not self.has_parsed(data):
            return None

        self.post_process(data)
        return cast(T, data)
