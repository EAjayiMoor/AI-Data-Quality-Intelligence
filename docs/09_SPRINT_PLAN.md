# Sprint Plan

## Execution control gates

- Work proceeds phase-by-phase with explicit gate checks.
- Before each phase: objective, assumptions, acceptance criteria, file list, test plan, and LLM/cost impact are declared.
- After each phase: acceptance evidence is recorded before moving forward.

## Current phase status

- Active phase: **Phase 10 - Executive summary and Moorhouse UI alignment**
- Scope: persist assessment runs (success and failure), store usage-cost records, and display latest saved summary per service request.
- Update (2026-09-25): added status-alignment KPI (system status vs AI recommendation) to Executive summary and AI Assessment run-set metrics.
- Update (2026-09-25): added one-command release script for commit/push + Azure ACR build + Web App deployment with health check.
- Update (2026-09-26): added SR deep-dive "AI matches system status" flag in AI Assessment page latest saved summary.
- Out of scope: live provider API calls and non-assessment pages.

## Phase 8 exit checklist

- Every assessment run is persisted with explicit status (`success` or `failed`).
- Successful runs persist recommendation, confidence, evidence, exceptions, and usage-cost rows.
- Failed runs persist failure status and an `assessment_failure` exception.
- Cost tracking persists input/output tokens and calculated GBP cost for recorded usage.
- Assessment page displays latest saved assessment summary for selected service request.
- Assessment page blocks unchanged reruns by default and supports an explicit force-rerun override.
- Exceptions page provides exception-type counts, persisted-record filters, and drill-back into Assessment.
- Executive summary page is the default landing page with KPI cards for outcomes, risk and cost.
- Core Streamlit pages apply Moorhouse UI colour, spacing and callout conventions for consistent presentation.
- Quality gates pass: `ruff`, `mypy`, and `pytest`.
## Delivery structure

Four focused sprints, each ending in a working increment. Duration is intentionally not prescribed; progress is controlled by exit criteria.

## Sprint 0: Foundation and contracts

### Goal
Remove ambiguity before feature development.

### Deliverables
- Approved product spec and domain model.
- Architecture and data model.
- Business rules and confidence policy.
- Cost model.
- Repository standards and CI checks.
- Synthetic benchmark-case definitions.

### Exit criteria
- Controlled statuses agreed.
- LLM input/output contract agreed.
- Database schema reviewed.
- Pricing configuration structure exists without hard-coded live prices.
- Backlog is ordered.

## Sprint 1: Connected-data vertical slice

### Goal
Display one complete synthetic service request and its connected data.

### Deliverables
- Database schema and migrations.
- Synthetic seed data.
- Data-access functions.
- Streamlit assessment page with record selection and timeline.
- Referential-integrity and retrieval tests.

### Demo
Select a record and view ordered notes, quotes and payments.

### Exit criteria
- Seed command is repeatable.
- No client-derived data exists.
- Connected records display correctly.
- Automated data tests pass.

## Sprint 2: Evidence-backed assessment

### Goal
Produce and validate one LLM recommendation.

### Deliverables
- Versioned business-rule configuration.
- Prompt template and Pydantic response contract.
- Assessment service.
- Evidence-ID validation.
- Stored assessment result.
- Assessment UI summary and evidence display.
- Benchmark tests covering clear, sparse and contradictory cases.

### Demo
Run an assessment and show recommendation, confidence, evidence and exceptions.

### Exit criteria
- Normal path uses one model call.
- Invalid statuses and source IDs are rejected.
- Failures are visible.
- Benchmark report is generated.

## Sprint 3: Cost transparency and exception views

### Goal
Make model usage measurable and findings explorable.

### Deliverables
- Usage and cost capture.
- Configurable pricing file.
- Cost page.
- Exception page and filters.
- Projection calculator with explicit assumptions.
- Cost regression checks.

### Demo
Show per-assessment cost, aggregate cost, projected cost and exception lists.

### Exit criteria
- Every call is logged.
- Retry cost is included.
- Dashboards require no additional LLM call.
- Missing prices are handled honestly.

## Sprint 4: Controlled interrogation and release hardening

### Goal
Complete the client-facing demo without widening scope.

### Deliverables
- Controlled questions over stored results.
- Methodology page.
- End-to-end tests.
- Error-state review.
- Security/data review.
- Demo script and release checklist.

### Demo
Complete the full journey from record selection to assessment, evidence, cost, exceptions and stored-result interrogation.

### Exit criteria
- All must-have acceptance criteria pass.
- Known limitations are documented.
- Setup documentation is reproducible.
- No critical or high-severity open defects.

## Deferred backlog
- Large-scale batch processing.
- Human review workflow.
- Incremental note processing.
- Provider/model comparison.
- Production authentication and authorisation.
- Source-system integration.









