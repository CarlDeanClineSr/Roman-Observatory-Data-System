from pathlib import Path

from roman_observatory.policy import decide_product, load_policy


def test_v01_never_auto_downloads_asdf() -> None:
    policy = load_policy(Path("config/download_policy.v1.json"))
    decision = decide_product(
        filename="example_cal.asdf",
        size_bytes=10,
        source_access="PUBLIC",
        policy=policy,
    )
    assert decision.permitted is False
    assert decision.decision == "METADATA_ONLY_AUTOMATIC_DOWNLOAD_DISABLED"


def test_restricted_source_is_metadata_only() -> None:
    policy = load_policy(Path("config/download_policy.v1.json"))
    decision = decide_product(
        filename="telemetry.fits",
        size_bytes=1,
        source_access="RESTRICTED",
        policy=policy,
    )
    assert decision.permitted is False
    assert decision.decision == "METADATA_ONLY_RESTRICTED_SOURCE"
