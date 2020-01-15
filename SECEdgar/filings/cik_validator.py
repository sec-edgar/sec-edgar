import warnings

from SECEdgar.network_client import NetworkClient
from SECEdgar.utils.exceptions import CIKError, EDGARQueryError


class CIKValidator(object):
    """Validates company tickers and/or company names based on CIK availability.

    Used internally by the CIK class. Not intended for outside use.

    Args:
        lookups (Union[str, list, tuple]): List of tickers and/or company names for
            which to find CIKs.
        **kwargs: Any keyword arguments needed to be passed to
            _EDGARBase (see class for more details).

    .. versionadded:: 0.1.5
    """

    def __init__(self, lookups, client=None, **kwargs):
        if isinstance(lookups, str):
            self._lookups = [lookups]
        else:
            try:
                if not all(type(o) is str for o in lookups):
                    raise TypeError("CIKs must be given as string or iterable.")
                self._lookups = lookups
            except TypeError:
                raise TypeError("CIKs must be given as string or iterable.")
        self._params = {'action': 'getcompany'}
        if client is None:
            self._client = NetworkClient(**kwargs)

    @property
    def path(self):
        return "cgi-bin/browse-edgar"

    @property
    def client(self):
        return self._client

    @property
    def params(self):
        return self._params

    def get_ciks(self):
        """
        Validate lookup values and return corresponding CIKs in order.

        Returns:
            ciks (dict): Dictionary with lookup terms as keys and CIKs as values.

        """
        ciks = dict()
        for lookup in self._lookups:
            try:
                result = self._get_cik(lookup)
                self._validate_cik(result)  # raises error if not valid CIK
                ciks[lookup] = result
            except CIKError:
                pass  # If multiple companies, found, just print out warnings
        return ciks

    def _get_cik(self, lookup):
        """
        Get cik for lookup value.
        """
        self._validate_lookup(lookup)  # make sure lookup is valid
        try:  # try to lookup by CIK
            self._params['CIK'] = lookup
            soup = self._client.get_soup(self.path, self.params)
            del self._params['CIK']
        except EDGARQueryError:  # fallback to lookup by company name
            self._params['company'] = lookup
            soup = self._client.get_soup(self.path, self.params)
            del self._params['company']
        try:
            span = soup.find('span', {'class': 'companyName'})
            return span.find('a').getText().split()[0]  # returns CIK
        except AttributeError:
            warnings.warn("Lookup '{0}' will be skipped. "
                          "Found multiple companies matching '{0}':".format(lookup))
            warnings.warn('\n'.join(self._get_cik_possibilities(soup)))

    @staticmethod
    def _get_cik_possibilities(soup):
        # Exclude table header
        table_rows = soup.find('table', {'summary': 'Results'}).find_all('tr')[1:]
        company_possibilities = []
        for row in table_rows:
            # Company names are in second column of table
            company_possibilities.append(
                    ''.join(row.find_all('td')[1].find_all(text=True)))
        return company_possibilities

    @staticmethod
    def _validate_cik(cik):
        """
        Check if CIK is 10 digit string.
        """
        if not (isinstance(cik, str) and len(cik) == 10 and cik.isdigit()):
            raise CIKError(cik)

    @staticmethod
    def _validate_lookup(lookup):
        if not isinstance(lookup, str):
            raise TypeError("Lookup value must be string. Given type {0}.".format(type(lookup)))
