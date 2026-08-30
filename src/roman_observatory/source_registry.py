"""Typed access to the frozen Roman public-source registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .contracts import load_json, validate_sources


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    name: str
    organization: str
    authority: str
    source_class: str
    access: str
    poll_mode: str
    url: str
    enabled: bool
    capture_raw_response: bool
    automatic_product_download: bool
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SourceRecord":
        return cls(
            source_id=str(value["source_id"]),
            name=str(value["name"]),
            organization=str(value["organization"]),
            authority=str(value["authority"]),
            source_class=str(value["source_class"]),
            access=str(value["access"]),
            poll_mode=str(value["poll_mode"]),
            url=str(value["url"]),
            enabled=bool(value.get("enabled", False)),
            capture_raw_response=bool(value.get("capture_raw_response", False)),
            automatic_product_download=bool(
                value.get("automatic_product_download", False)
            ),
            raw=dict(value),
        )


def load_sources(path: Path) -> list[SourceRecord]:
    value = load_json(path)
    validate_sources(value)
    sources = value["sources"]
    return [SourceRecord.from_dict(source) for source in sources]


def eligible_public_sources(sources: Iterable[SourceRecord]) -> list[SourceRecord]:
    """Return configured sources safe for unauthenticated bounded capture."""

    result: list[SourceRecord] = []
    for source in sources:
        if not source.enabled or not source.capture_raw_response:
            continue
        if source.access in {
            "MYST_AUTHENTICATED",
            "MANUAL_AUTHENTICATED_ONLY",
            "RESTRICTED",
        }:
            continue
        result.append(source)
    return result
