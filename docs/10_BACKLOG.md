# Prioritised Backlog

## Must have

### POC-001 Repository foundation
Create Python project structure, configuration handling, quality tools and CI.

### POC-002 Relational schema
Implement source, assessment, evidence, exception and cost tables.

### POC-003 Synthetic benchmark data
Create deterministic seed cases covering the approved scenario set.

### POC-004 Record retrieval
Retrieve one complete connected request in chronological order.

### POC-005 Assessment page shell
Select and display one request and its connected data.

### POC-006 LLM response contract
Define the structured schema and permitted values.

### POC-007 Assessment service
Build context, call the LLM and return a validated response.

### POC-008 Evidence validation
Reject evidence identifiers not present in supplied context.

### POC-009 Persist assessments
Store success and visible failure status with versions.

### POC-010 Present recommendation
Display status, confidence, evidence, contradictions and exceptions.

### POC-011 Capture usage and cost
Persist token usage, configured rates and calculated cost per call.

### POC-012 Cost dashboard
Show measured and projected costs with assumptions.

### POC-013 Exception dashboard
Filter stored assessments by exception and confidence.

### POC-014 Benchmark suite
Evaluate expected status, schema validity, evidence validity, tokens and cost.

### POC-015 Release hardening
Complete tests, methodology page, demo script and release checklist.

## Should have

### POC-016 Controlled ask-results page
Support approved question templates over stored results.

### POC-017 Prompt comparison report
Compare candidate prompt versions against the benchmark suite.

### POC-018 Context limit handling
Warn and flag when note history is truncated.

## Could have
- CSV export of assessment results.
- Model selector limited to preconfigured models.
- Simple human accept/amend feedback capture.

## Will not have in V1
- Autonomous agents.
- Natural-language write access.
- Fine-tuning.
- Vector search.
- Background job platform.
- Production identity and source-system integration.

## Dependency order
`POC-001 -> POC-002 -> POC-003 -> POC-004 -> POC-005 -> POC-006 -> POC-007 -> POC-008 -> POC-009 -> POC-010 -> POC-011 -> POC-012/013 -> POC-014 -> POC-015`
