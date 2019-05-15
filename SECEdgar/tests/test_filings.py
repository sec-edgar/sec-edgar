# Tests if filings are correctly received from EDGAR
import pytest


def test_10Q_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_10Q()


def test_10K_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_10K()


def test_SD_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_SD()


def test_8K_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_8K()


def test_13F_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_13F()


def test_4_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_4()
