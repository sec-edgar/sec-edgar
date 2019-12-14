from SECEdgar.base import _EDGARBase
from SECEdgar.utils.exceptions import CIKError


class CIK(_EDGARBase):
    def __init__(self, lookup, **kwargs):
        super(CIK, self).__init__(**kwargs)
        self._lookup = lookup
        self._cik = self._get_all_ciks()
        self.params.update({'action': 'getcompany'})

    @property
    def url(self):
        return "browse-edgar"

    @property
    def cik(self):
        return self._cik

    # TODO: Add implementation to get company names, state, and CIK from html
    def _get_all_ciks(self):
        if isinstance(self._lookup, str):
            return self._get_cik(self._lookup)
        elif isinstance(self._lookup, (tuple, list, set)):
            ciks = []
            for cik in self._lookup:
                ciks.append(self._get_cik(cik))
            return ciks
        else:
            raise CIKError(self._lookup)

    def _get_cik(self, cik):
        self.params['CIK'] = cik
        soup = self._execute_query()
        span = soup.find('span', {'class': 'companyName'})
        return span.find('a').getText().split()[0]  # get CIK number
