import pytest

from SECEdgar.tests.utils import datapath

from SECEdgar.filings import CIK
from SECEdgar.client import NetworkClient
from SECEdgar.utils.exceptions import EDGARQueryError


class MockSingleCIKLookupResponse:
    def __init__(self, *args):
        self.status_code = 200
        with open(datapath("single_cik_search_result.html")) as f:
            self.text = f.read()


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

    def test_multiple_results_company_name_search(self, monkeypatch, multiple_result_companies):
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKLookupResponse)
        assert len(CIK(multiple_result_companies).ciks) == 0

    def test_multiple_results_raises_warnings(self, multiple_result_companies):
        with pytest.warns(UserWarning):
            CIK(multiple_result_companies).ciks()

    def test_validate_cik(self):
        # string remains unchecked until query to allow for possibility of
        # using company name, ticker, or CIK as string
        with pytest.raises(EDGARQueryError):
            CIK('0notvalid0').ciks()
        with pytest.raises(EDGARQueryError):
            CIK('012345678910').ciks()
        # float and int not accepted, raising TypeError
        with pytest.raises(TypeError):
            CIK(1234567891011)
        with pytest.raises(TypeError):
            CIK(123.0)
