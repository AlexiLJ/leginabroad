import os

def var_getter(name: str):
    '''

    :param name: str name of the sys. variable
    :return: Any
    '''
    var = os.environ.get(name)
    print(name, var)
    return var
