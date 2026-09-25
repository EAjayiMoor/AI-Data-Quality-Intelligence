# Cost Model

## Objective

Make the economics of note processing visible and defensible for every assessment and projected dataset.

## Required measurements
For every LLM call capture:
- model and model version where available;
- input tokens;
- output tokens;
- cached input tokens where reported;
- configured input and output prices;
- calculated cost and currency;
- duration;
- success or failure;
- assessment and request identifiers.

## Calculation

```text
input_cost = (billable_input_tokens / 1,000,000) * input_price_per_million
output_cost = (output_tokens / 1,000,000) * output_price_per_million
total_call_cost = input_cost + output_cost
assessment_cost = sum(total_call_cost for all attempts)
```

Cached-token calculations must follow the provider's documented pricing and remain configurable.

## Configuration

Pricing is stored outside application logic:

```yaml
currency: GBP
models:
  configured-model-name:
    input_per_million: REPLACE_WITH_CURRENT_RATE
    output_per_million: REPLACE_WITH_CURRENT_RATE
    cached_input_per_million: null
    effective_from: YYYY-MM-DD
```

No illustrative rate may be presented as a live provider price.

## UI metrics
- Cost for selected assessment.
- Input and output tokens for selected assessment.
- Total successful-assessment cost.
- Average cost per successful assessment.
- Projected cost for a user-entered record count.
- Projection assumptions and benchmark basis.

## Projection

```text
projected_cost = representative_average_cost_per_assessment * target_record_count
```

Display the benchmark sample size, model, prompt version and note-volume profile. Do not imply the projection is a quotation.

## Engineering cost gates
- Every LLM path has cost capture.
- Normal assessment uses one call.
- Retried calls are included in total cost.
- Dashboards use persisted values, not new LLM calls.
- Benchmark results include short, typical and long note histories.
- Pull requests changing prompts compare token usage against the baseline.

## Benchmark report columns
- benchmark_case_id
- note_count
- input_character_count
- input_tokens
- output_tokens
- total_cost
- duration
- expected_status
- actual_status
- schema_valid
- evidence_valid
