from SECEdgar.base import _FilingBase


class Filing10K(_FilingBase):
    """Fetches 10-K reports from SEC for given CIK.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
    """

    def __init__(self, cik, **kwargs):
        super(Filing10K, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "10-K"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class Filing10Q(_FilingBase):
    """Fetches 10-Q reports from SEC for given CIK.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
    """

    def __init__(self, cik, **kwargs):
        super(Filing10Q, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "10-Q"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class Filing8K(_FilingBase):
    """Fetches 8-K reports from SEC for given CIK.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
    """

    def __init__(self, cik, **kwargs):
        super(Filing8K, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "8-K"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class FilingSD(_FilingBase):
    """Fetches SD reports from SEC for given CIK.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
    """

    def __init__(self, cik, **kwargs):
        super(FilingSD, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "SD"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class Filing13F(_FilingBase):
    """Fetches 13-F reports from SEC for given CIK.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
    """

    def __init__(self, cik, **kwargs):
        super(Filing13F, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "13-F"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class Filing4(_FilingBase):
    """Fetches '4' reports from SEC for given CIK.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
    """

    def __init__(self, cik, **kwargs):
        super(Filing4, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "4"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params
