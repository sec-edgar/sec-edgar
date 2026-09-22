#!/usr/bin/env python3
"""Run the gold set through an agent with the EDGAR MCP tools attached.

What it does, in order:

1. Starts ``edgar_mcp.server`` as a subprocess over stdio and asks it for its
   six tools.
2. For every question in ``gold.yaml``, runs an agent loop: model proposes tool
   calls, this harness executes them against the MCP server, feeds results
   back, repeats until the model answers or hits the turn limit.
3. Scores the answer for accuracy, refusal correctness, citation, tool-call
   count, latency and cost.
4. Repeats the whole set ``--runs`` times, because a single run of a
   non-deterministic system is an anecdote.
5. Writes ``results/run-<timestamp>.json`` and regenerates ``results/RESULTS.md``
   with the real numbers. Nobody hand-types a figure into the README.

Providers. ``--provider anthropic`` uses the Anthropic SDK. ``--provider
openai`` talks to any OpenAI-compatible ``/chat/completions`` endpoint, which
covers Groq, Mistral, OpenRouter, Together and a local vLLM. The OpenAI path
uses httpx directly rather than the ``openai`` package, so the dependency list
stays as short as the pinned one in pyproject.toml.

Free tiers. Groq and Mistral free keys have low per-minute request limits and
answer a 429 with a Retry-After header. ``--rpm`` throttles outgoing model
requests and defaults to a deliberately timid 20 for the OpenAI path.

Honesty rules this script follows:

* A question whose ``expected_value`` is still marked ``# VERIFY THIS`` is
  scored, but the results file says how many of them there were, so nobody
  reads the accuracy number as verified.
* Cost is computed from a hand-maintained price table. A model that is not in
  the table reports a null cost rather than a guess.
* Nothing is written to ``RESULTS.md`` except numbers this run measured.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parent
DEFAULT_GOLD = EVAL_DIR / "gold.yaml"
DEFAULT_RESULTS_DIR = EVAL_DIR / "results"

SYSTEM_PROMPT = """You are a research assistant for a junior equity analyst at \
a small fund. You answer questions about US public companies using only the \
EDGAR tools you have been given.

Rules you must follow:

1. Never state a financial figure that did not come from a tool call in this \
conversation. If the tools cannot produce it, say so.
2. Cite every figure: name the form (10-K, 10-Q, 20-F), the fiscal period, and \
the period end date. The analyst has to be able to check you.
3. When a tool returns an "error" key, read its "suggestion" field and follow \
it. Do not fall back on your own knowledge of the company.
4. When a company name is ambiguous, ask which company is meant. Do not pick.
5. When comparing companies, check whether their fiscal years line up and say \
so plainly if they do not.
6. When a figure was restated, give both the current and the prior value with \
their filing dates.
7. Be brief. Two or three sentences and the numbers.
"""

# --------------------------------------------------------------------------- #
# Price table
# --------------------------------------------------------------------------- #

#: USD per million tokens, (input, output). HAND-MAINTAINED — check your
#: provider's current pricing page before quoting a cost figure. A model that
#: is not listed reports cost as null, never as an estimate.
PRICES: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-opus-4-5": (5.00, 25.00),
    "claude-haiku-4-5": (1.00, 5.00),
    # Groq and Mistral free tiers bill nothing, so zero is the true cost, not
    # an estimate. Paid tiers differ; update these if you move off free.
    "llama-3.3-70b-versatile": (0.0, 0.0),
    "moonshotai/kimi-k2-instruct": (0.0, 0.0),
    "mistral-large-latest": (0.0, 0.0),
    "mistral-small-latest": (0.0, 0.0),
    "open-mistral-nemo": (0.0, 0.0),
}


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #


@dataclass
class Question:
    """One gold-set entry.

    Attributes:
        id: Stable identifier.
        question: The text asked verbatim.
        category: lookup, comparison, ambiguous, refusal or restatement.
        expected_behavior: answer, clarify, refuse or disclose_restatement.
        expected_value: The number the answer must contain, or None.
        tolerance_pct: Allowed deviation, in percent.
        must_mention: Substrings the answer must contain.
        must_not_hallucinate: Whether inventing a figure is the failure mode.
        verified: False when expected_value is still a placeholder.
        notes: Free text from the gold file.
    """

    id: str
    question: str
    category: str
    expected_behavior: str
    expected_value: float | None
    tolerance_pct: float | None
    must_mention: list[str]
    must_not_hallucinate: bool
    verified: bool
    notes: str = ""


@dataclass
class Attempt:
    """The outcome of asking one question once.

    Attributes:
        question_id: Which question.
        run: Which repeat, 1-based.
        answer: The model's final text.
        tool_calls: Tool calls made, name and arguments.
        latency_s: Wall-clock seconds for the whole loop.
        input_tokens: Prompt tokens billed.
        output_tokens: Completion tokens billed.
        cost_usd: Cost, or None when the model is not in the price table.
        scores: Per-criterion booleans and derived values.
        error: Set when the attempt failed outright.
    """

    question_id: str
    run: int
    answer: str
    tool_calls: list[dict[str, Any]]
    latency_s: float
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    scores: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


# --------------------------------------------------------------------------- #
# Gold set
# --------------------------------------------------------------------------- #


def load_gold(path: Path) -> tuple[list[Question], dict[str, Any]]:
    """Read and validate the gold set.

    Args:
        path: Path to ``gold.yaml``.

    Returns:
        The questions and the file's ``meta`` block.

    Raises:
        SystemExit: If the file is malformed or a required field is missing.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "questions" not in raw:
        sys.exit(f"{path} has no 'questions' list.")

    # A value is treated as verified only if its line has no VERIFY marker.
    source_lines = path.read_text(encoding="utf-8").splitlines()
    unverified_ids: set[str] = set()
    current_id: str | None = None
    for line in source_lines:
        stripped = line.strip()
        if stripped.startswith("- id:"):
            current_id = stripped.split(":", 1)[1].strip()
        if "VERIFY THIS" in stripped and current_id:
            unverified_ids.add(current_id)

    questions: list[Question] = []
    for entry in raw["questions"]:
        missing = {"id", "question", "category"} - set(entry)
        if missing:
            sys.exit(f"gold entry {entry.get('id', '?')} is missing {sorted(missing)}")
        questions.append(
            Question(
                id=entry["id"],
                question=" ".join(entry["question"].split()),
                category=entry["category"],
                expected_behavior=entry.get("expected_behavior", "answer"),
                expected_value=entry.get("expected_value"),
                tolerance_pct=entry.get("tolerance_pct"),
                must_mention=entry.get("must_mention") or [],
                must_not_hallucinate=bool(entry.get("must_not_hallucinate", True)),
                verified=entry["id"] not in unverified_ids,
                notes=" ".join((entry.get("notes") or "").split()),
            )
        )
    return questions, raw.get("meta", {})


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #

