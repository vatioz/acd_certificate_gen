"""
Azure Content Understanding integration helpers.

This module encapsulates:
- Analyzer job submission
- Job status polling
- Mapping analyzer output to the application's people schema
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import requests
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, ContentSettings, generate_blob_sas

from data_utils import detect_gender_from_name


class AnalyzerConfigError(Exception):
    """Raised when required analyzer configuration is missing."""


class AnalyzerApiError(Exception):
    """Raised when analyzer API call fails."""


class ContentUnderstandingClient:
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        analyzer_id: str,
        api_version: str,
        region: str = "",
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.analyzer_id = analyzer_id
        self.api_version = api_version
        self.region = region.strip()

    @classmethod
    def from_env(cls) -> "ContentUnderstandingClient":
        endpoint = os.getenv("CONTENT_UNDERSTANDING_ENDPOINT", "").strip()
        api_key = os.getenv("CONTENT_UNDERSTANDING_API_KEY", "").strip()
        analyzer_id = os.getenv("CONTENT_UNDERSTANDING_ANALYZER_ID", "").strip()
        api_version = os.getenv("CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01").strip()
        region = os.getenv("CONTENT_UNDERSTANDING_REGION", "").strip()

        missing = []
        if not endpoint:
            missing.append("CONTENT_UNDERSTANDING_ENDPOINT")
        if not api_key:
            missing.append("CONTENT_UNDERSTANDING_API_KEY")
        if not analyzer_id:
            missing.append("CONTENT_UNDERSTANDING_ANALYZER_ID")

        if missing:
            raise AnalyzerConfigError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        return cls(
            endpoint=endpoint,
            api_key=api_key,
            analyzer_id=analyzer_id,
            api_version=api_version,
            region=region,
        )

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        if self.region:
            headers["Ocp-Apim-Subscription-Region"] = self.region
        return headers

    def submit_document(self, file_url: str) -> Dict[str, Optional[str]]:
        submit_url = (
            f"{self.endpoint}/contentunderstanding/analyzers/{self.analyzer_id}:analyze"
            f"?api-version={self.api_version}"
        )

        payload = {
            "inputs": [
                {
                    "url": file_url,
                }
            ]
        }

        response = requests.post(
            submit_url,
            headers=self._headers(),
            json=payload,
            timeout=60,
        )

        if response.status_code not in (200, 201, 202):
            if response.status_code == 401:
                raise AnalyzerApiError(
                    "Submit failed (401). Verify Content Understanding endpoint/key match the SAME Azure resource, "
                    "analyzer exists on that resource, and try setting CONTENT_UNDERSTANDING_REGION if your setup "
                    "requires regional header. "
                    f"endpoint={self.endpoint}, analyzerId={self.analyzer_id}, apiVersion={self.api_version}. "
                    f"Response: {response.text[:500]}"
                )
            raise AnalyzerApiError(
                f"Submit failed ({response.status_code}): {response.text[:500]}"
            )

        operation_location = response.headers.get("operation-location") or response.headers.get("Operation-Location")
        response_json = _safe_json(response)

        result_id = (
            response_json.get("id")
            or response_json.get("resultId")
            or response_json.get("result_id")
            or _extract_result_id(operation_location)
        )

        return {
            "operation_id": result_id,
            "operation_location": operation_location,
        }

    def poll_operation(self, operation_id: Optional[str], operation_location: Optional[str]) -> Dict[str, Any]:
        if operation_location:
            status_url = operation_location
        elif operation_id:
            status_url = (
                f"{self.endpoint}/contentunderstanding/analyzerResults/{operation_id}"
                f"?api-version={self.api_version}"
            )
        else:
            raise AnalyzerApiError("Missing operation identifier for polling.")

        response = requests.get(status_url, headers=self._headers(), timeout=60)

        if response.status_code not in (200, 201, 202):
            if response.status_code == 401:
                raise AnalyzerApiError(
                    "Polling failed (401). Verify Content Understanding endpoint/key/resource alignment and optional "
                    "CONTENT_UNDERSTANDING_REGION. "
                    f"endpoint={self.endpoint}, analyzerId={self.analyzer_id}, apiVersion={self.api_version}. "
                    f"Response: {response.text[:500]}"
                )
            raise AnalyzerApiError(
                f"Polling failed ({response.status_code}): {response.text[:500]}"
            )

        data = _safe_json(response)
        normalized_status = _normalize_status(data)
        return {
            "status": normalized_status,
            "raw": data,
            "error": _extract_error_message(data),
        }


def upload_pdf_to_blob_and_get_sas_url(pdf_bytes: bytes, file_name: str, expiry_minutes: int = 30) -> str:
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "").strip()
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "").strip()
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "").strip()
    account_url = os.getenv("AZURE_STORAGE_BLOB_ENDPOINT", "").strip()

    missing = []
    if not account_name:
        missing.append("AZURE_STORAGE_ACCOUNT_NAME")
    if not account_key:
        missing.append("AZURE_STORAGE_ACCOUNT_KEY")
    if not container_name:
        missing.append("AZURE_STORAGE_CONTAINER_NAME")

    if missing:
        raise AnalyzerConfigError(
            "Missing required Azure Storage environment variables: " + ", ".join(missing)
        )

    if not account_url:
        account_url = f"https://{account_name}.blob.core.windows.net"

    blob_service = BlobServiceClient(account_url=account_url, credential=account_key)
    container_client = blob_service.get_container_client(container_name)
    if not container_client.exists():
        container_client.create_container()

    safe_name = _sanitize_filename(file_name)
    blob_name = f"incoming/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid4().hex}_{safe_name}"

    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(
        pdf_bytes,
        overwrite=True,
        content_settings=ContentSettings(content_type="application/pdf"),
    )

    sas_token = generate_blob_sas(
        account_name=account_name,
        account_key=account_key,
        container_name=container_name,
        blob_name=blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
    )

    return f"{account_url.rstrip('/')}/{container_name}/{blob_name}?{sas_token}"


def delete_blob_from_sas_url(blob_sas_url: str) -> bool:
    """Delete a blob using its SAS URL. Returns True if deleted or already missing."""
    if not blob_sas_url:
        return False

    try:
        from azure.core.exceptions import ResourceNotFoundError
        from azure.storage.blob import BlobClient

        blob_client = BlobClient.from_blob_url(blob_sas_url)
        blob_client.delete_blob(delete_snapshots="include")
        return True
    except ResourceNotFoundError:
        return True
    except Exception:
        return False


def map_analyzer_result_to_people(analyzer_response: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[int]]:
    participants = _extract_participants(analyzer_response)

    people: List[Dict[str, Any]] = []
    first_counter: Optional[int] = None

    for participant in participants:
        first_name = _value_text(participant, "FirstName")
        last_name = _value_text(participant, "LastName")
        pre = _value_text(participant, "AcademicTitleBefore")
        post = _value_text(participant, "AcademicTitleAfter")
        dob = _value_text(participant, "DateOfBirth")
        row_id = _value_text(participant, "Id")

        if not first_name and not last_name:
            continue

        full_name = f"{first_name} {last_name}".strip()
        detected_gender, gender_detected = detect_gender_from_name(first_name)

        if first_counter is None:
            try:
                first_counter = int(row_id)
            except (TypeError, ValueError):
                first_counter = None

        people.append(
            {
                "name": full_name,
                "dob_raw": dob,
                "dob": dob,
                "gender": detected_gender if detected_gender else "female",
                "gender_detected": gender_detected,
                "pre": pre,
                "post": post,
            }
        )

    return people, first_counter


def _safe_json(response: requests.Response) -> Dict[str, Any]:
    try:
        return response.json()
    except ValueError:
        return {}


def _extract_result_id(operation_location: Optional[str]) -> Optional[str]:
    if not operation_location:
        return None

    tail = operation_location.rstrip("/").split("/")[-1]
    if "?" in tail:
        tail = tail.split("?", 1)[0]
    return tail or None


def _sanitize_filename(file_name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]", "_", file_name)
    if not normalized:
        return "upload.pdf"
    if not normalized.lower().endswith(".pdf"):
        return f"{normalized}.pdf"
    return normalized


def _normalize_status(data: Dict[str, Any]) -> str:
    raw_status = (
        str(
            data.get("status")
            or data.get("state")
            or data.get("result", {}).get("status")
            or "running"
        )
        .strip()
        .lower()
    )

    if raw_status in {"succeeded", "completed", "done", "success"}:
        return "succeeded"
    if raw_status in {"failed", "error", "cancelled", "canceled"}:
        return "failed"
    return "running"


def _extract_error_message(data: Dict[str, Any]) -> str:
    error = data.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("details")
        if isinstance(message, str):
            return message

    if isinstance(error, str):
        return error

    return ""


def _extract_participants(data: Dict[str, Any]) -> List[Any]:
    candidate_paths = [
        ("fields", "Participants"),
        ("result", "fields", "Participants"),
        ("analyzeResult", "fields", "Participants"),
        ("output", "fields", "Participants"),
        ("result", "analyzeResult", "fields", "Participants"),
    ]

    for path in candidate_paths:
        node = data
        for part in path:
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(part)

        participants = _participants_from_node(node)
        if participants:
            return participants

    contents = data.get("result", {}).get("contents")
    if isinstance(contents, list):
        for content in contents:
            if not isinstance(content, dict):
                continue
            fields = content.get("fields")
            if not isinstance(fields, dict):
                continue
            participants_node = fields.get("Participants")
            participants = _participants_from_node(participants_node)
            if participants:
                return participants

    return []


def _participants_from_node(node: Any) -> List[Any]:
    if isinstance(node, list):
        return node

    if not isinstance(node, dict):
        return []

    if isinstance(node.get("valueArray"), list):
        return node["valueArray"]

    if isinstance(node.get("values"), list):
        return node["values"]

    if isinstance(node.get("value"), list):
        return node["value"]

    return []


def _value_text(item: Any, key: str) -> str:
    if not isinstance(item, dict):
        return ""

    if isinstance(item.get("valueObject"), dict):
        item = item["valueObject"]

    value = item.get(key)

    if isinstance(value, dict):
        if "valueString" in value and value["valueString"] is not None:
            return str(value["valueString"]).strip()
        if "valueDate" in value and value["valueDate"] is not None:
            return str(value["valueDate"]).strip()
        if "content" in value and value["content"] is not None:
            return str(value["content"]).strip()
        if "value" in value and value["value"] is not None:
            return str(value["value"]).strip()
        return ""

    if value is None:
        return ""

    return str(value).strip()
