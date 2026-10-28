import json
import os
from pathlib import Path


_MISSING = object()


def get_git_parent_dir(search_start: str = "leginabroad") -> Path:
    cwd_parts = list(Path.cwd().parts)
    if search_start not in cwd_parts:
        raise RuntimeError(f"No parent dir: {search_start} detected")

    while cwd_parts and cwd_parts[-1] != search_start:
        cwd_parts.pop()

    return Path(*cwd_parts) / ".git"



def get_active_branch_name() -> str:
    head_file = get_git_parent_dir() / "HEAD"
    with open(head_file) as f:
        content = f.read().splitlines()
    for line in content:
        if line.startswith("ref:"):
            return line.partition("refs/heads/")[2]
    # detached HEAD case
    return "DETACHED_HEAD"



def var_getter(name: str, default=_MISSING):
    """
    Return a setting from the process environment.

    The branch-based JSON lookup remains as a temporary fallback so the current
    host deployment keeps working while Docker is introduced. Containers should
    always provide settings through environment variables.
    """
    if name in os.environ:
        value = os.environ[name]
        if value:
            return value
        raise RuntimeError(f"Environment variable {name} is set but empty")

    try:
        branch = get_active_branch_name()
        paths_file = Path(__file__).parent.resolve() / "pathes.json"
        with paths_file.open(encoding="utf-8") as paths_stream:
            storage = json.load(paths_stream).get(branch)
        if not storage:
            raise RuntimeError(f"No legacy settings file is configured for branch {branch}")
        with Path(storage).open(encoding="utf-8") as storage_stream:
            value = json.load(storage_stream).get(name)
    except (FileNotFoundError, RuntimeError) as error:
        if default is not _MISSING:
            return default
        raise RuntimeError(
            f"Missing required setting {name}. Set it as an environment variable "
            "or configure the legacy settings files."
        ) from error

    if value is not None:
        return value
    if default is not _MISSING:
        return default
    raise RuntimeError(f"Missing required setting {name}")
