from SECEdgar.filings import CIK


class TestCIK(object):
    def test_cik_returns_correct_values(self, valid_companies):
        returned_ciks = CIK(valid_companies.keys()).lookup_dict
        for company, cik in valid_companies.items():
            if returned_ciks[company] != cik:
                raise AssertionError("CIK for {0} expected "
                                     "{1}, got {2}".format(company, cik, returned_ciks[company]))
