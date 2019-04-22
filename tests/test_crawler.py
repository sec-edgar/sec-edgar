import pytest


class TestCrawler(object):
    @pytest.mark.xfail(raises=TypeError)
    def test_10Q_positional_requirements():
        return crawler.filing_10Q()

    @pytest.mark.xfail(raises=TypeError)
    def test_10K_positional_requirements():
        return crawler.filing_10K()

    @pytest.mark.xfail(raises=TypeError)
    def test_SD_positional_requirements():
        return crawler.filing_SD()

    @pytest.mark.xfail(raises=TypeError)
    def test_8K_positional_requirements():
        return crawler.filing_8K()

    @pytest.mark.xfail(raises=TypeError)
    def test_13F_positional_requirements():
        return crawler.filing_13F()
