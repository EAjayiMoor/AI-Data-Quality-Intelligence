from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    provider: str
    url: str


def load_database_config() -> DatabaseConfig:
    provider = os.getenv("DATABASE_PROVIDER", "postgres")
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://poc_user:poc_password@localhost:5432/ai_data_quality_poc",
    )
    return DatabaseConfig(provider=provider, url=url)
