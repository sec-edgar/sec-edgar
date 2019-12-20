import pytest

from SECEdgar.filings import CIK
from SECEdgar.utils.exceptions import EDGARQueryError


class TestCIK(object):
    def test_cik_returns_correct_values(self, valid_companies):
        returned_ciks = CIK(valid_companies.keys()).lookup_dict
        for ticker, cik in valid_companies.items():
            if returned_ciks[ticker] != cik:
                raise AssertionError("CIK for {0} expected "
                                     "{1}, got {2}".format(ticker, cik, returned_ciks[ticker]))

    def test_cik_company_name(self, single_result_companies):
        returned_ciks = CIK(single_result_companies.keys()).lookup_dict
        for company_name, cik in single_result_companies.items():
            if returned_ciks[company_name] != single_result_companies[company_name]:
                raise AssertionError("CIK for {0} expected "
                                     "{1}, got {2}".format(company_name,
                                                           cik, returned_ciks[company_name]))

    @pytest.mark.skip(reason='This feature is currently in progress.')
    def test_multiple_results_company_name_search(self, multiple_result_companies):
        # TODO: Add support for when lookup returns multiple companies
        for company_name in multiple_result_companies:
            pass

    def test_validate_cik(self):
        # string remains unchecked until query to allow for possibility of
        # using company name, ticker, or CIK as string
        with pytest.raises(EDGARQueryError):
            CIK('0notvalid0')
        with pytest.raises(EDGARQueryError):
            CIK('012345678910')
        # float and int not accepted, raising CIKError
        with pytest.raises(TypeError):
            CIK(1234567891011)
        with pytest.raises(TypeError):
            CIK(123.0)
