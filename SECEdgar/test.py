# -*- coding:utf-8 -*-
import time
from crawler import SecCrawler


def test():
    t1 = time.time()
    # file containig company name and corresponding cik codes
    seccrawler = SecCrawler()

    company_code_list = list()   # company code list
    cik_list = list()            # cik code list
    date_list = list()           # pror date list
    count_list = list()

    try:
        with open("data.txt", "r") as f:
            # get the comapny  quotes and cik number from the file.
            for columns in (raw.strip().split() for raw in f):
                company_code_list.append(columns[0])
                cik_list.append(columns[1])
                date_list.append(columns[2])
                count_list.append(columns[3])
    except:
        print("No input file Found")

    # call different  API from the crawler
    for i in range(1, len(cik_list)):
        seccrawler.filing_SD(company_code_list[i], cik_list[i],
                             date_list[i], count_list[i])
        seccrawler.filing_10K(company_code_list[i], cik_list[i],
                              date_list[i], count_list[i])
        seccrawler.filing_8K(company_code_list[i], cik_list[i],
                             date_list[i], count_list[i])
        seccrawler.filing_10Q(company_code_list[i], cik_list[i],
                              date_list[i], count_list[i])

    t2 = time.time()
    print("Total Time taken: {0}".format(t2 - t1))


if __name__ == '__main__':
    test()
