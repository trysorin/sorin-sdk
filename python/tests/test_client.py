import pytest
import responses as resp_lib
from requests.exceptions import Timeout, ConnectionError

from sorin import SorinClient

BASE_URL = "https://sorin-eight.vercel.app"
AUTH_URL = f"{BASE_URL}/api/runtime/advisory-authorize"
AGENT_KEY = "test-agent-key"


def make_client(**kwargs) -> SorinClient:
    return SorinClient(agent_key=AGENT_KEY, base_url=BASE_URL, **kwargs)


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

    @resp_lib.activate
    def test_reasoning_included_when_provided(self):
        resp_lib.add(resp_lib.POST, AUTH_URL, json={"allowed": True}, status=200)
        client = make_client()
        client.authorize(
            action="list-pulls",
            connector="github",
            resource_id="org/repo",
            reasoning="checking for open PRs",
        )

        import json
        payload = json.loads(resp_lib.calls[0].request.body)
        assert payload["reasoning"] == "checking for open PRs"

    @resp_lib.activate
    def test_reasoning_omitted_when_not_provided(self):
        resp_lib.add(resp_lib.POST, AUTH_URL, json={"allowed": True}, status=200)
        client = make_client()
        client.authorize(
            action="list-pulls",
            connector="github",
            resource_id="org/repo",
        )

        import json
        payload = json.loads(resp_lib.calls[0].request.body)
        assert "reasoning" not in payload


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

    def test_session_id_is_stable(self):
        client = make_client()
        sid_1 = client.session_id
        sid_2 = client.session_id
        assert sid_1 == sid_2
