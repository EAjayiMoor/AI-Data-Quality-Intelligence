# ADR-003: Cost Observability by Default

## Status
Accepted

## Context
Note volume directly affects model input and therefore assessment economics.

## Decision
Record provider-reported token usage and versioned configured prices for every LLM call. Include retry cost and surface measured/projected cost in the UI.

## Consequences
- Cost becomes testable and visible.
- Pricing configuration must be maintained.
- Projections are labelled as assumptions, not quotations.
