from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ai_data_quality_poc.storage.config import load_database_config


def build_engine() -> Engine:
    config = load_database_config()
    return create_engine(config.url, future=True)


def check_database_health() -> bool:
    engine = build_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
