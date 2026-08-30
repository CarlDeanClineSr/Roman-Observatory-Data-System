from __future__ import annotations

from pathlib import Path
import json
from urllib.parse import unquote

from roman_observatory.mast_catalog import run_mast_catalog
from roman_observatory.mast_client import MastClient


class FakeResponse:
    def __init__(self, payload):
        self.status_code = 200
        self.url = "https://mast.stsci.edu/api/v0/invoke"
        self.headers = {"Content-Type": "application/json"}
        self.content = json.dumps(payload).encode("utf-8")


class RoutingSession:
    def __init__(self, expected_product_obsid: str | None = "42"):
        self.expected_product_obsid = expected_product_obsid

    def post(self, url, data, headers, timeout):
        del url, headers, timeout
        request = json.loads(unquote(data.removeprefix("request=")))
        service = request["service"]
        if service == "Mast.Missions.List":
            return FakeResponse({"status": "COMPLETE", "data": [{"distinctValue": "Roman"}]})
        if service == "Mast.Caom.Filtered":
            columns = request["params"]["columns"]
            collection = request["params"]["filters"][0]["values"][0]
            if columns == "COUNT_BIG(*)":
                count = 1 if collection == "Roman" else 0
                return FakeResponse({"status": "COMPLETE", "data": [{"count": count}]})
            return FakeResponse(
                {
                    "status": "COMPLETE",
                    "data": [{"obsid": "42", "obs_collection": "Roman", "target_name": "demo"}],
                }
            )
        if service == "Mast.Caom.Products":
            if self.expected_product_obsid is not None:
                assert request["params"]["obsid"] == self.expected_product_obsid
            return FakeResponse(
                {
                    "status": "COMPLETE",
                    "data": [{"obsid": "42", "productFilename": "ambiguous.asdf", "size": 12}],
                }
            )
        raise AssertionError(service)


def test_mast_product_service_uses_comma_joined_obsids() -> None:
    client = MastClient(
        invoke_url="https://mast.stsci.edu/api/v0/invoke",
        session=RoutingSession(expected_product_obsid="1,2,3"),
    )
    invocation = client.list_products([1, 2, 3], pagesize=10)
    assert invocation.request["service"] == "Mast.Caom.Products"
    assert invocation.request["params"]["obsid"] == "1,2,3"


def test_mast_catalog_is_metadata_only_and_ambiguous_rows_quarantine(tmp_path: Path) -> None:
    manifest = run_mast_catalog(
        config_path=Path("config/mast_metadata.v1.json"),
        outdir=tmp_path / "mast",
        session=RoutingSession(),
    )
    assert manifest["status"] == "SUCCESS"
    assert manifest["products_downloaded"] == 0
    assert manifest["flight_data_assumed"] is False
    observations = json.loads((tmp_path / "mast/mast_observations.json").read_text())
    products = json.loads((tmp_path / "mast/mast_products.json").read_text())
    assert observations[0]["roman_origin_class"] == "UNKNOWN_QUARANTINE"
    assert products[0]["roman_origin_class"] == "UNKNOWN_QUARANTINE"
    assert products[0]["downloaded"] is False
