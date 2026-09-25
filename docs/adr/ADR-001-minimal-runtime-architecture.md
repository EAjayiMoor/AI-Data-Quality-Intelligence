# ADR-001: Minimal Runtime Architecture

## Status
Accepted

## Context
The PoC must demonstrate connected-data reasoning, explainability and cost transparency without recreating an enterprise data platform.

## Decision
Use Streamlit, a single Python application, SQLAlchemy, a relational database and one approved LLM API. Do not use an agent framework, vector database or microservices in Version 1.

## Consequences
- Faster, clearer delivery.
- Easier testing and cost attribution.
- Some scale and integration concerns are deliberately deferred.
