import pytest


@pytest.mark.parametrize(
    "exc",
    [
        "EDGARQueryError",
        "CIKError",
        "FilingTypeError"

    ]
)
def test_exception_importable(exc):
    from secedgar import exceptions

    err = getattr(exceptions, exc)
    assert err is not None

    # check that we can raise on them
    msg = "^$"

    with pytest.raises(err, match=msg):
        raise err()
