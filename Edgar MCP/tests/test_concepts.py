"""Concept resolution: fallback order, restatements, units, fiscal years.

This is the file that matters. Everything the README claims about
``get_financial_concept`` is asserted here against fixtures, so the claims stay
true when the code changes.
"""

from __future__ import annotations

import asyncio

import pytest

from edgar_mcp.client import SECClient
from edgar_mcp.concepts import (
    CONCEPT_CHAINS,
    get_financial_concept,
    list_concepts,
    resolve_concept,
)
from edgar_mcp.errors import InvalidInputError

TESTCO = "9999901"
FALLBACK_SYSTEMS = "9999902"
RESTATED_METALS = "9999903"
CONTINENTAL = "9999906"


# --------------------------------------------------------------------------- #
# The chains themselves
# --------------------------------------------------------------------------- #


def test_revenue_chain_is_in_the_documented_order() -> None:
    # This exact order is quoted in the README and in the tool docstring. If it
    # changes, both are wrong, so the order is pinned here.
    assert [t.tag for t in CONCEPT_CHAINS["revenue"].tags] == [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
    ]


def test_every_required_concept_exists() -> None:
    required = {
        "revenue",
        "net_income",
        "total_assets",
        "total_liabilities",
        "cash",
        "operating_income",
        "rnd_expense",
        "shares_outstanding",
    }
    assert required <= set(CONCEPT_CHAINS)


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("revenue", "revenue"),
        ("Net Sales", "revenue"),
        ("sales", "revenue"),
        ("net income", "net_income"),
        ("profit", "net_income"),
        ("R&D", "rnd_expense"),
        ("r and d", "rnd_expense"),
        ("COGS", "cost_of_revenue"),
        ("total assets", "total_assets"),
        ("share count", "shares_outstanding"),
    ],
)
def test_plain_english_aliases_resolve(alias: str, canonical: str) -> None:
    assert resolve_concept(alias).name == canonical


def test_unknown_concept_error_lists_the_supported_ones() -> None:
    with pytest.raises(InvalidInputError) as excinfo:
        resolve_concept("free cash flow")
    assert "revenue" in excinfo.value.suggestion
    assert excinfo.value.details["supported_concepts"]


def test_list_concepts_reports_each_chain() -> None:
    concepts = list_concepts()
    revenue = next(c for c in concepts if c["concept"] == "revenue")
    assert len(revenue["fallback_chain"]) == 5
    assert revenue["fallback_chain"][0].startswith("us-gaap:")


# --------------------------------------------------------------------------- #
# Fallback selection
# --------------------------------------------------------------------------- #


def test_first_tag_wins_when_the_filer_reports_it(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(TESTCO, "revenue", client=sec_client))
    assert result["matched_tag"] == (
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
    )
    # Only one tag should have been tried: the chain stops at the first hit.
    assert [t["tag"] for t in result["tags_tried"]] == [result["matched_tag"]]
    assert result["tags_tried"][0]["result"] == "matched"


def test_chain_falls_through_missing_tags_in_order(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(FALLBACK_SYSTEMS, "revenue", client=sec_client))
    assert result["matched_tag"] == "us-gaap:Revenues"
    tried = [t["tag"] for t in result["tags_tried"]]
    assert tried == [
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax",
        "us-gaap:Revenues",
    ]
    assert tried[0] != result["matched_tag"]
    assert result["tags_tried"][0]["result"] == "not_reported_by_this_filer"


def test_tags_tried_is_present_on_success_and_on_failure(sec_client: SECClient) -> None:
    ok = asyncio.run(get_financial_concept(TESTCO, "revenue", client=sec_client))
    missing = asyncio.run(get_financial_concept(TESTCO, "total_liabilities", client=sec_client))
    assert "tags_tried" in ok
    assert "tags_tried" in missing
    assert "matched_tag" in ok
    assert "matched_tag" in missing


def test_no_tag_matched_is_an_error_not_a_zero(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(TESTCO, "operating_income", client=sec_client))
    assert result["matched_tag"] is None
    assert result["values"] == []
    assert result["error"]
    assert result["suggestion"]
    assert "estimate" in result["suggestion"].lower()


def test_falling_back_adds_a_note_naming_the_preferred_tag(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(FALLBACK_SYSTEMS, "revenue", client=sec_client))
    joined = " ".join(result["notes"])
    assert "RevenueFromContractWithCustomerExcludingAssessedTax" in joined
    assert "generic Revenues tag" in joined


# --------------------------------------------------------------------------- #
# Restatements
# --------------------------------------------------------------------------- #


def test_restatement_returns_the_latest_filed_value(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(RESTATED_METALS, "revenue", client=sec_client))
    fy2023 = next(v for v in result["values"] if v["fy"] == 2023)
    assert fy2023["value"] == 51000000000
    assert fy2023["filed"] == "2024-08-09"
    assert fy2023["form"] == "10-K/A"


def test_restatement_carries_the_prior_value_and_date(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(RESTATED_METALS, "revenue", client=sec_client))
    fy2023 = next(v for v in result["values"] if v["fy"] == 2023)
    assert fy2023["restated"] is True
    assert fy2023["prior_value"] == 55000000000
    assert fy2023["prior_filed"] == "2024-02-20"
    assert fy2023["restatement_delta"] == pytest.approx(-4000000000)
    assert "restatement_note" in fy2023


