"""Filing history, section extraction, full-text search, and the comparison tool.

The comparison tests are here rather than in their own file because
``compare_companies`` is mostly an integration of the other modules, and the
thing worth testing about it — that a fiscal-year mismatch is caught and
announced — needs two companies with real, different year ends.
"""

from __future__ import annotations

import asyncio

import pytest

from edgar_mcp import server
from edgar_mcp.client import SECClient
from edgar_mcp.errors import InvalidInputError, NotFoundError
from edgar_mcp.filings import (
    base_form,
    form_family,
    get_filing_section,
    html_to_text,
    is_amendment,
    list_filings,
    search_full_text,
)

TESTCO = "9999901"


# --------------------------------------------------------------------------- #
# Form variants
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("form", "expected"),
    [("10-K", "10-K"), ("10-K/A", "10-K"), ("10-KT", "10-KT"), ("8-K/A", "8-K"),
     ("20-F", "20-F"), ("10-q/a", "10-Q")],
)
def test_base_form_strips_only_the_amendment_suffix(form: str, expected: str) -> None:
    assert base_form(form) == expected


@pytest.mark.parametrize(
    ("form", "expected"),
    [("10-K", False), ("10-K/A", True), ("10-KT", False), ("10-KT/A", True)],
)
def test_is_amendment(form: str, expected: bool) -> None:
    assert is_amendment(form) is expected


def test_annual_form_family_covers_the_variants() -> None:
    family = form_family("10-K")
    assert {"10-K", "10-K/A", "10-KT", "10-KT/A"} <= family
    assert "10-Q" not in family


# --------------------------------------------------------------------------- #
# list_filings
# --------------------------------------------------------------------------- #


def test_list_filings_returns_the_history_newest_first(sec_client: SECClient) -> None:
    result = asyncio.run(list_filings(TESTCO, client=sec_client))
    assert result["company"] == "Testco Industries Inc"
    assert result["filings_matched"] == 5
    assert result["filings"][0]["filing_date"] == "2025-02-14"


def test_a_10k_filter_includes_amendments_and_transition_reports(
    sec_client: SECClient,
) -> None:
    result = asyncio.run(list_filings(TESTCO, form="10-K", client=sec_client))
    forms = [f["form"] for f in result["filings"]]
    assert sorted(forms) == ["10-K", "10-K", "10-K/A", "10-KT"]
    assert "10-Q" not in forms


def test_exact_form_excludes_the_variants(sec_client: SECClient) -> None:
    result = asyncio.run(list_filings(TESTCO, form="10-K", exact_form=True, client=sec_client))
    assert {f["form"] for f in result["filings"]} == {"10-K"}


def test_an_amended_filing_is_marked_superseded(sec_client: SECClient) -> None:
    result = asyncio.run(list_filings(TESTCO, form="10-K", client=sec_client))
    original = next(
        f for f in result["filings"] if f["accession_number"] == "0000999901-24-000010"
    )
    amendment = next(
        f for f in result["filings"] if f["accession_number"] == "0000999901-24-000030"
    )
    assert original["superseded"] is True
    assert original["superseded_by"] == amendment["accession_number"]
    assert amendment["is_amendment"] is True
    assert original["accession_number"] in amendment["supersedes"]


def test_the_unamended_annual_report_is_not_marked_superseded(sec_client: SECClient) -> None:
    result = asyncio.run(list_filings(TESTCO, form="10-K", client=sec_client))
    latest = next(
        f for f in result["filings"] if f["accession_number"] == "0000999901-25-000010"
    )
    assert latest["superseded"] is False


def test_fiscal_year_end_is_reported_in_the_notes(sec_client: SECClient) -> None:
    result = asyncio.run(list_filings(TESTCO, client=sec_client))
    assert result["fiscal_year_end"] == "1231"
    assert any("fiscal year ends" in n for n in result["notes"])


def test_date_filters_narrow_the_result(sec_client: SECClient) -> None:
    result = asyncio.run(list_filings(TESTCO, since="2024-06-01", client=sec_client))
    assert [f["filing_date"] for f in result["filings"]] == ["2025-02-14", "2024-08-09"]


def test_a_bad_date_is_an_input_error(sec_client: SECClient) -> None:
    with pytest.raises(InvalidInputError):
        asyncio.run(list_filings(TESTCO, since="last Tuesday", client=sec_client))


def test_no_matching_filings_is_an_error_with_a_suggestion(sec_client: SECClient) -> None:
    result = asyncio.run(list_filings(TESTCO, form="20-F", client=sec_client))
    assert result["filings"] == []
    assert "20-F" in result["suggestion"]


def test_archive_urls_use_the_unpadded_cik(sec_client: SECClient) -> None:
    result = asyncio.run(list_filings(TESTCO, client=sec_client))
    url = result["filings"][0]["document_url"]
    assert "/edgar/data/9999901/" in url
    assert "/edgar/data/0009999901/" not in url


# --------------------------------------------------------------------------- #
# Section extraction
# --------------------------------------------------------------------------- #


def test_html_to_text_removes_markup_and_decodes_entities() -> None:
    text = html_to_text("<p>Revenue &amp; costs</p><style>.a{}</style><div>Next</div>")
    assert "Revenue & costs" in text
    assert "<" not in text
    assert ".a{}" not in text


def test_section_extraction_prefers_the_body_over_the_contents_entry(
    sec_client: SECClient,
) -> None:
    result = asyncio.run(
        get_filing_section(
            TESTCO, "0000999901-25-000010", "risk_factors", client=sec_client
        )
    )
    assert "fictional risk" in result["text"]
    # The table-of-contents line ends with a page number. If the extractor
    # picked it, the body would be a few dozen characters long.
    assert result["chars_returned"] > 200
    assert result["section_label"].startswith("Item 1A")


