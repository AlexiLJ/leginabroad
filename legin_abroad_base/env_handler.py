import json
from pathlib import Path


def get_git_parent_dir(search_start: str = 'leginabroad'):
    cwd = list(Path.cwd().parts) # getting splitted cwd dir
    if search_start not in cwd:
        raise Exception(f'No parent dir: {search_start} detected')
    for path_part in cwd[::-1]:
        if path_part != search_start:
            cwd.pop()
        break
    return Path(*cwd) / '.git'

def get_active_branch_name() -> str:
    """
    :return: str
    """
    hidden_dir = get_git_parent_dir() / "HEAD"
    hidden_dir.chmod(0o444)
    # assert head_dir.is_file()
    with open(hidden_dir) as f:
        content = f.read().splitlines()
    for line in content:
        if line[0:4] == "ref:":
            return line.partition("refs/heads/")[2]


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

