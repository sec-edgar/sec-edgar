"""The MCP server: six tools over SEC EDGAR, and nothing else.

Six is a ceiling, not a target. Every extra tool is another entry in the
model's context on every turn and another way for it to pick wrong. The tools
here are the smallest set that answers an equity analyst's questions:

===================================  ===================================
``resolve_company``                  name or ticker to CIK, or refuse
``list_filings``                     filing history, amendments flagged
``get_financial_concept``            one XBRL concept as a time series
``compare_companies``                one concept across N filers
``get_filing_section``               named section from a filing's text
``search_full_text``                 keyword search, 2001 onward
===================================  ===================================

**Every docstring in this file is a prompt.** The model never reads
``concepts.py``. It reads the docstring, decides whether to call the tool, and
decides what to do with what comes back. Anything the model must know to use a
result honestly — that full-text search misses pre-2001 filings, that a matched
tag may not be the tag the analyst assumed, that a fiscal year label is the
filer's and not the calendar's — belongs in the docstring, in plain language,
not in a comment.

**Logging goes to stderr and only to stderr.** In stdio transport, stdout *is*
the JSON-RPC channel between this process and the client. A stray ``print``, a
logging handler with no stream argument, a warning from a dependency — any byte
written to stdout is parsed as a protocol frame, fails to parse, and takes the
session down. The handler below is pinned to ``sys.stderr`` for that reason.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import client as client_module
from . import companies as companies_module
from . import concepts as concepts_module
from . import filings as filings_module
from .client import SECClient
from .errors import error_response, is_error, tool_error_boundary

# stdout belongs to JSON-RPC. Nothing in this process may write to it.
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("edgar_mcp")

mcp = FastMCP(
    "edgar",
    instructions=(
        "Tools for reading what US public companies actually reported to the "
        "SEC. Every figure comes from an EDGAR filing and carries the XBRL tag, "
        "fiscal period, form type and filing date it came from. Quote those in "
        "your answers. When a tool returns an 'error' key, read the "
        "'suggestion' field and follow it; do not answer the user from your own "
        "knowledge of a company's financials, because the whole point of these "
        "tools is that the user is going to trust the number."
    ),
)

#: Two companies' fiscal years are not comparable if their period end dates are
#: further apart than this. Six weeks is the point past which a quarter of
#: trading activity separates the two figures.
FISCAL_MISALIGNMENT_DAYS = 45


# --------------------------------------------------------------------------- #
# Tool 1 — resolve_company
# --------------------------------------------------------------------------- #


@mcp.tool()
@tool_error_boundary
async def resolve_company(query: str) -> dict[str, Any]:
    """Find a company's SEC CIK number from a ticker symbol or a company name.

    Call this first, before any other tool. Every other tool needs a CIK.

    A ticker symbol resolves exactly and is never a guess. A company name is
    always a guess, because SEC filer names are not unique: "Apple" matches
    Apple Inc. and Apple Hospitality REIT, and "Delta" matches several
    unrelated filers. Prefer a ticker whenever the user gave you one.

    When two names score too closely to separate, this tool refuses to choose
    and returns `resolved: false` with a `candidates` list. Do not pick one of
    the candidates yourself. Ask the user which company they mean, quoting the
    names and tickers, and then call this tool again with the ticker.

    A company that is not in the result is very likely not an SEC filer at all.
    Private companies (Stripe, SpaceX, OpenAI), foreign companies with no US
    listing, and subsidiaries that do not file separately are simply absent
    from EDGAR. If a name does not resolve, say the company does not appear to
    file with the SEC. Do not answer from memory.

    Args:
        query: A ticker symbol such as "NVDA", or a company name such as
            "NVIDIA Corporation".

    Returns:
        On a confident match: cik, ticker, name, confidence and match_type
        ("ticker_exact", "name_exact" or "name_fuzzy"), plus ranked candidates.
        On an ambiguous match: resolved false, an error, a suggestion, and the
        ranked candidates to put to the user.
    """
    return await companies_module.resolve_company(query)


# --------------------------------------------------------------------------- #
# Tool 2 — list_filings
# --------------------------------------------------------------------------- #


@mcp.tool()
@tool_error_boundary
async def list_filings(
    cik: str,
    form: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """List a company's SEC filings, newest first, with amendments flagged.

    Use this to find out what a company filed and when, to get an accession
    number for `get_filing_section`, or to check whether a company files at all.

    Form types have variants that all mean "annual report": 10-K is the normal
    one, 10-K/A is an amendment to a previously filed one, and 10-KT is a
    transition report covering a short year after the company changed its
    fiscal calendar. Asking for form "10-K" returns all of these. A foreign
    private issuer files 20-F or 40-F instead and will have no 10-K at all —
    if a company you expect to see has no annual report, ask for form "20-F".

    Amendments matter for accuracy. When a 10-K/A exists, the original 10-K is
    marked `superseded: true` with `superseded_by` pointing at the amendment.
    A figure taken from a superseded filing may have been revised. Prefer the
    amendment, and say which filing you used.

    The response also reports `fiscal_year_end` as MM-DD. Read it before
    comparing this company's fiscal year with another company's.

    Args:
        cik: The company's CIK, from resolve_company. Zero padding optional.
        form: Filter to a form type, e.g. "10-K", "10-Q", "8-K", "20-F".
            Amendment and transition variants are included automatically.
        since: Only filings filed on or after this date, as YYYY-MM-DD.
        until: Only filings filed on or before this date, as YYYY-MM-DD.
        limit: Maximum filings to return. Default 20.

    Returns:
        company, cik, fiscal_year_end, and a filings list. Each filing carries
        form, base_form, is_amendment, filing_date, period_of_report,
        accession_number, superseded flags, and URLs to the document and index.
    """
    return await filings_module.list_filings(
        cik, form=form, since=since, until=until, limit=limit
    )


# --------------------------------------------------------------------------- #
# Tool 3 — get_financial_concept
# --------------------------------------------------------------------------- #


@mcp.tool()
@tool_error_boundary
async def get_financial_concept(
    cik: str,
    concept: str,
    period: str = "annual",
    fiscal_year: int | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    """Get one reported financial figure as a time series, with its XBRL tag.

    This is the tool that answers "what was revenue". Supported concepts:

      revenue, net_income, total_assets, total_liabilities, cash,
      operating_income, rnd_expense, shares_outstanding, gross_profit,
      cost_of_revenue

    Plain-English aliases work too: "sales", "net sales", "profit", "R&D",
    "COGS", "cash and equivalents", "share count".

    There is no XBRL tag called "revenue". Companies tag the same economic
    figure differently depending on the year and their accounting policy, so
    this tool walks an ordered fallback chain and tells you which tag actually
    matched. **Always read `matched_tag` and quote it if it is not the first
    entry in `fallback_chain`.** A revenue figure that came from
    `SalesRevenueGoodsNet` covers goods only, and an answer that does not say
    so is misleading. `tags_tried` shows every tag attempted and why each one
    was skipped.

    Restatements are surfaced, not hidden. When a period was reported with a
    different value in an earlier filing, that period carries `restated: true`
    plus `prior_value` and `prior_filed`. The current value is the most
    recently filed one. When you see `restated: true`, say so in your answer
    and give both figures. An analyst who quotes a restated number without
    knowing it was restated will be wrong in a meeting.

    Fiscal years are the company's, not the calendar's. NVIDIA's fiscal 2024
    ended 28 January 2024. Apple's fiscal 2024 ended 28 September 2024. The
    `fy` field is the fiscal year the period belongs to; `start` and `end` are
    the actual dates. Always state the period end date alongside a fiscal-year
    figure.

    Units are never mixed. The response names the single `unit` used and lists
    `units_available`. If the unit is not USD, the company reports in a foreign
    currency and the figure must not be compared with a dollar figure.

    This tool does not compute ratios, margins, growth rates or per-share
    figures. To answer a margin question, fetch the two underlying concepts for
    the same period and divide, and say in your answer that you calculated it.

    Args:
        cik: The company's CIK, from resolve_company.
        concept: A concept name or alias, e.g. "revenue" or "R&D".
        period: "annual" for fiscal-year figures, "quarterly" for quarters, or
            "all". Default "annual".
        fiscal_year: Return only this fiscal year, e.g. 2024. Omit to get a
            series of recent years.
        limit: Maximum periods to return, newest first. Default 8.

    Returns:
        matched_tag, tags_tried, fallback_chain, unit, units_available, notes,
        and a values list. Each value carries value, fy, fp, start, end, filed,
        form, accession_number, restated, and prior_value/prior_filed when the
        figure changed between filings.
    """
    return await concepts_module.get_financial_concept(
        cik, concept, period=period, fiscal_year=fiscal_year, limit=limit
    )


# --------------------------------------------------------------------------- #
# Tool 4 — compare_companies
# --------------------------------------------------------------------------- #


def _period_end(value: dict[str, Any]) -> date | None:
    """Parse a value record's period end date.

    Args:
        value: One entry from a concept series.

    Returns:
        The end date, or None if it is missing or malformed.
    """
    raw = value.get("end")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _fiscal_alignment(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure how far apart the compared periods actually end.

    "FY2024" is a label each company assigns to its own twelve months. NVIDIA's
    fiscal 2024 ended in January 2024 and Apple's ended in September 2024:
    nearly eight months apart, covering different macroeconomic conditions and,
    in NVIDIA's case, a different phase of a demand cycle. The two numbers can
    be put in the same table and the table will be wrong.

    Args:
        rows: The per-company result rows, each with a period ``end``.

    Returns:
        A dict with ``spread_days``, ``aligned`` and, when misaligned, a
        ``warning`` written for the model to repeat to the user.
    """
    dated = [(r, _period_end(r)) for r in rows if _period_end(r) is not None]
    if len(dated) < 2:
        return {"spread_days": 0, "aligned": True}

    earliest = min(dated, key=lambda pair: pair[1])  # type: ignore[arg-type,return-value]
    latest = max(dated, key=lambda pair: pair[1])  # type: ignore[arg-type,return-value]
    spread = (latest[1] - earliest[1]).days  # type: ignore[operator]

    result: dict[str, Any] = {
        "spread_days": spread,
        "aligned": spread <= FISCAL_MISALIGNMENT_DAYS,
        "earliest_period_end": earliest[1].isoformat(),  # type: ignore[union-attr]
        "latest_period_end": latest[1].isoformat(),  # type: ignore[union-attr]
    }
    if spread > FISCAL_MISALIGNMENT_DAYS:
        result["warning"] = (
            f"FISCAL YEAR MISALIGNMENT: these companies label the same fiscal "
            f"year but their periods end {spread} days apart — "
            f"{earliest[0]['company']} ends {earliest[1].isoformat()} and "  # type: ignore[union-attr]
            f"{latest[0]['company']} ends {latest[1].isoformat()}. "  # type: ignore[union-attr]
            f"These figures cover different date ranges and are not directly "
            f"comparable. State this in your answer, give both period end "
            f"dates, and do not present a difference between them as a "
            f"like-for-like comparison."
        )
    return result


