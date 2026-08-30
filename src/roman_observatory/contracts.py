"""Validation for the frozen Roman bootstrap contracts."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
from typing import Any
from urllib.parse import urlparse

from . import DOMAIN, MISSION


class ContractError(ValueError):
    """Raised when a Roman system contract violates a frozen boundary."""


REQUIRED_BLOCKED_DESTINATIONS = {
    "SUN_EARTH_L1_SPACE_WEATHER",
    "PLASMA_PIPELINE",
    "CHI_B24M",
    "GANNON_HOLDOUT",
}
REQUIRED_HARD_DISTINCTIONS = {
    "SIMULATED_IS_NOT_FLIGHT",
    "GROUND_TEST_IS_NOT_FLIGHT",
    "TRIPLET_TEST_IS_NOT_FLIGHT",
    "WORKSHOP_BUILD22_IS_NOT_FLIGHT",
    "SUN_EARTH_L1_SPACE_WEATHER_IS_NOT_WFI_LEVEL_1",
    "SUN_EARTH_L1_SPACE_WEATHER_IS_NOT_CGI_LEVEL_1",
}
REQUIRED_CONTRACTS = (
    "sources.v1.json",
    "download_policy.v1.json",
    "product_classes.v1.json",
    "mast_metadata.v1.json",
    "workshop_build22_manifest.v1.json",
    "nvcpp_export_contract.v1.json",
    "bootstrap_freeze.v1.json",
)


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object and report a useful contract error."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing contract: {path}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"invalid JSON contract: {path}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"contract root must be an object: {path}")
    return value


def _require_identity(value: dict[str, Any], *, name: str) -> None:
    if value.get("mission") != MISSION:
        raise ContractError(f"{name}: mission must be {MISSION}")
    if value.get("domain") != DOMAIN:
        raise ContractError(f"{name}: domain must be {DOMAIN}")


def validate_sources(value: dict[str, Any]) -> dict[str, int]:
    _require_identity(value, name="sources")
    if value.get("status") != "SOURCE_REGISTRY_FROZEN_V1":
        raise ContractError("sources: status must be SOURCE_REGISTRY_FROZEN_V1")
    if value.get("automatic_product_downloads") is not False:
        raise ContractError("sources: automatic product downloads must be false")
    sources = value.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ContractError("sources: nonempty sources list required")
    seen: set[str] = set()
    enabled = 0
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ContractError(f"sources[{index}] must be an object")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise ContractError(f"sources[{index}]: source_id required")
        if source_id in seen:
            raise ContractError(f"sources: duplicate source_id {source_id}")
        seen.add(source_id)
        url = source.get("url")
        if not isinstance(url, str) or urlparse(url).scheme != "https":
            raise ContractError(f"sources[{source_id}]: HTTPS URL required")
        if source.get("automatic_product_download") is not False:
            raise ContractError(
                f"sources[{source_id}]: automatic_product_download must be false"
            )
        if source.get("enabled") is True:
            enabled += 1
        if source_id == "ROMAN_RESEARCH_NEXUS_HUB":
            if source.get("enabled") is not False:
                raise ContractError("authenticated Nexus Hub must remain disabled")
            if source.get("automated_public_scrape") is not False:
                raise ContractError("authenticated Nexus Hub scraping must remain false")
    return {"source_count": len(sources), "enabled_source_count": enabled}


def validate_download_policy(value: dict[str, Any]) -> dict[str, Any]:
    _require_identity(value, name="download policy")
    if value.get("default_mode") != "METADATA_ONLY":
        raise ContractError("download policy: default_mode must be METADATA_ONLY")
    if value.get("automatic_product_downloads_enabled") is not False:
        raise ContractError("download policy: automatic downloads must be disabled")
    if value.get("external_download_scripts_execute_automatically") is not False:
        raise ContractError("download policy: external scripts must not auto-execute")
    blocked = set(value.get("blocked_destination_domains", []))
    missing = REQUIRED_BLOCKED_DESTINATIONS - blocked
    if missing:
        raise ContractError(f"download policy: missing blocked destinations {sorted(missing)}")
    max_page = value.get("max_public_page_bytes")
    if not isinstance(max_page, int) or max_page < 1024 or max_page > 64 * 1024 * 1024:
        raise ContractError("download policy: invalid max_public_page_bytes")
    hosts = value.get("allowed_hosts")
    if not isinstance(hosts, list) or not all(isinstance(item, str) for item in hosts):
        raise ContractError("download policy: allowed_hosts must be a string list")
    return {
        "automatic_product_downloads_enabled": False,
        "max_public_page_bytes": max_page,
        "allowed_host_count": len(hosts),
    }


def validate_product_classes(value: dict[str, Any]) -> dict[str, int]:
    _require_identity(value, name="product classes")
    if value.get("bare_l1_label_allowed") is not False:
        raise ContractError("product classes: a bare L1 label must be forbidden")
    labels = value.get("data_level_labels")
    if not isinstance(labels, list) or any(label == "L1" for label in labels):
        raise ContractError("product classes: namespaced data level labels required")
    distinctions = set(value.get("hard_distinctions", []))
    missing = REQUIRED_HARD_DISTINCTIONS - distinctions
    if missing:
        raise ContractError(f"product classes: missing distinctions {sorted(missing)}")
    origins = value.get("origin_classes")
    if not isinstance(origins, list) or "UNKNOWN_QUARANTINE" not in origins:
        raise ContractError("product classes: UNKNOWN_QUARANTINE required")
    return {"origin_class_count": len(origins), "data_level_count": len(labels)}


def validate_mast(value: dict[str, Any]) -> dict[str, Any]:
    _require_identity(value, name="MAST metadata")
    if value.get("metadata_only") is not True or value.get("download_products") is not False:
        raise ContractError("MAST metadata contract must be metadata-only")
    if value.get("flight_data_assumed") is not False:
        raise ContractError("MAST metadata contract must not assume flight data")
    url = value.get("invoke_url")
    if not isinstance(url, str) or url != "https://mast.stsci.edu/api/v0/invoke":
        raise ContractError("MAST metadata contract has unexpected invoke_url")
    candidates = value.get("candidate_obs_collections")
    if not isinstance(candidates, list) or not candidates:
        raise ContractError("MAST metadata contract needs collection candidates")
    return {
        "candidate_collection_count": len(candidates),
        "sample_observation_row_limit": value.get("sample_observation_row_limit"),
        "sample_product_row_limit": value.get("sample_product_row_limit"),
    }


def validate_workshop_manifest(value: dict[str, Any]) -> dict[str, Any]:
    _require_identity(value, name="workshop manifest")
    common = value.get("common_classification")
    if not isinstance(common, dict):
        raise ContractError("workshop manifest needs common_classification")
    if common.get("origin_class") != "SIMULATED" or common.get("flight_data") is not False:
        raise ContractError("workshop manifest must be SIMULATED and non-flight")
    if common.get("download_decision") != "METADATA_ONLY_NOT_AUTHORIZED":
        raise ContractError("workshop manifest download decision changed without review")
    if value.get("automatic_download") is not False:
        raise ContractError("workshop manifest: automatic_download must be false")
    if value.get("execution_authorized") is not False:
        raise ContractError("workshop manifest: execution_authorized must be false")
    paths = value.get("remote_paths")
    if not isinstance(paths, list) or value.get("item_count") != len(paths):
        raise ContractError("workshop manifest item_count mismatch")
    if len(paths) != 36:
        raise ContractError("workshop manifest must retain the 36 pinned source paths")
    if not all(isinstance(item, str) and item for item in paths):
        raise ContractError("workshop manifest paths must be nonempty strings")
    if len(paths) != len(set(paths)):
        raise ContractError("workshop manifest contains duplicate paths")
    return {"item_count": len(paths), "execution_authorized": False}


def validate_export_contract(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("source_system") != "ROMAN_OBSERVATORY_DATA_SYSTEM":
        raise ContractError("export contract: incorrect source system")
    if value.get("destination_system") != "NVCPP":
        raise ContractError("export contract: incorrect destination system")
    if value.get("destination_domain") != DOMAIN:
        raise ContractError("export contract: destination must be astronomical")
    forbidden_true = (
        "raw_telescope_arrays_allowed",
        "bulk_products_allowed",
        "sun_earth_l1_space_weather_allowed",
        "plasma_pipeline_allowed",
        "chi_B24M_allowed",
        "gannon_holdout_allowed",
    )
    for key in forbidden_true:
        if value.get(key) is not False:
            raise ContractError(f"export contract: {key} must be false")
    return {"allowed_export_kind_count": len(value.get("allowed_export_kinds", []))}



def validate_bootstrap_freeze(value: dict[str, Any], *, project_root: Path) -> dict[str, Any]:
    _require_identity(value, name="bootstrap freeze")
    if value.get("status") != "BOOTSTRAP_CONTRACTS_FROZEN_V1":
        raise ContractError("bootstrap freeze: unexpected status")
    if value.get("hash_algorithm") != "SHA-256":
        raise ContractError("bootstrap freeze: SHA-256 required")
    files = value.get("files")
    if not isinstance(files, list) or value.get("file_count") != len(files):
        raise ContractError("bootstrap freeze: file_count mismatch")
    verified = 0
    for item in files:
        if not isinstance(item, dict):
            raise ContractError("bootstrap freeze: file entry must be an object")
        relative = item.get("path")
        expected = item.get("sha256")
        expected_size = item.get("size_bytes")
        if not isinstance(relative, str) or not relative.startswith("config/"):
            raise ContractError("bootstrap freeze: only config paths may be frozen")
        path = project_root / relative
        try:
            raw = path.read_bytes()
        except FileNotFoundError as exc:
            raise ContractError(f"bootstrap freeze: missing {relative}") from exc
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ContractError(
                f"bootstrap freeze: hash mismatch for {relative}; expected {expected}, got {actual}"
            )
        if len(raw) != expected_size:
            raise ContractError(f"bootstrap freeze: size mismatch for {relative}")
        verified += 1
    return {"verified_file_count": verified, "hash_algorithm": "SHA-256"}


def validate_all(project_root: Path) -> dict[str, Any]:
    """Validate all frozen v0.1 contracts and return a machine-readable report."""

    config = project_root / "config"
    missing = [name for name in REQUIRED_CONTRACTS if not (config / name).is_file()]
    if missing:
        raise ContractError(f"missing required contracts: {missing}")
    report = {
        "status": "VALID",
        "mission": MISSION,
        "domain": DOMAIN,
        "contracts": {
            "sources": validate_sources(load_json(config / "sources.v1.json")),
            "download_policy": validate_download_policy(
                load_json(config / "download_policy.v1.json")
            ),
            "product_classes": validate_product_classes(
                load_json(config / "product_classes.v1.json")
            ),
            "mast_metadata": validate_mast(load_json(config / "mast_metadata.v1.json")),
            "workshop_manifest": validate_workshop_manifest(
                load_json(config / "workshop_build22_manifest.v1.json")
            ),
            "nvcpp_export": validate_export_contract(
                load_json(config / "nvcpp_export_contract.v1.json")
            ),
            "bootstrap_freeze": validate_bootstrap_freeze(
                load_json(config / "bootstrap_freeze.v1.json"),
                project_root=project_root,
            ),
        },
    }
    return report
