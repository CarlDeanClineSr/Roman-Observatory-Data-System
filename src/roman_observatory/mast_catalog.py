"""Build a bounded Roman MAST observation/product metadata catalog."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from typing import Any

import requests

from .classifier import classify_record
from .contracts import load_json, validate_mast
from .mast_client import MastClient, MastError, MastInvocation


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return path


def _write_raw(path: Path, invocation: MastInvocation) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(invocation.raw_bytes)
    result = invocation.summary()
    result["raw_path"] = str(path)
    return result


def _obsid(row: dict[str, Any]) -> str | None:
    for key in ("obsid", "obsID", "obs_id", "obsId"):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def run_mast_catalog(
    *,
    config_path: Path,
    outdir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]:
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
    observations: list[dict[str, Any]] = []
    products: list[dict[str, Any]] = []

    try:
        missions, invocation = client.list_missions()
        raw_evidence.append(_write_raw(raw_dir / "mast_missions.json", invocation))
    except MastError as exc:
        errors.append(f"missions: {exc}")

    observation_limit = int(config["sample_observation_row_limit"])
    for collection in config["candidate_obs_collections"]:
        try:
            count, count_invocation = client.count_collection(collection)
            collection_counts[collection] = count
            raw_evidence.append(
                _write_raw(
                    raw_dir / f"mast_count_{collection.casefold()}.json", count_invocation
                )
            )
            if count > 0:
                sample = client.sample_collection(collection, pagesize=observation_limit)
                raw_evidence.append(
                    _write_raw(
                        raw_dir / f"mast_observations_{collection.casefold()}.json", sample
                    )
                )
                rows = sample.payload.get("data", [])
                if not isinstance(rows, list):
                    raise MastError("observation sample data is not a list")
                for row in rows[:observation_limit]:
                    if not isinstance(row, dict):
                        continue
                    normalized = dict(row)
                    normalized["roman_origin_class"] = classify_record(
                        normalized, source_id="MAST_ROMAN_MISSION"
                    )
                    normalized["flight_data_assumed"] = False
                    observations.append(normalized)
        except (MastError, ValueError) as exc:
            collection_counts.setdefault(collection, 0)
            errors.append(f"{collection}: {exc}")

    obsids: list[str] = []
    for row in observations:
        value = _obsid(row)
        if value and value not in obsids:
            obsids.append(value)
        if len(obsids) >= int(config["sample_product_observation_limit"]):
            break
    if obsids:
        try:
            product_invocation = client.list_products(
                obsids, pagesize=int(config["sample_product_row_limit"])
            )
            raw_evidence.append(
                _write_raw(raw_dir / "mast_products.json", product_invocation)
            )
            rows = product_invocation.payload.get("data", [])
            if not isinstance(rows, list):
                raise MastError("product sample data is not a list")
            for row in rows[: int(config["sample_product_row_limit"])]:
                if not isinstance(row, dict):
                    continue
                normalized = dict(row)
                normalized["roman_origin_class"] = classify_record(
                    normalized, source_id="MAST_ROMAN_MISSION"
                )
                normalized["download_decision"] = "METADATA_ONLY"
                normalized["downloaded"] = False
                products.append(normalized)
        except (MastError, ValueError) as exc:
            errors.append(f"products: {exc}")

    _write_json(outdir / "mast_observations.json", observations)
    _write_json(outdir / "mast_products.json", products)
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
        "manifest_version": "1.0.0",
        "status": status,
        "mission": "ROMAN",
        "domain": "ASTRONOMICAL_OBSERVATORY",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "metadata_only": True,
        "flight_data_assumed": False,
        "products_downloaded": 0,
        "mission_list": missions,
        "collection_counts": collection_counts,
        "observation_row_count": len(observations),
        "product_row_count": len(products),
        "origin_class_counts": {
            label: sum(row.get("roman_origin_class") == label for row in observations + products)
            for label in sorted(
                {str(row.get("roman_origin_class")) for row in observations + products}
            )
        },
        "raw_evidence": raw_evidence,
        "raw_evidence_index_sha256": evidence_hash,
        "errors": errors,
        "outputs": {
            "observations": "mast_observations.json",
            "products": "mast_products.json",
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
