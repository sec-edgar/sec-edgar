"""Filing history, section extraction, and full-text search.

Three separate kinds of mess:

**Form variants.** A filer's annual report can arrive as ``10-K``, ``10-K/A``
(an amendment), ``10-KT`` (a transition period after a fiscal year change), or
``10-KT/A``. An analyst who asks for "10-K filings" means all of them. An
analyst who reads a figure out of a 10-K that was later amended is reading a
number the company has withdrawn. :func:`list_filings` matches on the base form
by default and marks every filing that a later amendment supersedes.

**Filing HTML.** EDGAR holds documents from 1993 to today. There is no
consistent markup, no section metadata, and the same "Item 1A. Risk Factors"
string appears in the table of contents, in the cross-references, and at the
section itself. :func:`get_filing_section` picks the occurrence that yields the
longest body, which is a heuristic and is documented as one.

**Full-text search.** EDGAR's full-text index starts in 2001. Anything earlier
is invisible to it, silently — the search returns zero hits rather than an
error, which is exactly the failure mode that gets an analyst to conclude a
company never mentioned something. :func:`search_full_text` says so in its
response, every time, and refuses date ranges that start before 2001.
"""

from __future__ import annotations

import html
import logging
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlencode

from .client import FULL_TEXT_SEARCH_URL, SECClient, get_client
from .companies import pad_cik, unpad_cik
from .errors import InvalidInputError, NotFoundError, SECError

logger = logging.getLogger(__name__)

#: EDGAR's full-text index does not reach further back than this.
FULL_TEXT_EARLIEST_YEAR = 2001

ARCHIVE_BASE = "https://www.sec.gov/Archives/edgar/data"

_AMENDMENT_SUFFIX = re.compile(r"/A(?:[0-9]*)$", re.IGNORECASE)


def base_form(form: str) -> str:
    """Strip the amendment suffix from a form type.

    ``10-K/A`` becomes ``10-K``. ``10-KT`` stays ``10-KT`` because a transition
    report is a different report, not an amended one.

    Args:
        form: A form type as EDGAR writes it.

    Returns:
        The base form type, upper-cased.
    """
    return _AMENDMENT_SUFFIX.sub("", (form or "").strip().upper())


def is_amendment(form: str) -> bool:
    """Report whether a form type is an amendment.

    Args:
        form: A form type as EDGAR writes it.

    Returns:
        True for ``10-K/A``, ``10-Q/A``, ``8-K/A`` and similar.
    """
    return bool(_AMENDMENT_SUFFIX.search((form or "").strip()))


def form_family(form: str) -> set[str]:
    """Return every form type that a request for ``form`` should match.

    ``10-K`` matches the transition report and both amendments, because an
    analyst asking for annual reports wants all four.

    Args:
        form: The requested form type.

    Returns:
        The set of matching form types, upper-cased.
    """
    root = base_form(form)
    family = {root, f"{root}/A"}
    if root == "10-K":
        family |= {"10-KT", "10-KT/A", "10-K405", "10-K405/A"}
    if root == "10-Q":
        family |= {"10-QT", "10-QT/A"}
    return family


