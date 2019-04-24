# Tests if filings are correctly received from EDGAR
import pytest


@pytest.mark.xfail(raises=TypeError)
def test_10Q_requires_args(crawler):
    return crawler.filing_10Q()


@pytest.mark.xfail(raises=TypeError)
def test_10K_requires_args(crawler):
    return crawler.filing_10K()


@pytest.mark.xfail(raises=TypeError)
def test_SD_requires_args(crawler):
    return crawler.filing_SD()


@pytest.mark.xfail(raises=TypeError)
def test_8K_requires_args(crawler):
    return crawler.filing_8K()


@pytest.mark.xfail(raises=TypeError)
def test_13F_requires_args(crawler):
    return crawler.filing_13F()


@pytest.mark.xfail(raises=TypeError)
def test_4_requires_args(crawler):
    return crawler.filing_4()
