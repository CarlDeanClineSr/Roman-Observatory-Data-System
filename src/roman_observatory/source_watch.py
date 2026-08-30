"""Bounded exact-byte capture for approved public Roman sources."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
from typing import Any
from urllib.parse import urlparse

import requests

from .policy import host_allowed, load_policy
from .source_registry import SourceRecord, eligible_public_sources, load_sources


class SourceWatchError(RuntimeError):
    """Raised when a configured public source cannot be safely captured."""


_LOGIN_URL_HINTS = (
    "/login",
    "/signin",
    "sign-in",
    "single-sign-on",
    "/sso",
)

_LOGIN_TITLE_HINTS = (
    "sign in",
    "log in",
    "login",
    "authentication required",
    "access denied",
)


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "source"


def _extension(content_type: str) -> str:
    lower = content_type.casefold()
    if "json" in lower:
        return ".json"
    if "html" in lower:
        return ".html"
    if "xml" in lower:
        return ".xml"
    return ".bin"


def _title(raw: bytes, content_type: str) -> str | None:
    if "html" not in content_type.casefold():
        return None
    text = raw.decode("utf-8", errors="replace")
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _read_bounded(response: requests.Response, max_bytes: int) -> bytes:
    length = response.headers.get("Content-Length")
    if length and length.isdigit() and int(length) > max_bytes:
        raise SourceWatchError(f"response Content-Length exceeds {max_bytes} bytes")
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > max_bytes:
            raise SourceWatchError(f"response exceeded {max_bytes} bytes while reading")
        chunks.append(bytes(chunk))
    return b"".join(chunks)


def _login_wall_suspected(summary: dict[str, Any]) -> bool:
    final_url = str(summary.get("final_url") or "").casefold()
    title = str(summary.get("title") or "").casefold()
    return any(hint in final_url for hint in _LOGIN_URL_HINTS) or any(
        hint in title for hint in _LOGIN_TITLE_HINTS
    )


def _classify_response(
    source: SourceRecord,
    summary: dict[str, Any],
    *,
    policy: dict[str, Any],
) -> tuple[str, str]:
    """Classify one captured HTTP response without treating denial as success."""

    status = int(summary["http_status"])
    final_url = str(summary["final_url"])
    if not final_url.startswith("https://") or not host_allowed(final_url, policy):
        return "RESTRICTED", "REDIRECTED_OUTSIDE_ALLOWLIST"
    if source.access == "CDN_RESTRICTED" and status in {401, 403}:
        return "RESTRICTED", "CDN_RESTRICTED"
    if status in {401, 403}:
        return "RESTRICTED", f"HTTP_{status}"
    if _login_wall_suspected(summary):
        return "RESTRICTED", "LOGIN_WALL_SUSPECTED"
    if 200 <= status < 400:
        return "SUCCESS", "AVAILABLE"
    return "UNAVAILABLE", f"HTTP_{status}"


def fetch_source(
    source: SourceRecord,
    *,
    policy: dict[str, Any],
    session: requests.Session | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Capture one bounded HTTP response, including public denial responses."""

    if not host_allowed(source.url, policy):
        raise SourceWatchError(f"host is not allowed for source {source.source_id}")
    parsed = urlparse(source.url)
    if parsed.scheme != "https":
        raise SourceWatchError("only HTTPS sources are allowed")
    client = session or requests.Session()
    try:
        response = client.get(
            source.url,
            timeout=30,
            stream=True,
            allow_redirects=True,
            headers={
                "User-Agent": "Roman-Observatory-Data-System/0.1 (+metadata-only)",
                "Accept": "application/json,text/html,text/plain,*/*;q=0.2",
            },
        )
    except requests.RequestException as exc:
        raise SourceWatchError(f"transport failed: {exc.__class__.__name__}") from exc
    raw = _read_bounded(response, int(policy["max_public_page_bytes"]))
    content_type = response.headers.get("Content-Type", "")
    summary = {
        "requested_url": source.url,
        "final_url": str(response.url),
        "http_status": int(response.status_code),
        "content_type": content_type,
        "last_modified": response.headers.get("Last-Modified"),
        "etag": response.headers.get("ETag"),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "raw_size_bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "title": _title(raw, content_type),
    }
    return raw, summary


def _previous_hashes(path: Path | None) -> dict[str, str]:
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    results = value.get("sources", []) if isinstance(value, dict) else []
    return {
        str(item["source_id"]): str(item["raw_sha256"])
        for item in results
        if isinstance(item, dict) and item.get("source_id") and item.get("raw_sha256")
    }


