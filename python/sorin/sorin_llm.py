"""
SorinLLM / SorinOpenAI — Sorin-aware wrappers around the provider SDKs.

Both SDKs are built on httpx. We install event hooks on the underlying
http_client to auto-thread `parent_request_id`:

  - Request hook injects `x-sorin-parent-request-id` if the SDK's contextvar
    holds a previous LLM call's request_id.
  - Response hook captures `x-sorin-request-id` from the proxy response so
    the next LLM or tool call chains to this turn.

Agents don't touch anything — the same `messages.create(...)` or
`chat.completions.create(...)` call sites work unchanged.
"""

import anthropic
import httpx
from openai import OpenAI

from ._context import get_current_parent, set_current_parent


def _inject_parent_header(request: httpx.Request) -> None:
    parent = get_current_parent()
    if parent and "x-sorin-parent-request-id" not in request.headers:
        request.headers["x-sorin-parent-request-id"] = parent


def _capture_request_id(response: httpx.Response) -> None:
    # Response bodies are lazy; only touch headers.
    rid = response.headers.get("x-sorin-request-id")
    if rid:
        set_current_parent(rid)


def _build_http_client() -> httpx.Client:
    return httpx.Client(
        event_hooks={
            "request": [_inject_parent_header],
            "response": [_capture_request_id],
        },
        timeout=httpx.Timeout(60.0),
    )


class SorinLLM(anthropic.Anthropic):
    def __init__(self, agent_key: str, base_url: str = "https://sorin-eight.vercel.app", **kwargs):
        kwargs.setdefault("http_client", _build_http_client())
        super().__init__(
            api_key=agent_key,
            base_url=f"{base_url.rstrip('/')}/api/runtime/llm",
            **kwargs
        )


class SorinOpenAI(OpenAI):
    def __init__(self, agent_key: str, base_url: str = "https://sorin-eight.vercel.app", **kwargs):
        kwargs.setdefault("http_client", _build_http_client())
        super().__init__(
            api_key=agent_key,
            base_url=f"{base_url.rstrip('/')}/api/runtime/openai/v1",
            **kwargs
        )
