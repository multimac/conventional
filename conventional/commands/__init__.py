from asyncio import run
from pathlib import Path
from typing import Optional

from confuse import Configuration
from typer import Argument, Context, FileText, Option, Typer

group = Typer()


@group.command("list-commits")
def _list_commits(
    ctx: Context,
    *,
    output: FileText = Option(
        "-",
        help="A file to write commits to. If `-`, commits will be written to stdout.",
        mode="w",
    ),
    from_rev: Optional[str] = Option(
        None, "--from", help="The commit or tag to start from when listing commits from."
    ),
    from_last_tag: bool = Option(
        False,
        "--from-last-tag",
        help="If given, the commit list will start from the most-recent tag.",
    ),
    to_rev: str = Option("HEAD", "--to", help="The commit or tag to stop at listing commits."),
    reverse: bool = Option(
        False,
        "--reverse",
        help="If given, the list of commits will be reversed (ie. oldest commit first).",
    ),
    parse: bool = Option(
        False, "--parse", help="If set, commits will be parsed with `parse-commit`."
    ),
    include_unparsed: bool = Option(
        False,
        help="If set, commits which fail to be parsed will be included in the output. See `parse-commit`.",
    ),
    path: Optional[Path] = Argument(None),
) -> None:
    """
    Retrieves commits from the git repository at PATH, or the current directory if PATH is not provided.
    """

    from .list_commits import main

    run(
        main(
            ctx.find_object(Configuration),
            output=output,
            from_rev=from_rev,
            from_last_tag=from_last_tag,
            to_rev=to_rev,
            reverse=reverse,
            parse=parse,
            include_unparsed=include_unparsed,
            path=path,
        )
    )


@group.command("parse-commit")
def _parse_commit(
    ctx: Context,
    *,
    input: FileText = Option(
        "-", help="A file to read commits from. If `-`, commits will be read from stdin."
    ),
    output: FileText = Option(
        "-",
        help="A file to write parsed commits to. If `-`, parsed commits will be written to stdout.",
        mode="w",
    ),
    include_unparsed: bool = Option(
        False, help="If set, commits which fail to be parsed will be returned."
    ),
) -> None:
    """
    Parses a stream of commits in the given file or from stdin.
    """

    from .parse_commit import main

    run(
        main(
            ctx.find_object(Configuration),
            input=input,
            output=output,
            include_unparsed=include_unparsed,
        )
    )


@group.command("template")
def _template(
    ctx: Context,
    *,
    input: Optional[FileText] = Option(
        None,
        help="A file to read commits from. If `-`, commits will be read from stdin. Defaults to reading commits from a git repository in the current directory.",
    ),
    output: FileText = Option(
        "-",
        help="A file to write parsed commits to. If `-`, parsed commits will be written to stdout.",
        mode="w",
    ),
    include_unparsed: bool = Option(
        False,
        help="If set, commits which fail to be parsed will be returned. See `parse-commit`.",
    ),
    path: Optional[Path] = Argument(None),
) -> None:
    """
    Reads a stream of commits from the given file or stdin and uses them to render a template.
    """

    from .template import main

    run(
        main(
            ctx.find_object(Configuration),
            input=input,
            output=output,
            include_unparsed=include_unparsed,
            path=path,
        )
    )
