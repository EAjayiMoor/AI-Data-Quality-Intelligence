from pathlib import Path

APP_SOURCE = Path("app/main.py")


def test_streamlit_ui_uses_current_width_api() -> None:
    source = APP_SOURCE.read_text(encoding="utf-8")

    assert "use_container_width" not in source


def test_kpi_rows_do_not_use_cramped_fixed_column_counts() -> None:
    source = APP_SOURCE.read_text(encoding="utf-8")

    assert "st.columns(5)" not in source
    assert "st.columns(6)" not in source
