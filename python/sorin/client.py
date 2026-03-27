import logging
import uuid
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class SorinClient:
    def __init__(
        self,
        agent_key: str,
        base_url: str = "https://sorin-eight.vercel.app",
        session_id: Optional[str] = None,
        sdk_version: str = "0.1.0",
        timeout: int = 5,
    ):
        self.agent_key = agent_key
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id or str(uuid.uuid4())
        self.sdk_version = sdk_version
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {agent_key}",
        })

    def capture_intent(
        self,
        plan: dict,
        reasoning: str,
        request_id: Optional[str] = None,
        advisory_result: Optional[dict] = None,
    ) -> None:
        payload = {
            "agent_key": self.agent_key,
            "plan": plan,
            "action": plan.get("action"),
            "connector": plan.get("connector"),
            "resource_id": plan.get("resource_id"),
            "reasoning": {"text": reasoning},
            "advisory_result": advisory_result,
            "request_id": request_id,
            "session_id": self.session_id,
            "sdk_version": self.sdk_version,
            "sdk_language": "python",
        }
        try:
            response = self._session.post(
                f"{self.base_url}/api/runtime/log-intent",
                json=payload,
                timeout=self.timeout,
            )
            if not response.ok:
                logger.warning(
                    "capture_intent: non-200 response",
                    extra={"status": response.status_code, "body": response.text},
                )
        except Exception as e:
            logger.error(
                "capture_intent: request failed",
                extra={"error": str(e)},
            )

    def authorize(
        self,
        action: str,
        connector: str,
        resource_id: str,
        resource_type: str = "repo",
        request_id: Optional[str] = None,
    ) -> dict:
        payload = {
            "action": action,
            "connector": connector,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "request_id": request_id,
        }
        try:
            response = self._session.post(
                f"{self.base_url}/api/runtime/advisory-authorize",
                json=payload,
                timeout=3,
            )
            if not response.ok:
                logger.warning(
                    "authorize: non-200 response",
                    extra={"status": response.status_code, "body": response.text},
                )
                return {"allowed": False, "reason": "advisory check failed"}
            return response.json()
        except Exception as e:
            logger.error(
                "authorize: request failed",
                extra={"error": str(e)},
            )
            return {"allowed": False, "reason": "advisory check failed"}