_SCALE = {
    "trillion": 1e12,
    "billion": 1e9,
    "million": 1e6,
    "thousand": 1e3,
    "t": 1e12,
    "b": 1e9,
    "m": 1e6,
    "k": 1e3,
}

_NUMBER = re.compile(
    r"(?<![\w.])\$?\s?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*"
    r"(trillion|billion|million|thousand|[TBMK])?\b",
    re.IGNORECASE,
)

_REFUSAL_MARKERS = (
    "does not file",
    "do not file",
    "not file with the sec",
    "not an sec filer",
    "is private",
    "privately held",
    "not in edgar",
    "not available in edgar",
    "not covered by",
    "cannot provide",
    "can't provide",
    "cannot answer",
    "unable to",
    "i cannot",
    "i can't",
    "no data",
    "not available",
    "does not appear to file",
    "has not been filed",
    "in the future",
    "future period",
    "not something these tools",
    "outside the scope",
    "outside what",
    "not included in edgar",
    "only covers filings from 2001",
    "begins in 2001",
    "starts in 2001",
)

_CLARIFY_MARKERS = (
    "which company",
    "which of these",
    "did you mean",
    "could you clarify",
    "can you clarify",
    "please specify",
    "which margin",
    "ambiguous",
    "more than one",
    "i assumed",
    "i interpreted",
    "i have used",
    "i used",
    "assuming",
)

_FORM_MARKERS = ("10-k", "10-q", "20-f", "40-f", "8-k", "10-kt")


def extract_numbers(text: str) -> list[float]:
    """Pull every plausible figure out of an answer, normalising scale words.

    "$60.9 billion", "60,922 million" and "60922000000" all become the same
    magnitude, so a correct answer written in any of those styles scores.

    Args:
        text: The model's answer.

    Returns:
        Every number found, in whole units.
    """
    values: list[float] = []
    for match in _NUMBER.finditer(text):
        digits = match.group(1).replace(",", "")
        try:
            value = float(digits)
        except ValueError:
            continue
        suffix = (match.group(2) or "").lower()
        if suffix:
            value *= _SCALE.get(suffix, 1.0)
        values.append(value)
    return values


def value_matches(text: str, expected: float, tolerance_pct: float) -> bool:
    """Check whether an answer contains the expected figure.

    Args:
        text: The model's answer.
        expected: The gold value, in whole units.
        tolerance_pct: Allowed deviation in percent.

    Returns:
        True if any number in the answer is within tolerance.
    """
    if expected == 0:
        return 0.0 in extract_numbers(text)
    limit = abs(expected) * tolerance_pct / 100.0
    return any(abs(value - expected) <= limit for value in extract_numbers(text))


def looks_like_refusal(text: str) -> bool:
    """Judge whether an answer declines to give a figure.

    Heuristic, and it is reported as one. It matches on refusal phrasing and
    then requires that the answer is not simultaneously asserting a large
    figure, which is how a hedged-but-still-wrong answer gets caught.

    Args:
        text: The model's answer.

    Returns:
        True if the answer reads as a refusal.
    """
    lowered = text.lower()
    if not any(marker in lowered for marker in _REFUSAL_MARKERS):
        return False
    # A "sorry, but it was $X billion" answer is not a refusal.
    big_numbers = [v for v in extract_numbers(text) if v >= 1e6]
    return not big_numbers


def looks_like_clarification(text: str) -> bool:
    """Judge whether an answer asks for clarification or states its assumption.

    Args:
        text: The model's answer.

    Returns:
        True if the answer either asks which interpretation was meant or names
        the interpretation it chose.
    """
    lowered = text.lower()
    if any(marker in lowered for marker in _CLARIFY_MARKERS):
        return True
    return "?" in text


