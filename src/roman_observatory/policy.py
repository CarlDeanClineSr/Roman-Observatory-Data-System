"""Metadata-first retrieval and Roman/NVCPP firewall policy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .contracts import (
    REQUIRED_BLOCKED_DESTINATIONS,
    ContractError,
    load_json,
    validate_download_policy,
)


@dataclass(frozen=True)
class DownloadDecision:
    decision: str
    permitted: bool
    reason: str
    size_bytes: int | None
    filename: str | None


def load_policy(path: Path) -> dict[str, Any]:
    value = load_json(path)
    validate_download_policy(value)
    return value


def host_allowed(url: str, policy: dict[str, Any]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    allowed = {str(item).lower() for item in policy.get("allowed_hosts", [])}
    return host in allowed


def compound_suffix(filename: str) -> str:
    lower = filename.lower()
    for suffix in (".tar.gz", ".tar.bz2"):
        if lower.endswith(suffix):
            return suffix
    dot = lower.rfind(".")
    return lower[dot:] if dot >= 0 else ""


def decide_product(
    *,
    filename: str | None,
    size_bytes: int | None,
    source_access: str,
    policy: dict[str, Any],
) -> DownloadDecision:
    """Return a policy decision; this function never performs a download."""

    if source_access not in {"PUBLIC", "PUBLIC_DOCUMENTATION"}:
        return DownloadDecision(
            "METADATA_ONLY_RESTRICTED_SOURCE",
            False,
            "source is not an approved unauthenticated public product source",
            size_bytes,
            filename,
        )
    if not policy.get("automatic_product_downloads_enabled", False):
        return DownloadDecision(
            "METADATA_ONLY_AUTOMATIC_DOWNLOAD_DISABLED",
            False,
            "v0.1 contract disables automatic product downloads",
            size_bytes,
            filename,
        )
    if filename:
        suffix = compound_suffix(filename)
        if suffix in set(policy.get("automatic_blocked_suffixes", [])):
            return DownloadDecision(
                "REQUIRE_MANUAL_APPROVAL_BLOCKED_CONTAINER",
                False,
                f"container suffix {suffix} is blocked from automatic retrieval",
                size_bytes,
                filename,
            )
    if size_bytes is None:
        return DownloadDecision(
            "REQUIRE_MANUAL_APPROVAL_UNKNOWN_SIZE",
            False,
            "product size is unknown",
            size_bytes,
            filename,
        )
    if size_bytes > int(policy["max_auto_download_bytes"]):
        return DownloadDecision(
            "REQUIRE_MANUAL_APPROVAL_SIZE_LIMIT",
            False,
            "product exceeds the automatic per-file size ceiling",
            size_bytes,
            filename,
        )
    return DownloadDecision(
        "ELIGIBLE_BUT_NOT_EXECUTED",
        True,
        "product passed static policy but no download action exists in v0.1",
        size_bytes,
        filename,
    )


def assert_firewall(policy: dict[str, Any]) -> None:
    blocked = set(policy.get("blocked_destination_domains", []))
    missing = REQUIRED_BLOCKED_DESTINATIONS - blocked
    if missing:
        raise ContractError(f"Roman firewall missing destinations: {sorted(missing)}")
