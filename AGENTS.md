# Agent Engineering Instructions

## Mission
Build only what is needed to demonstrate evidence-backed AI status assessment from connected synthetic operational data, with explainability and cost transparency.

## Mandatory reading order
1. `README.md`
2. `docs/01_PRODUCT_SPEC.md`
3. `docs/02_DOMAIN_MODEL.md`
4. `docs/03_ARCHITECTURE.md`
5. The active ticket
6. Relevant ADRs

## Before editing
State:
- objective;
- assumptions;
- acceptance criteria;
- files expected to change;
- tests to run;
- expected LLM/cost impact.

## Engineering rules
1. Implement one ticket at a time.
2. Prefer the smallest working vertical change.
3. Do not add frameworks or dependencies without an ADR.
4. Do not introduce agents into the runtime architecture.
5. Keep SQL deterministic and parameterised.
6. The LLM never receives database credentials.
7. Validate all model output with Pydantic.
8. Validate all evidence identifiers against supplied context.
9. Capture token usage and cost for every LLM call.
10. Do not call the LLM for dashboards or stored-result filters.
11. Use synthetic data only.
12. Do not claim tests passed unless they were executed.
13. Stop when acceptance criteria pass.

## Required checks
Run the project's configured equivalents of:

```text
format
lint
type-check
unit and integration tests
benchmark suite for LLM-impacting changes
```

## Completion response
Report:
- summary;
- changed files;
- executed commands and results;
- acceptance-criteria mapping;
- token/cost impact;
- limitations.

## Prohibited behaviour
- Broad “build the whole app” changes.
- Silent schema or lifecycle changes.
- Fabricated test results.
- Hard-coded secrets or live provider prices.
- New infrastructure added “for later”.
- Presenting invalid LLM output as a valid assessment.
