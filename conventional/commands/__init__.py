from asyncio import run
from typing import Optional

from confuse import Configuration
from typer import Context, FileText, Option, Typer

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
    unreleased_version: Optional[str] = Option(
        None, help="If set, will be used as the tag name for unreleased commits."
    ),
    template_name: Optional[str] = Option(
        None, help="If set, will override the name of the template to be loaded."
    ),
) -> None:
    """
    Reads a stream of commits from the given file or stdin and uses them to render a template.
    """

    from .template import main

    config = ctx.find_object(Configuration)

    if template_name is not None:
        config.set_args({"template.name": template_name}, dots=True)

    run(
        main(
            config,
            input=input,
            output=output,
            include_unparsed=include_unparsed,
            unreleased_version=unreleased_version,
        )
    )
