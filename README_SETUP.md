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

## 8) One-command release to Azure

From the repo root, run:

```powershell
.\scripts\release_to_azure.ps1 -CommitMessage "Your release message"
```

What it does end-to-end:
- stages changes automatically (excluding `batch_live_run_records.json` and `batch_live_run_summary.json`);
- runs `pytest tests/test_executive_metrics.py -q` (unless `-SkipTests`);
- commits and pushes to `origin/main`;
- builds a tagged image in `crmhcdemo` ACR;
- updates and restarts `ai-data-quality-intel` Azure Web App;
- waits for a `200` health check.

Useful switches:

```powershell
# Preview steps without changing anything
.\scripts\release_to_azure.ps1 -CommitMessage "Preview" -DryRun

# Release without test execution
.\scripts\release_to_azure.ps1 -CommitMessage "Hotfix" -SkipTests
```
