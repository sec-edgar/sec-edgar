import os
import shutil

import pytest
from click.testing import CliRunner
from secedgar.cli import cli
from secedgar.exceptions import FilingTypeError


def run_cli_command(cli_instance, user_input, directory, catch_exceptions=False):
    runner = CliRunner()
    user_input = "-u 'My User Agent (email@example.com)' " + \
        user_input + " --directory {}".format(directory)
    return runner.invoke(cli_instance, user_input, catch_exceptions=catch_exceptions)


def check_bad_inputs(cli_instance, user_input, expected_exception, directory):
    # SystemExit does not raise exception by runner
    if expected_exception is SystemExit:
        result = run_cli_command(cli_instance, user_input, directory)
        assert result.exit_code != 0
    else:
        with pytest.raises(expected_exception):
            run_cli_command(cli_instance, user_input, directory)


class TestCLI:
    @pytest.mark.parametrize(
        "user_input,expected_exception",
        [
            ("filing -l aapl msft Facebook", SystemExit),  # missing filing type
            ("filing -l aapl -t null", FilingTypeError),  # unrecognized filing type
            ("filing -l aapl -t FILING_10Q -n abc", SystemExit),  # count is not int
            ("filing -l aapl -t FILING_10Q -n 0", ValueError),  # no filings available if 0 picked
        ]
    )
    def test_cli_filing_bad_inputs(self, user_input, expected_exception, tmp_data_directory):
        check_bad_inputs(cli, user_input, expected_exception, tmp_data_directory)

    @pytest.mark.parametrize(
        "user_input,count",
        [
            ("filing -l aapl -l msft -l amzn -t FILING_10Q -n {}", 10),
            ("filing -l aapl -l msft -l amzn -t FILING_10Q -n {}", 1),
        ]
    )
    def test_cli_filing_multiple_companies_input(
            self,
            user_input,
            count,
            tmp_data_directory,
            mock_cik_validator_get_multiple_ciks,
            mock_single_cik_filing,
            mock_filing_response):
        try:
            if count is not None:
                user_input = user_input.format(count)
            result = run_cli_command(cli, user_input, tmp_data_directory)
            assert result.exit_code == 0
            txt_files = [f for *_, files in os.walk(tmp_data_directory) for f in files]
            if count is None:
                assert len(txt_files) == 3
            else:
                assert len(txt_files) == 3 * count
        finally:
            shutil.rmtree(tmp_data_directory)

    @pytest.mark.parametrize(
        "user_input,expected_exception",
        [
            ("daily", SystemExit),
            ("daily -d 2020", ValueError)
        ]
    )
    def test_cli_daily_bad_inputs(self, user_input, expected_exception, tmp_data_directory):
        check_bad_inputs(cli, user_input, expected_exception, tmp_data_directory)
