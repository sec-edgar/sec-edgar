import datetime
import os

def make_path(path, **kwargs):
    """Make directory based on filing info.

    Args:
        path (str): Path to be made if it doesn't exist.
        **kwargs: Keyword arguments to pass to ``os.makedirs``.

    Raises:
        OSError: If there is a problem making the path.

    Returns:
        None
    """
    if not os.path.exists(path):
        os.makedirs(path, **kwargs)

def batch(iterable, n):
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx:min(ndx + n, length)]

