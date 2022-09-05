# Tests if filings are correctly received from EDGAR
import datetime
import os

import pytest
from secedgar.cik_lookup import CIKLookup
from secedgar.client import NetworkClient
from secedgar.core import CompanyFilings, FilingType
from secedgar.exceptions import FilingTypeError, NoFilingsError
from secedgar.tests.utils import MockResponse


@pytest.fixture
def mock_cik_validator_get_single_cik(monkeypatch):
    """Mocks response for getting a single CIK."""
    monkeypatch.setattr(CIKLookup, "get_ciks",
                        lambda *args, **kwargs: {"aapl": "0000320193"})


@pytest.fixture(scope="module")
def mock_cik_validator_get_multiple_ciks(monkeymodule):
    """Mocks response for getting a single CIK."""
    monkeymodule.setattr(
        CIKLookup, "get_ciks", lambda *args: {
            "aapl": "0000320193",
            "msft": "1234",
            "amzn": "5678"
        })


@pytest.fixture(scope="module")
def mock_single_cik_not_found(monkeymodule):
    """NetworkClient get_response method will return html with CIK not found message."""
    monkeymodule.setattr(
        NetworkClient, "get_response",
        MockResponse(datapath_args=["CIK", "cik_not_found.html"]))


@pytest.fixture(scope="module")
def mock_single_cik_filing(monkeymodule):
    """Returns mock response of filinghrefs for getting filing URLs."""
    monkeymodule.setattr(
        NetworkClient, "get_response",
        MockResponse(datapath_args=["filings", "aapl_10q_filings.xml"]))


class MockSingleCIKFilingLimitedResponses:

    def __init__(self, num_responses):
        self._called_count = 0
        self._num_responses = num_responses

    def __call__(self, *args):
        if self._called_count * 10 < self._num_responses:
            self._called_count += 1
            return MockResponse(
                datapath_args=["filings", "aapl_10q_filings.xml"])
        else:
            return MockResponse(content=bytes("", "utf-8"))


# FIXME: This may not be working as expected. Need to look into this more.
@pytest.fixture
def mock_single_cik_filing_limited_responses(monkeypatch):
    """Mocks when only a limited number of filings are available.

    Should be reset with each function run, since calls left decreases
    after each call."""
    mock_limited_responses = MockSingleCIKFilingLimitedResponses(
        num_responses=10)
    monkeypatch.setattr(NetworkClient, "get_response", mock_limited_responses)


