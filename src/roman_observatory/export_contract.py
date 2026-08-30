"""Validation for one small Roman-to-NVCPP astronomical export."""

from __future__ import annotations

from typing import Any

from .contracts import ContractError, validate_export_contract


def validate_export_payload(payload: dict[str, Any], contract: dict[str, Any]) -> None:
    validate_export_contract(contract)
    required = set(contract.get("required_fields", []))
    missing = required - set(payload)
    if missing:
        raise ContractError(f"export payload missing fields: {sorted(missing)}")
    if payload.get("destination_domain") != "ASTRONOMICAL_OBSERVATORY":
        raise ContractError("export destination domain changed")
    forbidden = {
        "sun_earth_l1_space_weather_allowed": False,
        "plasma_pipeline_allowed": False,
        "chi_B24M_allowed": False,
        "gannon_holdout_allowed": False,
        "raw_telescope_arrays_included": False,
        "bulk_products_included": False,
    }
    for key, expected in forbidden.items():
        if payload.get(key) is not expected:
            raise ContractError(f"export payload firewall violation: {key}")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ContractError("export records must be a list")
