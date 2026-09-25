# Acceptance Criteria

## End-to-end
- A user can select a seeded request and view all connected records.
- A user can run an assessment and see a stored recommendation.
- A successful result shows permitted status, confidence, evidence and cost.
- Failure does not appear as a successful recommendation.

## Data
- Foreign keys prevent orphan source records.
- Notes appear chronologically.
- Seed generation is repeatable.
- Dataset contains no client-derived data.

## Assessment
- Normal path makes one LLM call.
- Response is validated against the structured schema.
- Recommended status is from the controlled list.
- Evidence identifiers exist in the supplied context.
- `insufficient_evidence` is permitted without fabricated evidence.
- Contradictions and missing evidence are distinct.

## Cost
- Input and output tokens are stored when returned by the provider.
- Cost uses configured, versioned rates.
- Retries contribute to assessment cost.
- Aggregate dashboards do not call the LLM.
- Projections state their assumptions.

## UI
- Synthetic-data status is visible.
- Cost is visible next to the selected assessment result.
- Evidence is readable without inspecting raw JSON.
- Exception links lead to the relevant record.
- Limitations are visible on the methodology page.

## Engineering
- Formatting, linting, type checking and automated tests pass.
- No secrets are committed.
- No unapproved dependency is introduced.
- Material decisions are captured through ADRs.
- Setup instructions work from a clean environment.
