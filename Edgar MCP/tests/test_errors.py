"""The error contract: every tool returns a dict, no tool ever raises.

If one tool raises, the agent loop sees an unstructured protocol error, the
model gets nothing it can act on, and the honest-refusal behaviour the eval set
measures stops working. So this is asserted for all six tools, against a client
whose every request fails.
"""

from __future__ import annotations

import asyncio

import pytest

from edgar_mcp import client as client_module
from edgar_mcp import server
from edgar_mcp.client import SECClient
from edgar_mcp.errors import (
    REQUIRED_ERROR_KEYS,
    AmbiguityError,
    InvalidInputError,
    NotFoundError,
    RateLimitError,
    SECError,
    UpstreamUnavailableError,
    error_response,
    is_error,
    tool_error_boundary,
)


def assert_error_shape(payload: object) -> None:
    """Assert a value satisfies the structured-error contract.

    Args:
        payload: A tool return value.
    """
    assert isinstance(payload, dict), f"tool returned {type(payload).__name__}, not a dict"
    for key in REQUIRED_ERROR_KEYS:
        assert key in payload, f"{key} missing from error response"
        assert isinstance(payload[key], str) and payload[key].strip()


# --------------------------------------------------------------------------- #
# The primitives
# --------------------------------------------------------------------------- #


def test_error_response_has_both_required_keys() -> None:
    payload = error_response("It broke.", "Try the other tool.")
    assert payload == {"error": "It broke.", "suggestion": "Try the other tool."}


def test_error_response_drops_empty_extras() -> None:
    payload = error_response("It broke.", "Try again.", status_code=None, candidates=[])
    assert "status_code" not in payload
    assert payload["candidates"] == []


def test_is_error_only_matches_structured_failures() -> None:
    assert is_error({"error": "x", "suggestion": "y"}) is True
    assert is_error({"values": []}) is False
    assert is_error("error") is False
    assert is_error(None) is False


@pytest.mark.parametrize(
    "exc_class",
    [SECError, NotFoundError, RateLimitError, UpstreamUnavailableError, InvalidInputError,
     AmbiguityError],
)
def test_every_exception_type_has_a_usable_default_suggestion(exc_class: type) -> None:
    exc = exc_class("something went wrong")
    payload = exc.to_response()
    assert_error_shape(payload)
    # A suggestion the model cannot act on is worse than none, so it must be a
    # sentence, not a stub.
    assert len(payload["suggestion"].split()) >= 6


def test_a_custom_suggestion_overrides_the_default() -> None:
    exc = NotFoundError("gone", suggestion="Call resolve_company with a ticker symbol.")
    assert exc.to_response()["suggestion"] == "Call resolve_company with a ticker symbol."


def test_boundary_converts_a_sec_error() -> None:
    @tool_error_boundary
    async def failing_tool() -> dict:
        raise RateLimitError("throttled")

    assert_error_shape(asyncio.run(failing_tool()))


def test_boundary_converts_an_unexpected_exception() -> None:
    @tool_error_boundary
    async def buggy_tool() -> dict:
        return {"value": {}["missing"]}

    payload = asyncio.run(buggy_tool())
    assert_error_shape(payload)
    assert "buggy_tool" in payload["error"]
    assert payload["tool"] == "buggy_tool"
    assert "memory" in payload["suggestion"].lower()


def test_boundary_passes_successful_results_through_untouched() -> None:
    @tool_error_boundary
    async def good_tool() -> dict:
        return {"value": 1}

    assert asyncio.run(good_tool()) == {"value": 1}


# --------------------------------------------------------------------------- #
# The six tools
# --------------------------------------------------------------------------- #


def test_the_server_exposes_exactly_six_tools() -> None:
    tools = asyncio.run(server.mcp.list_tools())
    names = sorted(t.name for t in tools)
    assert names == [
        "compare_companies",
        "get_filing_section",
        "get_financial_concept",
        "list_filings",
        "resolve_company",
        "search_full_text",
    ]


def test_every_tool_has_a_substantial_description() -> None:
    # The docstring is the prompt. A one-line description is a bug.
    for tool in asyncio.run(server.mcp.list_tools()):
        assert tool.description, f"{tool.name} has no description"
        assert len(tool.description.split()) > 60, f"{tool.name} description is too thin"


TOOL_CALLS = [
    ("resolve_company", {"query": "NVDA"}),
    ("list_filings", {"cik": "1045810"}),
    ("get_financial_concept", {"cik": "1045810", "concept": "revenue"}),
    ("compare_companies", {"companies": ["NVDA", "AAPL"], "concept": "revenue"}),
    (
        "get_filing_section",
        {"cik": "1045810", "accession_number": "0001045810-24-000029",
         "section": "risk_factors"},
    ),
    ("search_full_text", {"query": "supply chain"}),
]


@pytest.mark.parametrize(("tool_name", "kwargs"), TOOL_CALLS)
def test_no_tool_raises_when_the_network_is_down(
    tool_name: str, kwargs: dict, offline_client: SECClient
) -> None:
    client_module.set_client(offline_client)
    tool = getattr(server, tool_name)
    payload = asyncio.run(tool(**kwargs))
    assert_error_shape(payload)


@pytest.mark.parametrize(
    ("tool_name", "kwargs"),
    [
        ("get_financial_concept", {"cik": "1045810", "concept": "free cash flow"}),
        ("get_financial_concept", {"cik": "not-a-cik", "concept": "revenue"}),
        ("get_financial_concept", {"cik": "1045810", "concept": "revenue", "period": "yearly"}),
        ("list_filings", {"cik": "1045810", "since": "last Tuesday"}),
        ("get_filing_section", {"cik": "1", "accession_number": "x", "section": "item 99"}),
        ("search_full_text", {"query": ""}),
        ("search_full_text", {"query": "y2k", "date_from": "1998-01-01"}),
        ("compare_companies", {"companies": ["NVDA"], "concept": "revenue"}),
    ],
)
def test_bad_arguments_produce_structured_errors_not_exceptions(
    tool_name: str, kwargs: dict, installed_client: SECClient
) -> None:
    payload = asyncio.run(getattr(server, tool_name)(**kwargs))
    assert_error_shape(payload)


def test_pre_2001_search_refuses_and_explains_why(installed_client: SECClient) -> None:
    payload = asyncio.run(
        server.search_full_text(query="Y2K remediation", date_from="1998-01-01")
    )
    assert_error_shape(payload)
    assert "2001" in payload["error"]
    assert "2001" in payload["suggestion"]


def test_ambiguous_company_resolution_returns_candidates(installed_client: SECClient) -> None:
    payload = asyncio.run(server.resolve_company(query="Aperture"))
    assert payload["resolved"] is False
    assert_error_shape(payload)
    assert len(payload["candidates"]) >= 2
