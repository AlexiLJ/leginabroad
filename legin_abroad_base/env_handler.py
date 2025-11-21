import json
from pathlib import Path


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


def var_getter(name: str):
    """
    Getting sys. variables based on the git branch
    :param name: str name of the sys. variable
    :return: Any
    """
    branch = get_active_branch_name()
    pathes = Path(__file__).parent.resolve() / "pathes.json"
    with open(pathes) as p:
        storage = json.load(p).get(branch)  # environment variables
    with open(Path(storage)) as st:
        var = json.load(st).get(name)
    return var
