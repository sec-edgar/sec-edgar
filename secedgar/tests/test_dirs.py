# Tests if directories correctly built for files
import os


def test_if_default_data_path_built(crawler, valid_make_dir_args):
    crawler._make_directory(**valid_make_dir_args)
    assert os.path.isdir(crawler.data_path)
