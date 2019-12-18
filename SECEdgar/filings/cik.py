from SECEdgar.base import _EDGARBase
from SECEdgar.utils.exceptions import CIKError


class CIK(_EDGARBase):
    """
    Class to get and validate CIK by ticker.

    Attributes:
        lookup (Union[str, list]): Ticker or list of tickers.

    .. versionadded:: 0.1.5
    """
    def __init__(self, lookup, **kwargs):
        super(CIK, self).__init__(**kwargs)
        self._lookup = lookup
        self._cik = self._get_all_ciks()
        self._params['action'] = 'getcompany'

    @property
    def url(self):
        return "browse-edgar"

    @property
    def cik(self):
        return self._cik

    def _get_all_ciks(self):
        """
        Gets CIKs based on _lookup attribute.

        Returns:
            ciks (Union[str, list]): CIKs as string or list of strings
            based on lookup attribute.

        Raises:
            CIKError: If any given value in _lookup does not return
            CIK.
        """
        if isinstance(self._lookup, str):
            return self._get_cik(self._lookup)
        elif isinstance(self._lookup, (tuple, list, set)):
            ciks = []
            for cik in self._lookup:
                ciks.append(self._get_cik(cik))
            return ciks
        else:
            raise CIKError(self._lookup)

    def _get_cik(self, lookup):
        """
        Get CIK for given lookup value.

        Args:
            lookup (str): Symbol ticker to lookup.

        Returns:
            cik (str): CIK string for given ticker if it exists.

        Raises:
            EDGARQuerryError: If request returns invalid response or
            no such CIK is returned for given ticker.
        """
        self.params['CIK'] = lookup
        soup = self.get_soup()
        span = soup.find('span', {'class': 'companyName'})
        return span.find('a').getText().split()[0]  # get CIK number
