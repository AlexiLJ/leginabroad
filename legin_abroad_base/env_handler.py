import os
import json

def var_getter(name: str, storage: str|None = "~/.django_env"):
    '''

    :param name: str name of the sys. variable
    :param storage: str|None
    :return: Any
    '''
    if storage:
        with open(storage) as st:
            var = json.load(st)
            var = var.get(name)
    else:
        var = os.environ.get(name)
    print(name, var)
    return var


