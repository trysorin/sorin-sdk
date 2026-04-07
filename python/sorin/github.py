from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import SorinClient


class GitHubConnector:
    def __init__(self, client: "SorinClient"):
        self._client = client

    def _run(self, action: str, resource_id: str, resource_type: str, reasoning: str, endpoint: str, payload: dict) -> dict:
        """Shared flow: capture_intent → authorize → HTTP call."""
        request_id = self._client._new_request_id()

        self._client.capture_intent(
            plan={"connector": "github", "action": action, "resource_type": resource_type, "resource_id": resource_id},
            reasoning=reasoning,
            request_id=request_id,
        )

        auth = self._client.authorize(
            action=action,
            connector="github",
            resource_id=resource_id,
            resource_type=resource_type,
            request_id=request_id,
        )

        if not auth.get("allowed", True):
            raise PermissionError(f"[sorin] Action '{action}' blocked: {auth.get('reason')}")

        payload["request_id"] = request_id
        response = self._client._session.post(
            f"{self._client.base_url}/api/runtime/github/{endpoint}",
            json=payload,
        )

        if response.status_code == 202:
            data = response.json()
            approval_request_id = data["approval_request_id"]
            print(f"[sorin] Approval required for '{action}'. Waiting...")
            decision = self._client.wait_for_approval(approval_request_id=approval_request_id)
            if not decision["approved"]:
                raise PermissionError(f"[sorin] '{action}' denied: {decision.get('reason')}")
            payload["approval_request_id"] = approval_request_id
            response = self._client._session.post(
                f"{self._client.base_url}/api/runtime/github/{endpoint}",
                json=payload,
            )

        if not response.ok:
            raise Exception(f"[sorin] GitHub '{action}' failed: {response.text}")

        return response.json()

    def list_prs(self, owner: str, repo: str, reasoning: str = "Listing open pull requests") -> dict:
        return self._run("list-pulls", f"{owner}/{repo}", "repo", reasoning, "list-pulls",
                         {"owner": owner, "repo": repo})

    def comment(self, owner: str, repo: str, pr_number: int, message: str, reasoning: str = "Commenting on pull request") -> dict:
        return self._run("comment-pr", f"{owner}/{repo}#{pr_number}", "pull_request", reasoning, "comment",
                         {"owner": owner, "repo": repo, "prNumber": pr_number, "message": message})

    def read_file(self, owner: str, repo: str, path: str, ref: str = "main", reasoning: str = "Reading file contents") -> dict:
        return self._run("read-file", f"{owner}/{repo}", "repo", reasoning, "read-file",
                         {"owner": owner, "repo": repo, "path": path, "ref": ref})

    def create_branch(self, owner: str, repo: str, branch: str, from_branch: str = "main", reasoning: str = "Creating a new branch") -> dict:
        return self._run("create-branch", f"{owner}/{repo}", "repo", reasoning, "create-branch",
                         {"owner": owner, "repo": repo, "branch": branch, "from_branch": from_branch})

    def push_file(self, owner: str, repo: str, path: str, content: str, message: str, branch: str, sha: str = None, reasoning: str = "Pushing file changes") -> dict:
        payload = {"owner": owner, "repo": repo, "path": path, "content": content, "message": message, "branch": branch}
        if sha:
            payload["sha"] = sha
        return self._run("push-file", f"{owner}/{repo}", "repo", reasoning, "push-file", payload)

    def create_pr(self, owner: str, repo: str, title: str, body: str, head: str, base: str = "main", reasoning: str = "Opening a pull request") -> dict:
        return self._run("create-pr", f"{owner}/{repo}", "repo", reasoning, "create-pr",
                         {"owner": owner, "repo": repo, "title": title, "body": body, "head": head, "base": base})
