"""Company name and ticker resolution to CIK.

Two problems live here, and the second one is the interesting one.

**CIK padding.** EDGAR wants a 10-digit zero-padded CIK in API paths
(``CIK0000320193``) and an unpadded one in archive paths
(``/Archives/edgar/data/320193/...``). Getting this wrong produces a 404 that
reads exactly like "this company does not file", which is the worst kind of
bug: it looks like data. Both forms come from :func:`pad_cik` and
:func:`unpad_cik`, and nothing else in the repository formats a CIK.

**Name matching.** Ticker symbols are unique; names are not. "Apple" matches
Apple Inc. and Apple Hospitality REIT. "Delta" matches Delta Air Lines and
several unrelated filers. The rule this module enforces is that an exact ticker
match wins outright and everything else is a ranked guess — and when the top
two guesses are within :data:`AMBIGUITY_MARGIN` of each other, the tool refuses
to pick and hands the candidates back for the user to choose from.

The refusal is the feature. A resolver that silently picks the top match is
right most of the time and catastrophically wrong the rest of the time, and the
analyst has no way to tell those two cases apart from the answer text.

Matching uses :class:`difflib.SequenceMatcher` from the standard library. It is
not the best string matcher available. It is good enough at this scale
(~10,000 filers), it needs no dependency, and it is deterministic — which
matters because the eval numbers have to be reproducible.
"""

from __future__ import annotations

import difflib
import logging
import re
from typing import Any

from .client import SECClient, get_client
from .errors import InvalidInputError, SECError

logger = logging.getLogger(__name__)

#: If the top two fuzzy scores are closer than this, refuse to choose.
#: Tuned by hand against the ambiguous cases in evals/gold.yaml. Raising it
#: makes the tool ask for clarification more often; lowering it makes it guess.
AMBIGUITY_MARGIN = 0.05

#: Below this score, treat the query as unmatched rather than returning junk.
MIN_MATCH_SCORE = 0.55

#: How many ranked candidates to return.
MAX_CANDIDATES = 5

#: Stripped before comparison so "Apple Inc." and "Apple" score as identical.
#: Deliberately short: "Holdings" and "Group" are load-bearing in some names
#: ("Alphabet" vs "Alphabet Holdings" would be different filers) so they stay.
_CORPORATE_SUFFIXES = (
    "incorporated",
    "corporation",
    "company",
    "limited",
    "inc",
    "corp",
    "co",
    "ltd",
    "plc",
    "llc",
    "lp",
    "sa",
    "nv",
    "ag",
    "the",
)

_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_WHITESPACE = re.compile(r"\s+")

# Cached ticker map, keyed by nothing: there is one of them and it changes
# roughly daily. The on-disk HTTP cache handles staleness; this only avoids
# re-parsing a 1 MB document on every call within one process.
_ticker_cache: list[dict[str, Any]] | None = None


def pad_cik(cik: str | int) -> str:
    """Normalise any CIK spelling to the 10-digit zero-padded form.

    Accepts ``320193``, ``"320193"``, ``"0000320193"``, ``"CIK0000320193"`` and
    surrounding whitespace. Returns ``"0000320193"`` for all of them.

    Args:
        cik: A CIK in any of the forms EDGAR or a user might produce.

    Returns:
        The CIK as exactly 10 digits.

    Raises:
        InvalidInputError: If the value is empty, non-numeric after stripping
            the optional ``CIK`` prefix, or longer than 10 digits.
    """
    raw = str(cik).strip()
    if not raw:
        raise InvalidInputError("An empty value was given where a CIK was expected.")

    if raw[:3].upper() == "CIK":
        raw = raw[3:].strip()
    raw = raw.lstrip("-")

    if not raw.isdigit():
        raise InvalidInputError(
            f"{cik!r} is not a CIK. A CIK is a number, optionally written with "
            "a 'CIK' prefix and leading zeros.",
            suggestion=(
                "Call resolve_company with the ticker symbol or company name "
                "to get a CIK, then pass that CIK to this tool."
            ),
        )
    if len(raw.lstrip("0")) > 10:
        raise InvalidInputError(
            f"{cik!r} has more than 10 significant digits and cannot be a CIK.",
            suggestion="Call resolve_company to obtain a valid CIK.",
        )
    return raw.zfill(10)[-10:] if len(raw) > 10 else raw.zfill(10)


def unpad_cik(cik: str | int) -> str:
    """Return the CIK without leading zeros, as archive URLs want it.

    Args:
        cik: A CIK in any accepted form.

    Returns:
        The CIK with leading zeros stripped, e.g. ``"320193"``. A CIK of zero
        returns ``"0"`` rather than an empty string.
    """
    stripped = pad_cik(cik).lstrip("0")
    return stripped or "0"