class TestCompanyFilings:
    valid_dates = [
        datetime.datetime(2020, 1, 1),
        datetime.datetime(2020, 2, 1),
        datetime.datetime(2020, 3, 1),
        datetime.datetime(2020, 4, 1),
        datetime.datetime(2020, 5, 1),
        "20200101",
        20200101,
        None
    ]
    bad_dates = [
        1,
        2020010101,
        "2020010101",
        "2020",
        "0102"
    ]

    class TestCompanyFilingsClient:

        def test_user_agent_client_none(self):
            with pytest.raises(TypeError):
                _ = CompanyFilings(cik_lookup="aapl",
                                   filing_type=FilingType.FILING_10Q,
                                   user_agent=None,
                                   client=None)

        def test_user_agent_set_to_client(self, mock_user_agent):
            aapl = CompanyFilings(cik_lookup="aapl",
                                  filing_type=FilingType.FILING_10Q,
                                  user_agent=mock_user_agent)
            assert aapl.client.user_agent == mock_user_agent

        def test_client_property_set(self, mock_user_agent):
            aapl = CompanyFilings(cik_lookup="aapl",
                                  filing_type=FilingType.FILING_10Q,
                                  client=NetworkClient(user_agent=mock_user_agent))
            assert aapl.client.user_agent == mock_user_agent

    def test_count_returns_exact(self, mock_user_agent, mock_cik_validator_get_single_cik,
                                 mock_single_cik_filing):
        count = 10
        aapl = CompanyFilings(user_agent=mock_user_agent,
                              cik_lookup="aapl",
                              filing_type=FilingType.FILING_10Q,
                              count=count)
        urls = aapl.get_urls()["aapl"]
        assert len(urls) == count, """Count should return exact number of filings.
                                 Got {0}, but expected {1} URLs.""".format(urls, count)

    @pytest.mark.parametrize("count", [None, 5, 10, 15, 27, 33])
    def test_count_setter_on_init(self, mock_user_agent, count):
        filing = CompanyFilings(user_agent=mock_user_agent,
                                cik_lookup="aapl",
                                filing_type=FilingType.FILING_10Q,
                                count=count)
        assert filing.count == count

    @pytest.mark.parametrize("start_date", valid_dates)
    def test_good_start_date_setter_on_init(self, start_date, mock_user_agent):
        filing = CompanyFilings(
            cik_lookup="aapl",
            filing_type=FilingType.FILING_10Q,
            start_date=start_date,
            user_agent=mock_user_agent)
        assert filing.start_date == start_date

    @pytest.mark.parametrize("bad_start_date", bad_dates)
    def test_bad_start_date_setter_on_init(self, mock_user_agent, bad_start_date):
        with pytest.raises(TypeError):
            CompanyFilings(user_agent=mock_user_agent,
                           cik_lookup="aapl",
                           filing_type=FilingType.FILING_10Q,
                           start_date=bad_start_date)

    @pytest.mark.parametrize("end_date", valid_dates)
    def test_good_end_date_setter_on_init(self, end_date, mock_user_agent):
        filing = CompanyFilings(
            cik_lookup="aapl",
            filing_type=FilingType.FILING_10Q,
            end_date=end_date,
            user_agent=mock_user_agent)
        assert filing.end_date == end_date

    @pytest.mark.parametrize("bad_end_date", bad_dates)
    def test_bad_end_date_setter_on_init(self, mock_user_agent, bad_end_date):
        with pytest.raises(TypeError):
            CompanyFilings(user_agent=mock_user_agent,
                           cik_lookup="aapl",
                           filing_type=FilingType.FILING_10Q,
                           end_date=bad_end_date)

    @pytest.mark.parametrize("count,expected_error", [(-1, ValueError),
                                                      (0, ValueError),
                                                      (0.0, TypeError),
                                                      (1.0, TypeError),
                                                      ("1", TypeError)])
    def test_count_setter_bad_values(self, mock_user_agent, count, expected_error):
        with pytest.raises(expected_error):
            CompanyFilings(user_agent=mock_user_agent,
                           cik_lookup="aapl",
                           filing_type=FilingType.FILING_10Q,
                           count=count)

    def test_date_is_sanitized(self, mock_user_agent):
        start_date = datetime.datetime(2012, 3, 1)
        end_date = datetime.datetime(2015, 1, 1)
        aapl = CompanyFilings(user_agent=mock_user_agent,
                              cik_lookup="aapl",
                              filing_type=FilingType.FILING_10Q,
                              count=10,
                              start_date=start_date,
                              end_date=end_date)
        assert aapl.params["dateb"] == "20150101"
        assert aapl.params["datea"] == "20120301"
        assert aapl.start_date == datetime.datetime(2012, 3, 1)
        assert aapl.end_date == datetime.datetime(2015, 1, 1)

    def test_date_is_sanitized_when_changed(self, mock_user_agent):
        aapl = CompanyFilings(user_agent=mock_user_agent,
                              cik_lookup="aapl",
                              filing_type=FilingType.FILING_10Q,
                              count=10,
                              start_date="20150101")
        assert aapl.start_date == "20150101"
        aapl.start_date = datetime.datetime(2010, 1, 1)
        assert aapl.start_date == datetime.datetime(2010, 1, 1)
        assert aapl.params["datea"] == "20100101"

    @pytest.mark.parametrize("date,expected",
                             [("20120101", "20120101"), (20120101, 20120101),
                              (datetime.datetime(2012, 1, 1), "20120101")])
    def test_end_date_setter(self, mock_user_agent, date, expected):
        f = CompanyFilings(cik_lookup="aapl",
                           user_agent=mock_user_agent,
                           filing_type=FilingType.FILING_10Q,
                           start_date=datetime.datetime(2010, 1, 1),
                           end_date=datetime.datetime(2015, 1, 1))
        f.end_date = date
        assert f.end_date == date and f.params.get("dateb") == expected

    def test_txt_urls(self, mock_user_agent,
                      mock_cik_validator_get_single_cik,
                      mock_single_cik_filing):
        aapl = CompanyFilings(user_agent=mock_user_agent,
                              cik_lookup="aapl",
                              filing_type=FilingType.FILING_10Q,
                              count=10)
        first_txt_url = aapl.get_urls()["aapl"][0]
        assert first_txt_url.split(".")[-1] == "txt"

    @pytest.mark.smoke
    def test_txt_urls_smoke(self, real_test_client):
        aapl = CompanyFilings(client=real_test_client,
                              cik_lookup="aapl",
                              filing_type=FilingType.FILING_10Q,
                              count=10)
        first_txt_url = aapl.get_urls()["aapl"][0]
        assert first_txt_url.split(".")[-1] == "txt"

    @pytest.mark.parametrize("new_filing_type",
                             (FilingType.FILING_10K, FilingType.FILING_8K,
                              FilingType.FILING_13FHR, FilingType.FILING_SD))
    def test_filing_type_setter(self, mock_user_agent, new_filing_type):
        f = CompanyFilings(user_agent=mock_user_agent,
                           cik_lookup="aapl",
                           filing_type=FilingType.FILING_10Q)
        f.filing_type = new_filing_type
        assert f.filing_type == new_filing_type

    @pytest.mark.parametrize("bad_filing_type",
                             ("10-k", "10k", "10-q", "10q", 123))
    def test_bad_filing_type_setter(self, mock_user_agent, bad_filing_type):
        f = CompanyFilings(user_agent=mock_user_agent,
                           cik_lookup="aapl",
                           filing_type=FilingType.FILING_10Q)
        with pytest.raises(FilingTypeError):
            f.filing_type = bad_filing_type

    @pytest.mark.parametrize("bad_filing_type",
                             ("10-j", "10-k", "ssd", "invalid", 1))
    def test_invalid_filing_type_types(self, mock_user_agent, bad_filing_type):
        with pytest.raises(FilingTypeError):
            CompanyFilings(user_agent=mock_user_agent,
                           cik_lookup="0000320193",
                           filing_type=bad_filing_type)

    @pytest.mark.parametrize("bad_cik_lookup", (1234567891011, 12345, 123.0))
    def test_validate_cik_type_inside_filing(self, mock_user_agent, bad_cik_lookup):
        with pytest.raises(TypeError):
            CompanyFilings(user_agent=mock_user_agent,
                           cik_lookup=bad_cik_lookup,
                           filing_type=FilingType.FILING_10K)

    @pytest.mark.parametrize("no_urls", ({}, {
        "aapl": [],
        "fb": [],
        "msft": []
    }))
    def test_save_no_filings_raises_error(self, tmp_data_directory, monkeypatch,
                                          mock_user_agent, no_urls):
        monkeypatch.setattr(CompanyFilings, "get_urls", lambda x: no_urls)
        f = CompanyFilings(user_agent=mock_user_agent,
                           cik_lookup="aapl", filing_type=FilingType.FILING_10K)
        with pytest.raises(NoFilingsError):
            f.save(tmp_data_directory)

    def test_filing_save_multiple_ciks(self, tmp_data_directory,
                                       mock_user_agent,
                                       mock_cik_validator_get_multiple_ciks,
                                       mock_single_cik_filing,
                                       mock_filing_response):
        f = CompanyFilings(["aapl", "amzn", "msft"],
                           FilingType.FILING_10Q,
                           user_agent=mock_user_agent,
                           count=3)
        f.save(tmp_data_directory)
        assert len(os.listdir(tmp_data_directory)) > 0

    @pytest.mark.smoke
    def test_filing_save_multiple_ciks_smoke(self, tmp_data_directory,
                                             real_test_client):
        f = CompanyFilings(["aapl", "amzn", "msft"],
                           FilingType.FILING_10Q,
                           client=real_test_client,
                           count=3)
        f.save(tmp_data_directory)
        assert len(os.listdir(tmp_data_directory)) > 0

    def test_filing_save_single_cik(self, tmp_data_directory,
                                    mock_user_agent,
                                    mock_cik_validator_get_single_cik,
                                    mock_single_cik_filing,
                                    mock_filing_response):
        f = CompanyFilings("aapl", FilingType.FILING_10Q, user_agent=mock_user_agent, count=3)
        f.save(tmp_data_directory)
        assert len(os.listdir(tmp_data_directory)) > 0

    @pytest.mark.smoke
    def test_filing_save_single_cik_smoke(self, tmp_data_directory,
                                          real_test_client):
        f = CompanyFilings("aapl", FilingType.FILING_10Q, client=real_test_client, count=3)
        f.save(tmp_data_directory)
        assert len(os.listdir(tmp_data_directory)) > 0

    def test_filing_get_urls_returns_single_list_of_urls(
            self, mock_user_agent,
            mock_cik_validator_get_multiple_ciks, mock_single_cik_filing):
        # Uses same response for filing links (will all be filings for aapl)
        f = CompanyFilings(cik_lookup=["aapl", "msft", "amzn"],
                           user_agent=mock_user_agent,
                           filing_type=FilingType.FILING_10Q,
                           count=5)
        assert all(
            len(f.get_urls().get(key)) == 5 for key in f.get_urls().keys())

    @pytest.mark.parametrize("count", [10, 25, 30])
    def test_filing_returns_correct_number_of_urls(
            self, count, mock_user_agent, mock_cik_validator_get_multiple_ciks,
            mock_single_cik_filing):
        # Uses same response for filing links (will all be filings for aapl)
        f = CompanyFilings(cik_lookup=["aapl", "msft", "amzn"],
                           filing_type=FilingType.FILING_10Q,
                           user_agent=mock_user_agent,
                           count=count,
                           client=NetworkClient(user_agent=mock_user_agent, batch_size=10))
        assert all(
            len(f.get_urls().get(key)) == count for key in f.get_urls().keys())

    @pytest.mark.parametrize("count,raises_error", [(5, False),
                                                    (10, False),
                                                    (20, True),
                                                    (30, True),
                                                    (40, True)])
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    # For collections.abc warning 3.8+
    def test_filings_warning_lt_count(self, recwarn, count, raises_error,
                                      tmp_data_directory,
                                      mock_user_agent,
                                      mock_cik_validator_get_single_cik,
                                      mock_single_cik_filing_limited_responses,
                                      mock_filing_response):  # noqa:E501
        f = CompanyFilings(cik_lookup="aapl",
                           filing_type=FilingType.FILING_10Q,
                           count=count,
                           client=NetworkClient(batch_size=10, user_agent=mock_user_agent))
        f.save(tmp_data_directory)
        if raises_error:
            w = recwarn.pop(UserWarning)
            assert issubclass(w.category, UserWarning)
        else:
            try:
                w = recwarn.pop(UserWarning)
                # Allow XMLParsedAsHTMLWarning, but don't allow others
                if w and w._category_name == "XMLParsedAsHTMLWarning":
                    pass
                else:
                    pytest.fail("Expected no UserWarning, but received one.")
            # Should raise assertion error since no UserWarning should be found
            except AssertionError:
                pass

    @pytest.mark.smoke
    @pytest.mark.slow
    def test_filing_simple_example_smoke(self, tmp_data_directory,
                                         mock_user_agent):
        my_filings = CompanyFilings(cik_lookup="IBM",
                                    filing_type=FilingType.FILING_10Q,
                                    user_agent=mock_user_agent,
                                    count=3)
        my_filings.save(tmp_data_directory)
        assert len(os.listdir(tmp_data_directory)) > 0, "No file or directory created after save."

    def test__filter_filing_links(self, mock_user_agent, mock_single_cik_filing):
        f = CompanyFilings(cik_lookup="aapl",
                           filing_type=FilingType.FILING_10Q,
                           user_agent=mock_user_agent)
        data = f.client.get_soup("", {})  # Get mock data from mock_single_cik_filing
        links = f._filter_filing_links(data)
        assert len(links) == 10
        assert all(["BAD_LINK" not in link for link in links])

    def test_same_urls_fetched(self, mock_user_agent, mock_single_cik_filing):
        # mock_single_filing_cik has more than 10 URLs
        # using count = 5 should help test whether the same URLs
        # are fetched each time
        f = CompanyFilings(cik_lookup="aapl",
                           filing_type=FilingType.FILING_10Q,
                           user_agent=mock_user_agent,
                           count=5)
        first_urls = f.get_urls()
        second_urls = f.get_urls()
        assert all(f == s for f, s in zip(first_urls, second_urls))

    @pytest.mark.parametrize(
        "bad_ownership",
        [
            "notright",
            "_exclude",
            "_include",
            "notvalid",
            1,
            True,
            False
        ]
    )
    def test_ownership(self, bad_ownership, mock_user_agent):
        with pytest.raises(ValueError):
            CompanyFilings(
                cik_lookup="aapl",
                filing_type=FilingType.FILING_10Q,
                user_agent=mock_user_agent,
                ownership=bad_ownership
            )

    def test_good_ownership(self, mock_user_agent):
        shared_params = dict(
            cik_lookup="aapl",
            filing_type=FilingType.FILING_10Q,
            user_agent=mock_user_agent,
        )
        f_include = CompanyFilings(
            **shared_params,
            ownership="include"
        )
        f_exclude = CompanyFilings(
            **shared_params,
            ownership="exclude"
        )
        assert f_include.ownership == "include"
        assert f_exclude.ownership == "exclude"

        # Change ownership type
        f_include.ownership = "exclude"
        assert f_include.ownership == "exclude"

    def test_start_date_change_to_none(self, mock_user_agent):
        start_date = datetime.date(2020, 1, 1)
        f = CompanyFilings(
            cik_lookup="aapl",
            filing_type=FilingType.FILING_10Q,
            user_agent=mock_user_agent,
            start_date=start_date
        )
        assert f.start_date == start_date
        assert f.params["datea"] == "20200101"
        f.start_date = None
        assert f.start_date is None
        assert "datea" not in f.params

    def test_end_date_change_to_none(self, mock_user_agent):
        end_date = datetime.date(2020, 1, 1)
        f = CompanyFilings(
            cik_lookup="aapl",
            filing_type=FilingType.FILING_10Q,
            user_agent=mock_user_agent,
            end_date=end_date
        )
        assert f.end_date == end_date
        assert f.params["dateb"] == "20200101"
        f.end_date = None
        assert f.end_date is None
        assert "dateb" not in f.params
