import pytest


@pytest.fixture(scope="session")
def tmp_data_directory(tmpdir_factory):
    return str(tmpdir_factory.mktemp("tmp_data"))
