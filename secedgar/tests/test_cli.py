import pytest
from click.testing import CliRunner
from secedgar.cli import daily, filing
from secedgar.exceptions import FilingTypeError


def run_cli_command(cli, user_input, directory, catch_exceptions=False):
    runner = CliRunner()
    user_input = user_input + " --directory {}".format(directory)
    return runner.invoke(cli, user_input, catch_exceptions=catch_exceptions)


def check_bad_inputs(cli, user_input, expected_exception, directory):
    # SystemExit does not raise exception by runner
    if expected_exception is SystemExit:
        result = run_cli_command(cli, user_input, directory)
        assert result.exit_code != 0
    else:
        with pytest.raises(expected_exception):
            run_cli_command(cli, user_input, directory)


class TestCLIFiling:

    @pytest.mark.parametrize(
        "user_input,expected_exception",
        [
            ("-l aapl msft Facebook -u 'My User Agent (email@example.com)'", SystemExit),  # missing filing type
            ("-l aapl -t null -u 'My User Agent (email@example.com)'", FilingTypeError),  # unrecognized filing type
            ("-l aapl -t FILING_10Q -n abc -u 'My User Agent (email@example.com)'", SystemExit),  # count is not int
            ("-l aapl -t FILING_10Q -n 0 -u 'My User Agent (email@example.com)'", ValueError)  # no filings available if 0 picked
        ]
    )
    def test_filing_bad_inputs(self, user_input, expected_exception, tmp_data_directory):
        check_bad_inputs(filing, user_input, expected_exception, tmp_data_directory)

    @pytest.mark.parametrize(
        "user_input",
        [
            "-l aapl -l msft -l amzn -t FILING_10Q -x 'My User Agent (email@example.com)'",
            "-l aapl -l msft -l amzn -t FILING_10Q -n 10 -u 'My User Agent (email@example.com)'",
            "-l aapl -l msft -l amzn -t FILING_10Q -n 1 -u 'My User Agent (email@example.com)'",
        ]
    )
    def test_multiple_companies_input(self, user_input, tmp_data_directory):
        pass


class TestCLIDaily:

    @pytest.mark.parametrize(
        "user_input,expected_exception",
        [
            ("", SystemExit),
            ("-d 2020 -u 'My User Agent (email@example.com)'", ValueError)
        ]
    )
    def test_daily_bad_inputs(self, user_input, expected_exception, tmp_data_directory):
        check_bad_inputs(daily, user_input, expected_exception, tmp_data_directory)
