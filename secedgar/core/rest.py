import requests
from secedgar.cik_lookup import CIKLookup

API_BASE = "https://data.sec.gov/api/"
XBRL_BASE = "{0}xbrl/".format(API_BASE)


def _get_lookup_dict(lookups, user_agent):
    cik_lookup = CIKLookup(lookups=lookups,
                           user_agent=user_agent,
                           client=None)
    return cik_lookup.lookup_dict


def _combine_dicts(*dicts):
    if len(dicts) == 1:
        return dicts[0]
    else:
        first = dicts[0]
        # add each dict to combined dict
        for d in dicts[1:]:
            for k in first.keys():
                first[k] = first[k] + d[k]
        return first


def get_submissions(lookups, user_agent, recent=True):
    """Get information about submissions for entities.

    Args:
        lookups (list of str or str): Tickers or CIKs to get submission data for.
        user_agent (str): User agent to provide the SEC.
        recent (bool, optional): Whether or not to only get the most recent.
            Setting ``recent`` to True will give at least one year of filings or 1000 filings
            (whichever is more). Setting ``recent`` to False will return all filings.
            Defaults to True.

    Returns:
        dict: Dictionary with keys being the lookups and values being the responses from the API.
    """
    lookup_dict = _get_lookup_dict(lookups=lookups, user_agent=user_agent)
    submissions_dict = dict()
    url_base = "https://data.sec.gov/submissions/"
    for lookup, cik in lookup_dict.items():
        resp = requests.get("{0}CIK{1}.json".format(url_base, cik.zfill(10)),
                            headers={"user-agent": user_agent})
        resp_json = resp.json()
        if not recent:
            try:
                older_submission_files = resp_json["filings"]["files"]
            except KeyError:
                pass

            # Get data for older submission files and add to recent
            older_submissions = [requests.get("{0}{1}".format(url_base, f["name"]),
                                              headers={"user-agent": user_agent}).json()
                                 for f in older_submission_files]

            resp_json["filings"]["recent"] = _combine_dicts(resp_json["filings"]["recent"],
                                                            *older_submissions)
        submissions_dict[lookup] = resp_json
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


def get_xbrl_frames(lookups,
                    user_agent,
                    concept_name,
                    year,
                    quarter=None,
                    currency="USD",
                    instantaneous=False):
    lookup_dict = _get_lookup_dict(lookups=lookups, user_agent=user_agent)
    xbrl_frames = dict()
    for lookup, cik in lookup_dict.items():
        # Create URL
        period = "CY{0}".format(year) if quarter is None else "CY{0}Q{1}".format(year, quarter)
        if instantaneous:
            period += "I"
        url = "{0}frames/us-gaap/{1}/{2}/{3}.json".format(XBRL_BASE, concept_name, currency, period)

        # Request and add to dictionary
        resp = requests.get(url, headers={"user-agent": user_agent})
        xbrl_frames[lookup] = resp.json()
    return xbrl_frames


if __name__ == "__main__":
    user_agent = "Nunya Business (nunyabusiness@gmail.com)"
    lookups = ["aapl"]

    # submissions = get_submissions(lookups=lookups, user_agent=user_agent, recent=False)
    # print(submissions["aapl"])

    # concepts = get_company_concepts(lookups=lookups,
    #                                 user_agent=user_agent,
    #                                 concept_name="AccountsPayableCurrent")
    # print(concepts)

    # facts = get_company_facts(lookups=lookups, user_agent=user_agent)
    # print(facts)

    frames = get_xbrl_frames(lookups=lookups, user_agent=user_agent,
                             concept_name="AccountsPayableCurrent", year=2020)
    print(frames)
