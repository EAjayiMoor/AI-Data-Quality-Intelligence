# ADR-002: Structured LLM Contract

## Status
Accepted

## Context
Free-form model output is difficult to validate and display safely.

## Decision
Require a Pydantic-validated response containing recommended status, confidence, evidence references, contradictions, missing evidence, exceptions and explanation.

## Consequences
- Invalid output can be rejected.
- Evidence can be traced to supplied records.
- Prompt/provider changes must preserve the contract.
