from bs4 import BeautifulSoup
from SECEdgar.parser import VALID_GAAP_ELEMENTS


class Parser(object):

    @staticmethod
    def parse(file):
        with open(file) as f:
            tag_list = BeautifulSoup(f, 'lxml').find_all()
        info = {k: [tag.attrs.update(tag.text) for tag in [t for t in tag_list if t.name ==
                                                           'us-gaap:{}'.format(k.lower())]] for k in VALID_GAAP_ELEMENTS}
        return info
