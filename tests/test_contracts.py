from pathlib import Path

from roman_observatory.contracts import validate_all


def test_all_bootstrap_contracts_validate() -> None:
    report = validate_all(Path("."))
    assert report["status"] == "VALID"
    assert report["mission"] == "ROMAN"
    assert report["domain"] == "ASTRONOMICAL_OBSERVATORY"
    assert report["contracts"]["workshop_manifest"]["item_count"] == 36
