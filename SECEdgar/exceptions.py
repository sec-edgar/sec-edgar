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
        return "Field {field} not found in endpoint {endpoint}".format(self.field, self.endpoint)
