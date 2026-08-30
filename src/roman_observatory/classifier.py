"""Conservative Roman provenance and processing-level classification."""

from __future__ import annotations

from typing import Any, Iterable


ALLOWED_ORIGIN_CLASSES = {
    "OFFICIAL_INFO",
    "SIMULATED",
    "GROUND_TEST",
    "FLIGHT_ENGINEERING_PUBLIC",
    "FLIGHT_SCIENCE",
    "COMMUNITY_DERIVED",
    "ROMAN_SYSTEM_DERIVED",
    "UNKNOWN_QUARANTINE",
}


def _flatten_text(record: dict[str, Any]) -> str:
    values: list[str] = []
    for key, value in record.items():
        if isinstance(value, (str, int, float, bool)):
            values.append(f"{key}={value}")
        elif isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray, dict)):
            values.extend(str(item) for item in value)
    return " ".join(values).casefold()


def classify_record(
    record: dict[str, Any],
    *,
    source_id: str | None = None,
    source_class: str | None = None,
) -> str:
    """Classify a record without promoting ambiguity to flight provenance."""

    if source_class in ALLOWED_ORIGIN_CLASSES and source_class != "OFFICIAL_INFO":
        return source_class
    if source_id == "MAST_WFI_TRIPLET_TEST":
        return "GROUND_TEST"
    if source_id in {
        "ROMAN_DATA_WORKSHOP_REPOSITORY",
        "ROMAN_DATA_WORKSHOP_DOWNLOAD_SCRIPT",
        "IPAC_ROMAN_SIMULATIONS_INSTRUMENT",
    }:
        return "SIMULATED"

    explicit = record.get("origin_class")
    if explicit in ALLOWED_ORIGIN_CLASSES:
        if explicit.startswith("FLIGHT_") and record.get("flight_provenance_confirmed") is not True:
            return "UNKNOWN_QUARANTINE"
        return str(explicit)

    text = _flatten_text(record)
    ground_tokens = ("triplet", "dcl", "tvac", "ground_test", "ground test")
    simulated_tokens = (
        "simulated",
        "simulation",
        "roman_data_workshop",
        "build22",
        "roman i-sim",
        "stips",
        "corgisim",
        "openuniverse",
    )
    if any(token in text for token in ground_tokens):
        return "GROUND_TEST"
    if any(token in text for token in simulated_tokens):
        return "SIMULATED"
    if source_class == "OFFICIAL_INFO":
        return "OFFICIAL_INFO"
    return "UNKNOWN_QUARANTINE"


def normalize_data_level(raw_level: Any, *, instrument: str | None) -> str:
    """Return a namespaced Roman processing level or NOT_APPLICABLE.

    The raw token ``L1`` is never returned because it collides with the
    Sun-Earth L1 location used by space-weather programs.
    """

    if raw_level is None:
        return "NOT_APPLICABLE"
    token = str(raw_level).strip().upper().replace(" ", "_")
    if token in {"NOT_APPLICABLE", "N/A", "NONE"}:
        return "NOT_APPLICABLE"
    inst = (instrument or "").strip().upper()
    aliases = {
        "WFI": {
            "0": "WFI_LEVEL_0_RESTRICTED",
            "L0": "WFI_LEVEL_0_RESTRICTED",
            "LEVEL_0": "WFI_LEVEL_0_RESTRICTED",
            "1": "WFI_LEVEL_1",
            "L1": "WFI_LEVEL_1",
            "LEVEL_1": "WFI_LEVEL_1",
            "2": "WFI_LEVEL_2",
            "L2": "WFI_LEVEL_2",
            "LEVEL_2": "WFI_LEVEL_2",
            "3": "WFI_LEVEL_3",
            "L3": "WFI_LEVEL_3",
            "LEVEL_3": "WFI_LEVEL_3",
            "4": "WFI_LEVEL_4",
            "L4": "WFI_LEVEL_4",
            "LEVEL_4": "WFI_LEVEL_4",
            "5": "WFI_LEVEL_5",
            "L5": "WFI_LEVEL_5",
            "LEVEL_5": "WFI_LEVEL_5",
        },
        "CGI": {
            "0": "CGI_LEVEL_0_RESTRICTED",
            "L0": "CGI_LEVEL_0_RESTRICTED",
            "LEVEL_0": "CGI_LEVEL_0_RESTRICTED",
            "1": "CGI_LEVEL_1",
            "L1": "CGI_LEVEL_1",
            "LEVEL_1": "CGI_LEVEL_1",
            "2A": "CGI_LEVEL_2A",
            "L2A": "CGI_LEVEL_2A",
            "LEVEL_2A": "CGI_LEVEL_2A",
            "2B": "CGI_LEVEL_2B",
            "L2B": "CGI_LEVEL_2B",
            "LEVEL_2B": "CGI_LEVEL_2B",
        },
    }
    if inst not in aliases:
        return "NOT_APPLICABLE"
    return aliases[inst].get(token, "NOT_APPLICABLE")
