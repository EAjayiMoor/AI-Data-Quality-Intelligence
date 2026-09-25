# Test Strategy

## Test pyramid

### Unit tests
- Cost calculations.
- Confidence and exception mapping.
- Prompt-context assembly.
- Pydantic validation.
- Evidence-ID validation.
- Projection calculations.

### Integration tests
- Database migrations.
- Foreign-key enforcement.
- Connected-record retrieval.
- Assessment persistence.
- Cost-record persistence.

### Contract tests
- LLM response schema.
- Required fields and enums.
- Invalid status rejection.
- Unknown evidence-source rejection.
- Malformed response handling.

### Benchmark tests
Use fixed synthetic cases for:
- clear accepted unpaid;
- clear completed;
- cancelled after quote;
- contradictory notes;
- sparse evidence;
- long note history;
- recorded-status mismatch.

Capture expected status, actual status, schema validity, evidence validity, tokens, cost and duration.

### UI smoke tests
- Page loads.
- Request selection works.
- Assessment result renders.
- Failure state renders.
- Cost and exception pages load without an LLM call.

## Non-functional checks
- Secrets absent from repository.
- Logs do not expose full note text by default.
- Context cap is enforced.
- Database query count remains reasonable for one assessment.

## Regression policy
Changes to prompts, rules, model or context assembly require the benchmark suite. A change cannot be accepted solely because one example looks better.

## Test evidence
Every completed ticket records:
- commands executed;
- pass/fail result;
- failing tests if any;
- benchmark comparison for LLM-impacting changes;
- known limitations.