def _parse_date(value: Any) -> date | None:
    """Parse an ISO date, returning None on anything unparseable.

    Args:
        value: A date string or anything else.

    Returns:
        The parsed date or None.
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _rows_from_recent(recent: dict[str, Any]) -> list[dict[str, Any]]:
    """Transpose EDGAR's column-oriented filing history into rows.

    ``submissions.json`` stores filings as parallel arrays, one per field. Rows
    are only well-formed if every array is the same length, which is not
    guaranteed when EDGAR changes the schema, so the shortest array wins.

    Args:
        recent: The ``filings.recent`` object.

    Returns:
        A list of per-filing dicts.
    """
    if not isinstance(recent, dict):
        return []
    columns = {k: v for k, v in recent.items() if isinstance(v, list)}
    if not columns:
        return []
    length = min(len(v) for v in columns.values())
    return [{k: v[i] for k, v in columns.items()} for i in range(length)]


def _filing_urls(cik_unpadded: str, accession: str, primary_document: str) -> dict[str, str]:
    """Build the archive URLs for one filing.

    Args:
        cik_unpadded: The CIK with leading zeros stripped. Archive paths use
            the unpadded form; the API uses the padded one.
        accession: The accession number with dashes.
        primary_document: The primary document filename.

    Returns:
        A dict with ``index_url`` and, when known, ``document_url``.
    """
    folder = accession.replace("-", "")
    base = f"{ARCHIVE_BASE}/{cik_unpadded}/{folder}"
    urls = {"index_url": f"{base}/{accession}-index.htm"}
    if primary_document:
        urls["document_url"] = f"{base}/{primary_document}"
    return urls


def _mark_superseding(filings: list[dict[str, Any]]) -> None:
    """Link each amendment to the filing it supersedes, in place.

    Two filings are the same report if they share a base form and a period of
    report. When one of them is an amendment, the other is stale.

    Args:
        filings: The filing dicts to annotate.
    """
    originals: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for f in filings:
        if not f["is_amendment"]:
            originals.setdefault((f["base_form"], f.get("period_of_report") or ""), []).append(f)

    for amendment in filings:
        if not amendment["is_amendment"]:
            continue
        key = (amendment["base_form"], amendment.get("period_of_report") or "")
        targets = originals.get(key, [])
        if not targets:
            continue
        amendment["supersedes"] = [t["accession_number"] for t in targets]
        for target in targets:
            target["superseded"] = True
            target["superseded_by"] = amendment["accession_number"]
            target["superseded_note"] = (
                f"A {amendment['form']} filed {amendment['filing_date']} amends "
                f"this filing. Figures taken from here may have been revised."
            )


async def list_filings(
    cik: str | int,
    *,
    form: str | None = None,
    exact_form: bool = False,
    since: str | None = None,
    until: str | None = None,
    limit: int = 20,
    client: SECClient | None = None,
) -> dict[str, Any]:
    """List a company's filings, newest first, with amendments flagged.

    Args:
        cik: The company's CIK in any spelling.
        form: Filter to one form type, e.g. ``"10-K"``. By default this also
            matches the amendment and transition variants.
        exact_form: Match the form string exactly, excluding variants.
        since: Keep filings on or after this ISO date.
        until: Keep filings on or before this ISO date.
        limit: Maximum filings to return.
        client: The HTTP client. Defaults to the process-wide one.

    Returns:
        A dict with ``company``, ``cik``, ``filings`` and a
        ``fiscal_year_end`` field. Each filing carries ``form``,
        ``base_form``, ``is_amendment``, ``superseded``, dates, and URLs.

    Raises:
        InvalidInputError: If a date argument is not an ISO date.
    """
    padded = pad_cik(cik)
    unpadded = unpad_cik(padded)
    http = client or get_client()

    since_d, until_d = _parse_date(since), _parse_date(until)
    if since and since_d is None:
        raise InvalidInputError(
            f"since={since!r} is not an ISO date.",
            suggestion="Call this tool again with a date formatted YYYY-MM-DD.",
        )
    if until and until_d is None:
        raise InvalidInputError(
            f"until={until!r} is not an ISO date.",
            suggestion="Call this tool again with a date formatted YYYY-MM-DD.",
        )

    payload = await http.submissions(padded)
    recent = (payload.get("filings") or {}).get("recent") or {}
    rows = _rows_from_recent(recent)

    wanted = None if form is None else ({base_form(form)} if exact_form else form_family(form))

    filings: list[dict[str, Any]] = []
    for row in rows:
        raw_form = str(row.get("form", "")).upper()
        if wanted is not None and raw_form not in wanted:
            continue
        filed = _parse_date(row.get("filingDate"))
        if since_d and (filed is None or filed < since_d):
            continue
        if until_d and (filed is None or filed > until_d):
            continue

        accession = str(row.get("accessionNumber", ""))
        record: dict[str, Any] = {
            "accession_number": accession,
            "form": raw_form,
            "base_form": base_form(raw_form),
            "is_amendment": is_amendment(raw_form),
            "filing_date": row.get("filingDate"),
            "period_of_report": row.get("reportDate") or None,
            "primary_document": row.get("primaryDocument") or None,
            "description": row.get("primaryDocDescription") or None,
            "is_xbrl": bool(row.get("isXBRL")),
            "superseded": False,
        }
        record.update(
            _filing_urls(unpadded, accession, str(row.get("primaryDocument") or ""))
        )
        filings.append(record)

    _mark_superseding(filings)
    truncated = len(filings) > limit
    result: dict[str, Any] = {
        "cik": unpadded,
        "company": payload.get("name"),
        "fiscal_year_end": payload.get("fiscalYearEnd"),
        "form_filter": sorted(wanted) if wanted else None,
        "filings_returned": min(len(filings), limit),
        "filings_matched": len(filings),
        "filings": filings[:limit],
    }

    notes: list[str] = []
    if payload.get("fiscalYearEnd"):
        fye = str(payload["fiscalYearEnd"])
        notes.append(
            f"This company's fiscal year ends on {fye[:2]}-{fye[2:]} (MM-DD). "
            "Its FY2024 is not the same date range as a December filer's FY2024."
        )
    if any(f["superseded"] for f in filings[:limit]):
        notes.append(
            "Some filings below were amended later. Fields superseded_by and "
            "superseded_note say which. Prefer the amendment for any figure."
        )
    if truncated:
        notes.append(
            f"{len(filings)} filings matched and {limit} were returned. Raise "
            "limit or narrow the date range to see the rest."
        )
    # filings.files lists older history in separate JSON documents. This tool
    # reads only filings.recent, which covers roughly the last 1,000 filings.
    extra_files = (payload.get("filings") or {}).get("files") or []
    if extra_files:
        earliest = filings[-1]["filing_date"] if filings else None
        notes.append(
            "Only the recent filing history was read. EDGAR keeps older "
            f"filings in {len(extra_files)} additional index files that this "
            f"tool does not fetch, so filings before {earliest} may be missing. "
            "Say so if the user asks about filings from the 1990s or 2000s."
        )
    result["notes"] = notes

    if not filings:
        result["error"] = (
            f"No filings matched for CIK {unpadded}"
            + (f" with form {form}" if form else "")
            + (f" since {since}" if since else "")
            + "."
        )
        result["suggestion"] = (
            "Call this tool again without the form filter to see what the "
            "company does file. A company that files 20-F rather than 10-K is "
            "a foreign private issuer and reports annually in a different form."
        )
    return result


# --------------------------------------------------------------------------- #
# Section extraction
# --------------------------------------------------------------------------- #

#: Section aliases mapped to the "Item N" heading they live under. Only 10-K
#: and 10-Q items are here; other forms are not item-structured.
SECTION_PATTERNS: dict[str, tuple[str, str]] = {
    "business": (r"item\s*1\b", "Item 1. Business"),
    "risk_factors": (r"item\s*1a\b", "Item 1A. Risk Factors"),
    "legal_proceedings": (r"item\s*3\b", "Item 3. Legal Proceedings"),
    "properties": (r"item\s*2\b", "Item 2. Properties"),
    "mda": (r"item\s*7\b", "Item 7. Management's Discussion and Analysis"),
    "market_risk": (r"item\s*7a\b", "Item 7A. Quantitative and Qualitative Disclosures"),
    "financial_statements": (r"item\s*8\b", "Item 8. Financial Statements"),
    "controls": (r"item\s*9a\b", "Item 9A. Controls and Procedures"),
}

#: Aliases a model is likely to send.
SECTION_ALIASES = {
    "item 1": "business",
    "item 1a": "risk_factors",
    "item 2": "properties",
    "item 3": "legal_proceedings",
    "item 7": "mda",
    "item 7a": "market_risk",
    "item 8": "financial_statements",
    "item 9a": "controls",
    "risk factors": "risk_factors",
    "risks": "risk_factors",
    "management discussion": "mda",
    "management's discussion and analysis": "mda",
    "md&a": "mda",
    "mdna": "mda",
    "legal": "legal_proceedings",
    "financials": "financial_statements",
}

_SCRIPT_STYLE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_BLOCK_END = re.compile(
    r"</(p|div|tr|table|h[1-6]|li|br)\s*>|<br\s*/?>", re.IGNORECASE
)
_TAG = re.compile(r"<[^>]+>")
_BLANKS = re.compile(r"[ \t\xa0]+")
_NEWLINES = re.compile(r"\n{3,}")

#: The next "Item N" heading, used to find where a section ends.
_ANY_ITEM = re.compile(r"^\s*item\s*\d{1,2}[ab]?\b", re.IGNORECASE | re.MULTILINE)


def html_to_text(raw: str) -> str:
    """Flatten filing HTML into plain text.

    Written with regular expressions rather than an HTML parser on purpose:
    filing documents run to tens of megabytes, a tree parse of one is slow
    enough to time out a tool call, and the structure is not worth preserving.

    Args:
        raw: The document source. Inline XBRL and plain HTML both work.

    Returns:
        Text with block boundaries turned into newlines and entities decoded.
    """
    text = _SCRIPT_STYLE.sub(" ", raw)
    text = _BLOCK_END.sub("\n", text)
    text = _TAG.sub(" ", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = _BLANKS.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _NEWLINES.sub("\n\n", text).strip()


def extract_section(text: str, section: str) -> tuple[str | None, dict[str, Any]]:
    """Pull one item section out of a flattened filing.

    The same heading string appears in the table of contents, in "see Item 1A"
    cross-references, and at the section itself. Rather than guess which is
    which, this takes every occurrence, measures the text between it and the
    next item heading, and keeps the longest. The table of contents entry
    always loses because the next heading is one line below it.

    Args:
        text: The flattened filing text.
        section: A canonical section key from :data:`SECTION_PATTERNS`.

    Returns:
        A tuple of (section text or None, diagnostics dict). The diagnostics
        always report how many candidate headings were seen, so the caller can
        say when extraction was uncertain.
    """
    pattern, _label = SECTION_PATTERNS[section]
    heading = re.compile(rf"^\s*{pattern}", re.IGNORECASE | re.MULTILINE)
    starts = [m.start() for m in heading.finditer(text)]
    diagnostics: dict[str, Any] = {"headings_found": len(starts)}
    if not starts:
        return None, diagnostics

    best: tuple[int, int] | None = None
    for start in starts:
        following = _ANY_ITEM.search(text, start + 40)
        end = following.start() if following else len(text)
        if best is None or (end - start) > (best[1] - best[0]):
            best = (start, end)

    assert best is not None  # noqa: S101 - starts is non-empty, so best is set
    body = text[best[0] : best[1]].strip()
    diagnostics["chars_found"] = len(body)
    if len(body) < 200:
        # Every occurrence was a table-of-contents line or a cross-reference.
        diagnostics["reason"] = "only_table_of_contents_matches"
        return None, diagnostics
    return body, diagnostics


def _canonical_section(section: str) -> str:
    """Map a user- or model-supplied section name onto a canonical key.

    Args:
        section: What the caller asked for.

    Returns:
        The canonical key.

    Raises:
        InvalidInputError: If the section is not one this tool extracts.
    """
    key = " ".join((section or "").lower().replace("_", " ").split())
    if key.replace(" ", "_") in SECTION_PATTERNS:
        return key.replace(" ", "_")
    if key in SECTION_ALIASES:
        return SECTION_ALIASES[key]
    raise InvalidInputError(
        f"{section!r} is not a section this tool can extract.",
        suggestion=(
            "Call this tool again with one of: " + ", ".join(sorted(SECTION_PATTERNS)) + "."
        ),
        details={"supported_sections": sorted(SECTION_PATTERNS)},
    )


async def get_filing_section(
    cik: str | int,
    accession_number: str,
    section: str,
    *,
    max_chars: int = 20000,
    client: SECClient | None = None,
) -> dict[str, Any]:
    """Extract one named section from a filing's primary document.

    Args:
        cik: The company's CIK in any spelling.
        accession_number: The filing's accession number, with or without dashes.
        section: A section key or alias, e.g. ``"risk_factors"``.
        max_chars: Truncate the returned text at this many characters.
        client: The HTTP client. Defaults to the process-wide one.

    Returns:
        A dict with ``text``, ``section``, ``document_url``, ``truncated`` and
        an ``extraction_confidence`` field, or a structured error.

    Raises:
        InvalidInputError: If the section name is not supported.
        SECError: If EDGAR fails.
    """
    canonical = _canonical_section(section)
    padded = pad_cik(cik)
    unpadded = unpad_cik(padded)
    http = client or get_client()

    normalized = accession_number.strip()
    if "-" not in normalized and len(normalized) == 18:
        normalized = f"{normalized[:10]}-{normalized[10:12]}-{normalized[12:]}"

    payload = await http.submissions(padded)
    rows = _rows_from_recent((payload.get("filings") or {}).get("recent") or {})
    match = next((r for r in rows if str(r.get("accessionNumber")) == normalized), None)
    if match is None:
        raise NotFoundError(
            f"Accession number {normalized} is not in the recent filing history "
            f"for CIK {unpadded}.",
            suggestion=(
                "Call list_filings for this CIK to get valid accession numbers, "
                "then call this tool again with one of them."
            ),
        )

    urls = _filing_urls(unpadded, normalized, str(match.get("primaryDocument") or ""))
    document_url = urls.get("document_url")
    if not document_url:
        raise NotFoundError(
            f"Filing {normalized} has no primary document recorded in EDGAR.",
            suggestion=(
                "Open the filing index instead and tell the user you could not "
                f"read the document: {urls['index_url']}"
            ),
        )

    raw = await http.get_text(document_url)
    text = html_to_text(raw)
    body, diagnostics = extract_section(text, canonical)

    common = {
        "cik": unpadded,
        "accession_number": normalized,
        "form": str(match.get("form", "")).upper(),
        "filing_date": match.get("filingDate"),
        "period_of_report": match.get("reportDate"),
        "section": canonical,
        "section_label": SECTION_PATTERNS[canonical][1],
        "document_url": document_url,
        "document_chars": len(text),
        "extraction": diagnostics,
    }

    if body is None:
        return {
            **common,
            "error": (
                f"Could not locate {SECTION_PATTERNS[canonical][1]} in this "
                f"document. The filing was fetched and read; the section "
                f"heading was either absent or only appeared in the table of "
                f"contents."
            ),
            "suggestion": (
                "Older filings and filings that incorporate sections by "
                "reference to an exhibit do not contain the section inline. "
                "Tell the user which filing you read and that the section was "
                f"not in it, and give them the URL: {document_url}. Do not "
                "summarise the section from memory."
            ),
        }

    truncated = len(body) > max_chars
    return {
        **common,
        "text": body[:max_chars],
        "chars_returned": min(len(body), max_chars),
        "truncated": truncated,
        "extraction_confidence": "high" if diagnostics["headings_found"] <= 2 else "medium",
        "notes": [
            "Section boundaries are found by matching item headings in "
            "flattened text. Tables inside the section lose their column "
            "alignment. Quote figures from get_financial_concept rather than "
            "from a table read out of this text."
        ]
        + (
            [f"Text was truncated at {max_chars} characters of {len(body)}."]
            if truncated
            else []
        ),
    }


# --------------------------------------------------------------------------- #
# Full-text search
# --------------------------------------------------------------------------- #


def _hit_to_result(hit: dict[str, Any]) -> dict[str, Any] | None:
    """Normalise one full-text search hit.

    The response shape is Elasticsearch's, and it is not a documented API, so
    every field access here is defensive.

    Args:
        hit: One element of ``hits.hits``.

    Returns:
        A flattened result, or None if the hit is unrecognisable.
    """
    source = hit.get("_source")
    if not isinstance(source, dict):
        return None

    # _id is "0001045810-24-000029:nvda-20240128.htm".
    identifier = str(hit.get("_id", ""))
    accession, _, document = identifier.partition(":")

    ciks = source.get("ciks") or []
    names = source.get("display_names") or []
    result = {
        "accession_number": accession or None,
        "document": document or None,
        "form": source.get("file_type") or source.get("root_form"),
        "filing_date": source.get("file_date"),
        "company": names[0] if names else None,
        "cik": unpad_cik(ciks[0]) if ciks else None,
    }
    if result["cik"] and accession:
        folder = accession.replace("-", "")
        result["index_url"] = (
            f"{ARCHIVE_BASE}/{result['cik']}/{folder}/{accession}-index.htm"
        )
    return result


async def search_full_text(
    query: str,
    *,
    forms: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
    client: SECClient | None = None,
) -> dict[str, Any]:
    """Search the text of EDGAR filings from 2001 onward.

    Args:
        query: The search phrase. Wrap it in double quotes for an exact phrase.
        forms: Restrict to these form types, e.g. ``["10-K"]``.
        date_from: ISO start date. Must be 2001-01-01 or later.
        date_to: ISO end date.
        limit: Maximum hits to return.
        client: The HTTP client. Defaults to the process-wide one.

    Returns:
        A dict with ``results``, ``total_hits`` and a ``coverage`` field that
        always restates the 2001 cutoff, or a structured error.

    Raises:
        InvalidInputError: If the query is empty or the date range starts
            before EDGAR's full-text index does.
        SECError: If the search backend fails.
    """
    query = (query or "").strip()
    if not query:
        raise InvalidInputError(
            "No search phrase was given.",
            suggestion="Call this tool again with the phrase the user asked about.",
        )

    from_d, to_d = _parse_date(date_from), _parse_date(date_to)
    if date_from and from_d is None:
        raise InvalidInputError(
            f"date_from={date_from!r} is not an ISO date.",
            suggestion="Call this tool again with a date formatted YYYY-MM-DD.",
        )
    if from_d and from_d.year < FULL_TEXT_EARLIEST_YEAR:
        raise InvalidInputError(
            f"EDGAR full-text search only covers filings from "
            f"{FULL_TEXT_EARLIEST_YEAR} onward, and date_from is {date_from}.",
            suggestion=(
                "Tell the user plainly that EDGAR's full-text index begins in "
                f"{FULL_TEXT_EARLIEST_YEAR} and that filings before then cannot "
                "be searched by keyword. Do not run the search with a later "
                "start date and present the result as if it covered the period "
                "they asked about. If they need pre-2001 text, they must read "
                "the filings directly; list_filings can find them."
            ),
            details={"earliest_year": FULL_TEXT_EARLIEST_YEAR},
        )

    params: dict[str, str] = {"q": query}
    if forms:
        params["forms"] = ",".join(f.strip().upper() for f in forms if f.strip())
    if from_d or to_d:
        params["dateRange"] = "custom"
        if from_d:
            params["startdt"] = from_d.isoformat()
        if to_d:
            params["enddt"] = to_d.isoformat()

    url = f"{FULL_TEXT_SEARCH_URL}?{urlencode(params)}"
    http = client or get_client()
    try:
        payload = await http.get_json(url)
    except NotFoundError as exc:
        raise SECError(
            "EDGAR's full-text search backend rejected the request.",
            suggestion=(
                "This endpoint is not part of SEC's documented API and its "
                "shape changes. Fall back to list_filings plus "
                "get_filing_section, and tell the user keyword search is "
                "unavailable."
            ),
        ) from exc

    hits = ((payload or {}).get("hits") or {}).get("hits") or []
    total = ((payload or {}).get("hits") or {}).get("total") or {}
    total_value = total.get("value") if isinstance(total, dict) else total

    results = [r for r in (_hit_to_result(h) for h in hits[:limit]) if r]
    coverage = (
        f"EDGAR full-text search covers filings from {FULL_TEXT_EARLIEST_YEAR} "
        "to today. Filings before then are in EDGAR but are not in this index, "
        "so zero results never means the phrase was never filed."
    )

    response: dict[str, Any] = {
        "query": query,
        "forms": params.get("forms"),
        "date_from": params.get("startdt"),
        "date_to": params.get("enddt"),
        "total_hits": total_value,
        "results_returned": len(results),
        "results": results,
        "coverage": coverage,
    }
    if not results:
        response["error"] = f"No filings since {FULL_TEXT_EARLIEST_YEAR} match {query!r}."
        response["suggestion"] = (
            "Try a shorter phrase or drop the form filter. State the "
            f"{FULL_TEXT_EARLIEST_YEAR} coverage limit in your answer if the "
            "user's question was about an earlier period."
        )
    return response