def test_a_period_repeated_with_the_same_value_is_not_a_restatement(
    sec_client: SECClient,
) -> None:
    # Testco's FY2022 appears in two filings with an identical value. That is a
    # comparative column, not a revision, and flagging it would cry wolf.
    result = asyncio.run(get_financial_concept(TESTCO, "revenue", client=sec_client))
    fy2022 = next(v for v in result["values"] if v["fy"] == 2022)
    assert fy2022["restated"] is False
    assert "prior_value" not in fy2022
    assert fy2022["filings_reporting_this_period"] == 2


def test_restatement_is_surfaced_in_the_notes(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(RESTATED_METALS, "revenue", client=sec_client))
    assert any("restated" in n.lower() for n in result["notes"])


# --------------------------------------------------------------------------- #
# Units
# --------------------------------------------------------------------------- #


def test_dollars_and_dollars_per_share_are_never_mixed(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(TESTCO, "net_income", client=sec_client))
    assert result["unit"] == "USD"
    assert set(result["units_available"]) == {"USD", "USD/shares"}
    # 4.4 is the per-share figure in the fixture. If it appears, units mixed.
    assert all(v["value"] > 1_000_000 for v in result["values"])


def test_a_shares_concept_never_returns_a_dollar_unit(sec_client: SECClient) -> None:
    result = asyncio.run(
        get_financial_concept(TESTCO, "shares_outstanding", client=sec_client)
    )
    assert result["unit"] == "shares"
    assert "USD" in result["units_available"]
    assert result["values"][0]["value"] == 5000000000


def test_multiple_units_available_is_reported_in_the_notes(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(TESTCO, "net_income", client=sec_client))
    assert any("units" in n.lower() for n in result["notes"])


def test_foreign_currency_is_flagged(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(CONTINENTAL, "revenue", client=sec_client))
    assert result["unit"] == "EUR"
    assert any("EUR" in n for n in result["notes"])


# --------------------------------------------------------------------------- #
# Periods and fiscal years
# --------------------------------------------------------------------------- #


def test_annual_period_excludes_quarters(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(TESTCO, "revenue", client=sec_client))
    # The fixture holds a Q1 fact. It must not appear in an annual series.
    assert all(v["fp"] == "FY" for v in result["values"])
    assert 30000000000 not in [v["value"] for v in result["values"]]


def test_quarterly_period_returns_the_quarter(sec_client: SECClient) -> None:
    result = asyncio.run(
        get_financial_concept(TESTCO, "revenue", period="quarterly", client=sec_client)
    )
    assert [v["value"] for v in result["values"]] == [30000000000]
    assert result["values"][0]["form"] == "10-Q"


def test_fiscal_year_is_the_period_not_the_filing(sec_client: SECClient) -> None:
    # Testco's FY2022 revenue is reported again in the FY2023 10-K, where the
    # raw fy field says 2023. The period still belongs to fiscal 2022.
    result = asyncio.run(get_financial_concept(TESTCO, "revenue", client=sec_client))
    fy2022 = next(v for v in result["values"] if v["fy"] == 2022)
    assert fy2022["value"] == 111000000000
    assert fy2022["end"] == "2022-12-31"
    assert {v["fy"] for v in result["values"]} == {2022, 2023, 2024}


def test_a_june_year_end_filer_keeps_its_own_fiscal_year_label(
    sec_client: SECClient,
) -> None:
    result = asyncio.run(get_financial_concept(FALLBACK_SYSTEMS, "revenue", client=sec_client))
    fy2024 = next(v for v in result["values"] if v["fy"] == 2024)
    assert fy2024["end"] == "2024-06-30"
    assert fy2024["start"] == "2023-07-01"


def test_fiscal_year_filter_selects_one_period(sec_client: SECClient) -> None:
    result = asyncio.run(
        get_financial_concept(TESTCO, "revenue", fiscal_year=2023, client=sec_client)
    )
    assert len(result["values"]) == 1
    assert result["values"][0]["value"] == 122000000000


def test_missing_fiscal_year_is_an_error_with_a_way_forward(sec_client: SECClient) -> None:
    result = asyncio.run(
        get_financial_concept(TESTCO, "revenue", fiscal_year=1999, client=sec_client)
    )
    assert result["values"] == []
    assert "1999" in result["error"]
    assert result["suggestion"]


def test_every_value_carries_its_provenance(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(TESTCO, "revenue", client=sec_client))
    for value in result["values"]:
        for field in ("fy", "fp", "start", "end", "filed", "form", "accession_number"):
            assert field in value, f"{field} missing from a returned value"


def test_bad_period_argument_is_rejected(sec_client: SECClient) -> None:
    with pytest.raises(InvalidInputError):
        asyncio.run(
            get_financial_concept(TESTCO, "revenue", period="yearly", client=sec_client)
        )


def test_series_is_newest_first_and_respects_the_limit(sec_client: SECClient) -> None:
    result = asyncio.run(get_financial_concept(TESTCO, "revenue", limit=2, client=sec_client))
    assert len(result["values"]) == 2
    assert result["values"][0]["end"] > result["values"][1]["end"]
    assert result["periods_available"] == 3