def has_citation(text: str) -> bool:
    """Judge whether an answer names its source filing and period.

    Args:
        text: The model's answer.

    Returns:
        True if a form type and a period marker both appear.
    """
    lowered = text.lower()
    form = any(marker in lowered for marker in _FORM_MARKERS)
    period = bool(re.search(r"\b(fy|fiscal)\b", lowered)) or bool(
        re.search(r"\b(19|20)\d{2}\b", lowered)
    )
    return form and period


def score_attempt(question: Question, attempt: Attempt) -> None:
    """Score one attempt in place.

    Args:
        question: The gold entry.
        attempt: The attempt to score. Its ``scores`` dict is populated.
    """
    text = attempt.answer or ""
    refused = looks_like_refusal(text)
    should_refuse = question.expected_behavior == "refuse"

    scores: dict[str, Any] = {
        "refused": refused,
        "should_refuse": should_refuse,
        "refusal_correct": refused == should_refuse,
        "cited": has_citation(text),
        "tool_calls": len(attempt.tool_calls),
        "must_mention_hits": [
            phrase for phrase in question.must_mention if phrase.lower() in text.lower()
        ],
        "must_mention_total": len(question.must_mention),
    }
    scores["must_mention_ok"] = len(scores["must_mention_hits"]) == len(question.must_mention)

    if question.expected_value is not None and question.tolerance_pct is not None:
        scores["accuracy_applicable"] = True
        scores["accurate"] = value_matches(
            text, float(question.expected_value), float(question.tolerance_pct)
        )
        scores["numbers_in_answer"] = extract_numbers(text)[:8]
    else:
        scores["accuracy_applicable"] = False
        scores["accurate"] = None

    if question.expected_behavior == "clarify":
        scores["clarified"] = looks_like_clarification(text)
        scores["needs_manual_review"] = True
    elif question.expected_behavior == "disclose_restatement":
        lowered = text.lower()
        scores["disclosed_restatement"] = any(
            word in lowered for word in ("restat", "revised", "unchanged", "first reported")
        )
        scores["needs_manual_review"] = True
    else:
        scores["needs_manual_review"] = False

    if attempt.error:
        scores["errored"] = True
    attempt.scores = scores


# --------------------------------------------------------------------------- #
# Providers
# --------------------------------------------------------------------------- #


class RateLimiter:
    """Spaces outgoing model requests to stay inside a free-tier quota."""

    def __init__(self, requests_per_minute: float) -> None:
        """Configure the limiter.

        Args:
            requests_per_minute: Ceiling. Zero or less disables throttling.
        """
        self.interval = 60.0 / requests_per_minute if requests_per_minute > 0 else 0.0
        self._last = 0.0

    async def wait(self) -> None:
        """Sleep long enough to keep the configured spacing."""
        if self.interval <= 0:
            return
        gap = time.monotonic() - self._last
        if gap < self.interval:
            await asyncio.sleep(self.interval - gap)
        self._last = time.monotonic()


class Provider:
    """Interface every model backend implements."""

    name = "provider"

    def __init__(self, model: str, limiter: RateLimiter, max_tokens: int = 1500) -> None:
        """Store common settings.

        Args:
            model: Model identifier.
            limiter: Outgoing request throttle.
            max_tokens: Response cap.
        """
        self.model = model
        self.limiter = limiter
        self.max_tokens = max_tokens

    def price(self, input_tokens: int, output_tokens: int) -> float | None:
        """Cost this call, or None if the model has no entry in the table.

        Args:
            input_tokens: Prompt tokens.
            output_tokens: Completion tokens.

        Returns:
            Cost in USD, or None when unknown.
        """
        prices = PRICES.get(self.model)
        if prices is None:
            return None
        return input_tokens / 1e6 * prices[0] + output_tokens / 1e6 * prices[1]

    async def run(
        self, question: str, tools: list[dict[str, Any]], call_tool: Any, max_turns: int
    ) -> tuple[str, list[dict[str, Any]], int, int]:
        """Run one agent loop.

        Args:
            question: The user question.
            tools: Tool schemas in this provider's format.
            call_tool: Async callable ``(name, args) -> str``.
            max_turns: Maximum model turns.

        Returns:
            The answer text, the tool calls made, input tokens, output tokens.

        Raises:
            NotImplementedError: Always; subclasses implement this.
        """
        raise NotImplementedError

    async def aclose(self) -> None:
        """Release any held resources."""
        return None