def normalize_name(name: str) -> str:
    """Lower-case a company name and drop punctuation and corporate suffixes.

    Args:
        name: A raw company name.

    Returns:
        The comparison form. Returns the punctuation-stripped name unchanged if
        removing suffixes would leave nothing behind (a filer literally named
        "The Company Inc" should not normalise to the empty string).
    """
    text = _NON_ALNUM.sub(" ", name.lower())
    text = _WHITESPACE.sub(" ", text).strip()
    words = [w for w in text.split(" ") if w and w not in _CORPORATE_SUFFIXES]
    return " ".join(words) if words else text


def score_name(query: str, candidate: str) -> float:
    """Score how well a query matches a company name, from 0.0 to 1.0.

    Three signals, in order of precedence:

    * exact match after normalisation scores 1.0;
    * the query being a whole-word prefix of the name scores 0.92, so "Apple"
      ranks Apple Inc. above a filer that merely contains the letters;
    * otherwise the ratio from :class:`difflib.SequenceMatcher`, with a small
      bonus when every query word appears in the name.

    Args:
        query: What the user typed.
        candidate: A company name from EDGAR's ticker file.

    Returns:
        A score between 0.0 and 1.0.
    """
    q = normalize_name(query)
    c = normalize_name(candidate)
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0

    q_words = q.split(" ")
    c_words = c.split(" ")

    if c_words[: len(q_words)] == q_words:
        return 0.92

    ratio = difflib.SequenceMatcher(None, q, c).ratio()
    if all(word in c_words for word in q_words):
        ratio = max(ratio, 0.85)

    # Character-ratio matching alone is fooled by shared boilerplate: "Stripe
    # Payments Holdings" and "Aperture Holdings Corp" share enough letters to
    # score 0.59, which is above the acceptance threshold and completely wrong.
    # People type the distinctive part of a name first, so if the query's first
    # word has no counterpart anywhere in the candidate, this is not a match.
    head = q_words[0]
    if not any(_words_relate(head, word) for word in c_words):
        ratio = min(ratio, 0.5)

    return round(min(ratio, 0.99), 4)


def _words_relate(head: str, word: str) -> bool:
    """Decide whether two single words plausibly refer to the same thing.

    Args:
        head: The first word of the user's query.
        word: One word from a candidate company name.

    Returns:
        True if one is a prefix of the other or they are close spellings,
        which covers "nvidia"/"nvidia", "goog"/"google" and "walmart"/"wal".
    """
    if word.startswith(head) or head.startswith(word):
        return True
    return difflib.SequenceMatcher(None, head, word).ratio() >= 0.8


async def load_ticker_map(client: SECClient | None = None) -> list[dict[str, Any]]:
    """Load and normalise EDGAR's ticker-to-CIK file.

    The published shape is a JSON object whose keys are row numbers and whose
    values are ``{"cik_str": int, "ticker": str, "title": str}``. Entries that
    do not have that shape are skipped rather than crashing the tool, because
    this file has gained fields before.

    Args:
        client: The HTTP client. Defaults to the process-wide one.

    Returns:
        A list of ``{"cik", "ticker", "title"}`` dicts, CIKs zero-padded.
    """
    global _ticker_cache
    if _ticker_cache is not None:
        return _ticker_cache

    payload = await (client or get_client()).company_tickers()
    rows = payload.values() if isinstance(payload, dict) else payload

    companies: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or "cik_str" not in row:
            continue
        try:
            companies.append(
                {
                    "cik": pad_cik(row["cik_str"]),
                    "ticker": str(row.get("ticker", "")).upper(),
                    "title": str(row.get("title", "")),
                }
            )
        except SECError:
            continue

    _ticker_cache = companies
    logger.info("loaded %d companies from the SEC ticker file", len(companies))
    return companies


def reset_ticker_cache() -> None:
    """Drop the in-process ticker map. Used by tests and by ``--no-cache``."""
    global _ticker_cache
    _ticker_cache = None


def _candidate(record: dict[str, Any], score: float, match_type: str) -> dict[str, Any]:
    """Shape one candidate for the response.

    Args:
        record: A row from :func:`load_ticker_map`.
        score: Its match score.
        match_type: How it matched, for the model to reason about.

    Returns:
        The candidate dict.
    """
    return {
        "cik": unpad_cik(record["cik"]),
        "cik_padded": record["cik"],
        "ticker": record["ticker"],
        "name": record["title"],
        "score": round(score, 4),
        "match_type": match_type,
    }


