from SECEdgar.filings.cik_validator import CIKValidator


class CIK(object):
    """
    Validates CIKs (Central Index Keys) by ticker.

    Attributes:
        lookup (Union[str, list]): Ticker, company name, or list of tickers and/or company names.

    .. versionadded:: 0.1.5
    """

    def __init__(self, lookups, **kwargs):
        super(CIK, self).__init__(**kwargs)
        self._validator = CIKValidator(lookups)
        # TODO: Differ validation until later?
        self._lookup_dict = None
        self._ciks = None

    @property
    def ciks(self):
        """:obj:`list` of :obj:`str`: List of CIKs (as string of digits) transformed from lookups."""
        if self._ciks is None:
            self._lookup_dict = self._validator.get_ciks()
            self._ciks = list(self._lookup_dict.values())
        return self._ciks

    @property
    def lookup_dict(self):
        """:obj:`dict`: Dictionary that makes tickers and company names to CIKs."""
        if self._lookup_dict is None:
            self._lookup_dict = self._validator.get_ciks()
        return self._lookup_dict
