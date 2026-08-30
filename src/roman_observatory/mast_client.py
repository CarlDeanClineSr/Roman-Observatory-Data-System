"""Small evidence-preserving client for bounded MAST metadata queries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import time
from typing import Any, Iterable
from urllib.parse import quote

import requests


class MastError(RuntimeError):
    """Raised when MAST transport or response validation fails."""


@dataclass(frozen=True)
class MastInvocation:
    request: dict[str, Any]
    payload: dict[str, Any]
    raw_bytes: bytes
    http_status: int
    final_url: str
    content_type: str
    retrieved_utc: str
    attempts: int

    @property
    def raw_sha256(self) -> str:
        return hashlib.sha256(self.raw_bytes).hexdigest()

    def summary(self) -> dict[str, Any]:
        data = self.payload.get("data")
        return {
            "service": self.request.get("service"),
            "http_status": self.http_status,
            "final_url": self.final_url,
            "content_type": self.content_type,
            "retrieved_utc": self.retrieved_utc,
            "attempts": self.attempts,
            "raw_size_bytes": len(self.raw_bytes),
            "raw_sha256": self.raw_sha256,
            "mast_status": self.payload.get("status"),
            "row_count": len(data) if isinstance(data, list) else None,
        }


class MastClient:
    def __init__(
        self,
        *,
        invoke_url: str,
        timeout_seconds: float = 45,
        max_poll_seconds: float = 60,
        poll_interval_seconds: float = 1,
        session: requests.Session | None = None,
    ) -> None:
        if invoke_url != "https://mast.stsci.edu/api/v0/invoke":
            raise ValueError("unexpected MAST invoke URL")
        self.invoke_url = invoke_url
        self.timeout_seconds = float(timeout_seconds)
        self.max_poll_seconds = float(max_poll_seconds)
        self.poll_interval_seconds = float(poll_interval_seconds)
        self.session = session or requests.Session()

    def invoke(self, request_object: dict[str, Any]) -> MastInvocation:
        if not isinstance(request_object, dict) or not request_object.get("service"):
            raise ValueError("MAST request must include service")
        request_copy = json.loads(json.dumps(request_object))
        request_copy.setdefault("format", "json")
        request_copy.setdefault(
            "cachebreaker",
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )
        encoded = quote(
            json.dumps(request_copy, sort_keys=True, separators=(",", ":")), safe=""
        )
        body = "request=" + encoded
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "Roman-Observatory-Data-System/0.1 (+metadata-only)",
        }
        start = time.monotonic()
        attempts = 0
        while True:
            attempts += 1
            try:
                response = self.session.post(
                    self.invoke_url,
                    data=body,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
            except requests.RequestException as exc:
                raise MastError(f"MAST transport failed: {exc.__class__.__name__}") from exc
            if response.status_code != 200:
                raise MastError(f"MAST returned HTTP {response.status_code}")
            raw = bytes(response.content)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MastError("MAST returned non-JSON content") from exc
            if not isinstance(payload, dict):
                raise MastError("MAST response root is not an object")
            status = str(payload.get("status", "COMPLETE")).upper()
            if status in {"ERROR", "FAILED"}:
                message = payload.get("msg") or payload.get("message") or "unspecified error"
                raise MastError(f"MAST service failed: {message}")
            if status != "EXECUTING":
                return MastInvocation(
                    request=request_copy,
                    payload=payload,
                    raw_bytes=raw,
                    http_status=response.status_code,
                    final_url=str(response.url),
                    content_type=response.headers.get("Content-Type", ""),
                    retrieved_utc=datetime.now(timezone.utc).isoformat(),
                    attempts=attempts,
                )
            if time.monotonic() - start >= self.max_poll_seconds:
                raise MastError("MAST long-poll timeout")
            time.sleep(self.poll_interval_seconds)

    def list_missions(self) -> tuple[list[str], MastInvocation]:
        response = self.invoke(
            {"service": "Mast.Missions.List", "params": {}, "format": "json"}
        )
        data = response.payload.get("data", [])
        if not isinstance(data, list):
            raise MastError("Mast.Missions.List data is not a list")
        missions = {
            row.get("distinctValue", "").strip()
            for row in data
            if isinstance(row, dict) and isinstance(row.get("distinctValue"), str)
        }
        return sorted(item for item in missions if item), response

    def count_collection(self, collection: str) -> tuple[int, MastInvocation]:
        if not collection.strip():
            raise ValueError("collection must not be empty")
        response = self.invoke(
            {
                "service": "Mast.Caom.Filtered",
                "format": "json",
                "params": {
                    "columns": "COUNT_BIG(*)",
                    "filters": [{"paramName": "obs_collection", "values": [collection]}],
                    "obstype": "all",
                },
            }
        )
        return extract_count(response.payload), response

    def sample_collection(self, collection: str, *, pagesize: int) -> MastInvocation:
        if pagesize < 1 or pagesize > 500:
            raise ValueError("pagesize must be between 1 and 500")
        return self.invoke(
            {
                "service": "Mast.Caom.Filtered",
                "format": "json",
                "pagesize": pagesize,
                "page": 1,
                "removenullcolumns": True,
                "params": {
                    "columns": "*",
                    "filters": [{"paramName": "obs_collection", "values": [collection]}],
                    "obstype": "all",
                },
            }
        )

    def list_products(self, obsids: Iterable[str | int], *, pagesize: int) -> MastInvocation:
        """Fetch bounded product metadata using the documented Mast.Caom.Products service."""

        values = [str(value).strip() for value in obsids if str(value).strip()]
        if not values:
            raise ValueError("at least one obsid is required")
        if pagesize < 1 or pagesize > 500:
            raise ValueError("pagesize must be between 1 and 500")
        return self.invoke(
            {
                "service": "Mast.Caom.Products",
                "format": "json",
                "pagesize": pagesize,
                "page": 1,
                "params": {"obsid": ",".join(values)},
            }
        )


def extract_count(payload: dict[str, Any]) -> int:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return 0
    row = data[0]
    if not isinstance(row, dict):
        raise MastError("MAST count row is not an object")
    for value in row.values():
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return max(0, value)
        if isinstance(value, float) and value.is_integer():
            return max(0, int(value))
        if isinstance(value, str):
            cleaned = value.strip().replace(",", "")
            if re.fullmatch(r"[+-]?\d+", cleaned):
                return max(0, int(cleaned))
    raise MastError("MAST count response did not contain an integer")
