"""Create a bounded, hash-linked Roman status export for NVCPP astronomy."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from typing import Any

from .contracts import load_json
from .export_contract import validate_export_payload


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_records(manifest: dict[str, Any], *, limit: int = 100) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(manifest.get("sources"), list):
        for item in manifest["sources"][:limit]:
            if not isinstance(item, dict):
                continue
            records.append(
                {
                    "record_type": "PUBLIC_SOURCE_STATUS",
                    "source_id": item.get("source_id"),
                    "status": item.get("status"),
                    "change_state": item.get("change_state"),
                    "retrieved_utc": item.get("retrieved_utc"),
                    "raw_sha256": item.get("raw_sha256"),
                    "raw_size_bytes": item.get("raw_size_bytes"),
                }
            )
    else:
        records.append(
            {
                "record_type": "ROMAN_METADATA_STATUS",
                "status": manifest.get("status"),
                "created_utc": manifest.get("created_utc"),
                "collection_counts": manifest.get("collection_counts", {}),
                "observation_row_count": manifest.get("observation_row_count", 0),
                "product_row_count": manifest.get("product_row_count", 0),
                "origin_class_counts": manifest.get("origin_class_counts", {}),
                "products_downloaded": manifest.get("products_downloaded", 0),
            }
        )
    return records


def build_export(
    *,
    source_manifest: Path,
    contract_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    source = load_json(source_manifest)
    contract = load_json(contract_path)
    payload = {
        "export_contract_version": contract["export_contract_version"],
        "export_kind": "PUBLIC_MISSION_STATUS",
        "source_system": "ROMAN_OBSERVATORY_DATA_SYSTEM",
        "destination_system": "NVCPP",
        "destination_domain": "ASTRONOMICAL_OBSERVATORY",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_manifest_path": str(source_manifest),
        "source_manifest_sha256": sha256_file(source_manifest),
        "sun_earth_l1_space_weather_allowed": False,
        "plasma_pipeline_allowed": False,
        "chi_B24M_allowed": False,
        "gannon_holdout_allowed": False,
        "raw_telescope_arrays_included": False,
        "bulk_products_included": False,
        "records": _safe_records(source),
    }
    validate_export_payload(payload, contract)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return payload