class AnthropicProvider(Provider):
    """Anthropic Messages API with tool use."""

    name = "anthropic"

    def __init__(self, model: str, limiter: RateLimiter, max_tokens: int = 1500) -> None:
        """Create the SDK client.

        Args:
            model: Model identifier.
            limiter: Outgoing request throttle.
            max_tokens: Response cap.

        Raises:
            SystemExit: If the SDK or the API key is missing.
        """
        super().__init__(model, limiter, max_tokens)
        try:
            from anthropic import AsyncAnthropic
        except ImportError:  # pragma: no cover - exercised only without the extra
            sys.exit("pip install 'anthropic==1.4.0' to use --provider anthropic")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY is not set.")
        self._client = AsyncAnthropic(max_retries=4)

    @staticmethod
    def convert_tools(mcp_tools: list[Any]) -> list[dict[str, Any]]:
        """Convert MCP tool definitions to Anthropic's schema.

        Args:
            mcp_tools: Tools from ``session.list_tools()``.

        Returns:
            Anthropic tool definitions.
        """
        return [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            for t in mcp_tools
        ]

    async def run(
        self, question: str, tools: list[dict[str, Any]], call_tool: Any, max_turns: int
    ) -> tuple[str, list[dict[str, Any]], int, int]:
        """Run the Anthropic agent loop.

        Args:
            question: The user question.
            tools: Anthropic tool definitions.
            call_tool: Async callable ``(name, args) -> str``.
            max_turns: Maximum model turns.

        Returns:
            Answer text, tool calls, input tokens, output tokens.
        """
        messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
        made: list[dict[str, Any]] = []
        in_tokens = out_tokens = 0
        answer = ""

        for _ in range(max_turns):
            await self.limiter.wait()
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )
            in_tokens += response.usage.input_tokens
            out_tokens += response.usage.output_tokens

            text = "".join(b.text for b in response.content if b.type == "text")
            if text:
                answer = text
            uses = [b for b in response.content if b.type == "tool_use"]
            if not uses:
                break

            messages.append({"role": "assistant", "content": response.content})
            results = []
            for use in uses:
                made.append({"name": use.name, "arguments": use.input})
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": use.id,
                        "content": await call_tool(use.name, use.input),
                    }
                )
            messages.append({"role": "user", "content": results})

        return answer, made, in_tokens, out_tokens

    async def aclose(self) -> None:
        """Close the SDK client."""
        await self._client.close()


