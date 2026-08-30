from pathlib import Path
import json

from roman_observatory.exporter import build_export


def test_export_is_small_and_firewalled(tmp_path: Path) -> None:
    manifest = tmp_path / "source.json"
    manifest.write_text(
        json.dumps(
            {
                "status": "SUCCESS",
                "sources": [
                    {
                        "source_id": "NASA_ROMAN_HOME",
                        "status": "SUCCESS",
                        "change_state": "FIRST_CAPTURE",
                        "retrieved_utc": "2026-08-30T00:00:00Z",
                        "raw_sha256": "a" * 64,
                        "raw_size_bytes": 12,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "nvcpp_approved_export.json"
    payload = build_export(
        source_manifest=manifest,
        contract_path=Path("config/nvcpp_export_contract.v1.json"),
        out_path=out,
    )
    assert payload["destination_domain"] == "ASTRONOMICAL_OBSERVATORY"
    assert payload["raw_telescope_arrays_included"] is False
    assert payload["chi_B24M_allowed"] is False
    assert out.stat().st_size < 100_000
