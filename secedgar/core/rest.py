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
        url = "{0}/companyconcept/CIK{1}/us-gaap/{2}.json".format(
            XBRL_BASE,
            cik.zfill(10),
            concept_name
        )
        resp = requests.get(url,
                            headers={"user-agent": user_agent})
        company_concepts[lookup] = resp.json()
    return company_concepts


if __name__ == "__main__":
    user_agent = "Nunya Business (nunyabusiness@gmail.com)"
    lookups = ["aapl"]

    # submissions = get_submissions(lookups=lookups, user_agent=user_agent)
    # print(submissions)

    # concepts = get_company_concepts(lookups=lookups,
    #                                 user_agent=user_agent,
    #                                 concept_name="AccountsPayableCurrent")
    print(concepts)
