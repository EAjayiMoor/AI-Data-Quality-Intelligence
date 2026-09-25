from __future__ import annotations

from ai_data_quality_poc.storage.db import check_database_health

if __name__ == "__main__":
    healthy = check_database_health()
    status = "healthy" if healthy else "unhealthy"
    print(f"Database is {status}.")
