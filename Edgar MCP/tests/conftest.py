"""Shared test fixtures. The whole suite runs offline.

No test in this repository touches sec.gov. Every HTTP response comes from
``tests/fixtures/``, served through an ``httpx.MockTransport`` that is injected
into the real :class:`~edgar_mcp.client.SECClient`. That means the caching,
retry, rate-limiting and URL-building code under test is the same code that
runs in production — only the socket is replaced.

Every number in the fixtures is invented. See ``tests/fixtures/README.md``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest

from edgar_mcp import client as client_module
from edgar_mcp import companies as companies_module
from edgar_mcp.client import (
    COMPANY_CONCEPT_URL,
    COMPANY_TICKERS_URL,
    FULL_TEXT_SEARCH_URL,
    SUBMISSIONS_URL,
    SECClient,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"

# Fictional CIKs, zero-padded exactly as the API path wants them.
TESTCO = "0009999901"
FALLBACK = "0009999902"
RESTATED = "0009999903"
FOREIGN = "0009999906"


def load_fixture(name: str) -> Any:
    """Read one fixture file.

    Args:
        name: Filename inside ``tests/fixtures``.

    Returns:
        The parsed JSON.
    """
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _concept_url(cik: str, taxonomy: str, tag: str) -> str:
    """Build a companyconcept URL for the route table.

    Args:
        cik: Padded CIK.
        taxonomy: XBRL taxonomy.
        tag: XBRL tag.

    Returns:
        The absolute URL.
    """
    return COMPANY_CONCEPT_URL.format(cik=cik, taxonomy=taxonomy, tag=tag)


#: URL to fixture filename. Anything not in here returns 404, which is exactly
#: what EDGAR does for a tag a filer has never reported — so the fallback-chain
#: tests get a realistic miss for free.
ROUTES: dict[str, str] = {
    COMPANY_TICKERS_URL: "fixture_company_tickers.json",
    SUBMISSIONS_URL.format(cik=TESTCO): "fixture_submissions_testco.json",
    _concept_url(
        TESTCO, "us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"
    ): "fixture_concept_revenue_preferred.json",
    _concept_url(TESTCO, "us-gaap", "NetIncomeLoss"): "fixture_concept_mixed_units.json",
    _concept_url(
        TESTCO, "dei", "EntityCommonStockSharesOutstanding"
    ): "fixture_concept_shares_outstanding.json",
    _concept_url(FALLBACK, "us-gaap", "Revenues"): "fixture_concept_revenues_generic.json",
    _concept_url(
        RESTATED, "us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"
    ): "fixture_concept_revenue_restated.json",
    _concept_url(FOREIGN, "us-gaap", "Revenues"): "fixture_concept_foreign_currency.json",
}

_PADDING = "Padding sentence to push this section past the minimum length. " * 12

#: A deliberately awkward stand-in for filing HTML: the section heading appears
#: once in a table of contents and once at the real section, which is the exact
#: ambiguity get_filing_section has to resolve. Entirely synthetic.
SYNTHETIC_10K_HTML = f"""
<html><head><style>.x{{color:red}}</style></head><body>
<table><tr><td>Item 1A.</td><td>Risk Factors</td><td>14</td></tr>
<tr><td>Item 7.</td><td>Management&#39;s Discussion and Analysis</td><td>31</td></tr></table>
<p>Item 1. Business</p>
<p>Testco Industries Inc is a fictional company that exists only in this test
fixture. It manufactures nothing and sells nothing.</p>
<p>Item 1A. Risk Factors</p>
<p>An investment in our fictional securities involves fictional risk.
{_PADDING}</p>
<p>Item 2. Properties</p>
<p>We lease no property.</p>
</body></html>
"""

DOCUMENT_URL = (
    "https://www.sec.gov/Archives/edgar/data/9999901/000099990125000010/tstc-20241231.htm"
)


def fixture_handler(request: httpx.Request) -> httpx.Response:
    """Serve a fixture for a known URL, 404 for anything else.

    Args:
        request: The outgoing request.

    Returns:
        A 200 with the fixture body, or a 404.
    """
    url = str(request.url)
    if url in ROUTES:
        return httpx.Response(200, json=load_fixture(ROUTES[url]))
    if url == DOCUMENT_URL:
        return httpx.Response(200, text=SYNTHETIC_10K_HTML)
    if url.startswith(FULL_TEXT_SEARCH_URL):
        return httpx.Response(200, json=load_fixture("fixture_full_text_search.json"))
    return httpx.Response(404, json={"error": "not found in fixtures"})


@pytest.fixture(autouse=True)
def _isolate_module_state() -> Iterator[None]:
    """Clear the process-wide client and ticker cache around every test.

    Both are deliberately global in production — one token bucket has to see
    every request — so tests have to reset them or they leak between cases.

    Yields:
        None.
    """
    companies_module.reset_ticker_cache()
    client_module.set_client(None)
    yield
    companies_module.reset_ticker_cache()
    client_module.set_client(None)


@pytest.fixture
def sec_client(tmp_path: Path) -> SECClient:
    """A real SECClient wired to the fixture transport and a temp cache.

    Args:
        tmp_path: pytest's per-test temporary directory.

    Returns:
        The client.
    """
    return SECClient(
        user_agent="Arnav arnavhpd@gmail.com",
        transport=httpx.MockTransport(fixture_handler),
        cache_dir=tmp_path / ".cache",
        requests_per_second=10.0,
        burst=10.0,
    )


@pytest.fixture
def installed_client(sec_client: SECClient) -> SECClient:
    """Install the fixture-backed client as the process-wide one.

    The MCP tool functions in ``server.py`` take no client argument, so the
    only way to test them is to install the client they will reach for.

    Args:
        sec_client: The fixture-backed client.

    Returns:
        The same client, now installed.
    """
    client_module.set_client(sec_client)
    return sec_client


@pytest.fixture
def offline_client(tmp_path: Path) -> SECClient:
    """A client whose every request fails, for testing the error contract.

    Args:
        tmp_path: pytest's per-test temporary directory.

    Returns:
        A client that raises a connection error on every request.
    """

    def always_fails(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated network failure", request=request)

    return SECClient(
        user_agent="Arnav arnavhpd@gmail.com",
        transport=httpx.MockTransport(always_fails),
        cache_dir=tmp_path / ".cache",
        max_retries=0,
        burst=10.0,
    )
