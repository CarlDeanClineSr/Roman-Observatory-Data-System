from __future__ import annotations

from pathlib import Path
import json

from roman_observatory.source_watch import run_source_watch


class FakeResponse:
    status_code = 200
    url = "https://science.nasa.gov/mission/roman-space-telescope/"
    headers = {"Content-Type": "text/html", "ETag": '"abc"'}
    content = b"<html><title>Roman</title><body>evidence</body></html>"

    def iter_content(self, chunk_size: int):
        del chunk_size
        yield self.content


class FakeSession:
    def get(self, *args, **kwargs):
        del args, kwargs
        return FakeResponse()


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
    assert manifest["status"] == "SUCCESS"
    assert manifest["products_downloaded"] == 0
    assert manifest["sources"][0]["change_state"] == "FIRST_CAPTURE"
    assert manifest["sources"][0]["raw_sha256"]
    assert (tmp_path / "run/raw/NASA_ROMAN_HOME.html").is_file()
