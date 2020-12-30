import warnings
import json

from secedgar.client.network_client import NetworkClient
from secedgar.utils.cik_map import get_cik_map
from secedgar.utils.exceptions import CIKError, EDGARQueryError


class CIKLookup:
    """CIK Lookup object.

    Given list of tickers/company names to lookup, this object can return associated CIKs.

    Attributes:
        lookup (Union[str, list]): Ticker, company name, or list of tickers and/or company names.

    .. versionadded:: 0.1.5
    """

    def __init__(self, lookups, **kwargs):
        super().__init__(**kwargs)
        if lookups and isinstance(lookups, str):
            self._lookups = [lookups]  # make single string into list
        else:
            # Check that iterable only contains strings and is not empty
            if not (lookups and all(type(o) is str for o in lookups)):
                raise TypeError("CIKs must be given as string or iterable.")
            self._lookups = lookups
        self._params = {'action': 'getcompany'}

        # TODO: Differ validation until later?
        self._lookup_dict = None
        self._ciks = None
        self._cik_maps = None

    @property
    def ciks(self):
        """:obj:`list` of :obj:`str`: List of CIKs (as string of digits)."""
        if self._ciks is None:
            self._lookup_dict = self.get_ciks()
            self._ciks = list(self._lookup_dict.values())
        return self._ciks

    @property
    def lookup_dict(self):
        """:obj:`dict`: Dictionary that makes tickers and company names to CIKs."""
        if self._lookup_dict is None:
            self._lookup_dict = self.get_ciks()
        return self._lookup_dict

    @property
    def lookups(self):
        """`list` of `str` to lookup (to get CIK values)."""
        return self._lookups

    @property
    def cik_maps(self):
        """Get dictionary of tickers to CIK numbers.

        Returns:
            Dictionary with a ticker and title dictionary lookup

        .. versionadded:: 0.1.6
        """
        if self._cik_maps:
            return self._cik_maps
    
        response = self._client.get_response('files/company_tickers.json')
        json_response = json.loads(response.text)
        ticker_map = {v['ticker']: str(v["cik_str"]) for v in json_response.values()}
        title_map = {v['title']: str(v["cik_str"]) for v in json_response.values()}
        self._cik_maps = (ticker_map, title_map)
        return self._cik_maps

    def get_ciks(self):
        """Validate lookup values and return corresponding CIKs.

        Returns:
            ciks (dict): Dictionary with lookup terms as keys and CIKs as values.

        """
        ciks = {}
        to_lookup = set(self.lookups)
        found = set()

        # First, try to get all CIKs with ticker map
        (ticker_map, title_map) = self.cik_maps
        for lookup in to_lookup:
            if lookup.upper() in ticker_map:
                # Tickers in map are upper case, so look up with upper case
                ciks[lookup] = ticker_map[lookup.upper()]
                found.add(lookup)
            elif lookup in title_map:
                ciks[lookup] = title_map[lookup]
                found.add(lookup)
        to_lookup -= found

        # Finally, if lookups are still left, look them up through the SEC's search
        for lookup in to_lookup:
            try:
                result = self._search_for_cik(lookup)
                self._validate_cik(result)  # raises error if not valid CIK
                ciks[lookup] = result
            except CIKError:
                pass  # If multiple companies, found, just print out warnings
        return ciks

    def _search_for_cik(self, lookup):
        """ Search for a comapany using the EDGAR search.

        .. warning: This method will warn when lookup returns multiple possibilities for a
            CIK are found.

        Args:
            lookup (str): CIK, company name, or ticker symbol which was looked up.

        Returns:
            CIK (str): CIK for lookup.
        """
        # At this point, the lookup term should be a company name.
        self._params['company'] = lookup
        soup = self._client.get_soup("cgi-bin/browse-edgar", self._params)
        try:  # try to get single CIK for lookup
            span = soup.find('span', {'class': 'companyName'})
            return span.find('a').getText().split()[0]  # returns single CIK
        except AttributeError:  # warn and skip if multiple possibilities for CIK found
            table_rows = soup.find('table', {'summary': 'Results'}).find_all('tr')[1:]
            cik_possibilities = [''.join(row.find_all('td')[1].find_all(text=True)) for row in table_rows]
            warning_message = """Lookup '{0}' will be skipped.
                          Found multiple companies matching '{0}':
                          {1}""".format(lookup, '\n'.join(cik_possibilities(soup)))
            warnings.warn(warning_message)

    @staticmethod
    def _validate_cik(cik):
        """Check if CIK is 10 digit string."""
        if not (isinstance(cik, str) and len(cik) == 10 and cik.isdigit()):
            raise CIKError(cik)
