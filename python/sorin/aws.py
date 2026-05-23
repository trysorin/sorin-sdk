from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .client import SorinClient


class AWSConnector:
    def __init__(self, client: "SorinClient"):
        self._client = client

    def _run(
        self,
        action: str,
        resource_id: str,
        resource_type: str,
        reasoning: str,
        endpoint: str,
        payload: dict,
        tool_use_id: Optional[str] = None,
    ) -> dict:
        """Shared flow: authorize → HTTP call → approval gate if required."""
        request_id = self._client._new_request_id()

        auth = self._client.authorize(
            action=action,
            connector="aws",
            resource_id=resource_id,
            resource_type=resource_type,
            request_id=request_id,
            reasoning=reasoning,
        )

        if not auth.get("allowed", True):
            raise PermissionError(f"[sorin] Action '{action}' blocked: {auth.get('reason')}")

        payload["request_id"] = request_id
        headers = {"X-Sorin-Tool-Use-Id": tool_use_id} if tool_use_id else None
        response = self._client._session.post(
            f"{self._client.base_url}/api/runtime/aws/{endpoint}",
            json=payload,
            headers=headers,
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
                f"{self._client.base_url}/api/runtime/aws/{endpoint}",
                json=payload,
                headers=headers,
            )

        if not response.ok:
            raise Exception(f"[sorin] AWS '{action}' failed: {response.text}")

        return response.json()

    # -------------------------------------------------------------------------
    # S3
    # -------------------------------------------------------------------------

    def s3_list_buckets(
        self,
        reasoning: str = "Listing S3 buckets",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        return self._run(
            "s3-list-buckets", "*", "s3_bucket", reasoning,
            "s3/list-buckets", {}, tool_use_id=tool_use_id,
        )

    def s3_list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 100,
        reasoning: str = "Listing S3 objects",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        payload: dict = {"bucket": bucket, "maxKeys": max_keys}
        if prefix is not None:
            payload["prefix"] = prefix
        return self._run(
            "s3-list-objects", bucket, "s3_bucket", reasoning,
            "s3/list-objects", payload, tool_use_id=tool_use_id,
        )

    def s3_get_object(
        self,
        bucket: str,
        key: str,
        reasoning: str = "Reading S3 object",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        return self._run(
            "s3-get-object", f"{bucket}/{key}", "s3_bucket", reasoning,
            "s3/get-object", {"bucket": bucket, "key": key}, tool_use_id=tool_use_id,
        )

    def s3_put_object(
        self,
        bucket: str,
        key: str,
        content: str,
        content_type: str = "text/plain",
        reasoning: str = "Writing S3 object",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        return self._run(
            "s3-put-object", f"{bucket}/{key}", "s3_bucket", reasoning,
            "s3/put-object",
            {"bucket": bucket, "key": key, "content": content, "contentType": content_type},
            tool_use_id=tool_use_id,
        )

    def s3_delete_object(
        self,
        bucket: str,
        key: str,
        reasoning: str = "Deleting S3 object",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        return self._run(
            "s3-delete-object", f"{bucket}/{key}", "s3_bucket", reasoning,
            "s3/delete-object", {"bucket": bucket, "key": key}, tool_use_id=tool_use_id,
        )

    # -------------------------------------------------------------------------
    # EC2
    # -------------------------------------------------------------------------

    def ec2_describe_instances(
        self,
        instance_ids: Optional[List[str]] = None,
        max_results: int = 50,
        reasoning: str = "Describing EC2 instances",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        payload: dict = {"maxResults": max_results}
        if instance_ids:
            payload["instanceIds"] = instance_ids
        return self._run(
            "ec2-describe-instances", "*", "ec2_instance", reasoning,
            "ec2/describe-instances", payload, tool_use_id=tool_use_id,
        )

    def ec2_start_instance(
        self,
        instance_id: str,
        reasoning: str = "Starting EC2 instance",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        return self._run(
            "ec2-start-instance", instance_id, "ec2_instance", reasoning,
            "ec2/start-instance", {"instanceId": instance_id}, tool_use_id=tool_use_id,
        )

    def ec2_stop_instance(
        self,
        instance_id: str,
        reasoning: str = "Stopping EC2 instance",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        return self._run(
            "ec2-stop-instance", instance_id, "ec2_instance", reasoning,
            "ec2/stop-instance", {"instanceId": instance_id}, tool_use_id=tool_use_id,
        )

    # -------------------------------------------------------------------------
    # Lambda
    # -------------------------------------------------------------------------

    def lambda_list_functions(
        self,
        max_items: int = 50,
        reasoning: str = "Listing Lambda functions",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        return self._run(
            "lambda-list-functions", "*", "lambda_function", reasoning,
            "lambda/list-functions", {"maxItems": max_items}, tool_use_id=tool_use_id,
        )

    def lambda_invoke(
        self,
        function_name: str,
        payload: Optional[str] = None,
        invocation_type: str = "RequestResponse",
        reasoning: str = "Invoking Lambda function",
        tool_use_id: Optional[str] = None,
    ) -> dict:
        body: dict = {"functionName": function_name, "invocationType": invocation_type}
        if payload is not None:
            body["payload"] = payload
        return self._run(
            "lambda-invoke-function", function_name, "lambda_function", reasoning,
            "lambda/invoke-function", body, tool_use_id=tool_use_id,
        )
