# Architecture

## Logical view

```text
User
  |
Streamlit UI
  |
Python application services
  |-- Record retrieval service
  |-- Assessment service
  |-- Result validation service
  |-- Cost calculation service
  |-- Stored-results query service
  |
  |---- PostgreSQL / local SQLite
  |
  |---- Approved LLM API
```

## Responsibilities

### Streamlit UI
- Select and display records.
- Trigger assessments.
- Display results, exceptions and cost.
- Query stored assessment results through controlled question types.

### Python services
- Retrieve connected records with deterministic SQL.
- Assemble only the required context.
- Load approved rules and prompt version.
- Call the LLM once per assessment in the normal path.
- Validate the structured response.
- Calculate cost from measured token usage.
- Store valid results and visible failures.

### LLM
- Interpret relevant free-text notes and structured facts.
- Return a recommendation, evidence references, contradictions, missing evidence, confidence and concise explanation.
- It does not connect directly to the database or write source records.

### Database
- Store synthetic source data.
- Enforce relational integrity.
- Store versioned assessments and cost records.

## Normal assessment flow
1. User selects a service request.
2. Python retrieves its request, notes, quotes and payments.
3. Python applies deterministic cleaning, ordering and size limits.
4. Python assembles rules, data and required output schema.
5. One LLM request is made.
6. Pydantic validates the response.
7. Python verifies status values and evidence identifiers.
8. Token usage and cost are recorded.
9. Valid results are stored and displayed.
10. Invalid results are logged as failed and not presented as valid assessments.

## Cost controls
- One normal-path model call per assessment.
- Send only data for the selected request.
- Do not resend stored assessment results to derive dashboards.
- Use deterministic queries for filtering and aggregation.
- Cap note count and context size, with an explicit truncation warning.
- Store prompt, model and pricing versions.
- No automatic retry beyond one retry for malformed output.

## Failure handling
- Database failure: show an actionable error and preserve no partial assessment.
- LLM timeout: record failed run with known usage if supplied.
- Invalid JSON/schema: retry once with the validation error, then fail visibly.
- Unknown evidence identifier: reject the assessment.
- Missing pricing configuration: store token usage but mark cost unavailable.

## Deployment modes
- Local development: Streamlit plus SQLite or local PostgreSQL.
- Shared demo: Streamlit application plus managed PostgreSQL and approved secret storage.

## Explicit exclusions
No LangChain, agent framework, vector store, message queue, event bus, service mesh or microservice split is required for Version 1.