class OpenAICompatProvider(Provider):
    """Any OpenAI-compatible ``/chat/completions`` endpoint.

    Verified shape-wise against Groq, Mistral and OpenRouter, all of which
    implement the same tool-calling schema. Uses httpx directly so the
    ``openai`` package is not a dependency of this repository.
    """

    name = "openai"

    def __init__(
        self,
        model: str,
        limiter: RateLimiter,
        max_tokens: int = 1500,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """Configure the endpoint.

        Args:
            model: Model identifier.
            limiter: Outgoing request throttle.
            max_tokens: Response cap.
            base_url: Endpoint root, e.g. ``https://api.groq.com/openai/v1``.
            api_key: Bearer token.

        Raises:
            SystemExit: If the base URL or key is missing.
        """
        super().__init__(model, limiter, max_tokens)
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "")).rstrip("/")
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.base_url:
            sys.exit("Set OPENAI_BASE_URL (e.g. https://api.groq.com/openai/v1).")
        if not key:
            sys.exit("Set OPENAI_API_KEY.")
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=120.0,
        )

    @staticmethod
    def convert_tools(mcp_tools: list[Any]) -> list[dict[str, Any]]:
        """Convert MCP tool definitions to OpenAI's function schema.

        Args:
            mcp_tools: Tools from ``session.list_tools()``.

        Returns:
            OpenAI tool definitions.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    # Some endpoints truncate long descriptions. The first
                    # paragraph carries the decision-relevant guidance.
                    "description": (t.description or "")[:1024],
                    "parameters": t.inputSchema,
                },
            }
            for t in mcp_tools
        ]

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST to the endpoint, retrying on 429 and 5xx.

        Args:
            payload: The request body.

        Returns:
            The parsed response.

        Raises:
            RuntimeError: If the endpoint keeps failing.
        """
        for attempt in range(12):
            await self.limiter.wait()
            response = await self._http.post("/chat/completions", json=payload)
            if response.status_code == 200:
                return response.json()
            if response.status_code in (429, 500, 502, 503, 529):
                header = response.headers.get("retry-after")
                delay = float(header) if header and header.replace(".", "").isdigit() else 2.0 * (
                    2**attempt
                )
                print(
                    f"    provider returned {response.status_code}; "
                    f"waiting {delay:.1f}s",
                    file=sys.stderr,
                )
                await asyncio.sleep(min(delay, 120.0))
                continue
            raise RuntimeError(f"{response.status_code}: {response.text[:400]}")
        raise RuntimeError("provider kept failing after 12 attempts")

    async def run(
        self, question: str, tools: list[dict[str, Any]], call_tool: Any, max_turns: int
    ) -> tuple[str, list[dict[str, Any]], int, int]:
        """Run the OpenAI-compatible agent loop.

        Args:
            question: The user question.
            tools: OpenAI tool definitions.
            call_tool: Async callable ``(name, args) -> str``.
            max_turns: Maximum model turns.

        Returns:
            Answer text, tool calls, input tokens, output tokens.
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        made: list[dict[str, Any]] = []
        in_tokens = out_tokens = 0
        answer = ""

        for _ in range(max_turns):
            data = await self._post(
                {
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "max_tokens": self.max_tokens,
                    "temperature": 0,
                }
            )
            usage = data.get("usage") or {}
            in_tokens += int(usage.get("prompt_tokens", 0))
            out_tokens += int(usage.get("completion_tokens", 0))

            message = (data.get("choices") or [{}])[0].get("message") or {}
            if message.get("content"):
                answer = message["content"]
            calls = message.get("tool_calls") or []
            if not calls:
                break

            messages.append(message)
            for call in calls:
                function = call.get("function") or {}
                name = function.get("name", "")
                try:
                    args = json.loads(function.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                made.append({"name": name, "arguments": args})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "name": name,
                        "content": await call_tool(name, args),
                    }
                )

        return answer, made, in_tokens, out_tokens

    async def aclose(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile.

    Args:
        values: The sample.
        pct: Percentile between 0 and 100.

    Returns:
        The percentile, or 0.0 for an empty sample.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round(pct / 100.0 * len(ordered) + 0.5)) - 1))
    return ordered[index]


def mean(values: list[float]) -> float:
    """Arithmetic mean, 0.0 for an empty list.

    Args:
        values: The sample.

    Returns:
        The mean.
    """
    return statistics.fmean(values) if values else 0.0


def stdev(values: list[float]) -> float:
    """Sample standard deviation, 0.0 when there are fewer than two points.

    Args:
        values: The sample.

    Returns:
        The standard deviation.
    """
    return statistics.stdev(values) if len(values) > 1 else 0.0


def summarise_run(attempts: list[Attempt]) -> dict[str, float]:
    """Compute one run's headline metrics.

    Args:
        attempts: Every attempt in one pass over the gold set.

    Returns:
        A dict of metric name to value.
    """
    scorable = [a for a in attempts if a.scores.get("accuracy_applicable")]
    latencies = [a.latency_s for a in attempts]
    costs = [a.cost_usd for a in attempts if a.cost_usd is not None]
    return {
        "accuracy_pct": 100.0
        * mean([1.0 if a.scores.get("accurate") else 0.0 for a in scorable]),
        "refusal_correct_pct": 100.0
        * mean([1.0 if a.scores.get("refusal_correct") else 0.0 for a in attempts]),
        "citation_pct": 100.0 * mean([1.0 if a.scores.get("cited") else 0.0 for a in attempts]),
        "must_mention_pct": 100.0
        * mean([1.0 if a.scores.get("must_mention_ok") else 0.0 for a in attempts]),
        "tool_calls_mean": mean([float(a.scores.get("tool_calls", 0)) for a in attempts]),
        "latency_p50_s": percentile(latencies, 50),
        "latency_p95_s": percentile(latencies, 95),
        "cost_usd_total": sum(costs) if costs else 0.0,
        "errors": float(sum(1 for a in attempts if a.error)),
    }


def aggregate(runs: list[list[Attempt]]) -> dict[str, Any]:
    """Combine every run into means, standard deviations and per-question rates.

    Args:
        runs: One list of attempts per run.

    Returns:
        The full summary written to the JSON and Markdown outputs.
    """
    per_run = [summarise_run(r) for r in runs]
    metrics = {
        key: {
            "mean": mean([r[key] for r in per_run]),
            "stdev": stdev([r[key] for r in per_run]),
            "runs": [r[key] for r in per_run],
        }
        for key in per_run[0]
    } if per_run else {}

    by_question: dict[str, dict[str, Any]] = {}
    for run in runs:
        for attempt in run:
            entry = by_question.setdefault(
                attempt.question_id,
                {
                    "passes": 0,
                    "attempts": 0,
                    "accuracy_applicable": attempt.scores.get("accuracy_applicable", False),
                    "tool_calls": [],
                    "latencies": [],
                    "answers": [],
                    "needs_manual_review": attempt.scores.get("needs_manual_review", False),
                },
            )
            entry["attempts"] += 1
            entry["tool_calls"].append(attempt.scores.get("tool_calls", 0))
            entry["latencies"].append(attempt.latency_s)
            entry["answers"].append(attempt.answer[:400])
            if _attempt_passed(attempt):
                entry["passes"] += 1

    for entry in by_question.values():
        entry["pass_rate"] = entry["passes"] / entry["attempts"] if entry["attempts"] else 0.0
        entry["tool_calls_mean"] = mean([float(v) for v in entry["tool_calls"]])
        entry["latency_mean_s"] = mean(entry["latencies"])

    by_category: dict[str, dict[str, float]] = {}
    return {
        "metrics": metrics,
        "per_run": per_run,
        "by_question": by_question,
        "by_category": by_category,
    }


def _attempt_passed(attempt: Attempt) -> bool:
    """Decide whether one attempt counts as correct overall.

    Args:
        attempt: The scored attempt.

    Returns:
        True if the attempt met the criteria that apply to its question.
    """
    scores = attempt.scores
    if attempt.error:
        return False
    if not scores.get("refusal_correct", False):
        return False
    if scores.get("accuracy_applicable") and not scores.get("accurate"):
        return False
    if "clarified" in scores and not scores["clarified"]:
        return False
    if "disclosed_restatement" in scores and not scores["disclosed_restatement"]:
        return False
    return bool(scores.get("must_mention_ok", True))


def add_category_rollup(summary: dict[str, Any], questions: list[Question]) -> None:
    """Add a per-category pass-rate rollup to the summary, in place.

    Args:
        summary: The aggregate summary.
        questions: The gold set, for the category of each question.
    """
    lookup = {q.id: q.category for q in questions}
    buckets: dict[str, list[float]] = {}
    for qid, entry in summary["by_question"].items():
        buckets.setdefault(lookup.get(qid, "unknown"), []).append(entry["pass_rate"])
    summary["by_category"] = {
        category: {"pass_rate_pct": 100.0 * mean(rates), "questions": len(rates)}
        for category, rates in sorted(buckets.items())
    }


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def write_results_md(
    path: Path,
    summary: dict[str, Any],
    questions: list[Question],
    config: dict[str, Any],
) -> None:
    """Write ``RESULTS.md`` from measured numbers only.

    Args:
        path: Where to write.
        summary: The aggregate summary.
        questions: The gold set.
        config: Run configuration, echoed into the header.
    """
    metrics = summary["metrics"]
    lookup = {q.id: q for q in questions}
    unverified = [q.id for q in questions if not q.verified and q.expected_value is not None]

    def row(label: str, key: str, unit: str = "", digits: int = 1) -> str:
        entry = metrics.get(key)
        if entry is None:
            return f"| {label} | not measured | | |"
        runs = ", ".join(f"{v:.{digits}f}" for v in entry["runs"])
        return (
            f"| {label} | {entry['mean']:.{digits}f}{unit} | "
            f"±{entry['stdev']:.{digits}f} | {runs} |"
        )

    lines = [
        "# Eval results",
        "",
        f"Generated by `evals/run_eval.py` on {config['finished_at']}.",
        "Every number below was measured by that run. Nothing here is typed by hand.",
        "",
        "## Run configuration",
        "",
        "| Setting | Value |",
        "|---|---|",
        f"| Provider | `{config['provider']}` |",
        f"| Model | `{config['model']}` |",
        f"| Questions | {config['question_count']} |",
        f"| Runs per question | {config['runs']} |",
        f"| Total attempts | {config['attempts']} |",
        f"| Server cache | {'disabled' if config['no_cache'] else 'enabled'} |",
        f"| Max turns per question | {config['max_turns']} |",
        "",
        "## Headline metrics",
        "",
        "Mean across runs, with the standard deviation across runs and the",
        "individual run values. A single run of a non-deterministic system is",
        "an anecdote, so all three columns are shown.",
        "",
        "| Metric | Mean | Std dev | Per run |",
        "|---|---|---|---|",
        row("Accuracy (numeric answers within tolerance)", "accuracy_pct", "%"),
        row("Refusal correctness", "refusal_correct_pct", "%"),
        row("Citation rate (names form and period)", "citation_pct", "%"),
        row("Required-phrase coverage", "must_mention_pct", "%"),
        row("Tool calls per question", "tool_calls_mean", "", 2),
        row("Latency p50 (s)", "latency_p50_s", "", 1),
        row("Latency p95 (s)", "latency_p95_s", "", 1),
        row("Cost per run (USD)", "cost_usd_total", "", 4),
        row("Errored attempts", "errors", "", 0),
        "",
    ]

    if unverified:
        lines += [
            "> **The accuracy number above is not trustworthy yet.** "
            f"{len(unverified)} of the questions with an expected value still "
            "carry an unverified placeholder in `gold.yaml` "
            f"(`{'`, `'.join(unverified)}`). Verify them against EDGAR and "
            "re-run before quoting accuracy anywhere.",
            "",
        ]

    lines += [
        "## Pass rate by category",
        "",
        "| Category | Questions | Pass rate |",
        "|---|---|---|",
    ]
    for category, entry in summary["by_category"].items():
        lines.append(
            f"| {category} | {entry['questions']} | {entry['pass_rate_pct']:.0f}% |"
        )

    lines += [
        "",
        "## Per question",
        "",
        "A pass requires the refusal decision to be right, the numeric answer",
        "to be within tolerance where one applies, and every required phrase",
        "to appear. Rows marked for review are scored by keyword and need a",
        "human to confirm.",
        "",
        "| ID | Category | Pass rate | Tool calls | Latency (s) | Review |",
        "|---|---|---|---|---|---|",
    ]
    for qid, entry in sorted(
        summary["by_question"].items(), key=lambda kv: kv[1]["pass_rate"]
    ):
        question = lookup.get(qid)
        lines.append(
            f"| `{qid}` | {question.category if question else '?'} | "
            f"{100 * entry['pass_rate']:.0f}% | {entry['tool_calls_mean']:.1f} | "
            f"{entry['latency_mean_s']:.1f} | "
            f"{'yes' if entry['needs_manual_review'] else ''} |"
        )

    failures = [
        (qid, entry)
        for qid, entry in summary["by_question"].items()
        if entry["pass_rate"] < 1.0
    ]
    lines += ["", "## Failures", ""]
    if not failures:
        lines.append("No question failed on any run.")
    else:
        lines.append(
            f"{len(failures)} of {len(summary['by_question'])} questions failed at "
            "least one run. Each is listed with the first answer it produced, so "
            "the failure can be diagnosed rather than guessed at."
        )
        lines.append("")
        for qid, entry in sorted(failures, key=lambda kv: kv[1]["pass_rate"]):
            question = lookup.get(qid)
            lines += [
                f"### `{qid}` — {100 * entry['pass_rate']:.0f}% pass rate",
                "",
                f"**Question.** {question.question if question else ''}",
                "",
                f"**What it tests.** {question.notes if question else ''}",
                "",
                "**First answer.**",
                "",
                "```",
                entry["answers"][0] if entry["answers"] else "(no answer)",
                "```",
                "",
            ]

    lines += [
        "## How to read this",
        "",
        "* Accuracy counts only questions with a numeric expected value.",
        "  Comparison, ambiguity and refusal questions are scored on behaviour.",
        "* Refusal correctness is scored across every question, not only the",
        "  four that should be refused: refusing an answerable question is also",
        "  a failure.",
        "* Refusal, clarification and citation are detected by keyword. The",
        "  detector is in `run_eval.py` and can be read. Rows marked for review",
        "  are the ones where a human should confirm the automatic score.",
        "* Cost is computed from the hand-maintained price table in",
        "  `run_eval.py`. A model missing from that table reports zero.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def build_provider(args: argparse.Namespace) -> Provider:
    """Construct the provider named on the command line.

    Args:
        args: Parsed arguments.

    Returns:
        A ready provider.
    """
    limiter = RateLimiter(args.rpm)
    if args.provider == "anthropic":
        return AnthropicProvider(args.model, limiter, args.max_tokens)
    return OpenAICompatProvider(args.model, limiter, args.max_tokens)


async def run_eval(args: argparse.Namespace) -> int:
    """Run the whole evaluation.

    Args:
        args: Parsed arguments.

    Returns:
        A process exit code.
    """
    questions, meta = load_gold(Path(args.gold))
    if args.only:
        wanted = set(args.only.split(","))
        questions = [q for q in questions if q.id in wanted or q.category in wanted]
    if args.limit:
        questions = questions[: args.limit]
    if not questions:
        sys.exit("No questions selected.")

    provider = build_provider(args)
    server_args = ["-m", "edgar_mcp.server"]
    if args.no_cache:
        server_args.append("--no-cache")

    env = dict(os.environ)
    env.setdefault("PYTHONPATH", str(REPO_ROOT / "src"))
    env.setdefault("EDGAR_MCP_USER_AGENT", "Arnav arnavhpd@gmail.com")

    params = StdioServerParameters(command=sys.executable, args=server_args, env=env)

    runs: list[list[Attempt]] = []
    spend = 0.0
    halted = False
    started_at = datetime.now(timezone.utc)

    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        listing = await session.list_tools()
        print(
            f"MCP server exposes {len(listing.tools)} tools: "
            f"{', '.join(t.name for t in listing.tools)}",
            file=sys.stderr,
        )
        tools = type(provider).convert_tools(listing.tools)  # type: ignore[attr-defined]

        async def call_tool(name: str, arguments: dict[str, Any]) -> str:
            """Execute one MCP tool call and return its text payload.

            Args:
                name: Tool name.
                arguments: Tool arguments.

            Returns:
                The tool result as text the model can read.
            """
            try:
                result = await session.call_tool(name, arguments)
            except Exception as exc:  # noqa: BLE001 - surfaced to the model
                return json.dumps(
                    {"error": f"tool transport failure: {exc}", "suggestion": "Try another tool."}
                )
            parts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
            return "\n".join(parts) if parts else json.dumps(result.structuredContent or {})

        for run_index in range(1, args.runs + 1):
            attempts: list[Attempt] = []
            for position, question in enumerate(questions, start=1):
                if args.max_cost and spend >= args.max_cost:
                    print(
                        f"HALTED: spend ${spend:.4f} reached --max-cost "
                        f"${args.max_cost:.4f}",
                        file=sys.stderr,
                    )
                    halted = True
                    break

                print(
                    f"[run {run_index}/{args.runs}] "
                    f"[{position}/{len(questions)}] {question.id}",
                    file=sys.stderr,
                )
                started = time.monotonic()
                error: str | None = None
                answer, calls, in_tok, out_tok = "", [], 0, 0
                try:
                    answer, calls, in_tok, out_tok = await provider.run(
                        question.question, tools, call_tool, args.max_turns
                    )
                except Exception as exc:  # noqa: BLE001 - recorded, never fatal
                    error = f"{type(exc).__name__}: {exc}"
                    print(f"    attempt failed: {error}", file=sys.stderr)

                cost = provider.price(in_tok, out_tok)
                if cost:
                    spend += cost
                attempt = Attempt(
                    question_id=question.id,
                    run=run_index,
                    answer=answer,
                    tool_calls=calls,
                    latency_s=time.monotonic() - started,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost_usd=cost,
                    error=error,
                )
                score_attempt(question, attempt)
                attempts.append(attempt)
            runs.append(attempts)
            if halted:
                break

    await provider.aclose()

    if not any(runs):
        sys.exit("No attempts completed; nothing to report.")

    summary = aggregate([r for r in runs if r])
    add_category_rollup(summary, questions)

    finished_at = datetime.now(timezone.utc)
    config = {
        "provider": provider.name,
        "model": args.model,
        "runs": len(runs),
        "question_count": len(questions),
        "attempts": sum(len(r) for r in runs),
        "no_cache": args.no_cache,
        "max_turns": args.max_turns,
        "max_cost_usd": args.max_cost,
        "halted_on_cost": halted,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": finished_at.isoformat(timespec="seconds"),
        "gold_meta": meta,
        "unverified_expected_values": [
            q.id for q in questions if not q.verified and q.expected_value is not None
        ],
    }

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = finished_at.strftime("%Y%m%dT%H%M%SZ")
    json_path = results_dir / f"run-{stamp}.json"
    json_path.write_text(
        json.dumps(
            {
                "config": config,
                "summary": summary,
                "attempts": [
                    {
                        "question_id": a.question_id,
                        "run": a.run,
                        "answer": a.answer,
                        "tool_calls": a.tool_calls,
                        "latency_s": round(a.latency_s, 3),
                        "input_tokens": a.input_tokens,
                        "output_tokens": a.output_tokens,
                        "cost_usd": a.cost_usd,
                        "scores": a.scores,
                        "error": a.error,
                    }
                    for run in runs
                    for a in run
                ],
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    write_results_md(results_dir / "RESULTS.md", summary, questions, config)

    print(f"\nWrote {json_path}", file=sys.stderr)
    print(f"Wrote {results_dir / 'RESULTS.md'}", file=sys.stderr)
    metrics = summary["metrics"]
    for key in ("accuracy_pct", "refusal_correct_pct", "citation_pct", "tool_calls_mean"):
        entry = metrics.get(key)
        if entry:
            print(f"  {key}: {entry['mean']:.1f} (sd {entry['stdev']:.1f})", file=sys.stderr)
    print(f"  total spend: ${spend:.4f}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        The parser.
    """
    parser = argparse.ArgumentParser(
        description="Run the EDGAR MCP gold set through an agent and score it."
    )
    parser.add_argument("--gold", default=str(DEFAULT_GOLD), help="Path to gold.yaml.")
    parser.add_argument(
        "--results-dir", default=str(DEFAULT_RESULTS_DIR), help="Where to write results."
    )
    parser.add_argument(
        "--provider",
        default=os.environ.get("EVAL_PROVIDER", "anthropic"),
        choices=["anthropic", "openai"],
        help="anthropic, or openai for any OpenAI-compatible endpoint.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("EVAL_MODEL", "claude-sonnet-4-5"),
        help="Model identifier for the chosen provider.",
    )
    parser.add_argument(
        "--runs", type=int, default=3, help="Passes over the gold set. Default 3."
    )
    parser.add_argument(
        "--max-turns", type=int, default=8, help="Model turns per question. Default 8."
    )
    parser.add_argument(
        "--max-tokens", type=int, default=1500, help="Response token cap. Default 1500."
    )
    parser.add_argument(
        "--rpm",
        type=float,
        default=None,
        help="Model requests per minute. Defaults to 50 for Anthropic and 20 "
        "for OpenAI-compatible endpoints, which suits Groq and Mistral free "
        "tiers.",
    )
    parser.add_argument(
        "--max-cost",
        type=float,
        default=5.0,
        help="Halt when estimated spend reaches this many USD. Default 5.",
    )
    parser.add_argument(
        "--only", default=None, help="Comma-separated question ids or categories."
    )
    parser.add_argument("--limit", type=int, default=None, help="Use only the first N questions.")
    parser.add_argument(
        "--no-cache", action="store_true", help="Run the MCP server with its cache disabled."
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Load and check gold.yaml, print the distribution, and exit. "
        "Needs no API key and no network.",
    )
    return parser