def test_section_aliases_work(sec_client: SECClient) -> None:
    result = asyncio.run(
        get_filing_section(TESTCO, "0000999901-25-000010", "Item 1A", client=sec_client)
    )
    assert result["section"] == "risk_factors"


def test_a_missing_section_is_an_error_with_the_document_url(sec_client: SECClient) -> None:
    result = asyncio.run(
        get_filing_section(TESTCO, "0000999901-25-000010", "controls", client=sec_client)
    )
    assert "error" in result
    assert result["document_url"] in result["suggestion"]
    assert "memory" in result["suggestion"]


def test_an_unknown_accession_number_is_a_not_found_error(sec_client: SECClient) -> None:
    with pytest.raises(NotFoundError):
        asyncio.run(
            get_filing_section(
                TESTCO, "0000000000-00-000000", "risk_factors", client=sec_client
            )
        )


def test_truncation_is_reported(sec_client: SECClient) -> None:
    result = asyncio.run(
        get_filing_section(
            TESTCO, "0000999901-25-000010", "risk_factors", max_chars=100, client=sec_client
        )
    )
    assert result["truncated"] is True
    assert result["chars_returned"] == 100


# --------------------------------------------------------------------------- #
# Full-text search
# --------------------------------------------------------------------------- #


def test_search_returns_hits_and_always_states_its_coverage(sec_client: SECClient) -> None:
    result = asyncio.run(search_full_text("fictional risk", client=sec_client))
    assert result["results_returned"] == 2
    assert result["results"][0]["cik"] == "9999901"
    assert result["results"][0]["accession_number"] == "0000999901-25-000010"
    assert "2001" in result["coverage"]


def test_search_refuses_a_pre_2001_start_date(sec_client: SECClient) -> None:
    with pytest.raises(InvalidInputError) as excinfo:
        asyncio.run(
            search_full_text("Y2K remediation", date_from="1998-01-01", client=sec_client)
        )
    assert "2001" in excinfo.value.message
    assert "2001" in excinfo.value.suggestion


def test_search_rejects_an_empty_query(sec_client: SECClient) -> None:
    with pytest.raises(InvalidInputError):
        asyncio.run(search_full_text("   ", client=sec_client))


# --------------------------------------------------------------------------- #
# compare_companies
# --------------------------------------------------------------------------- #


def test_aligned_fiscal_years_compare_cleanly(installed_client: SECClient) -> None:
    result = asyncio.run(
        server.compare_companies(
            companies=["TSTC", "RSTD"], concept="revenue", fiscal_year=2023
        )
    )
    assert result["comparable"] is True
    assert "warning" not in result
    assert result["fiscal_alignment"]["spread_days"] == 0
    assert [r["ticker"] for r in result["companies"]] == ["TSTC", "RSTD"]


def test_misaligned_fiscal_years_produce_a_prominent_warning(
    installed_client: SECClient,
) -> None:
    # Testco's fiscal year ends 31 December; Fallback Systems' ends 30 June.
    # Both call the result "FY2024" and the two periods share only six months.
    result = asyncio.run(
        server.compare_companies(
            companies=["TSTC", "FBSY"], concept="revenue", fiscal_year=2024
        )
    )
    assert result["comparable"] is False
    assert "FISCAL YEAR MISALIGNMENT" in result["warning"]
    assert result["fiscal_alignment"]["spread_days"] == 184
    assert "2024-06-30" in result["warning"]
    assert "2024-12-31" in result["warning"]


def test_different_matched_tags_are_called_out(installed_client: SECClient) -> None:
    result = asyncio.run(
        server.compare_companies(
            companies=["TSTC", "FBSY"], concept="revenue", fiscal_year=2024
        )
    )
    tags = {r["matched_tag"] for r in result["companies"]}
    assert len(tags) == 2
    assert any("different XBRL tags" in n for n in result["notes"])


def test_an_ambiguous_name_stops_the_whole_comparison(installed_client: SECClient) -> None:
    result = asyncio.run(
        server.compare_companies(companies=["TSTC", "Aperture"], concept="revenue")
    )
    assert "error" in result
    assert "suggestion" in result
    assert "companies" not in result
    assert result["ambiguous"][0]["query"] == "Aperture"


def test_a_restated_company_in_a_comparison_is_flagged(installed_client: SECClient) -> None:
    result = asyncio.run(
        server.compare_companies(
            companies=["TSTC", "RSTD"], concept="revenue", fiscal_year=2023
        )
    )
    restated = next(r for r in result["companies"] if r["ticker"] == "RSTD")
    assert restated["restated"] is True
    assert restated["prior_value"] == 55000000000
    assert any("restated" in n for n in result["notes"])


def test_comparison_without_a_year_uses_the_newest_common_year(
    installed_client: SECClient,
) -> None:
    # Testco reports 2022-2024; Restated Metals reports 2022-2023. Picking each
    # company's own newest year would compare 2024 against 2023 silently.
    result = asyncio.run(
        server.compare_companies(companies=["TSTC", "RSTD"], concept="revenue")
    )
    assert result["fiscal_year"] == 2023
    assert all(r["fy"] == 2023 for r in result["companies"])


def test_a_company_without_the_concept_is_listed_not_dropped(
    installed_client: SECClient,
) -> None:
    result = asyncio.run(
        server.compare_companies(
            companies=["TSTC", "RSTD", "ZZZZ"], concept="revenue", fiscal_year=2023
        )
    )
    assert [u["ticker"] for u in result["unavailable"]] == ["ZZZZ"]
    assert any("not in the comparison" in n for n in result["notes"])
