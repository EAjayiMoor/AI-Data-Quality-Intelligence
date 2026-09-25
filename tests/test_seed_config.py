from pathlib import Path

from ai_data_quality_poc.storage.seeding import load_scenario_config


def test_phase3_scenario_config_totals_are_consistent() -> None:
    config_path = Path("data/scenarios/phase3_scenarios.yaml")
    config = load_scenario_config(str(config_path))

    assert config.total_cases == 60
    assert len(config.case_plans) == 60
    assert config.total_notes_min == 1000
    assert config.total_notes_max == 1400
    assert "customer_contact" in config.note_categories
    assert "administrative" in config.note_categories
    assert "completion_signal" in config.note_categories
