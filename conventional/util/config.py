import pathlib
from typing import Optional

from .. import git


async def find_project_configuration_file(path: pathlib.Path = None) -> Optional[pathlib.Path]:
    path = path or pathlib.Path.cwd()

    if not await git.is_git_repository(path):
        return None

    root = await git.get_repository_root(path)
    config_file = root.joinpath(".conventional.yaml")

    return config_file if config_file.exists() else None
