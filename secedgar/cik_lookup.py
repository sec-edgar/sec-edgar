import functools
import warnings

import requests

from secedgar.client import NetworkClient
from secedgar.exceptions import CIKError, EDGARQueryError


@functools.lru_cache()
def get_cik_map():
    """Get dictionary of tickers and company names to CIK numbers.

    Uses ``functools.lru_cache`` to cache response if used in later calls.
    To clear cache, use ``get_cik_map.cache_clear()``.

    .. note::
       All company names and tickers are normalized by converting to upper case.

    Returns:
        Dictionary with keys "ticker" and "title". To get dictionary
            mapping tickers to CIKs, use "ticker". To get
            company names mapped to CIKs, use "title".

    .. note::

       If any tickers or titles are ``None``, the ticker or title will
       be excluded from the returned dictionary.

    .. versionadded:: 0.1.6
    """
    response = requests.get("https://www.sec.gov/files/company_tickers.json")
    json_response = response.json()
    return {key: {v[key].upper(): str(v["cik_str"]) for v in json_response.values()
                  if v[key] is not None}
            for key in ("ticker", "title")}


class CIKLookup:
    """CIK Lookup object.

    Given list of tickers/company names to lookup, this object can return associated CIKs.

    Args:
        lookup (Union[str, list]): Ticker, company name, or list of tickers and/or company names.
        client (secedgar.client.NetworkClient): A network client object to use. See
            :class:`secedgar.client.NetworkClient` for more details.

    .. versionadded:: 0.1.5
    """

    def __init__(self, lookups, client, **kwargs):
        if lookups and isinstance(lookups, str):
            self._lookups = [lookups]  # make single string into list
        else:
            # Check that iterable only contains strings and is not empty
            if not (lookups and all(type(o) is str for o in lookups)):
                raise TypeError("CIKs must be given as string or iterable.")
            self._lookups = lookups
        self._params = {}
        self._client = client or NetworkClient(**kwargs)
        self._lookup_dict = None
        self._ciks = None

    @property
    def ciks(self):
        """:obj:`list` of :obj:`str`: List of CIKs (as string of digits)."""
        if self._ciks is None:
            self._ciks = list(self.lookup_dict.values())
        return self._ciks

    @property
    def lookups(self):
        """`list` of `str` to lookup (to get CIK values)."""
        return self._lookups

    @property
    def path(self):
        """str: Path to add to client base."""
        return "cgi-bin/browse-edgar"

    @property
    def client(self):
        """``secedgar.client.NetworkClient``: Client to use to fetch requests."""
        return self._client

    @property
    def params(self):
        """:obj:`dict` Search parameters to add to client."""
        return self._params

    @property
    def lookup_dict(self):
        """:obj:`dict`: Dictionary that makes tickers and company names to CIKs."""
        if self._lookup_dict is None:
            self._lookup_dict = self.get_ciks()
        return self._lookup_dict

    # TODO: Add mock to test this functionality
    def _get_lookup_soup(self, lookup):
        """Gets `BeautifulSoup` object for lookup.

        First tries to lookup using CIK. Then falls back to company name.

        .. warning::
           Only to be used internally by `_get_cik_from_html` to get CIK from lookup.

        Args:
            lookup (str): CIK, company name, or ticker symbol to lookup.

        Returns:
            soup (bs4.BeautifulSoup): `BeautifulSoup` object to be used to get
                company CIK.
        """
        try:  # try to lookup by CIK
            self._params['CIK'] = lookup
            return self._client.get_soup(self.path, self.params)
        except EDGARQueryError:  # fallback to lookup by company name
            self.params.pop('CIK')  # delete this parameter so no conflicts arise
            self._params['company'] = lookup
            return self._client.get_soup(self.path, self.params)

    def _get_cik_from_html(self, lookup):
        """Gets CIK from `BeautifulSoup` object.

        .. warning: This method will warn when lookup returns multiple possibilities for a
            CIK are found.

        Args:
            lookup (str): CIK, company name, or ticker symbol which was looked up.

        Returns:
            CIK (str): CIK for lookup.
        """
        self._validate_lookup(lookup)
        soup = self._get_lookup_soup(lookup)
        try:  # try to get single CIK for lookup
            span = soup.find('span', {'class': 'companyName'})
            return span.find('a').getText().split()[0]  # returns single CIK
        except AttributeError:  # warn and skip if multiple possibilities for CIK found
            warning_message = """Lookup '{0}' will be skipped.
                          Found multiple companies matching '{0}':
                          {1}""".format(lookup, '\n'.join(self._get_cik_possibilities(soup)))
            warnings.warn(warning_message)
        finally:
            # Delete parameters after lookup
            self._params.pop('company', None)
            self._params.pop('CIK', None)

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
            # If there are no CIK possibilities, then no results were returned
            raise EDGARQueryError

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
            TypeError: If lookup is not a non-empty string.
        """
        if not (lookup and isinstance(lookup, str)):
            raise TypeError("Lookup value must be string. Given type {0}.".format(type(lookup)))

    def get_ciks(self):
        """Validate lookup values and return corresponding CIKs.

        Returns:
            ciks (dict): Dictionary with lookup terms as keys and CIKs as values.

        """
        ciks = {}
        to_lookup = set(self.lookups)

        cik_map = get_cik_map()

        # all keys upper case
        ticker_map = cik_map["ticker"]
        title_map = cik_map["title"]

        for lookup in to_lookup:
            lookup_norm = lookup.upper()
            if lookup_norm.isdigit():
                ciks[lookup] = lookup
            elif lookup_norm in ticker_map:
                ciks[lookup] = ticker_map[lookup_norm]
            elif lookup_norm in title_map:
                ciks[lookup] = title_map[lookup_norm]
            else:
                try:
                    result = self._get_cik_from_html(lookup)
                    self._validate_cik(result)  # raises CIKError if not valid CIK
                    ciks[lookup] = result
                except CIKError:
                    pass  # If multiple companies, found, print out warnings and skip
        return ciks
