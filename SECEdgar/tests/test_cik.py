from SECEdgar.filings import CIK


class TestCIK(object):
    def test_cik_returns_correct_values(self, valid_companies):
        returned_ciks = CIK(valid_companies.keys()).lookup_dict
        for ticker, cik in valid_companies.items():
            if returned_ciks[ticker] != cik:
                raise AssertionError("CIK for {0} expected "
                                     "{1}, got {2}".format(ticker, cik, returned_ciks[ticker]))

    def test_cik_company_name(self, single_result_companies):
        returned_ciks = CIK(single_result_companies.keys()).lookup_dict
        print(returned_ciks)
        for company_name, cik in single_result_companies.items():
            if returned_ciks[company_name] != single_result_companies[company_name]:
                raise AssertionError("CIK for {0} expected "
                                     "{1}, got {2}".format(company_name, cik, returned_ciks[company_name]))

    def test_multiple_results_company_name_search(self, multiple_result_companies):
        returned_ciks = CIK(multiple_result_companies).lookup_dict
        for company_name in multiple_result_companies:
            print(company_name)
