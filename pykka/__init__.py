#: Pykka's version as a tuple that can be used for comparison
VERSION = (0, 9)

def get_version():
    """Returns Pykka's version as a formatted string"""
    return '.'.join(map(str, VERSION))
