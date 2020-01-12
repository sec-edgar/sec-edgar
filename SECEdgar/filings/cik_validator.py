from SECEdgar.base import _EDGARBase
from SECEdgar.utils.exceptions import CIKError, EDGARQueryError


class CIKValidator(_EDGARBase):
    """
    .. versionadded:: 0.1.5
    """

    def __init__(self, lookups, **kwargs):
        super(CIKValidator, self).__init__(**kwargs)
        if isinstance(lookups, str):
            self._lookups = [lookups]
        else:
            try:
                if not all(type(o) is str for o in lookups):
                    raise TypeError("CIKs must be given as string or iterable.")
                self._lookups = lookups
            except TypeError:
                raise TypeError("CIKs must be given as string or iterable.")
        self._params['action'] = 'getcompany'

    @property
    def url(self):
        return "cgi-bin/browse-edgar"

    def get_ciks(self):
        """
        Validate lookup values and return corresponding CIKs in order.

        Returns:
            ciks (dict): Dictionary with lookup terms as keys and CIKs as values.

        """
        ciks = dict()
        for lookup in self._lookups:
            result = self._get_cik(lookup)
            self._validate_cik(result)  # raises error if not valid CIK
            ciks[lookup] = result
        return ciks

    def _get_cik(self, lookup):
        """
        Get cik for lookup value.
        """
        self._validate_lookup(lookup)  # make sure lookup is valid
        try:  # try to lookup by CIK
            self._params['CIK'] = lookup
            soup = self.get_soup()
            del self._params['CIK']
        except EDGARQueryError:  # fallback to lookup by company name
            # TODO: Handle case where multiple companies returned for lookup value
            self._params['company'] = lookup
            soup = self.get_soup()
            del self._params['company']
        span = soup.find('span', {'class': 'companyName'})
        return span.find('a').getText().split()[0]  # returns CIK

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
