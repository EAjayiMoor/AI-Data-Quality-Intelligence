# Setup and Run (Skeleton Stage)

## 1) Create virtual environment

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .[dev]
```

## 2) Start Postgres locally

```bash
docker compose up -d postgres
```

## 3) Run baseline checks

```bash
ruff check .
mypy src
pytest
```

## 4) Verify database connectivity

```bash
$env:PYTHONPATH = "src"
python scripts/check_db_health.py
```

## 5) Run migrations

```bash
$env:PYTHONPATH = "src"
.\.venv\Scripts\python -m alembic upgrade head
```

## 6) Generate synthetic source data (Phase 3)

```bash
$env:PYTHONPATH = "src"
.\.venv\Scripts\python scripts/reset_and_seed.py --config data/scenarios/phase3_scenarios.yaml
```

## 7) Run placeholder UI

```bash
$env:PYTHONPATH = "src"
streamlit run app/main.py
```

## Note

This stage includes deterministic synthetic source-data seeding. LLM assessment logic is still not implemented.
