"""CIK normalisation and company resolution.

The padding tests look trivial. They are not: EDGAR's API paths want
``CIK0000320193`` and its archive paths want ``320193``, and a CIK padded into
the wrong one returns a 404 that is indistinguishable from "this company does
not file". That failure mode is silent and looks like data, which is why it has
its own test file.

The resolution tests pin down the behaviour the eval set actually rewards: an
exact ticker wins outright, and two close name matches produce a refusal rather
than a guess.
"""

from __future__ import annotations

import asyncio

import pytest

from edgar_mcp.client import SECClient
from edgar_mcp.companies import (
    AMBIGUITY_MARGIN,
    normalize_name,
    pad_cik,
    resolve_company,
    score_name,
    unpad_cik,
)
from edgar_mcp.errors import InvalidInputError


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (320193, "0000320193"),
        ("320193", "0000320193"),
        ("0000320193", "0000320193"),
        ("CIK0000320193", "0000320193"),
        ("cik320193", "0000320193"),
        ("  320193  ", "0000320193"),
        (1045810, "0001045810"),
        ("1", "0000000001"),
        ("0000000000000320193", "0000320193"),
        ("1000000000", "1000000000"),
    ],
)
def test_pad_cik_normalises_every_spelling(raw: object, expected: str) -> None:
    assert pad_cik(raw) == expected  # type: ignore[arg-type]
    assert len(pad_cik(raw)) == 10  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0000320193", "320193"),
        (320193, "320193"),
        ("CIK0001045810", "1045810"),
        ("0000000000", "0"),
    ],
)
def test_unpad_cik_strips_leading_zeros(raw: object, expected: str) -> None:
    assert unpad_cik(raw) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["", "   ", "NVDA", "abc", "12a34", "12345678901234567891"])
def test_pad_cik_rejects_things_that_are_not_ciks(bad: str) -> None:
    with pytest.raises(InvalidInputError) as excinfo:
        pad_cik(bad)
    # The exception has to carry a model-actionable suggestion, because a tool
    # will turn it straight into a response the model reads.
    assert excinfo.value.suggestion


def test_pad_and_unpad_round_trip() -> None:
    for value in ("320193", "1045810", "789019", "1318605", "1018724"):
        assert unpad_cik(pad_cik(value)) == value


def test_normalize_name_drops_corporate_suffixes() -> None:
    assert normalize_name("Apple Inc.") == "apple"
    assert normalize_name("NVIDIA CORPORATION") == "nvidia"
    assert normalize_name("Tesla, Inc.") == "tesla"
    # A name made entirely of suffixes must not normalise to nothing.
    assert normalize_name("The Company Inc") != ""


def test_score_name_ranks_exact_above_prefix_above_fuzzy() -> None:
    exact = score_name("Testco Industries", "Testco Industries Inc")
    prefix = score_name("Testco", "Testco Industries Inc")
    fuzzy = score_name("Testco", "Zebra Manufacturing Company")
    assert exact == 1.0
    assert exact > prefix > fuzzy


def test_ticker_match_wins_outright(sec_client: SECClient) -> None:
    result = asyncio.run(resolve_company("TSTC", client=sec_client))
    assert result["resolved"] is True
    assert result["cik"] == "9999901"
    assert result["cik_padded"] == "0009999901"
    assert result["match_type"] == "ticker_exact"
    assert result["confidence"] == 1.0


def test_ticker_match_is_case_insensitive(sec_client: SECClient) -> None:
    result = asyncio.run(resolve_company("tstc", client=sec_client))
    assert result["resolved"] is True
    assert result["ticker"] == "TSTC"


def test_close_names_are_refused_not_guessed(sec_client: SECClient) -> None:
    # "Aperture" sits between Aperture Science Inc and Aperture Holdings Corp.
    result = asyncio.run(resolve_company("Aperture", client=sec_client))
    assert result["resolved"] is False
    assert result["ambiguous"] is True
    assert result["error"]
    assert result["suggestion"]
    assert len(result["candidates"]) >= 2
    assert result["margin"] < AMBIGUITY_MARGIN
    # The refusal must not smuggle a winner out through another key.
    assert "cik" not in result


def test_unambiguous_name_resolves_with_a_caveat(sec_client: SECClient) -> None:
    result = asyncio.run(resolve_company("Zebra Manufacturing", client=sec_client))
    assert result["resolved"] is True
    assert result["ticker"] == "ZZZZ"
    assert result["match_type"] in {"name_exact", "name_fuzzy"}


def test_unknown_company_returns_an_error_not_a_bad_guess(sec_client: SECClient) -> None:
    result = asyncio.run(resolve_company("Stripe Payments Holdings", client=sec_client))
    assert result["resolved"] is False
    assert result["candidates"] == []
    assert "suggestion" in result
    # The suggestion has to point the model at the private-company explanation,
    # not at a retry loop.
    assert "private" in result["suggestion"].lower()


def test_empty_query_raises_an_input_error(sec_client: SECClient) -> None:
    with pytest.raises(InvalidInputError):
        asyncio.run(resolve_company("   ", client=sec_client))
