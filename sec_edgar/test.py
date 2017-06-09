"""Quick example of how to use the library."""
from crawler import SecCrawler
from companies import COMPANIES


def main():
    """Pull info for apple and google."""
    sec_crawler = SecCrawler()

    apple = COMPANIES["Apple"]
    google = COMPANIES["Google"]

    # Pull 10Q's for apple
    sec_crawler.filing_10q(apple.code, apple.cik, '20170101', 2)

    # Pull 10K's for apple
    sec_crawler.filing_10k(google.code, google.cik, '20170101', 2)


if __name__ == '__main__':
    main()
