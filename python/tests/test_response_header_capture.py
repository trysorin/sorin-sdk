"""
When a Sorin LLM proxy sets `x-sorin-request-id` on its response,
SorinLLM / SorinOpenAI must capture it into the contextvar so the next
call chains to this turn.

The LLM SDKs (anthropic / openai) are built on httpx. SorinLLM installs
httpx event hooks to intercept the response. This test verifies the hook
fires by invoking it directly against a synthetic httpx.Response — avoiding
the need to stand up a real Anthropic/OpenAI API mock.
"""

import httpx

from sorin._context import clear_current_parent, get_current_parent
from sorin.sorin_llm import _capture_request_id, _inject_parent_header


def test_capture_hook_sets_parent_when_response_carries_header():
    clear_current_parent()
    resp = httpx.Response(
        status_code=200,
        headers={"x-sorin-request-id": "turn-1-uuid"},
        request=httpx.Request("POST", "https://x"),
    )
    _capture_request_id(resp)
    assert get_current_parent() == "turn-1-uuid"


def test_capture_hook_is_noop_without_header():
    clear_current_parent()
    resp = httpx.Response(
        status_code=200,
        headers={},
        request=httpx.Request("POST", "https://x"),
    )
    _capture_request_id(resp)
    assert get_current_parent() is None


def test_inject_hook_adds_parent_header_when_context_set():
    from sorin._context import set_current_parent
    clear_current_parent()
    set_current_parent("turn-0-uuid")
    req = httpx.Request("POST", "https://x")
    _inject_parent_header(req)
    assert req.headers["x-sorin-parent-request-id"] == "turn-0-uuid"
    clear_current_parent()


def test_inject_hook_is_noop_without_context():
    clear_current_parent()
    req = httpx.Request("POST", "https://x")
    _inject_parent_header(req)
    assert "x-sorin-parent-request-id" not in req.headers
