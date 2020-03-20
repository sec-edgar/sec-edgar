# Tests internal functions from SecCrawler
import os
import pytest


def test_fetch_report(crawler, valid_fetch_report_args):
    crawler._fetch_report(**valid_fetch_report_args)
    assert os.path.isdir(crawler.data_path)


class TestLegacySecCrawler(object):
    def test_10q_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_10Q()

    def test_10k_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_10K()

    def test_sd_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_SD()

    def test_8k_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_8K()

    def test_13f_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_13F()

    def test_4_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_4()
