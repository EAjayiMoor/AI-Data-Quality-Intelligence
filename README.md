# AI Data Quality PoC

## Purpose

This repository defines the delivery and engineering approach for a lightweight proof of concept demonstrating that an LLM can analyse connected operational data and free-text notes, recommend an evidence-backed status, identify exceptions and show the cost of processing.

## North-star statement

> This PoC demonstrates AI-derived status assessment from connected operational data and free-text notes, with explainability and cost transparency.

## PoC scope

### Included
- Synthetic connected data only.
- Service requests, notes, quotes and payments.
- LLM-assisted status recommendation.
- Evidence, confidence and exception outputs.
- Token and cost capture for every assessment.
- Streamlit user interface.
- Simple questions over stored assessment results.

### Excluded
- Production integration.
- Databricks.
- Multi-agent orchestration.
- Vector databases and knowledge graphs.
- Autonomous learning and model fine-tuning.
- Full case-management workflow.
- Unrestricted natural-language SQL generation.

## Proposed stack
- Python
- Streamlit
- PostgreSQL, with SQLite permitted for local-only development
- SQLAlchemy
- Pydantic
- One approved LLM API
- Pytest, Ruff and mypy

## Document map
1. `docs/01_PRODUCT_SPEC.md`
2. `docs/02_DOMAIN_MODEL.md`
3. `docs/03_ARCHITECTURE.md`
4. `docs/04_DATA_MODEL.md`
5. `docs/05_BUSINESS_RULES.md`
6. `docs/06_COST_MODEL.md`
7. `docs/07_USER_JOURNEYS_AND_UI.md`
8. `docs/08_ENGINEERING_METHOD.md`
9. `docs/09_SPRINT_PLAN.md`
10. `docs/10_BACKLOG.md`
11. `docs/11_ACCEPTANCE_CRITERIA.md`
12. `docs/12_TEST_STRATEGY.md`
13. `docs/13_SECURITY_AND_DATA.md`
14. `docs/14_RISK_REGISTER.md`
15. `docs/15_DEFINITION_OF_DONE.md`
16. `AGENTS.md`

## Delivery rule

Every proposed feature must directly support the north-star statement. If it does not, it is deferred.
