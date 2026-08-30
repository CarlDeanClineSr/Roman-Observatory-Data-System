"""Build a mission-list and collection-count-only Roman MAST evidence package."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from typing import Any

import requests

from .contracts import load_json, validate_mast
from .mast_client import MastClient, MastError, MastInvocation


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def _write_raw(path: Path, invocation: MastInvocation) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(invocation.raw_bytes)
    result = invocation.summary()
    result["raw_path"] = str(path)
    return result


def run_mast_catalog(
    *,
    config_path: Path,
    outdir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Run only the two authorized v0.1 query forms and stop."""

    config = load_json(config_path)
    validate_mast(config)
    outdir.mkdir(parents=True, exist_ok=True)
    raw_dir = outdir / "raw"
    raw_dir.mkdir(exist_ok=True)
    client = MastClient(
        invoke_url=config["invoke_url"],
        timeout_seconds=float(config["timeout_seconds"]),
        max_poll_seconds=float(config["max_poll_seconds"]),
        session=session,
    )

    errors: list[str] = []
    raw_evidence: list[dict[str, Any]] = []
    missions: list[str] = []
    collection_counts: dict[str, int] = {}

    try:
        missions, invocation = client.list_missions(
            max_rows=int(config["mission_list_row_cap"])
        )
        raw_evidence.append(_write_raw(raw_dir / "mast_missions.json", invocation))
    except (MastError, ValueError) as exc:
        errors.append(f"missions: {exc}")

    candidates = list(config["candidate_obs_collections"])
    query_cap = int(config["collection_query_cap"])
    if len(candidates) > query_cap:  # defensive; validate_mast also enforces this.
        raise ValueError("candidate collection count exceeds collection_query_cap")
    for collection in candidates:
        try:
            count, count_invocation = client.count_collection(
                collection,
                max_rows=int(config["count_response_row_cap"]),
            )
            collection_counts[collection] = count
            raw_evidence.append(
                _write_raw(
                    raw_dir / f"mast_count_{collection.casefold()}.json",
                    count_invocation,
                )
            )
        except (MastError, ValueError) as exc:
            collection_counts.setdefault(collection, 0)
            errors.append(f"{collection}: {exc}")

    _write_json(outdir / "mast_mission_list.json", missions)
    _write_json(outdir / "mast_collection_counts.json", collection_counts)
    evidence_hash = hashlib.sha256(
        json.dumps(raw_evidence, sort_keys=True).encode("utf-8")
    ).hexdigest()
    transport_successes = len(raw_evidence)
    if transport_successes and not errors:
        status = "SUCCESS"
    elif transport_successes:
        status = "PARTIAL"
    else:
        status = "FAILED"
    manifest = {
        "manifest_version": "1.1.0",
        "status": status,
        "mission": "ROMAN",
        "domain": "ASTRONOMICAL_OBSERVATORY",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "query_scope": config["query_scope"],
        "metadata_only": True,
        "flight_data_assumed": False,
        "mission_list_row_cap": int(config["mission_list_row_cap"]),
        "mission_row_count": len(missions),
        "collection_query_cap": query_cap,
        "collection_query_count": len(candidates),
        "count_response_row_cap": int(config["count_response_row_cap"]),
        "mission_list": missions,
        "collection_counts": collection_counts,
        "observation_queries_executed": 0,
        "observation_row_count": 0,
        "product_queries_executed": 0,
        "product_row_count": 0,
        "products_downloaded": 0,
        "raw_evidence": raw_evidence,
        "raw_evidence_index_sha256": evidence_hash,
        "errors": errors,
        "outputs": {
            "mission_list": "mast_mission_list.json",
            "collection_counts": "mast_collection_counts.json",
        },
        "firewall": {
            "sun_earth_l1_space_weather_allowed": False,
            "plasma_pipeline_allowed": False,
            "chi_B24M_allowed": False,
            "gannon_holdout_allowed": False,
        },
    }
    _write_json(outdir / "mast_catalog_manifest.json", manifest)
    return manifest
