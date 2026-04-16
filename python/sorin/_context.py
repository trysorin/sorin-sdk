"""
Causal parent-call contextvar for the Sorin SDK.

Auto-threads `parent_request_id` across LLM turns and tool calls so agents
get a full causal tree without touching their code. See the Sorin
migration 2026-04-16-call-chain-tracking.sql for the data model.

Usage (internal):
  from sorin._context import get_current_parent, set_current_parent

  # In an outbound HTTP call: if parent is set, inject x-sorin-parent-request-id.
  # In an LLM response handler: if response carries x-sorin-request-id,
  # call set_current_parent(value) so the NEXT call chains to this one.

Semantics:
  - contextvars propagate across `await` boundaries but NOT across raw threads.
    If an agent parallelizes tool execution via ThreadPoolExecutor, each
    worker thread starts with the default (None) unless the agent explicitly
    copies the context with `ctx.copy()`. This is expected Python behavior.
"""

import contextvars
from typing import Optional

_parent_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "sorin_parent_request_id",
    default=None,
)


def get_current_parent() -> Optional[str]:
    """Return the request_id of the most recent LLM call in this context, if any."""
    return _parent_request_id.get()


def set_current_parent(request_id: str) -> None:
    """Record the current LLM call's request_id so subsequent calls chain to it."""
    _parent_request_id.set(request_id)


def clear_current_parent() -> None:
    """Reset the parent. Useful in tests or between agent sessions."""
    _parent_request_id.set(None)
