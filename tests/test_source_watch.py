from __future__ import annotations

from pathlib import Path
import json

from roman_observatory.source_watch import run_source_watch


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        url: str = "https://science.nasa.gov/mission/roman-space-telescope/",
        content: bytes = b"<html><title>Roman</title><body>evidence</body></html>",
    ) -> None:
        self.status_code = status_code
        self.url = url
        self.headers = {"Content-Type": "text/html", "ETag": '"abc"'}
        self.content = content

    def iter_content(self, chunk_size: int):
        del chunk_size
        yield self.content


class FakeSession:
    def __init__(self, response: FakeResponse | None = None) -> None:
        self.response = response or FakeResponse()

    def get(self, *args, **kwargs):
        del args, kwargs
        return self.response


def _single_source_registry(tmp_path: Path) -> Path:
    original = json.loads(Path("config/sources.v1.json").read_text(encoding="utf-8"))
    original["sources"] = [original["sources"][0]]
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(original), encoding="utf-8")
    return path


def test_source_watch_preserves_hash_and_downloads_no_products(tmp_path: Path) -> None:
    manifest = run_source_watch(
        sources_path=_single_source_registry(tmp_path),
        policy_path=Path("config/download_policy.v1.json"),
        outdir=tmp_path / "run",
        session=FakeSession(),
    )
    record = manifest["sources"][0]
    assert manifest["status"] == "SUCCESS"
    assert manifest["products_downloaded"] == 0
    assert record["status"] == "SUCCESS"
    assert record["availability_state"] == "AVAILABLE"
    assert record["change_state"] == "FIRST_CAPTURE"
    assert record["requested_url"]
    assert record["http_status"] == 200
    assert record["raw_sha256"]
    assert (tmp_path / "run/raw/NASA_ROMAN_HOME.html").is_file()


def test_source_watch_records_403_as_restricted_with_evidence(tmp_path: Path) -> None:
    manifest = run_source_watch(
        sources_path=_single_source_registry(tmp_path),
        policy_path=Path("config/download_policy.v1.json"),
        outdir=tmp_path / "run",
        session=FakeSession(
            FakeResponse(
                status_code=403,
                content=b"<html><title>Access denied</title><body>Forbidden</body></html>",
            )
        ),
    )
    record = manifest["sources"][0]
    assert manifest["status"] == "PARTIAL"
    assert manifest["restricted_source_count"] == 1
    assert manifest["products_downloaded"] == 0
    assert record["status"] == "RESTRICTED"
    assert record["availability_state"] == "HTTP_403"
    assert record["requested_url"]
    assert record["final_url"]
    assert record["http_status"] == 403
    assert record["raw_sha256"]
    assert record["change_state"] == "FIRST_CAPTURE"
    assert (tmp_path / "run/raw/NASA_ROMAN_HOME.html").is_file()


def test_source_watch_marks_login_redirect_as_restricted(tmp_path: Path) -> None:
    manifest = run_source_watch(
        sources_path=_single_source_registry(tmp_path),
        policy_path=Path("config/download_policy.v1.json"),
        outdir=tmp_path / "run",
        session=FakeSession(
            FakeResponse(
                status_code=200,
                url="https://roman.science.stsci.edu/login",
                content=b"<html><title>Sign in</title><body>MyST</body></html>",
            )
        ),
    )
    record = manifest["sources"][0]
    assert manifest["status"] == "PARTIAL"
    assert record["status"] == "RESTRICTED"
    assert record["availability_state"] == "LOGIN_WALL_SUSPECTED"
    assert record["http_status"] == 200
    assert record["raw_sha256"]
    assert record["products_downloaded"] == 0