def run_source_watch(
    *,
    sources_path: Path,
    policy_path: Path,
    outdir: Path,
    previous_manifest: Path | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Capture every eligible configured source once; no linked products are followed."""

    policy = load_policy(policy_path)
    sources = eligible_public_sources(load_sources(sources_path))
    prior = _previous_hashes(previous_manifest)
    outdir.mkdir(parents=True, exist_ok=True)
    raw_dir = outdir / "raw"
    raw_dir.mkdir(exist_ok=True)
    results: list[dict[str, Any]] = []
    successes = 0
    restricted = 0
    unavailable = 0
    captured_responses = 0
    expectation_mismatches = 0
    expected_restricted = sum(
        source.raw.get("expected_watch_status") == "RESTRICTED" for source in sources
    )

    for source in sources:
        expected_status = str(source.raw.get("expected_watch_status", "SUCCESS"))
        expected_availability = source.raw.get("expected_availability_state")
        record: dict[str, Any] = {
            "source_id": source.source_id,
            "name": source.name,
            "organization": source.organization,
            "authority": source.authority,
            "source_class": source.source_class,
            "access": source.access,
            "poll_mode": source.poll_mode,
            "expected_status": expected_status,
            "expected_availability_state": expected_availability,
            "requested_url": source.url,
            "final_url": None,
            "http_status": None,
            "raw_sha256": None,
            "raw_size_bytes": None,
            "automatic_product_download": False,
            "products_downloaded": 0,
        }
        try:
            raw, summary = fetch_source(source, policy=policy, session=session)
            suffix = _extension(str(summary["content_type"]))
            raw_path = raw_dir / f"{_slug(source.source_id)}{suffix}"
            raw_path.write_bytes(raw)
            captured_responses += 1

            current = str(summary["raw_sha256"])
            previous = prior.get(source.source_id)
            if previous is None:
                change_state = "FIRST_CAPTURE"
            elif previous == current:
                change_state = "UNCHANGED"
            else:
                change_state = "CHANGED"

            source_status, availability_state = _classify_response(
                source,
                summary,
                policy=policy,
            )
            expectation_met = source_status == expected_status and (
                expected_availability is None
                or availability_state == expected_availability
            )
            if not expectation_met:
                expectation_mismatches += 1
            record.update(summary)
            record.update(
                {
                    "status": source_status,
                    "availability_state": availability_state,
                    "expectation_met": expectation_met,
                    "change_state": change_state,
                    "previous_raw_sha256": previous,
                    "raw_path": str(raw_path.relative_to(outdir)),
                }
            )
            if source_status == "SUCCESS":
                successes += 1
            elif source_status == "RESTRICTED":
                restricted += 1
            else:
                unavailable += 1
        except SourceWatchError as exc:
            unavailable += 1
            expectation_met = expected_status == "UNAVAILABLE"
            if not expectation_met:
                expectation_mismatches += 1
            record.update(
                {
                    "status": "UNAVAILABLE",
                    "availability_state": "NO_CAPTURE",
                    "expectation_met": expectation_met,
                    "error": str(exc),
                    "change_state": "UNKNOWN",
                    "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                }
            )
        results.append(record)

    if successes == len(results):
        status = "SUCCESS"
    elif captured_responses:
        status = "PARTIAL"
    else:
        status = "FAILED"
    expected_run_status = "PARTIAL" if expected_restricted else "SUCCESS"
    manifest = {
        "manifest_version": "1.1.0",
        "status": status,
        "expected_run_status": expected_run_status,
        "run_status_matches_expectation": (
            status == expected_run_status and expectation_mismatches == 0
        ),
        "mission": "ROMAN",
        "domain": "ASTRONOMICAL_OBSERVATORY",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_count": len(results),
        "successful_source_count": successes,
        "restricted_source_count": restricted,
        "expected_restricted_source_count": expected_restricted,
        "unavailable_source_count": unavailable,
        "captured_response_count": captured_responses,
        "expectation_mismatch_count": expectation_mismatches,
        "failed_source_count": unavailable,
        "automatic_product_downloads_enabled": False,
        "products_downloaded": 0,
        "source_registry_path": str(sources_path),
        "download_policy_path": str(policy_path),
        "sources": results,
        "firewall": {
            "sun_earth_l1_space_weather_allowed": False,
            "plasma_pipeline_allowed": False,
            "chi_B24M_allowed": False,
            "gannon_holdout_allowed": False,
        },
    }
    _write_json(outdir / "source_watch_manifest.json", manifest)
    return manifest
