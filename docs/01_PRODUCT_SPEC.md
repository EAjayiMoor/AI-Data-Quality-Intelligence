# Product Specification

## 1. Product statement

A lightweight demonstration showing how an LLM can review structured records and operational notes, recommend the likely lifecycle status, explain the evidence used, identify exceptions and expose processing cost.

## 2. Problem

Operational system statuses may not reflect the latest real-world position. Relevant evidence can be distributed across structured tables and lengthy free-text notes. Manual review is slow and makes the cost of assurance difficult to quantify.

## 3. Target users
- Client stakeholder viewing the demonstration.
- Operational reviewer investigating a record.
- Data or AI practitioner evaluating feasibility and economics.

## 4. Core user outcome

A user selects a service request and receives:
- current recorded status;
- AI-recommended status;
- confidence category;
- supporting evidence with note references;
- missing or contradictory evidence;
- exception category;
- tokens consumed and calculated cost.

## 5. MVP features
1. Browse synthetic service requests.
2. View connected notes, quotes and payments.
3. Run one LLM assessment for a selected request.
4. Store a validated structured assessment.
5. Display evidence, exception and confidence.
6. Display per-assessment and aggregate cost.
7. Filter previously assessed records by exception.
8. Ask controlled questions over stored assessment results.

## 6. Non-goals
- Rebuilding Databricks or Genie.
- Delivering production-grade throughput or availability.
- Allowing the model to update source records.
- Allowing arbitrary database access.
- Demonstrating autonomous agents.
- Claiming regulatory, operational or financial decisions can be automated.

## 7. Success measures

The PoC is successful when:
- a user can complete the end-to-end assessment journey;
- every successful recommendation contains traceable evidence;
- every model call records token usage and calculated cost;
- outputs conform to the approved schema and status list;
- representative benchmark cases pass the agreed expected outcomes;
- failures are visible and do not corrupt stored results;
- the complete demo can be run from documented setup instructions.

## 8. Product principles
- Evidence before assertion.
- Thin LLM layer, deterministic controls around it.
- Cost observable by default.
- Synthetic data only.
- Simple enough to explain in one architecture diagram.
- Robustness through contracts and tests, not extra frameworks.

## 9. Assumptions
- One LLM provider is configured through environment variables.
- Synthetic notes contain enough evidence to demonstrate realistic ambiguity.
- Cost rates are maintained in configuration and can be updated.
- The PoC does not require concurrent enterprise-scale usage.

## 10. Release boundary

Version 1 ends when the end-to-end selected-record assessment, exception view and cost view work reliably. Advanced chat, batch optimisation and review workflows are follow-on options only.
