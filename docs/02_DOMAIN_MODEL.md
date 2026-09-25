# Domain Model

## Core entities

### Service Request
The master operational case being assessed.

### Interaction Note
A dated free-text entry associated with one service request. Every note has a stable identifier so evidence can be cited.

### Quote
A commercial or operational quotation associated with a service request.

### Payment
A payment record associated with a service request.

### Assessment
A versioned LLM-produced recommendation for one service request at a point in time.

### Evidence Item
A reference to an input record supporting or contradicting the recommendation. It contains a source type, source identifier, date and concise explanation.

### Exception
A structured issue identified during assessment, such as status mismatch, contradictory evidence, missing evidence or low confidence.

### Confidence
A controlled value: `high`, `medium` or `low`. Confidence is not probability and must be defined by policy.

### Cost Record
The measured input/output token usage, configured unit prices and calculated cost for one model call.

## Relationships
- One service request has many interaction notes.
- One service request may have many quotes.
- One service request may have many payments.
- One service request may have many assessments over time.
- One assessment has many evidence items and exceptions.
- One assessment has one or more cost records if calls are retried.

## Controlled lifecycle statuses
- `new`
- `quoted`
- `accepted_unpaid`
- `accepted_paid`
- `in_delivery`
- `completed`
- `cancelled`
- `insufficient_evidence`

## Ubiquitous language
- **Recorded status:** value currently stored against the service request.
- **Recommended status:** value inferred from supplied evidence.
- **Status mismatch:** recorded and recommended statuses differ.
- **Supporting evidence:** source material supporting the recommendation.
- **Contradictory evidence:** source material inconsistent with the recommendation.
- **Missing evidence:** expected evidence that is not present. Absence is not proof of the opposite.
- **Assessment run:** one attempt to produce and validate a recommendation.
