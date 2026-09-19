"""Offline guards for maintenance changes to repository-owned workflows."""

from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ("ci.yml", "provenance_guard.yml", "mast_metadata_watch.yml", "public_source_watch.yml")


@pytest.mark.parametrize("name", WORKFLOWS)
def test_workflows_use_node24_actions_and_explicit_runner(name):
    text = (ROOT / ".github/workflows" / name).read_text()
    assert "runs-on: ubuntu-24.04" in text
    assert "ubuntu-latest" not in text
    actions = dict(re.findall(r"uses:\s+(actions/[^@\s]+)@(\S+)", text))
    expected = {
        "actions/checkout": "v6",
        "actions/setup-python": "v6",
        "actions/upload-artifact": "v7",
    }
    assert {"actions/checkout", "actions/setup-python"} <= actions.keys()
    for action, version in actions.items():
        assert version == expected[action]
    assert 'python-version: "3.12"' in text
    assert "contents: read" in text
    assert "ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION" not in text


@pytest.mark.parametrize("name", ("mast_metadata_watch.yml", "public_source_watch.yml"))
def test_provider_watches_remain_manual_and_bounded(name):
    text = (ROOT / ".github/workflows" / name).read_text()
    triggers = text.split("\non:\n", 1)[1].split("\npermissions:\n", 1)[0]
    assert triggers.strip() == "workflow_dispatch:"
    assert "actions/upload-artifact@v7" in text
    assert "if: always()" in text
    assert "retention-days: 90" in text
    assert "roman-watch validate" in text
    assert "roman-watch export" not in text
    assert "download.py" not in text
