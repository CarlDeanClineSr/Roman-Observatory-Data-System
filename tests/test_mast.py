from __future__ import annotations

from pathlib import Path
import json
from urllib.parse import unquote

import pytest

from roman_observatory.mast_catalog import run_mast_catalog
from roman_observatory.mast_client import MastClient, MastError


class FakeResponse:
    def __init__(self, payload):
        self.status_code = 200
        self.url = "https://mast.stsci.edu/api/v0/invoke"
        self.headers = {"Content-Type": "application/json"}
        self.content = json.dumps(payload).encode("utf-8")


class RoutingSession:
    def __init__(
        self,
        *,
        mission_rows: list[dict[str, object]] | None = None,
        count_rows: list[dict[str, object]] | None = None,
    ) -> None:
        self.mission_rows = mission_rows or [{"distinctValue": "Roman"}]
        self.count_rows = count_rows
        self.requests: list[dict[str, object]] = []

    def post(self, url, data, headers, timeout):
        del url, headers, timeout
        request = json.loads(unquote(data.removeprefix("request=")))
        self.requests.append(request)
        service = request["service"]
        if service == "Mast.Missions.List":
            return FakeResponse({"status": "COMPLETE", "data": self.mission_rows})
        if service == "Mast.Caom.Filtered":
            assert request["params"]["columns"] == "COUNT_BIG(*)"
            collection = request["params"]["filters"][0]["values"][0]
            if self.count_rows is not None:
                rows = self.count_rows
            else:
                count = 1 if collection == "Roman" else 0
                rows = [{"count": count}]
            return FakeResponse({"status": "COMPLETE", "data": rows})
        raise AssertionError(f"unauthorized MAST service requested: {service}")


def test_mast_catalog_only_queries_mission_list_and_collection_counts(tmp_path: Path) -> None:
    session = RoutingSession()
    manifest = run_mast_catalog(
        config_path=Path("config/mast_metadata.v1.json"),
        outdir=tmp_path / "mast",
        session=session,
    )
    assert manifest["status"] == "SUCCESS"
    assert manifest["query_scope"] == "MISSION_LIST_AND_COLLECTION_COUNTS_ONLY"
    assert manifest["products_downloaded"] == 0
    assert manifest["flight_data_assumed"] is False
    assert manifest["observation_queries_executed"] == 0
    assert manifest["observation_row_count"] == 0
    assert manifest["product_queries_executed"] == 0
    assert manifest["product_row_count"] == 0
    assert manifest["mission_row_count"] == 1
    assert manifest["collection_query_count"] == 1
    assert manifest["collection_counts"] == {"Roman": 1}
    services = [request["service"] for request in session.requests]
    assert services == [
        "Mast.Missions.List",
        "Mast.Caom.Filtered",
    ]
    assert all(
        request.get("params", {}).get("columns") == "COUNT_BIG(*)"
        for request in session.requests[1:]
    )
    assert json.loads((tmp_path / "mast/mast_mission_list.json").read_text()) == [
        "Roman"
    ]
    assert json.loads((tmp_path / "mast/mast_collection_counts.json").read_text()) == {
        "Roman": 1,
    }
    assert not (tmp_path / "mast/mast_observations.json").exists()
    assert not (tmp_path / "mast/mast_products.json").exists()


def test_mast_client_does_not_expose_observation_or_product_queries() -> None:
    client = MastClient(
        invoke_url="https://mast.stsci.edu/api/v0/invoke",
        session=RoutingSession(),
    )
    assert not hasattr(client, "sample_collection")
    assert not hasattr(client, "list_products")


def test_mission_list_hard_row_cap_stops_overflow() -> None:
    client = MastClient(
        invoke_url="https://mast.stsci.edu/api/v0/invoke",
        session=RoutingSession(
            mission_rows=[{"distinctValue": "Roman"}, {"distinctValue": "HST"}]
        ),
    )
    with pytest.raises(MastError, match="exceeding hard cap 1"):
        client.list_missions(max_rows=1)


def test_collection_count_hard_row_cap_stops_overflow() -> None:
    client = MastClient(
        invoke_url="https://mast.stsci.edu/api/v0/invoke",
        session=RoutingSession(count_rows=[{"count": 1}, {"count": 2}]),
    )
    with pytest.raises(MastError, match="exceeding hard cap 1"):
        client.count_collection("Roman", max_rows=1)