async def resolve_company(
    query: str,
    *,
    max_candidates: int = MAX_CANDIDATES,
    client: SECClient | None = None,
) -> dict[str, Any]:
    """Resolve a ticker or company name to a CIK, or refuse to guess.

    Args:
        query: A ticker symbol or a company name.
        max_candidates: How many ranked candidates to return.
        client: The HTTP client. Defaults to the process-wide one.

    Returns:
        On a confident match, a dict with ``resolved: True``, the winning
        company's ``cik``, ``ticker``, ``name``, ``confidence`` and
        ``match_type``, plus the runners-up under ``candidates``.

        On an ambiguous match, a dict with ``resolved: False``, ``error``,
        ``suggestion`` and the ranked ``candidates``. The caller must not pick
        one of these on the user's behalf.

        On no match at all, a dict with ``error`` and ``suggestion``.
    """
    query = (query or "").strip()
    if not query:
        raise InvalidInputError(
            "No company name or ticker was given.",
            suggestion="Ask the user which company they mean, then call this tool again.",
        )

    companies = await load_ticker_map(client)

    # 1. Exact ticker. Tickers are unique in this file, so this ends the search.
    upper = query.upper()
    exact = [c for c in companies if c["ticker"] == upper]
    if exact:
        winner = exact[0]
        return {
            "resolved": True,
            "query": query,
            "cik": unpad_cik(winner["cik"]),
            "cik_padded": winner["cik"],
            "ticker": winner["ticker"],
            "name": winner["title"],
            "confidence": 1.0,
            "match_type": "ticker_exact",
            "candidates": [_candidate(winner, 1.0, "ticker_exact")],
            "note": (
                "Matched on an exact ticker symbol. Ticker symbols are unique "
                "in EDGAR's file, so this identification is not a guess."
            ),
        }

    # 2. Fuzzy name match over every filer with a ticker.
    scored = sorted(
        (
            (score_name(query, c["title"]), c)
            for c in companies
            if c["title"]
        ),
        key=lambda pair: (-pair[0], pair[1]["title"]),
    )
    ranked = [
        _candidate(record, score, "name_fuzzy")
        for score, record in scored[:max_candidates]
        if score >= MIN_MATCH_SCORE
    ]

    if not ranked:
        best = scored[0][0] if scored else 0.0
        return {
            "resolved": False,
            "query": query,
            "error": f"No SEC filer name is close enough to {query!r} to identify.",
            "suggestion": (
                "Ask the user for the company's ticker symbol, or check whether "
                "the company is private. Private companies, foreign companies "
                "with no US listing, and subsidiaries that do not file "
                "separately are not in EDGAR at all. Do not answer from memory."
            ),
            "best_score": round(best, 4),
            "candidates": [],
        }

    top = ranked[0]

    # 3. An exact name match after normalisation is not a guess either.
    if top["score"] >= 0.999:
        return {
            "resolved": True,
            "query": query,
            "cik": top["cik"],
            "cik_padded": top["cik_padded"],
            "ticker": top["ticker"],
            "name": top["name"],
            "confidence": top["score"],
            "match_type": "name_exact",
            "candidates": ranked,
        }

    # 4. The refusal. Two close candidates means the tool does not know.
    if len(ranked) > 1 and (top["score"] - ranked[1]["score"]) < AMBIGUITY_MARGIN:
        return {
            "resolved": False,
            "query": query,
            "ambiguous": True,
            "error": (
                f"{query!r} matches more than one SEC filer and the top two are "
                f"too close to separate ({top['name']} at {top['score']:.2f}, "
                f"{ranked[1]['name']} at {ranked[1]['score']:.2f})."
            ),
            "suggestion": (
                "Do not pick one of these yourself. Ask the user which company "
                "they mean, listing the candidate names and tickers below. "
                "Once they answer, call resolve_company again with the ticker "
                "symbol, which resolves exactly."
            ),
            "candidates": ranked,
            "margin": round(top["score"] - ranked[1]["score"], 4),
            "ambiguity_margin": AMBIGUITY_MARGIN,
        }

    # 5. A clear winner, but still a guess. Say so.
    return {
        "resolved": True,
        "query": query,
        "cik": top["cik"],
        "cik_padded": top["cik_padded"],
        "ticker": top["ticker"],
        "name": top["name"],
        "confidence": top["score"],
        "match_type": "name_fuzzy",
        "candidates": ranked,
        "note": (
            "Matched on company name, not ticker. Name matching is a guess. "
            "State the full company name you used in your answer so the user "
            "can catch a wrong match."
        ),
    }


async def company_name(padded_cik: str, client: SECClient | None = None) -> str | None:
    """Look up a filer's name from the ticker file, without an extra request.

    Args:
        padded_cik: A 10-digit zero-padded CIK.
        client: The HTTP client. Defaults to the process-wide one.

    Returns:
        The company name, or None if this CIK has no ticker on file.
    """
    for record in await load_ticker_map(client):
        if record["cik"] == padded_cik:
            return record["title"]
    return None
