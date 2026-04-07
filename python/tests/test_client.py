import pytest
import responses as resp_lib
from requests.exceptions import Timeout, ConnectionError

from sorin import SorinClient

BASE_URL = "https://sorin-eight.vercel.app"
INTENT_URL = f"{BASE_URL}/api/runtime/log-intent"
AUTH_URL = f"{BASE_URL}/api/runtime/advisory-authorize"
AGENT_KEY = "test-agent-key"


def make_client(**kwargs) -> SorinClient:
    return SorinClient(agent_key=AGENT_KEY, base_url=BASE_URL, **kwargs)


# ---------------------------------------------------------------------------
# capture_intent
# ---------------------------------------------------------------------------

class TestCaptureIntent:

    @resp_lib.activate
    def test_returns_request_id_on_success(self):
        resp_lib.add(resp_lib.POST, INTENT_URL, json={"ok": True}, status=200)
        client = make_client()
        result = client.capture_intent(
            plan={"action": "list-pulls", "connector": "github", "resource_id": "org/repo"},
            reasoning="checking for open PRs",
            request_id="req-abc",
        )
        assert isinstance(result, str) and len(result) > 0

    @resp_lib.activate
    def test_auto_generates_request_id_if_not_provided(self):
        import re
        resp_lib.add(resp_lib.POST, INTENT_URL, json={"ok": True}, status=200)
        client = make_client()
        result = client.capture_intent(
            plan={"action": "list-pulls", "connector": "github", "resource_id": "org/repo"},
            reasoning="checking for open PRs",
        )
        assert re.match(r'^[0-9a-f-]{36}$', result)

    @resp_lib.activate
    def test_never_raises_on_http_error(self):
        resp_lib.add(resp_lib.POST, INTENT_URL, json={"error": "bad"}, status=500)
        client = make_client()
        # Should not raise
        client.capture_intent(
            plan={"action": "list-pulls", "connector": "github", "resource_id": "org/repo"},
            reasoning="test",
        )

    @resp_lib.activate
    def test_never_raises_on_timeout(self):
        resp_lib.add(resp_lib.POST, INTENT_URL, body=Timeout())
        client = make_client()
        # Should not raise
        client.capture_intent(
            plan={"action": "list-pulls", "connector": "github", "resource_id": "org/repo"},
            reasoning="test",
        )

    @resp_lib.activate
    def test_sends_correct_payload(self):
        resp_lib.add(resp_lib.POST, INTENT_URL, json={"ok": True}, status=200)
        client = make_client(session_id="fixed-session-id")
        client.capture_intent(
            plan={"action": "list-pulls", "connector": "github", "resource_id": "org/repo"},
            reasoning="checking for open PRs",
            request_id="req-123",
        )

        assert len(resp_lib.calls) == 1
        body = resp_lib.calls[0].request.body
        import json
        payload = json.loads(body)

        assert payload["action"] == "list-pulls"
        assert payload["connector"] == "github"
        assert payload["resource_id"] == "org/repo"
        assert payload["sdk_language"] == "python"
        assert payload["session_id"] == "fixed-session-id"
        assert payload["request_id"] == "req-123"
        assert payload["reasoning"] == {"text": "checking for open PRs"}


# ---------------------------------------------------------------------------
# authorize
# ---------------------------------------------------------------------------

class TestAuthorize:

    @resp_lib.activate
    def test_returns_allowed_true_on_success(self):
        resp_lib.add(resp_lib.POST, AUTH_URL, json={"allowed": True, "reason": "ok"}, status=200)
        client = make_client()
        result = client.authorize(
            action="list-pulls",
            connector="github",
            resource_id="org/repo",
        )
        assert result["allowed"] is True

    @resp_lib.activate
    def test_fails_open_on_http_error(self):
        resp_lib.add(resp_lib.POST, AUTH_URL, json={"error": "denied"}, status=403)
        client = make_client()
        result = client.authorize(
            action="list-pulls",
            connector="github",
            resource_id="org/repo",
        )
        assert result["allowed"] is True
        assert result["reason"] == "advisory_unavailable"

    @resp_lib.activate
    def test_fails_open_on_timeout(self):
        resp_lib.add(resp_lib.POST, AUTH_URL, body=Timeout())
        client = make_client()
        result = client.authorize(
            action="list-pulls",
            connector="github",
            resource_id="org/repo",
        )
        assert result["allowed"] is True
        assert result["reason"] == "advisory_unavailable"

    @resp_lib.activate
    def test_fails_open_on_connection_error(self):
        resp_lib.add(resp_lib.POST, AUTH_URL, body=ConnectionError())
        client = make_client()
        result = client.authorize(
            action="list-pulls",
            connector="github",
            resource_id="org/repo",
        )
        assert result["allowed"] is True
        assert result["reason"] == "advisory_unavailable"

    @resp_lib.activate
    def test_resource_type_defaults_to_repo(self):
        resp_lib.add(resp_lib.POST, AUTH_URL, json={"allowed": True}, status=200)
        client = make_client()
        client.authorize(
            action="list-pulls",
            connector="github",
            resource_id="org/repo",
        )

        import json
        payload = json.loads(resp_lib.calls[0].request.body)
        assert payload["resource_type"] == "repo"


# ---------------------------------------------------------------------------
# session_id
# ---------------------------------------------------------------------------

class TestSessionId:

    def test_auto_generated_if_not_provided(self):
        client = make_client()
        assert client.session_id is not None
        assert len(client.session_id) > 0

    def test_two_clients_get_different_session_ids(self):
        a = make_client()
        b = make_client()
        assert a.session_id != b.session_id

    @resp_lib.activate
    def test_same_session_id_reused_across_calls(self):
        resp_lib.add(resp_lib.POST, INTENT_URL, json={"ok": True}, status=200)
        resp_lib.add(resp_lib.POST, INTENT_URL, json={"ok": True}, status=200)

        client = make_client()
        plan = {"action": "list-pulls", "connector": "github", "resource_id": "org/repo"}
        client.capture_intent(plan=plan, reasoning="first call")
        client.capture_intent(plan=plan, reasoning="second call")

        import json
        sid_1 = json.loads(resp_lib.calls[0].request.body)["session_id"]
        sid_2 = json.loads(resp_lib.calls[1].request.body)["session_id"]
        assert sid_1 == sid_2 == client.session_id
