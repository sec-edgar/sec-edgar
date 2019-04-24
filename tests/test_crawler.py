# Tests internal functions from SecCrawler
import os


def test_fetch_report(crawler, valid_fetch_report_args):
    crawler._fetch_report(**valid_fetch_report_args)
    assert os.path.isdir(crawler.data_path)
