import pytest

from click.testing import CliRunner
from secedgar.cli import filing, daily
from secedgar.utils.exceptions import FilingTypeError


class CLITestingMixin:
    """CLI testing utilities mixin class."""

    def __init__(self, cli):
        self.cli = cli

    def run_cli_command(self, user_input, tmp_data_directory):
        runner = CliRunner()
        user_input = user_input + " --directory {}".format(tmp_data_directory)
        return runner.invoke(self.cli, user_input)

    def _test_bad_inputs(self, user_input, expected_exception, tmp_data_directory):
        # SystemExit does not raise exception by runner
        if expected_exception is SystemExit:
            result = self.run_cli_command(user_input, tmp_data_directory)
            assert result.exit_code != 0
        else:
            with pytest.raises(expected_exception):
                self.run_cli_command(user_input, tmp_data_directory)


class TestCLIFiling(CLITestingMixin):

    def __init__(self):
        super().__init__(cli=filing)

    @pytest.mark.parametrize(
        "user_input,expected_exception",
        [
            ("-l aapl msft Facebook", SystemExit),  # missing filing type
            ("-l aapl -t null", FilingTypeError),  # unrecognized filing type
            ("-l aapl -t FILING_10Q -n abc", SystemExit),  # count is not int
            ("-l aapl -t FILING_10Q -n 0", ValueError)  # no filings available if 0 picked
        ]
    )
    def test_filing_bad_inputs(self, user_input, expected_exception, tmp_data_directory):
        self._test_bad_inputs(user_input, expected_exception, tmp_data_directory)

    @pytest.mark.parametrize(
        "user_input",
        [
            "-l aapl msft fb FILING_10Q",
            "-l aapl msft fb FILING_10Q -n 10",
            "-l aapl msft fb FILING_10Q -n 1"
        ]
    )
    def test_multiple_companies_input(self, user_input, tmp_data_directory):
        pass


class TestCLIDaily(CLITestingMixin):

    def __init__(self, cli):
        super().__init__(cli=daily)

    @pytest.mark.parametrize(
        "user_input,expected_exception",
        [
            ("", SystemExit),
            ("-d 2020", SystemExit)
        ]
    )
    def test_daily_bad_inputs(self, user_input, expected_exception, tmp_data_directory):
        self._test_bad_inputs(user_input, expected_exception, tmp_data_directory)
