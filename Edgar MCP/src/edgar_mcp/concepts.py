"""XBRL concept resolution: the part of this project that earns its keep.

An analyst asks "what was revenue". There is no tag called revenue. Depending
on the filer, the year, and how the filer's accountants read ASC 606, the same
economic number is tagged as any of:

===============================================================  ============
``RevenueFromContractWithCustomerExcludingAssessedTax``          post-2018 norm
``RevenueFromContractWithCustomerIncludingAssessedTax``          includes sales tax
``Revenues``                                                     the generic tag
``SalesRevenueNet``                                              deprecated 2018
``SalesRevenueGoodsNet``                                         goods only
===============================================================  ============

So this module walks an explicit, ordered chain and **always reports which tag
it landed on**. A number without its tag is not an answer, it is a rumour. The
``matched_tag`` and ``tags_tried`` fields are in every response, including the
successful ones, so the model can quote the tag to the analyst and the analyst
can tell "revenue as the filer defined it" from "revenue as I defined it".

Three other pieces of mess are handled here.

**Restatements.** The same fiscal period appears many times in a
``companyconcept`` response with different ``filed`` dates. Most repeats are
harmless: last year's figure reappears as this year's comparative with the same
value. Some are not: a 10-K/A or a later 10-K reports a *different* value for a
period that was already published. We return the most recently filed value and,
when an earlier filing said something different, set ``restated: true`` and
carry ``prior_value`` and ``prior_filed`` so the answer can say so out loud.

**Units.** ``companyconcept`` returns a ``units`` object that can hold ``USD``,
``USD/shares``, ``shares``, ``EUR`` and more at the same time. We pick exactly
one unit, report it, and list what else was available. Mixing them would
produce a number that is off by a factor of a billion and looks fine.

**Fiscal years.** The ``fy`` and ``fp`` fields in a fact describe the *filing*
the fact appeared in, not the period the fact covers. Apple's FY2022 revenue
appears in the FY2022 10-K with ``fy: 2022`` and again in the FY2023 10-K with
``fy: 2023``. Filtering on the raw ``fy`` therefore returns the wrong year
about half the time. :func:`_infer_fiscal_year` derives the period's own fiscal
year instead, and both values are returned: ``fy`` is the period's year and
``reported_in_fy`` is the filing's.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from .client import SECClient, get_client
from .companies import pad_cik
from .errors import InvalidInputError, NotFoundError, SECError

logger = logging.getLogger(__name__)

#: Forms that carry an annual period.
ANNUAL_FORMS = frozenset({"10-K", "10-K/A", "10-KT", "10-KT/A", "20-F", "20-F/A", "40-F", "40-F/A"})

#: Forms that carry a quarterly period.
QUARTERLY_FORMS = frozenset({"10-Q", "10-Q/A"})

#: A duration fact is annual if it spans roughly a year. 52/53-week fiscal
#: calendars, transition periods and leap years all land inside this window.
ANNUAL_DAYS = (340, 400)

#: A duration fact is quarterly if it spans roughly a quarter.
QUARTERLY_DAYS = (60, 130)

#: Unit families. A concept declares which one it belongs to so a shares figure
#: can never be returned where dollars were asked for.
MONETARY = "monetary"
SHARES = "shares"
PER_SHARE = "per_share"


@dataclass(frozen=True)
class ConceptTag:
    """One rung of a fallback chain.

    Attributes:
        taxonomy: ``us-gaap``, ``dei`` or ``ifrs-full``.
        tag: The XBRL element name.
        caveat: Surfaced in the response only when this rung is the one that
            matched. This is how a deprecated or narrower tag announces itself.
    """

    taxonomy: str
    tag: str
    caveat: str | None = None

    @property
    def qualified(self) -> str:
        """The tag written as ``taxonomy:Tag``."""
        return f"{self.taxonomy}:{self.tag}"


@dataclass(frozen=True)
class ConceptChain:
    """An ordered fallback chain for one plain-English concept.

    Attributes:
        name: The canonical concept name, e.g. ``revenue``.
        label: How to describe it to a human.
        unit_family: Which units are acceptable for this concept.
        tags: The chain, tried in order. First one with usable facts wins.
        instant: True for balance-sheet concepts, which have an ``end`` date
            but no ``start``.
        aliases: Other spellings a user or model might send.
        note: Always attached to the response. Used where the concept is
            genuinely harder than it looks.
    """

    name: str
    label: str
    unit_family: str
    tags: tuple[ConceptTag, ...]
    instant: bool = False
    aliases: tuple[str, ...] = ()
    note: str | None = None


def _chain(
    name: str,
    label: str,
    unit_family: str,
    tags: list[tuple[str, str] | tuple[str, str, str]],
    *,
    instant: bool = False,
    aliases: tuple[str, ...] = (),
    note: str | None = None,
) -> ConceptChain:
    """Build a :class:`ConceptChain` from terse tuples.

    Args:
        name: Canonical concept name.
        label: Human label.
        unit_family: One of :data:`MONETARY`, :data:`SHARES`, :data:`PER_SHARE`.
        tags: ``(taxonomy, tag)`` or ``(taxonomy, tag, caveat)`` tuples.
        instant: True for balance-sheet concepts.
        aliases: Alternative spellings.
        note: A caveat that always applies to this concept.

    Returns:
        The chain.
    """
    return ConceptChain(
        name=name,
        label=label,
        unit_family=unit_family,
        tags=tuple(ConceptTag(*t) for t in tags),  # type: ignore[arg-type]
        instant=instant,
        aliases=aliases,
        note=note,
    )


#: The fallback chains. Order is the whole design; do not sort these.
CONCEPT_CHAINS: dict[str, ConceptChain] = {
    "revenue": _chain(
        "revenue",
        "Total revenue",
        MONETARY,
        [
            ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
            (
                "us-gaap",
                "RevenueFromContractWithCustomerIncludingAssessedTax",
                "This tag includes sales taxes collected from customers, so it "
                "runs slightly higher than the excluding-assessed-tax figure "
                "most filers report. Say so if comparing across companies.",
            ),
            (
                "us-gaap",
                "Revenues",
                "The filer used the generic Revenues tag rather than an "
                "ASC 606 contract-revenue tag. This is usual for filings "
                "before 2018 and for financial firms.",
            ),
            (
                "us-gaap",
                "SalesRevenueNet",
                "SalesRevenueNet was deprecated in the 2018 US-GAAP taxonomy. "
                "This figure comes from an older filing and may not be "
                "comparable with post-2018 revenue for the same company.",
            ),
            (
                "us-gaap",
                "SalesRevenueGoodsNet",
                "This tag covers revenue from goods only and excludes services. "
                "It is a floor, not a total.",
            ),
        ],
        aliases=("revenues", "total revenue", "net sales", "sales", "net revenue", "top line"),
    ),
    "net_income": _chain(
        "net_income",
        "Net income",
        MONETARY,
        [
            ("us-gaap", "NetIncomeLoss"),
            (
                "us-gaap",
                "ProfitLoss",
                "ProfitLoss includes income attributable to non-controlling "
                "interests. It is larger than net income attributable to the "
                "parent when the filer consolidates partly owned subsidiaries.",
            ),
            (
                "us-gaap",
                "NetIncomeLossAvailableToCommonStockholdersBasic",
                "This figure is after preferred dividends, so it is lower than "
                "headline net income for filers with preferred stock.",
            ),
        ],
        aliases=("net earnings", "profit", "earnings", "bottom line", "net profit"),
    ),
    "total_assets": _chain(
        "total_assets",
        "Total assets",
        MONETARY,
        [("us-gaap", "Assets")],
        instant=True,
        aliases=("assets", "balance sheet total"),
    ),
    "total_liabilities": _chain(
        "total_liabilities",
        "Total liabilities",
        MONETARY,
        [("us-gaap", "Liabilities")],
        instant=True,
        aliases=("liabilities", "total debt and liabilities"),
        note=(
            "There is no honest fallback for total liabilities. Some filers "
            "never tag the Liabilities total and only tag its components "
            "(LiabilitiesCurrent, LongTermDebtNoncurrent, and so on). Adding "
            "those up here would double-count for some filers and miss line "
            "items for others, so this tool returns nothing rather than a "
            "derived number. If this concept comes back empty, say the filer "
            "does not tag a liabilities total."
        ),
    ),
    "cash": _chain(
        "cash",
        "Cash and cash equivalents",
        MONETARY,
        [
            ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
            (
                "us-gaap",
                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
                "This figure includes restricted cash, which the analyst cannot "
                "spend. It is higher than unrestricted cash and equivalents.",
            ),
            (
                "us-gaap",
                "CashAndDueFromBanks",
                "A bank-specific tag. Not comparable with a non-financial "
                "company's cash balance.",
            ),
            ("us-gaap", "Cash", "The pre-2018 cash tag; excludes equivalents for some filers."),
        ],
        instant=True,
        aliases=("cash and equivalents", "cash and cash equivalents", "cash on hand"),
        note=(
            "Cash excludes short-term investments and marketable securities. "
            "Companies that hold most of their liquidity in securities will "
            "look much poorer on this concept than they are."
        ),
    ),
    "operating_income": _chain(
        "operating_income",
        "Operating income",
        MONETARY,
        [("us-gaap", "OperatingIncomeLoss")],
        aliases=("operating profit", "income from operations", "ebit"),
        note=(
            "Only OperatingIncomeLoss is used. The obvious fallbacks "
            "(pre-tax income, gross profit) are different quantities, and "
            "substituting one for operating income would be wrong in a way "
            "the reader could not detect. If this comes back empty, the filer "
            "does not report an operating income subtotal."
        ),
    ),
    "rnd_expense": _chain(
        "rnd_expense",
        "Research and development expense",
        MONETARY,
        [
            ("us-gaap", "ResearchAndDevelopmentExpense"),
            (
                "us-gaap",
                "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
                "Excludes in-process R&D acquired in business combinations, so "
                "it runs below the headline R&D line in acquisition years.",
            ),
            (
                "us-gaap",
                "ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost",
                "Software R&D only. Not the company's total R&D.",
            ),
        ],
        aliases=("r&d", "rnd", "research and development", "research expense", "r and d"),
    ),
    "shares_outstanding": _chain(
        "shares_outstanding",
        "Common shares outstanding",
        SHARES,
        [
            (
                "dei",
                "EntityCommonStockSharesOutstanding",
                "This is the cover-page share count, measured a few weeks after "
                "the fiscal period end rather than on the balance sheet date.",
            ),
            ("us-gaap", "CommonStockSharesOutstanding"),
            (
                "us-gaap",
                "CommonStockSharesIssued",
                "Issued shares include shares held in treasury, so this is "
                "higher than shares outstanding for any company that has "
                "bought back stock.",
            ),
            (
                "us-gaap",
                "WeightedAverageNumberOfDilutedSharesOutstanding",
                "A weighted average over the period, including dilutive "
                "instruments. This is the EPS denominator, not a point-in-time "
                "share count.",
            ),
        ],
        instant=True,
        aliases=("shares", "share count", "common shares", "outstanding shares"),
        note=(
            "Multi-class filers (Alphabet, Meta, Berkshire) tag each class "
            "separately. A single number from this concept may be one class "
            "only. Check the matched tag and the value against the cover page."
        ),
    ),
    "gross_profit": _chain(
        "gross_profit",
        "Gross profit",
        MONETARY,
        [("us-gaap", "GrossProfit")],
        aliases=("gross margin dollars", "gross income"),
        note=(
            "Gross profit is a dollar amount, not a margin. To get gross "
            "margin percent, fetch gross_profit and revenue for the same "
            "period and divide, and say in the answer that you computed it."
        ),
    ),
    "cost_of_revenue": _chain(
        "cost_of_revenue",
        "Cost of revenue",
        MONETARY,
        [
            ("us-gaap", "CostOfRevenue"),
            ("us-gaap", "CostOfGoodsAndServicesSold"),
            (
                "us-gaap",
                "CostOfGoodsSold",
                "Goods only; excludes the cost of services revenue.",
            ),
        ],
        aliases=("cogs", "cost of goods sold", "cost of sales"),
    ),
}

#: Alias lookup built once at import.
_ALIAS_INDEX: dict[str, str] = {}
for _chain_obj in CONCEPT_CHAINS.values():
    _ALIAS_INDEX[_chain_obj.name] = _chain_obj.name
    _ALIAS_INDEX[_chain_obj.name.replace("_", " ")] = _chain_obj.name
    for _alias in _chain_obj.aliases:
        _ALIAS_INDEX[_alias] = _chain_obj.name


def list_concepts() -> list[dict[str, Any]]:
    """Describe every supported concept, for the tool description and docs.

    Returns:
        One dict per concept with its name, label, aliases and chain.
    """
    return [
        {
            "concept": chain.name,
            "label": chain.label,
            "aliases": list(chain.aliases),
            "unit_family": chain.unit_family,
            "fallback_chain": [t.qualified for t in chain.tags],
        }
        for chain in CONCEPT_CHAINS.values()
    ]


def resolve_concept(name: str) -> ConceptChain:
    """Map a plain-English concept name onto a chain.

    Args:
        name: What the model asked for, e.g. ``"revenue"`` or ``"R&D"``.

    Returns:
        The matching chain.

    Raises:
        InvalidInputError: If nothing matches. The suggestion lists the
            supported concepts so the model can retry in one turn.
    """
    key = " ".join((name or "").lower().replace("_", " ").split())
    if key in _ALIAS_INDEX:
        return CONCEPT_CHAINS[_ALIAS_INDEX[key]]
    if key.replace(" ", "_") in CONCEPT_CHAINS:
        return CONCEPT_CHAINS[key.replace(" ", "_")]
    raise InvalidInputError(
        f"{name!r} is not a concept this server knows how to resolve.",
        suggestion=(
            "Call this tool again with one of: "
            + ", ".join(sorted(CONCEPT_CHAINS)) + ". "
            "If the user asked for a ratio or a margin, fetch the two "
            "underlying concepts and compute it yourself, saying that you "
            "computed it."
        ),
        details={"supported_concepts": sorted(CONCEPT_CHAINS)},
    )


# --------------------------------------------------------------------------- #
# Fact handling
# --------------------------------------------------------------------------- #


def _parse_date(value: Any) -> date | None:
    """Parse an ISO date from EDGAR, tolerating nulls and junk.

    Args:
        value: A string like ``"2024-01-28"``, or anything else.

    Returns:
        The date, or None if it could not be parsed.
    """
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _duration_days(fact: dict[str, Any]) -> int | None:
    """Length of a fact's period in days.

    Args:
        fact: A raw fact dict from ``companyconcept``.

    Returns:
        Days between start and end, or None for instant facts.
    """
    start, end = _parse_date(fact.get("start")), _parse_date(fact.get("end"))
    if start is None or end is None:
        return None
    return (end - start).days


def _matches_period(fact: dict[str, Any], period: str, *, instant: bool) -> bool:
    """Decide whether a fact belongs to the requested period type.

    Duration facts are classified by how long they run, which is the only
    reliable signal: a 10-K carries both the annual figure and, for some
    filers, quarterly ones. Instant facts have no duration, so they are
    classified by the form they were reported on.

    Args:
        fact: A raw fact dict.
        period: ``"annual"``, ``"quarterly"`` or ``"all"``.
        instant: Whether the concept is a balance-sheet concept.

    Returns:
        True if the fact should be kept.
    """
    if period == "all":
        return True
    days = _duration_days(fact)
    if days is None or instant:
        form = str(fact.get("form", ""))
        if period == "annual":
            return form in ANNUAL_FORMS
        return form in QUARTERLY_FORMS
    lo, hi = ANNUAL_DAYS if period == "annual" else QUARTERLY_DAYS
    return lo <= days <= hi


def _period_key(fact: dict[str, Any]) -> tuple[str, str]:
    """Key that identifies the economic period a fact covers.

    Deliberately *not* ``(fy, fp, form)``: those describe the filing, so the
    same period filed twice under different fiscal years would land in
    different groups and a restatement would go unnoticed. Start and end dates
    identify the period itself.

    Args:
        fact: A raw fact dict.

    Returns:
        A ``(start, end)`` tuple, with an empty start for instant facts.
    """
    return (str(fact.get("start") or ""), str(fact.get("end") or ""))


def _infer_fiscal_year(group: list[dict[str, Any]], period_end: date | None) -> int | None:
    """Work out which fiscal year a period belongs to.

    The first filing to report a period reports it as its own current period,
    so that filing's ``fy`` is the period's fiscal year. Later filings repeat
    the period as a comparative and carry their own, later, ``fy``.

    Args:
        group: Every fact covering one period, in any order.
        period_end: The period's end date, used as a fallback.

    Returns:
        The fiscal year, or None if it cannot be determined.
    """
    annual = [f for f in group if f.get("fp") == "FY" and isinstance(f.get("fy"), int)]
    if annual:
        earliest = min(annual, key=lambda f: str(f.get("filed", "9999-99-99")))
        return int(earliest["fy"])
    dated = [f for f in group if isinstance(f.get("fy"), int) and f.get("filed")]
    if dated:
        return int(min(dated, key=lambda f: str(f["filed"]))["fy"])
    return period_end.year if period_end else None


def _select_unit(units: dict[str, list[dict[str, Any]]], chain: ConceptChain) -> str | None:
    """Choose exactly one unit key and never mix two.

    Args:
        units: The ``units`` object from a ``companyconcept`` response.
        chain: The concept being resolved, which declares its unit family.

    Returns:
        The chosen unit key, or None if no unit matches the family.
    """
    keys = [k for k, v in units.items() if isinstance(v, list) and v]
    if not keys:
        return None

    if chain.unit_family == SHARES:
        preferred = [k for k in keys if k == "shares"]
    elif chain.unit_family == PER_SHARE:
        preferred = [k for k in keys if "/" in k]
    else:
        # Monetary. USD first; otherwise any three-letter currency code, which
        # is how EDGAR spells a foreign-currency filer. "USD/shares" is
        # excluded here so a per-share figure can never stand in for a total.
        preferred = [k for k in keys if k == "USD"] or [
            k for k in keys if len(k) == 3 and k.isalpha() and k.isupper()
        ]

    if not preferred:
        return None
    # Ties broken by fact count: the unit the filer actually uses.
    return max(preferred, key=lambda k: len(units[k]))


def _resolve_group(group: list[dict[str, Any]]) -> dict[str, Any]:
    """Collapse every filing of one period into a single answer.

    Args:
        group: Facts covering one period, from one tag and one unit.

    Returns:
        A dict describing the current value plus its restatement history.
    """
    ordered = sorted(
        group,
        key=lambda f: (str(f.get("filed", "")), str(f.get("accn", ""))),
        reverse=True,
    )
    current = ordered[0]
    distinct = {f.get("val") for f in ordered}

    prior: dict[str, Any] | None = None
    for fact in ordered[1:]:
        if fact.get("val") != current.get("val"):
            prior = fact
            break

    end = _parse_date(current.get("end"))
    record: dict[str, Any] = {
        "value": current.get("val"),
        "fy": _infer_fiscal_year(group, end),
        "fp": current.get("fp"),
        "start": current.get("start"),
        "end": current.get("end"),
        "filed": current.get("filed"),
        "form": current.get("form"),
        "accession_number": current.get("accn"),
        "frame": current.get("frame"),
        "reported_in_fy": current.get("fy"),
        "reported_in_fp": current.get("fp"),
        "filings_reporting_this_period": len(ordered),
        "restated": prior is not None,
    }
    if prior is not None:
        record["prior_value"] = prior.get("val")
        record["prior_filed"] = prior.get("filed")
        record["prior_form"] = prior.get("form")
        try:
            delta = float(current.get("val", 0)) - float(prior.get("val", 0))
            record["restatement_delta"] = delta
            if prior.get("val"):
                record["restatement_delta_pct"] = round(
                    100.0 * delta / abs(float(prior["val"])), 4
                )
        except (TypeError, ValueError, ZeroDivisionError):
            pass
        record["restatement_note"] = (
            f"This period was first reported as {prior.get('val')} on "
            f"{prior.get('filed')} in a {prior.get('form')} and now reads "
            f"{current.get('val')} as of the {current.get('form')} filed "
            f"{current.get('filed')}. Mention both figures in your answer."
        )
    if len(distinct) > 2:
        record["revision_count"] = len(distinct)
    return record


def _extract_series(
    payload: dict[str, Any],
    chain: ConceptChain,
    period: str,
) -> tuple[list[dict[str, Any]], str | None, list[str]]:
    """Turn one ``companyconcept`` payload into a clean time series.

    Args:
        payload: The raw response.
        chain: The concept chain being resolved.
        period: ``"annual"``, ``"quarterly"`` or ``"all"``.

    Returns:
        A tuple of (series newest first, chosen unit, units available).
    """
    units = payload.get("units") or {}
    if not isinstance(units, dict):
        return [], None, []
    available = sorted(k for k, v in units.items() if isinstance(v, list) and v)

    unit = _select_unit(units, chain)
    if unit is None:
        return [], None, available

    facts = [
        f
        for f in units[unit]
        if isinstance(f, dict)
        and f.get("val") is not None
        and _matches_period(f, period, instant=chain.instant)
    ]
    if not facts:
        return [], unit, available

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for fact in facts:
        groups.setdefault(_period_key(fact), []).append(fact)

    series = [_resolve_group(g) for g in groups.values()]
    series.sort(key=lambda r: (str(r.get("end") or ""), str(r.get("start") or "")), reverse=True)
    return series, unit, available


# --------------------------------------------------------------------------- #
# The public entry point
# --------------------------------------------------------------------------- #


async def get_financial_concept(
    cik: str | int,
    concept: str,
    *,
    period: str = "annual",
    fiscal_year: int | None = None,
    limit: int = 8,
    client: SECClient | None = None,
    company_label: str | None = None,
) -> dict[str, Any]:
    """Fetch one financial concept as a time series, walking the fallback chain.

    Args:
        cik: The company's CIK, in any spelling.
        concept: A plain-English concept name such as ``"revenue"``.
        period: ``"annual"``, ``"quarterly"`` or ``"all"``.
        fiscal_year: Keep only this fiscal year, if given.
        limit: Maximum periods to return, newest first.
        client: The HTTP client. Defaults to the process-wide one.
        company_label: Company name for the response, if already known.

    Returns:
        A dict carrying ``matched_tag``, ``tags_tried``, ``unit`` and a
        ``values`` list. ``matched_tag`` is None and ``values`` is empty when
        no tag in the chain produced usable data; that case also carries
        ``error`` and ``suggestion``.

    Raises:
        InvalidInputError: If the concept or period is not recognised.
        SECError: If EDGAR fails in a way that is not a plain 404.
    """
    if period not in {"annual", "quarterly", "all"}:
        raise InvalidInputError(
            f"period must be 'annual', 'quarterly' or 'all', not {period!r}.",
            suggestion="Call this tool again with period='annual'.",
        )

    chain = resolve_concept(concept)
    padded = pad_cik(cik)
    http = client or get_client()

    tags_tried: list[dict[str, Any]] = []
    matched: ConceptTag | None = None
    series: list[dict[str, Any]] = []
    unit: str | None = None
    units_available: list[str] = []
    entity_name = company_label

    for candidate in chain.tags:
        try:
            payload = await http.company_concept(padded, candidate.taxonomy, candidate.tag)
        except NotFoundError:
            tags_tried.append(
                {"tag": candidate.qualified, "result": "not_reported_by_this_filer"}
            )
            continue
        except SECError:
            tags_tried.append({"tag": candidate.qualified, "result": "fetch_failed"})
            raise

        entity_name = entity_name or payload.get("entityName")
        candidate_series, candidate_unit, candidate_units = _extract_series(
            payload, chain, period
        )
        if not candidate_series:
            tags_tried.append(
                {
                    "tag": candidate.qualified,
                    "result": "reported_but_no_matching_periods",
                    "units_available": candidate_units,
                }
            )
            continue

        matched = candidate
        series = candidate_series
        unit = candidate_unit
        units_available = candidate_units
        tags_tried.append(
            {
                "tag": candidate.qualified,
                "result": "matched",
                "periods_found": len(candidate_series),
            }
        )
        break

    response: dict[str, Any] = {
        "cik": str(int(padded)),
        "company": entity_name,
        "concept": chain.name,
        "concept_label": chain.label,
        "matched_tag": matched.qualified if matched else None,
        "tags_tried": tags_tried,
        "fallback_chain": [t.qualified for t in chain.tags],
        "period": period,
        "unit": unit,
        "units_available": units_available,
    }

    notes: list[str] = []
    if chain.note:
        notes.append(chain.note)
    if matched is not None and matched.caveat:
        notes.append(matched.caveat)
    if matched is not None and matched is not chain.tags[0]:
        notes.append(
            f"The preferred tag for {chain.name} is {chain.tags[0].qualified}. "
            f"This filer does not report it, so the figure comes from "
            f"{matched.qualified} instead. Name the tag in your answer."
        )
    if unit is not None and unit != "USD" and chain.unit_family == MONETARY:
        notes.append(
            f"This company reports in {unit}, not US dollars. Do not compare "
            f"the figure with a USD figure without converting it, and say "
            f"which currency it is in."
        )
    if len(units_available) > 1:
        notes.append(
            f"EDGAR returned several units for this tag ({', '.join(units_available)}). "
            f"Only {unit} was used. No values were mixed across units."
        )

    if matched is None:
        response["values"] = []
        response["error"] = (
            f"No tag in the {chain.name} fallback chain returned usable data "
            f"for CIK {int(padded)}."
        )
        response["suggestion"] = (
            "This filer does not tag this concept, or does not tag it for the "
            "requested period type. Try period='all' to see every period the "
            "filer does report, or call list_filings to check that the company "
            "files with the SEC at all. Do not estimate the number."
        )
        response["notes"] = notes
        return response

    if fiscal_year is not None:
        series = [r for r in series if r.get("fy") == fiscal_year]
        if not series:
            response["values"] = []
            response["error"] = (
                f"{chain.label} is reported for this company, but not for "
                f"fiscal year {fiscal_year}."
            )
            response["suggestion"] = (
                "Call this tool again without fiscal_year to see which periods "
                "are available, then tell the user which years you can cover. "
                "Note that the fiscal year label follows the company's own "
                "fiscal calendar, which may not match the calendar year."
            )
            response["notes"] = notes
            return response

    restated = [r for r in series[:limit] if r.get("restated")]
    if restated:
        notes.append(
            f"{len(restated)} of the returned periods were reported with a "
            f"different value in an earlier filing. Each carries "
            f"restated: true with prior_value and prior_filed. Mention the "
            f"restatement in your answer; do not quietly use the new number."
        )

    response["values"] = series[:limit]
    response["periods_returned"] = len(series[:limit])
    response["periods_available"] = len(series)
    response["notes"] = notes
    return response
