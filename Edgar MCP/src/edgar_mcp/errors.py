"""The error contract for every tool in this server.

Design choice, stated up front because it is the least obvious decision in the
codebase: **no tool ever raises an exception to the model.** Every failure path
returns a plain dict with two required keys::

    {"error": "<what went wrong, in one sentence>",
     "suggestion": "<what the MODEL should do on its next turn>"}

Two things follow from that, and both are deliberate.

**The `error` field is written for a human.** It is the sentence the analyst
will see quoted back to them if the model gives up. It names the thing that
failed and does not include stack traces, URLs with query strings, or Python
type names.

**The `suggestion` field is written for the model, not for the human.** It is
an instruction, phrased as an action the model can actually take with the tools
it has. "Call ``resolve_company`` with a ticker symbol instead of a company
name" is a good suggestion. "Please check your input" is a useless one, because
the model cannot act on it and will either apologise to the user or invent an
answer. Treat the suggestion as prompt engineering that happens at runtime:
it is the only channel this server has for steering the model's next move.

Why not raise? An MCP tool that raises returns an error to the client with
``isError: true``. Most agent loops surface that to the model as an unstructured
string, and some surface it as a hard failure that ends the turn. Neither gives
the model anything to do next. A structured, self-describing failure keeps the
model in the loop and — measurably, in the refusal category of the eval set —
makes it more likely to say "I could not find that" instead of guessing.

The one thing this module will not do is hide a failure behind a plausible
number. An error is always an error. There is no "best effort" return value.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

#: The two keys every failure response is guaranteed to contain.
REQUIRED_ERROR_KEYS = ("error", "suggestion")


class SECError(Exception):
    """A failure that a tool should convert into a structured response.

    Raised by the HTTP client and the data modules. Never allowed to escape a
    tool function: :func:`tool_error_boundary` converts it.

    Attributes:
        message: One sentence describing the failure, for a human reader.
        suggestion: One instruction describing what the model should try next.
        status_code: HTTP status that caused this, when there was one.
        details: Extra structured fields merged into the error response.
    """

    #: Fallback used when a subclass or caller does not supply one.
    default_suggestion = (
        "Report this failure to the user verbatim. Do not substitute a number "
        "from memory or from another source."
    )

    def __init__(
        self,
        message: str,
        *,
        suggestion: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Store the human message and the model-facing suggestion.

        Args:
            message: One sentence describing the failure.
            suggestion: What the model should do next. Falls back to
                :attr:`default_suggestion`.
            status_code: HTTP status code, when the failure was an HTTP one.
            details: Additional keys to merge into the structured response.
        """
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion or self.default_suggestion
        self.status_code = status_code
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        """Render this exception as the structured error a tool returns.

        Returns:
            A dict containing at least ``error`` and ``suggestion``.
        """
        return error_response(
            self.message,
            self.suggestion,
            status_code=self.status_code,
            **self.details,
        )


class NotFoundError(SECError):
    """EDGAR answered, and the answer was that this resource does not exist."""

    default_suggestion = (
        "EDGAR has no record at this identifier. Confirm the CIK with "
        "resolve_company before assuming the company does not file."
    )


class RateLimitError(SECError):
    """SEC rejected the request for volume reasons and retries did not clear it."""

    default_suggestion = (
        "The SEC rate limit is still engaged after automatic retries. Tell the "
        "user the data source is throttling and that the answer is unavailable "
        "right now. Do not retry more than once more in this conversation."
    )


class UpstreamUnavailableError(SECError):
    """EDGAR was unreachable, timed out, or returned a server error."""

    default_suggestion = (
        "EDGAR is not responding. Tell the user the filing service is "
        "unavailable and that you cannot verify a figure right now. Do not "
        "answer from memory."
    )


class InvalidInputError(SECError):
    """The caller passed something this tool cannot act on."""

    default_suggestion = (
        "The argument was not in a form this tool accepts. Re-read the tool "
        "description and call it again with a corrected argument."
    )


class AmbiguityError(SECError):
    """The request matched several things and picking one would be a guess.

    This is not a malfunction. It is the tool declining to guess, which is the
    behaviour the eval set rewards.
    """

    default_suggestion = (
        "Do not pick one of these candidates yourself. Ask the user which "
        "entity they mean, quoting the candidate names and tickers back to them."
    )


def error_response(error: str, suggestion: str, **extra: Any) -> dict[str, Any]:
    """Build the standard failure payload.

    Args:
        error: One sentence describing the failure, written for a human.
        suggestion: One instruction describing the model's next move.
        **extra: Additional structured fields. ``None`` values are dropped so
            the model is not handed empty keys to reason about.

    Returns:
        A dict with ``error`` and ``suggestion`` plus any non-``None`` extras.
    """
    payload: dict[str, Any] = {"error": error, "suggestion": suggestion}
    for key, value in extra.items():
        if value is not None:
            payload[key] = value
    return payload


def is_error(payload: Any) -> bool:
    """Report whether a tool result is a structured failure.

    Args:
        payload: Any tool return value.

    Returns:
        True if the value is a dict carrying an ``error`` key.
    """
    return isinstance(payload, dict) and "error" in payload


def tool_error_boundary(
    func: Callable[P, Awaitable[dict[str, Any]]],
) -> Callable[P, Awaitable[dict[str, Any]]]:
    """Guarantee that an async tool returns a dict and never raises.

    Wrap every MCP tool in this. A :class:`SECError` becomes its own structured
    response. Anything else — a bug in this codebase, a shape change in an SEC
    payload, a ``KeyError`` in a parser — becomes a generic structured response
    and is logged to stderr with a traceback so the maintainer can see it while
    the model still gets something it can act on.

    Args:
        func: The async tool implementation.

    Returns:
        The wrapped tool.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
        try:
            return await func(*args, **kwargs)
        except SECError as exc:
            logger.warning("%s returned a structured error: %s", func.__name__, exc.message)
            return exc.to_response()
        except Exception as exc:  # noqa: BLE001 - the whole point is to catch everything
            # Logged with a traceback to stderr. stdout is the JSON-RPC channel.
            logger.exception("%s raised an unhandled exception", func.__name__)
            return error_response(
                f"The {func.__name__} tool failed unexpectedly: "
                f"{type(exc).__name__}: {exc}",
                "This is a bug in the EDGAR server, not a problem with the "
                "question. Tell the user the tool failed and that you cannot "
                "verify a figure. Do not answer from memory. You may try one "
                "different tool if another one could answer the question.",
                tool=func.__name__,
            )

    return wrapper
