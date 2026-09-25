from pathlib import Path

from ai_data_quality_poc.storage.seeding import build_seed_payload, load_scenario_config


def test_seed_payload_matches_phase3_ranges_and_links() -> None:
    config = load_scenario_config(str(Path("data/scenarios/phase3_scenarios.yaml")))
    payload = build_seed_payload(config)

    assert len(payload["service_requests"]) == 60
    assert 1000 <= len(payload["interaction_notes"]) <= 1400

    request_ids = {row["id"] for row in payload["service_requests"]}
    assert all(row["service_request_id"] in request_ids for row in payload["interaction_notes"])
    assert all(row["service_request_id"] in request_ids for row in payload["quotes"])
    assert all(row["service_request_id"] in request_ids for row in payload["payments"])

    note_categories = {row["note_category"] for row in payload["interaction_notes"]}
    assert "risk_flag" in note_categories
    assert "cancellation_signal" in note_categories
    assert "completion_signal" in note_categories
