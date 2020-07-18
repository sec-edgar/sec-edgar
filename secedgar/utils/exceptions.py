class EDGARQueryError(Exception):
    """This error is thrown when a query receives a response that is not a 200 response."""
    pass


class EDGARFieldError(Exception):
    """This error is thrown when an invalid field is given to an endpoint."""
    pass


class CIKError(Exception):
    """This error is thrown when an invalid CIK is given."""
    pass


class FilingTypeError(Exception):
    """This error is thrown when an invalid filing type is given."""
    pass