@mcp.tool()
@tool_error_boundary
async def compare_companies(
    companies: list[str],
    concept: str,
    fiscal_year: int | None = None,
    period: str = "annual",
) -> dict[str, Any]:
    """Compare one financial figure across several companies, and check the dates line up.

    Give it tickers or company names and one concept. It resolves each company,
    fetches the same concept for each, and lines the figures up side by side.

    **Read the `warning` field before you write your answer.** Companies choose
    their own fiscal calendars. NVIDIA's fiscal 2024 ended in January 2024;
    Apple's ended in September 2024; Microsoft's ended in June 2024. All three
    are called "FY2024" and all three cover different months. When the period
    end dates in a comparison are more than 45 days apart, this tool sets
    `comparable: false` and a `warning`. Repeat that warning to the user in
    plain language and give the period end dates. A table of three numbers that
    quietly compares January to September is worse than no table.

    The tool also warns when the companies matched different XBRL tags, which
    means the figures are defined differently even when the dates line up, and
    when a company reports in a currency other than US dollars.

    If any company name is ambiguous, the whole comparison stops rather than
    guessing which filer was meant. A comparison that silently includes the
    wrong company looks completely normal.

    Args:
        companies: Tickers or company names, e.g. ["NVDA", "AAPL", "MSFT"].
            Two to about eight works; more is slow.
        concept: A concept name understood by get_financial_concept, such as
            "revenue" or "net_income".
        fiscal_year: The fiscal year to compare, e.g. 2024. Omit to use the
            most recent fiscal year that all the companies report.
        period: "annual" or "quarterly". Default "annual".

    Returns:
        comparable, warning, fiscal_year, unit, a companies list with one row
        per filer (value, fy, start, end, filed, form, matched_tag, restated),
        an unavailable list for companies with no data, and notes.
    """
    if not companies or len(companies) < 2:
        return error_response(
            "A comparison needs at least two companies.",
            "Call this tool again with two or more tickers, or call "
            "get_financial_concept if the user only asked about one company.",
        )

    resolved: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []

    for name in companies:
        match = await companies_module.resolve_company(name)
        if match.get("resolved"):
            resolved.append(match)
        elif match.get("ambiguous"):
            ambiguous.append({"query": name, "candidates": match.get("candidates", [])})
        else:
            unknown.append({"query": name, "error": match.get("error")})

    if ambiguous or unknown:
        return error_response(
            "The comparison was not run because "
            + ", ".join(
                [f"{a['query']!r} matches several SEC filers" for a in ambiguous]
                + [f"{u['query']!r} does not appear to file with the SEC" for u in unknown]
            )
            + ".",
            "Do not guess which company was meant and do not compare the "
            "remaining companies as if the list were complete. Ask the user to "
            "confirm, using the candidates below, then call this tool again "
            "with ticker symbols.",
            ambiguous=ambiguous or None,
            not_found=unknown or None,
            resolved_so_far=[r["name"] for r in resolved] or None,
        )

    series: dict[str, dict[str, Any]] = {}
    unavailable: list[dict[str, Any]] = []
    for match in resolved:
        result = await concepts_module.get_financial_concept(
            match["cik"],
            concept,
            period=period,
            limit=12,
            company_label=match["name"],
        )
        if is_error(result) or not result.get("values"):
            unavailable.append(
                {
                    "company": match["name"],
                    "ticker": match["ticker"],
                    "cik": match["cik"],
                    "reason": result.get("error", "No values were returned."),
                    "tags_tried": result.get("tags_tried"),
                }
            )
            continue
        series[match["ticker"] or match["cik"]] = {"match": match, "concept": result}

    if len(series) < 2:
        return error_response(
            f"Fewer than two companies report {concept} for the requested "
            f"period, so there is nothing to compare.",
            "Tell the user which companies do not tag this concept and name "
            "them. Do not fill the gap with a figure from memory or with a "
            "different concept.",
            unavailable=unavailable or None,
        )

    # Pick the fiscal year: the requested one, or the newest year every
    # remaining company reports. Falling back to "newest each" would compare
    # 2024 against 2023 without saying so.
    year_sets = [
        {v["fy"] for v in entry["concept"]["values"] if v.get("fy")}
        for entry in series.values()
    ]
    common_years = set.intersection(*year_sets) if year_sets else set()
    if fiscal_year is not None:
        chosen_year: int | None = fiscal_year
    elif common_years:
        chosen_year = max(common_years)
    else:
        return error_response(
            "These companies have no fiscal year in common in the data "
            "returned, so a comparison would compare different years.",
            "Fetch each company separately with get_financial_concept and "
            "present the figures with their period end dates instead of as a "
            "comparison.",
            years_by_company={
                ticker: sorted(y for y in years if y)
                for ticker, years in zip(series, year_sets, strict=True)
            },
        )

    rows: list[dict[str, Any]] = []
    for entry in series.values():
        match, result = entry["match"], entry["concept"]
        value = next((v for v in result["values"] if v.get("fy") == chosen_year), None)
        if value is None:
            unavailable.append(
                {
                    "company": match["name"],
                    "ticker": match["ticker"],
                    "cik": match["cik"],
                    "reason": f"No {concept} reported for fiscal year {chosen_year}.",
                    "fiscal_years_available": sorted(
                        {v["fy"] for v in result["values"] if v.get("fy")}, reverse=True
                    ),
                }
            )
            continue
        rows.append(
            {
                "company": match["name"],
                "ticker": match["ticker"],
                "cik": match["cik"],
                "value": value["value"],
                "unit": result["unit"],
                "fy": value["fy"],
                "fp": value["fp"],
                "start": value["start"],
                "end": value["end"],
                "filed": value["filed"],
                "form": value["form"],
                "matched_tag": result["matched_tag"],
                "restated": value.get("restated", False),
                "prior_value": value.get("prior_value"),
            }
        )

    if len(rows) < 2:
        return error_response(
            f"Only {len(rows)} of {len(companies)} companies report {concept} "
            f"for fiscal year {chosen_year}.",
            "Tell the user which companies are missing and why, and offer the "
            "years that are available. Do not compare a single company against "
            "nothing.",
            unavailable=unavailable or None,
            fiscal_year=chosen_year,
        )

    alignment = _fiscal_alignment(rows)
    tags = {r["matched_tag"] for r in rows}
    units = {r["unit"] for r in rows}

    notes: list[str] = []
    if len(tags) > 1:
        notes.append(
            "These companies matched different XBRL tags for the same concept "
            f"({', '.join(sorted(t for t in tags if t))}). The figures are not "
            "defined identically. Name the tags in your answer."
        )
    if len(units) > 1:
        notes.append(
            f"More than one currency or unit appears in this comparison "
            f"({', '.join(sorted(u for u in units if u))}). Do not compute a "
            "difference or a ratio across them."
        )
    if any(r["restated"] for r in rows):
        restated = [r["company"] for r in rows if r["restated"]]
        notes.append(
            f"{', '.join(restated)} restated this figure after first reporting "
            "it. The value shown is the most recent one. Mention the "
            "restatement."
        )
    if unavailable:
        notes.append(
            f"{len(unavailable)} of the requested companies are not in the "
            "comparison. They are listed under 'unavailable'. Say so rather "
            "than presenting the table as complete."
        )

    response: dict[str, Any] = {
        "concept": concept,
        "fiscal_year": chosen_year,
        "period": period,
        "unit": rows[0]["unit"] if len(units) == 1 else None,
        "comparable": bool(alignment["aligned"]) and len(tags) == 1 and len(units) == 1,
        "fiscal_alignment": alignment,
        "companies": sorted(rows, key=lambda r: r["value"] or 0, reverse=True),
        "unavailable": unavailable,
        "notes": notes,
    }
    if "warning" in alignment:
        response["warning"] = alignment["warning"]
    return response