def validate(path: Path) -> int:
    """Check the gold file and print its distribution.

    Args:
        path: Path to ``gold.yaml``.

    Returns:
        0 if the distribution matches the specification, 1 otherwise.
    """
    questions, meta = load_gold(path)
    counts: dict[str, int] = {}
    for question in questions:
        counts[question.category] = counts.get(question.category, 0) + 1

    expected = {
        "lookup": 8,
        "comparison": 6,
        "ambiguous": 5,
        "refusal": 4,
        "restatement": 2,
    }
    print(f"{len(questions)} questions in {path}")
    ok = len(questions) == 25
    for category, want in expected.items():
        got = counts.get(category, 0)
        flag = "ok" if got == want else f"EXPECTED {want}"
        ok = ok and got == want
        print(f"  {category:<12} {got:>2}  {flag}")

    unverified = [q.id for q in questions if not q.verified and q.expected_value is not None]
    print(f"\nverified expected values: {len(questions) - len(unverified)} of 25")
    if unverified:
        print("UNVERIFIED, marked '# VERIFY THIS' in gold.yaml:")
        for qid in unverified:
            print(f"  {qid}")
        print(
            "\nAccuracy computed against these means nothing. Check each one "
            "against the filing on EDGAR before quoting a score."
        )
    if meta:
        print(f"\nmeta.warning: {' '.join(str(meta.get('warning', '')).split())}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run.

    Args:
        argv: Command-line arguments.

    Returns:
        A process exit code.
    """
    args = build_parser().parse_args(argv)
    if args.validate:
        return validate(Path(args.gold))
    if args.rpm is None:
        args.rpm = 50.0 if args.provider == "anthropic" else 20.0
    return asyncio.run(run_eval(args))


if __name__ == "__main__":
    raise SystemExit(main())
