import pytest

from click.testing import CliRunner
from secedgar.cli import filing, daily
from secedgar.utils.exceptions import FilingTypeError


class TestCLI:
    pass


class TestCLIFiling(TestCLI):
    @pytest.mark.parametrize(
        "user_input,expected_exception",
        [
            ("-l aapl msft Facebook", SystemExit),  # missing filing type
            ("-l aapl -t null", KeyError),  # unrecognized filing type
            ("-l aapl -t FILING_10Q -n abc", SystemExit),  # count is not int
        ]
    )
    def test_filings_bad_inputs(self, user_input, expected_exception, tmp_data_directory):
        runner = CliRunner()
        user_input = user_input + " --directory {}".format(tmp_data_directory)
        if expected_exception is SystemExit:
            result = runner.invoke(filing, user_input, catch_exceptions=False)
            assert result.exit_code != 0
        else:
            with pytest.raises(expected_exception):
                runner.invoke(filing, user_input, catch_exceptions=False)


class TestCLIDaily(TestCLI):
    pass
