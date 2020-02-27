import warnings

from SECEdgar.client.network_client import NetworkClient
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
            self._lookups = [lookups]  # make single string into list
        else:
            try:
                # Check that iterable only contains strings and is not empty
                if not lookups or not all(type(o) is str for o in lookups):
                    raise TypeError
                self._lookups = lookups
            except TypeError:
                raise TypeError("CIKs must be given as string or iterable.")
        self._params = {'action': 'getcompany'}
        if client is None:
            self._client = NetworkClient(**kwargs)

    @property
    def path(self):
        """str: Path to add to client base."""
        return "cgi-bin/browse-edgar"

    @property
    def client(self):
        """``SECEdgar.client.base``: Client to use to fetch requests."""
        return self._client

    @property
    def params(self):
        """:obj:`dict` Search parameters to add to client."""
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
        self._validate_lookup(lookup)
        try:  # try to lookup by CIK
            self._params['CIK'] = lookup
            soup = self._client.get_soup(self.path, self.params)
        except EDGARQueryError:  # fallback to lookup by company name
            del self._params['CIK']  # delete this parameter so no conflicts arise
            self._params['company'] = lookup
            soup = self._client.get_soup(self.path, self.params)
        try:  # try to get single CIK for lookup
            span = soup.find('span', {'class': 'companyName'})
            return span.find('a').getText().split()[0]  # returns single CIK
        except AttributeError:  # warn and skip if multiple possibilities for CIK found
            warnings.warn("Lookup '{0}' will be skipped. "
                          "Found multiple companies matching '{0}':".format(lookup))
            warnings.warn('\n'.join(self._get_cik_possibilities(soup)))
        finally:
            # Delete parameters after lookup
            if self._params.get('company') is not None:
                del self._params['company']
            if self._params.get('CIK') is not None:
                del self._params['CIK']

    @staticmethod
    def _get_cik_possibilities(soup):
        """Get all CIK possibilities if multiple are listed.

        Args:
            soup (BeautifulSoup): BeautifulSoup object to search through.

        Returns:
            All possible companies that match lookup.
        """
        try:
            # Exclude table header
            table_rows = soup.find('table', {'summary': 'Results'}).find_all('tr')[1:]
            # Company names are in second column of table
            return [''.join(row.find_all('td')[1].find_all(text=True)) for row in table_rows]
        except AttributeError:
            raise EDGARQueryError  # If there are no CIK possibilities, then no results were returned

    @staticmethod
    def _validate_cik(cik):
        """Check if CIK is 10 digit string."""
        if not (isinstance(cik, str) and len(cik) == 10 and cik.isdigit()):
            raise CIKError(cik)

    @staticmethod
    def _validate_lookup(lookup):
        """Ensure that lookup is string.

        Args:
            lookup: Value to lookup.

        Raises:
            TypeError: If lookup is not string.
        """
        if not isinstance(lookup, str):
            raise TypeError("Lookup value must be string. Given type {0}.".format(type(lookup)))
