import pytest

from click.testing import CliRunner
from secedgar.cli import filing, daily
from secedgar.utils.exceptions import FilingTypeError


class CLITestingMixin:
    """CLI testing utilities mixin class."""
    @staticmethod
    def _test_bad_inputs(cli, user_input, expected_exception, tmp_data_directory):
        runner = CliRunner()
        user_input = user_input + " --directory {}".format(tmp_data_directory)

        # SystemExit does not raise exception by runner
        if expected_exception is SystemExit:
            result = runner.invoke(cli, user_input)
            assert result.exit_code != 0
        else:
            with pytest.raises(expected_exception):
                runner.invoke(filing, user_input, catch_exceptions=False)


class TestCLIFiling(CLITestingMixin):
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
        self._test_bad_inputs(filing, user_input, expected_exception, tmp_data_directory)


class TestCLIDaily(CLITestingMixin):
    @pytest.mark.parametrize(
        "user_input,expected_exception",
        [
            ("", SystemExit),
            ("-d 2020", SystemExit)
        ]
    )
    def test_daily_bad_inputs(self, user_input, expected_exception, tmp_data_directory):
        self._test_bad_inputs(daily, user_input, expected_exception, tmp_data_directory)
