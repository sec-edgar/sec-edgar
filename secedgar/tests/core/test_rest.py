import pytest

from secedgar.core.rest import (_combine_dicts, get_company_concepts,
                                get_company_facts, get_submissions,
                                get_xbrl_frames)


class TestRest:
    @pytest.mark.parametrize("dicts,expected",
                             [
                                 ([{"A": [1, 2, 3], "B": [4, 5, 6]},
                                  {"A": [7, 8], "B": [0, 1, 2]}],
                                  {'A': [1, 2, 3, 7, 8], 'B': [4, 5, 6, 0, 1, 2]}),
                                 ([{"A": [1, 2, 3]},
                                  {"B": [4, 5, 6]}],
                                  {"A": [1, 2, 3], "B": [4, 5, 6]}),
                                 ([{"A": [1]}],
                                  {"A": [1]})
                             ]
                             )
    def test__combine_dicts(self, dicts, expected):
        assert _combine_dicts(*dicts) == expected

    @pytest.mark.parametrize(
        "recent",
        [True, False]
    )
    @pytest.mark.smoke
    def test_get_submissions(self, mock_user_agent, recent):
        submissions = get_submissions(lookups=["aapl"],
                                      user_agent=mock_user_agent,
                                      recent=recent)
        assert submissions
        # Make sure Apple's CIK shows up properly
        assert str(submissions["aapl"]["cik"]) == "320193"

        # Make sure there are accession numbers
        assert submissions["aapl"]["filings"]["recent"]["accessionNumber"]

        # Result should be dictionary
        assert isinstance(submissions, dict)

    @pytest.mark.smoke
    def test_get_company_concepts(self, mock_user_agent):
        concept = "AccountsPayableCurrent"
        concepts = get_company_concepts(lookups=["AAPL"],
                                        user_agent=mock_user_agent,
                                        concept_name=concept)
        assert concepts
        # Ensure CIK is correct
        assert str(concepts["AAPL"]["cik"]) == "320193"

        # Make sure that there are results for accounts payable
        assert concepts["AAPL"]["units"]["USD"]

        # Result should be dictionary
        assert isinstance(concepts, dict)

    @pytest.mark.smoke
    def test_get_company_facts(self, mock_user_agent):
        facts = get_company_facts(lookups=["aapl"], user_agent=mock_user_agent)

        assert facts
        # Ensure CIK is correct - sometimes will give number, so cast to string
        assert str(facts["aapl"]["cik"]) == "320193"

        # Make sure there are facts
        assert facts["aapl"]["facts"]

        # Make sure that us-gaap and dei both are keys
        assert "us-gaap" in facts["aapl"]["facts"]
        assert "dei" in facts["aapl"]["facts"]

        # Make sure we can get Revenues for Apple
        assert facts["aapl"]["facts"]["us-gaap"]["Revenues"]["units"]["USD"]

        # Result should be dictionary
        assert isinstance(facts, dict)

    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "concept,instantaneous",
        [
            ("Revenues", False),
            ("Revenues", True)
        ]
    )
    def test_get_xbrl_frames(self, mock_user_agent, concept, instantaneous):
        frames = get_xbrl_frames(user_agent=mock_user_agent,
                                 concept_name=concept,
                                 year=2020,
                                 quarter=1,
                                 instantaneous=instantaneous)
        # Check to make sure we got the right frame
        assert frames["tag"] == concept

        # Make sure there is data
        assert frames["data"]

        # Data should have accn and cik as keys
        assert "accn" in frames["data"][0]
        assert "cik" in frames["data"][0]

        assert isinstance(frames, dict)
