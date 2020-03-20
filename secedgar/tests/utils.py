import os


def datapath(*args):
    """Get the path to a data file.

    Returns:
        path including ``secedgar/tests/data``.
    """
    base_path = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(base_path, *args)
