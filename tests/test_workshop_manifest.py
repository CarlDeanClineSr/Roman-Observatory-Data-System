import json
from pathlib import Path


def test_official_workshop_list_is_frozen_without_execution() -> None:
    value = json.loads(
        Path("config/workshop_build22_manifest.v1.json").read_text(encoding="utf-8")
    )
    assert value["source_file"] == "data/download.py"
    assert value["source_blob_sha"] == "17b4cc0d3c4ac8b5c31ec18bf71df143b0ac7e81"
    assert value["item_count"] == 36
    assert value["common_classification"]["origin_class"] == "SIMULATED"
    assert value["common_classification"]["flight_data"] is False
    assert value["automatic_download"] is False
    assert value["execution_authorized"] is False
    assert len(value["remote_paths"]) == 36
    assert value["common_classification"]["download_decision"] == "METADATA_ONLY_NOT_AUTHORIZED"
