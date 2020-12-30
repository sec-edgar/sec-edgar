import datetime
import os

from secedgar.utils.cik_map import get_cik_map  # noqa:F401

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



