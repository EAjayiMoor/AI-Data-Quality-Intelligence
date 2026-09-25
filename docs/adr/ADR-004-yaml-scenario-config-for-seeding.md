# ADR-004: YAML Scenario Configuration for Synthetic Seeding

## Status
Accepted

## Context

Phase 3 requires scenario-driven synthetic data generation with realistic note content and maintainable scenario definitions. The agreed approach is YAML-based scenario files and inclusion of `note_category` in seeded notes.

## Decision

- Use YAML files under `data/scenarios/` as the source of scenario and volume configuration.
- Add `PyYAML` as a project dependency to parse scenario files.
- Keep generation deterministic via fixed seed values.

## Consequences

### Positive
- Scenario packs are human-readable and easy to review.
- Non-code edits to counts and distributions are straightforward.
- Supports comments and structured nesting for long-lived maintenance.

### Trade-offs
- Introduces a small parsing dependency (`PyYAML`).
- Requires validation checks for scenario file quality.

