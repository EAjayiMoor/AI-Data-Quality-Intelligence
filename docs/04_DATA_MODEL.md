# Data Model

## Tables

### service_requests
- `id` UUID or string, primary key
- `customer_name` synthetic string
- `recorded_status` controlled string
- `created_at` timestamp
- `updated_at` timestamp

### interaction_notes
- `id` primary key
- `service_request_id` foreign key
- `note_timestamp` timestamp
- `note_category` controlled string
- `note_text` text
- `author_role` synthetic string

### quotes
- `id` primary key
- `service_request_id` foreign key
- `quote_timestamp` timestamp
- `quote_status` controlled string
- `amount` decimal, optional

### payments
- `id` primary key
- `service_request_id` foreign key
- `payment_timestamp` timestamp
- `payment_status` controlled string
- `amount` decimal, optional

### assessments
- `id` primary key
- `service_request_id` foreign key
- `recorded_status_snapshot`
- `recommended_status`
- `confidence`
- `explanation`
- `prompt_version`
- `rules_version`
- `model_name`
- `assessment_status`: success or failed
- `created_at`

### assessment_evidence
- `id` primary key
- `assessment_id` foreign key
- `evidence_type`: supporting or contradictory
- `source_type`: note, quote or payment
- `source_id`
- `explanation`

### assessment_exceptions
- `id` primary key
- `assessment_id` foreign key
- `exception_type`
- `description`

### cost_tracking
- `id` primary key
- `assessment_id` foreign key
- `call_sequence`
- `model_name`
- `input_tokens`
- `output_tokens`
- `cached_input_tokens`, optional
- `input_price_per_million`
- `output_price_per_million`
- `calculated_cost`
- `currency`
- `duration_ms`
- `call_status`
- `created_at`

## Integrity rules
- Child records must reference an existing service request.
- An evidence source identifier must exist in the supplied assessment context.
- Successful assessments must have a permitted recommended status.
- Successful assessments must contain at least one evidence item unless status is `insufficient_evidence`.
- Cost is derived from recorded token counts and versioned configured rates.

## Indexes
- `interaction_notes(service_request_id, note_timestamp)`
- `quotes(service_request_id)`
- `payments(service_request_id)`
- `assessments(service_request_id, created_at)`
- `assessment_exceptions(exception_type)`

## Synthetic data profile
Create a compact benchmark-oriented dataset containing:
- clear quoted cases;
- clear accepted but unpaid cases;
- clear accepted and paid cases;
- completed cases;
- cancelled cases;
- contradictory-note cases;
- sparse-evidence cases;
- long-note-history cases.

No UKPN names, identifiers, text or copied client data may be used.
