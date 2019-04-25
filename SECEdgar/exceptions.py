class EDGARQueryError(Exception):
    """
    This error is thrown when a query receives a response that is not a 200 response.
    """

    def __init__(self, response):
        self.response = response

    def __str__(self):
        return "An error occured while making the query. Received {response} response".format(response=self.response)


class EDGARFieldError(Exception):
    """
    This error is thrown when an invalid field is given to an endpoint.
    """

    def __init__(self, endpoint, field):
        self.endpoint = endpoint
        self.field = field

    def __str__(self):
        return "Field {field} not found in endpoint {endpoint}".format(field=self.field, endpoint=self.endpoint)


class CIKError(Exception):
    """
    This error is thrown when an invalid CIK is given.
    """

    def __init__(self, cik):
        self.cik = cik

    def __str__(self):
        return "CIK {cik} is not valid. Must be str or int with 10 digits.".format(cik=self.cik)
