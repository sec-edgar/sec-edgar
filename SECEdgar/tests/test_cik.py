from SECEdgar.filings import CIK


class TestCIK(object):
    def test_cik_returns_correct_values(self, valid_companies):
        for company, cik in valid_companies.items():
            returned_cik = CIK(company).cik
            if returned_cik != cik:
                raise AssertionError("CIK for {0} expected "
                                     "{1}, got {2}".format(company, cik, returned_cik))
