from __future__ import annotations

import ast
from pathlib import Path
import json


FORBIDDEN_IMPORT_ROOTS = {
    "observatory",
    "historical",
    "gannon",
    "dscovr",
    "space_weather",
    "solar_wind",
    "chi_B24M",
}


def test_no_cross_program_imports() -> None:
    for path in Path("src").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert name.split(".")[0] not in FORBIDDEN_IMPORT_ROOTS, (path, name)


def test_export_contract_keeps_all_non_astronomical_paths_closed() -> None:
    value = json.loads(Path("config/nvcpp_export_contract.v1.json").read_text())
    assert value["destination_domain"] == "ASTRONOMICAL_OBSERVATORY"
    assert value["sun_earth_l1_space_weather_allowed"] is False
    assert value["plasma_pipeline_allowed"] is False
    assert value["chi_B24M_allowed"] is False
    assert value["gannon_holdout_allowed"] is False