# --------------------------------------------------------------------------- #
# Tool 5 — get_filing_section
# --------------------------------------------------------------------------- #


@mcp.tool()
@tool_error_boundary
async def get_filing_section(
    cik: str,
    accession_number: str,
    section: str,
    max_chars: int = 20000,
) -> dict[str, Any]:
    """Read one named section out of a filing's text, e.g. Risk Factors or MD&A.

    Use this for narrative questions — what management said about demand, what
    risks the company discloses, what a legal proceeding is about. Do not use
    it to read financial figures: use get_financial_concept, which returns
    tagged numbers rather than text that used to be a table.

    Get the accession number from list_filings first.

    Sections this tool can extract, by key: business (Item 1), risk_factors
    (Item 1A), properties (Item 2), legal_proceedings (Item 3), mda (Item 7),
    market_risk (Item 7A), financial_statements (Item 8), controls (Item 9A).

    Section boundaries are found by matching item headings in the flattened
    document. This works well for 10-K and 10-Q filings from roughly 2005
    onward. It works less well on older filings, on filings that incorporate a
    section by reference to an exhibit or a proxy statement, and on filings
    that use unusual heading formats. When the section cannot be found the tool
    says so and gives you the document URL — pass that URL to the user rather
    than describing the section from memory.

    Long sections are truncated. Check `truncated` and say so if you summarise.

    Args:
        cik: The company's CIK, from resolve_company.
        accession_number: The filing's accession number from list_filings, in
            the form 0001045810-24-000029.
        section: A section key such as "risk_factors", or an alias such as
            "Item 1A" or "MD&A".
        max_chars: Maximum characters of section text to return. Default 20000.

    Returns:
        text, section_label, form, filing_date, period_of_report, document_url,
        chars_returned, truncated, and extraction_confidence.
    """
    return await filings_module.get_filing_section(
        cik, accession_number, section, max_chars=max_chars
    )


