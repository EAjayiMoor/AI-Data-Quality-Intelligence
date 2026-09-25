# Phase 3 Design Spec: Synthetic Data

## Purpose

Define a realistic, deterministic synthetic dataset for the AI Data Quality PoC. This phase adds synthetic records only and does not implement assessment logic.

## Scope

### In scope
- Deterministic seed design for `service_requests`, `interaction_notes`, `quotes`, and `payments`.
- Realism rules for note volume, ambiguity, contradiction, chronology, and author-role mix.
- Scenario packs and expected lifecycle outcomes.
- Seed acceptance criteria and verification checks.

### Out of scope
- LLM prompt design and assessment orchestration.
- Assessment/evidence/exception/cost table population.
- Production data ingestion.

## Design Principles

- Realistic over simplistic: avoid single-note obvious outcomes.
- Deterministic and repeatable: same seed input gives same dataset output.
- Explainable scenarios: each case has an intended status rationale.
- Benchmark-friendly: includes easy, medium, and hard/ambiguous cases.
- Synthetic-only: no client-derived names, identifiers, or text.

## Dataset Shape (Initial)

- Service requests: **60** total
- Notes: **~1,000–1,400** total (target average ~17–23 per request)
- Quotes: **50–90** total
- Payments: **45–85** total

### Case difficulty mix
- Easy: 18 cases
- Medium: 24 cases
- Hard: 18 cases

## Scenario Packs

Create at least the following scenario categories:

1. `clear_quoted`
2. `clear_accepted_unpaid`
3. `clear_accepted_paid`
4. `clear_completed`
5. `clear_cancelled`
6. `contradictory_timeline`
7. `sparse_evidence`
8. `long_history_with_reversal`

Minimum coverage:
- At least 2 hard cases from `contradictory_timeline`.
- At least 2 hard cases from `long_history_with_reversal`.
- At least 1 sparse case that should map to `insufficient_evidence`.

## Realism Rules for Interaction Notes

### Required note fields in Phase 3
- `note_category` is included in this phase.
- Recommended controlled values: `customer_contact`, `internal_update`, `scheduling`, `commercial`, `payment`, `delivery_update`, `completion_signal`, `cancellation_signal`, `risk_flag`, `administrative`.
- `channel` remains optional and can be deferred.

### Volume by case type
- Easy: 6–10 notes
- Medium: 12–20 notes
- Hard: 25–40 notes

### Author-role distribution (target)
- Advisor / case handler: 35%
- Operations scheduler: 20%
- Field engineer: 20%
- Billing / finance: 15%
- Team lead / quality: 10%

### Note clarity mix (target)
- Clear direct evidence: 30%
- Vague shorthand: 25%
- Partial or incomplete: 20%
- Contradictory content: 15%
- Admin/noise updates: 10%

### Chronology realism
- Include clustered updates (same day bursts) and quiet periods.
- Later notes may supersede earlier notes.
- Do not enforce perfectly regular spacing.

### Content realism constraints
- Use concise operational phrasing, abbreviations, and follow-up references.
- Include uncertainty language in medium/hard cases.
- Avoid fabricated sensitive data and real organizations.

## Determinism and IDs

- Fixed seed required (default `42`).
- Deterministic IDs:
  - `SR-0001...`
  - `NOTE-000001...`
  - `Q-0001...`
  - `PAY-0001...`
- Deterministic timestamp generation relative to per-case start dates.

## Status and Evidence Expectations

For each generated service request, define:
- expected recommended lifecycle status (from controlled list),
- difficulty level (`easy|medium|hard`),
- short rationale summary,
- expected exception likelihood (if any).

This metadata is used for benchmark validation in later phases.

## Seed Strategy

- Use **truncate-and-reseed** for repeatable local runs.
- Reset order should preserve referential integrity.
- Seed only source tables in Phase 3:
  - `service_requests`
  - `interaction_notes`
  - `quotes`
  - `payments`

## Verification Criteria (Phase 3 Exit)

1. Seed command is repeatable and deterministic.
2. Row counts match expected ranges.
3. Every child row references a valid parent `service_request_id`.
4. Hard cases have meaningful ambiguity/contradiction in notes.
5. Sparse cases exist and are discoverable.
6. No prohibited real-world data appears.
7. Basic retrieval query returns complete ordered timelines per request.

## Planned Deliverables for Phase 3 Implementation

- `scripts/seed_synthetic_data.py`
- `scripts/reset_and_seed.py`
- `data/scenarios/*.yaml` (or JSON equivalent)
- `tests/test_seed_integrity.py`
- `tests/test_seed_scenario_coverage.py`

## Decision Status

1. Final case count: **60 (agreed)**.
2. Notes volume target: **1,000–1,400 total (agreed)**.
3. Scenario format: **YAML (agreed)**.
4. Optional note fields in this phase: **include `note_category` (agreed)**; `channel` is deferred.
