from cgitb import lookup

import requests
from secedgar.cik_lookup import CIKLookup

API_BASE = "https://data.sec.gov/api/"
XBRL_BASE = "{0}xbrl/".format(API_BASE)


def _get_lookup_dict(lookups, user_agent):
    cik_lookup = CIKLookup(lookups=lookups,
                           user_agent=user_agent,
                           client=None)
    return cik_lookup.lookup_dict


def get_submissions(lookups, user_agent):
    lookup_dict = _get_lookup_dict(lookups=lookups, user_agent=user_agent)
    submissions_dict = dict()
    for lookup, cik in lookup_dict.items():
        resp = requests.get("https://data.sec.gov/submissions/CIK{0}.json".format(cik.zfill(10)),
                            headers={"user-agent": user_agent})
        submissions_dict[lookup] = resp.json()
    return submissions_dict


def get_company_concepts(lookups, user_agent, concept_name):
    lookup_dict = _get_lookup_dict(lookups=lookups, user_agent=user_agent)
    company_concepts = dict()
    for lookup, cik in lookup_dict.items():
        url = "{0}companyconcept/CIK{1}/us-gaap/{2}.json".format(
            XBRL_BASE,
            cik.zfill(10),
            concept_name
        )
        resp = requests.get(url,
                            headers={"user-agent": user_agent})
        company_concepts[lookup] = resp.json()
    return company_concepts


def get_company_facts(lookups, user_agent):
    lookup_dict = _get_lookup_dict(lookups=lookups, user_agent=user_agent)
    company_facts = dict()
    for lookup, cik in lookup_dict.items():
        url = "{0}companyfacts/CIK{1}.json".format(XBRL_BASE, cik.zfill(10))
        resp = requests.get(url, headers={"user-agent": user_agent})
        company_facts[lookup] = resp.json()
    return company_facts


def get_xbrl_frames(lookups, user_agent, concept_name, year, quarter=None, instantaneous=False):
    lookup_dict = _get_lookup_dict(lookups=lookups, user_agent=user_agent)
    xbrl_frames = dict()
    for lookup, cik in lookup_dict.items():
        # Create URL
        period = "CY{0}".format(year) if quarter is None else "CY{0}Q{1}".format(year, quarter)
        if instantaneous:
            period += "I"
        url = "{0}frames/us-gaap/{1}/{2}.json".format(XBRL_BASE, concept_name, period)

        # Request and add to dictionary
        resp = requests.get(url, headers={"user-agent": user_agent})
        xbrl_frames[lookup] = resp.json()
    return xbrl_frames


if __name__ == "__main__":
    user_agent = "Nunya Business (nunyabusiness@gmail.com)"
    lookups = ["aapl"]

    # submissions = get_submissions(lookups=lookups, user_agent=user_agent)
    # print(submissions)

    # concepts = get_company_concepts(lookups=lookups,
    #                                 user_agent=user_agent,
    #                                 concept_name="AccountsPayableCurrent")
    # print(concepts)

    # facts = get_company_facts(lookups=lookups, user_agent=user_agent)
    # print(facts)
