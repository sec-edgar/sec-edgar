from SECEdgar.filings.cik_validator import CIKValidator


class CIK(object):
    """
    Class to get and validate CIK by ticker.

    Attributes:
        lookup (Union[str, list]): Ticker or list of tickers.

    .. versionadded:: 0.1.5
    """

    def __init__(self, lookups, **kwargs):
        super(CIK, self).__init__(**kwargs)
        self._validator = CIKValidator(lookups)
        self._lookup_dict = self._validator.get_ciks()
        self._ciks = self._lookup_dict.values()

    @property
    def ciks(self):
        return self._ciks

    @property
    def lookup_dict(self):
        return self._lookup_dict
