# Definition of Done

A ticket is done only when all applicable statements are true.

## Scope
- Objective and acceptance criteria are satisfied.
- No unrelated feature or refactor is included.
- Out-of-scope items remain deferred.

## Code
- Code is formatted and linted.
- Type checks pass.
- No placeholder or dead code remains.
- Errors are handled visibly.
- Secrets and provider prices are not hard-coded.

## Tests
- Required unit/integration/contract tests pass.
- The affected user journey has been exercised.
- LLM-impacting changes include benchmark and cost comparison.
- Failure paths have been tested.

## Documentation
- Relevant document or ADR is updated.
- Configuration changes are explained.
- Known limitations are recorded.

## Evidence
The completion note includes:
- files changed;
- commands run;
- test results;
- benchmark/cost result where relevant;
- screenshots or concise manual-check result for UI work;
- remaining limitations.

## Review
- Reviewer verifies the ticket, not only code style.
- No critical/high-severity unresolved issue remains.
- Product owner accepts user-facing changes.