# --------------------------------------------------------------------------- #
# Tool 6 — search_full_text
# --------------------------------------------------------------------------- #


@mcp.tool()
@tool_error_boundary
async def search_full_text(
    query: str,
    forms: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search the full text of EDGAR filings. COVERS 2001 ONWARD ONLY.

    EDGAR's full-text index begins in 2001. Filings from 1993 to 2000 are in
    EDGAR and can be read with list_filings and get_filing_section, but they
    are not in this index and this tool cannot see them. **Zero results does
    not mean the phrase was never filed** — it may mean the filing predates
    2001. Say this to the user whenever their question touches an earlier
    period. This tool refuses a date range that starts before 2001 rather than
    quietly searching a shorter window than the user asked for.

    Use it to find which companies discussed a topic, or which filing of a
    company first mentioned something. Wrap a phrase in double quotes for an
    exact match: "supply chain constraints".

    This returns filings that match, not the matching text. Follow up with
    get_filing_section to read the surrounding language.

    Args:
        query: The phrase to search for. Use double quotes for exact phrases.
        forms: Restrict to form types, e.g. ["10-K", "10-Q"].
        date_from: Earliest filing date as YYYY-MM-DD. Must be 2001 or later.
        date_to: Latest filing date as YYYY-MM-DD.
        limit: Maximum results. Default 10.

    Returns:
        results (company, cik, form, filing_date, accession_number,
        index_url), total_hits, and a coverage statement restating the 2001
        limit.
    """
    return await filings_module.search_full_text(
        query, forms=forms, date_from=date_from, date_to=date_to, limit=limit
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        The parser used by :func:`main`.
    """
    parser = argparse.ArgumentParser(
        prog="edgar-mcp",
        description="MCP server exposing SEC EDGAR filing data as six tools.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the on-disk response cache and fetch everything fresh.",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Directory for cached SEC responses. Default .cache",
    )
    parser.add_argument(
        "--cache-ttl",
        type=float,
        default=None,
        help="Seconds before a cached response is refetched. 0 means never.",
    )
    parser.add_argument(
        "--user-agent",
        default=None,
        help="SEC User-Agent header, formatted 'Name email@example.com'.",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=client_module.MAX_REQUESTS_PER_SECOND,
        help="Requests per second ceiling. Cannot exceed 10.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity. Logs go to stderr.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Configure the shared client and run the server over stdio.

    Args:
        argv: Command-line arguments. Defaults to ``sys.argv[1:]``.
    """
    args = build_parser().parse_args(argv)
    logging.getLogger().setLevel(args.log_level)

    client_module.set_client(
        SECClient(
            user_agent=args.user_agent,
            cache_dir=args.cache_dir,
            use_cache=not args.no_cache,
            cache_ttl_seconds=args.cache_ttl,
            requests_per_second=args.rate_limit,
        )
    )
    if args.no_cache:
        companies_module.reset_ticker_cache()

    logger.info(
        "edgar-mcp starting: user_agent=%r cache=%s rate=%.1f/s",
        client_module.get_client().user_agent,
        "off" if args.no_cache else (args.cache_dir or ".cache"),
        args.rate_limit,
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
