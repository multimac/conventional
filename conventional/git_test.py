import logging
import pathlib
import subprocess

import pytest

from . import git

logging.basicConfig(force=True, level=logging.DEBUG)
pytestmark = pytest.mark.asyncio


@pytest.fixture()
def git_repository(tmp_path_factory) -> pathlib.PurePath:
    path = tmp_path_factory.mktemp("git")
    print(f"Git repository: {path.as_posix()}")

    subprocess.run(["git", "init"], cwd=str(path))
    return path


async def test_commit_list(git_repository: pathlib.PurePath) -> None:
    await git.create_commit(git_repository, "feat: A new feature", allow_empty=True)
    await git.create_commit(git_repository, "fix: And a minor fix", allow_empty=True)
    await git.create_commit(
        git_repository, "chore: A commit with a body\n\nThe body of the commit", allow_empty=True
    )

    commits = [commit async for commit in git.get_commits(path=git_repository)]
    expected_commits = [
        {"subject": "chore: A commit with a body", "body": "The body of the commit"},
        {"subject": "fix: And a minor fix"},
        {"subject": "feat: A new feature"},
    ]

    assert len(commits) == len(expected_commits)
    for actual, expected in zip(commits, expected_commits):
        assert expected == {k: v for k, v in actual.items() if k in expected}


async def test_commit_tags(git_repository: pathlib.PurePath) -> None:
    await git.create_commit(git_repository, "feat: Version A.B.C", allow_empty=True)
    await git.create_tag(git_repository, "vA.B.C")

    await git.create_commit(git_repository, "fix: And a minor fix", allow_empty=True)
    await git.create_tag(
        git_repository,
        "vA.B.C-1",
        "Some commit message which makes this an annotated tag\n\nWith a body",
    )

    tags = await git.get_tags(path=git_repository)
    commits = [commit async for commit in git.get_commits(path=git_repository)]

    expected_tags = [
        {"name": "vA.B.C", "object_name": commits[1]["rev"], "subject": "", "body": ""},
        {
            "name": "vA.B.C-1",
            "object_name": commits[0]["rev"],
            "subject": "Some commit message which makes this an annotated tag",
            "body": "With a body",
        },
    ]

    expected_commits = [
        {"subject": "fix: And a minor fix", "tags": [expected_tags[1]]},
        {"subject": "feat: Version A.B.C", "tags": [expected_tags[0]]},
    ]

    assert len(tags) == len(expected_tags)
    for actual_tag, expected_tag in zip(tags, expected_tags):
        assert expected_tag == {k: v for k, v in actual_tag.items() if k in expected_tag}

    assert len(commits) == len(expected_commits)
    for actual_commit, expected_commit in zip(commits, expected_commits):
        assert expected_commit == {k: v for k, v in actual_commit.items() if k in expected_commit}
