from roman_observatory.classifier import classify_record, normalize_data_level


def test_triplet_test_is_never_flight() -> None:
    assert classify_record({"title": "WFI DCL Triplet Test"}) == "GROUND_TEST"


def test_workshop_build22_is_never_flight() -> None:
    assert classify_record({"path": "Roman_Data_Workshop/ExampleData/Build22/a.asdf"}) == "SIMULATED"


def test_archive_collection_alone_does_not_prove_flight() -> None:
    record = {"obs_collection": "Roman", "dataRights": "PUBLIC"}
    assert classify_record(record, source_id="MAST_ROMAN_MISSION") == "UNKNOWN_QUARANTINE"


def test_explicit_flight_class_requires_confirmation() -> None:
    assert classify_record({"origin_class": "FLIGHT_SCIENCE"}) == "UNKNOWN_QUARANTINE"
    assert (
        classify_record(
            {"origin_class": "FLIGHT_SCIENCE", "flight_provenance_confirmed": True}
        )
        == "FLIGHT_SCIENCE"
    )


def test_data_levels_are_namespaced() -> None:
    assert normalize_data_level("L1", instrument="WFI") == "WFI_LEVEL_1"
    assert normalize_data_level("L1", instrument="CGI") == "CGI_LEVEL_1"
    assert normalize_data_level("L1", instrument=None) == "NOT_APPLICABLE"
