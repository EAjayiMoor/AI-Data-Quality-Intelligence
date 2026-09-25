# User Journeys and UI Specification

## Navigation
1. Assessment
2. Exceptions
3. Costs
4. Ask Results
5. Methodology

## Page 1: Assessment

### Header
- Product title.
- One-sentence PoC purpose.
- Visible “Synthetic data” label.

### Controls
- Service request selector.
- Run assessment button.
- Re-run warning when an assessment already exists.

### Summary row
- Recorded status.
- AI-recommended status.
- Confidence.
- Assessment cost.

### Evidence section
- Supporting evidence cards showing source type, source ID, date and explanation.
- Contradictory evidence shown separately.
- Missing evidence callout.

### Record data
- Chronological notes timeline.
- Quote and payment facts.

### Exceptions
- Status mismatch, low confidence, contradiction or missing evidence.

### Failure state
- Clear failure message.
- No recommendation displayed as valid.
- Technical details available in an expandable section.

## Page 2: Exceptions
- Count cards by exception type.
- Filterable list of assessed records.
- Link back to Assessment page.
- No LLM call required.

## Page 3: Costs
- Total completed assessments.
- Total measured cost.
- Average measured cost.
- Benchmark distribution by note volume.
- Projection control with assumptions.
- No LLM call required.

## Page 4: Ask Results

This page operates on persisted assessment results, not arbitrary raw database queries.

Supported intents:
- Explain a selected assessment.
- List assessed records by recommended status.
- List assessed records by exception.
- Show high/medium/low-confidence records.
- Summarise measured cost.

Prefer deterministic query templates. Use the LLM only to phrase an explanation where it adds value.

## Page 5: Methodology
- What the PoC demonstrates.
- Data model and synthetic-data statement.
- Status definitions.
- LLM role versus Python role.
- Cost calculation approach.
- Limitations and non-production disclaimer.

## Visual principles
- Executive-friendly hierarchy.
- Status and confidence colours used consistently.
- Evidence visible without scrolling through raw JSON.
- Cost shown near the recommendation.
- No technical jargon on primary pages.
