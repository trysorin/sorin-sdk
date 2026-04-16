import logging
import time
import uuid
from typing import Optional
import requests

from ._context import get_current_parent, set_current_parent
from .github import GitHubConnector

logger = logging.getLogger(__name__)


class _SorinSession(requests.Session):
    """
    requests.Session subclass that auto-threads parent-call context.

    On every outbound request:
      - If get_current_parent() is set, inject `x-sorin-parent-request-id`
        (unless the caller already set it explicitly).

    On every response:
      - If `x-sorin-request-id` is present, call set_current_parent(). Only
        LLM proxy routes emit this header, so tool-call responses from
        github/slack routes are naturally no-ops here.
    """

    def request(self, method, url, **kwargs):  # type: ignore[override]
        headers = kwargs.get("headers") or {}
        # Normalize to dict so we can set keys regardless of caller type.
        if not isinstance(headers, dict):
            headers = dict(headers)
        parent = get_current_parent()
        if parent and "x-sorin-parent-request-id" not in {k.lower() for k in headers}:
            headers["X-Sorin-Parent-Request-Id"] = parent
        kwargs["headers"] = headers

        response = super().request(method, url, **kwargs)

        rid = response.headers.get("x-sorin-request-id")
        if rid:
            set_current_parent(rid)
        return response


class SorinClient:
    def __init__(
        self,
        agent_key: str,
        base_url: str = "https://trysorin.com",
        session_id: Optional[str] = None,
        sdk_version: str = "0.1.0",
        timeout: int = 5,
    ):
        self.agent_key = agent_key
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id or str(uuid.uuid4())
        self.sdk_version = sdk_version
        self.timeout = timeout
        self._session = _SorinSession()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {agent_key}",
        })
        self.github = GitHubConnector(self)

    def _new_request_id(self) -> str:
        return str(uuid.uuid4())

    def authorize(
        self,
        action: str,
        connector: str,
        resource_id: str,
        resource_type: str = "repo",
        request_id: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> dict:
        payload = {
            "action": action,
            "connector": connector,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "request_id": request_id,
            "session_id": self.session_id,
        }
        if reasoning is not None:
            payload["reasoning"] = reasoning
        _fail_open = {"allowed": True, "reason": "advisory_unavailable", "warning": "Sorin advisory check unreachable — proceeding without authorization check"}
        try:
            response = self._session.post(
                f"{self.base_url}/api/runtime/advisory-authorize",
                json=payload,
                timeout=3,
            )
            if not response.ok:
                logger.warning(
                    "authorize: non-200 response — failing open",
                    extra={"status": response.status_code, "body": response.text},
                )
                return _fail_open
            return response.json()
        except Exception as e:
            logger.warning(
                "authorize: request failed — failing open",
                extra={"error": str(e)},
            )
            return _fail_open

    def wait_for_approval(
        self,
        approval_request_id: str,
        timeout_seconds: int = 600,
        poll_interval: int = 2,
    ) -> dict:
        """
        Polls /api/runtime/approval-status/{id} until the approval request
        is resolved or the timeout is reached.

        Returns:
          {"approved": True}
          {"approved": False, "reason": "denied"}
          {"approved": False, "reason": "timed_out"}
          {"approved": False, "reason": "client_timeout"}
          {"approved": False, "reason": "error"}
        """
        deadline = time.time() + timeout_seconds
        url = f"{self.base_url}/api/runtime/approval-status/{approval_request_id}"

        while time.time() < deadline:
            try:
                response = self._session.get(url, timeout=self.timeout)

                if response.status_code == 404:
                    logger.error("wait_for_approval: approval request not found")
                    return {"approved": False, "reason": "error"}

                if not response.ok:
                    logger.warning(
                        "wait_for_approval: non-200 response",
                        extra={"status": response.status_code, "body": response.text},
                    )
                    time.sleep(poll_interval)
                    continue

                data = response.json()
                status = data.get("status")

                if status == "approved":
                    return {"approved": True}
                if status == "denied":
                    return {"approved": False, "reason": "denied"}
                if status == "timed_out":
                    return {"approved": False, "reason": "timed_out"}

                # Still pending — print progress so the developer can see it waiting
                expires_at = data.get("expires_at")
                print(f"[sorin] Waiting for approval... (expires: {expires_at})")

            except Exception as e:
                logger.error(
                    "wait_for_approval: request failed",
                    extra={"error": str(e)},
                )

            time.sleep(poll_interval)

        return {"approved": False, "reason": "client_timeout"}
