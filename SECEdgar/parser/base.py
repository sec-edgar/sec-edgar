from bs4 import BeautifulSoup


class Parser(object):

    def to_pandas(self, doc):
        raise NotImplementedError


class Parser8K(Parser):
    def to_pandas(self, doc):
        soup = BeautifulSoup(doc)
        xbrl = soup.find_all('xbrl')
