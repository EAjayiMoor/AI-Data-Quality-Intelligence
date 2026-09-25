# Business Rules

## Purpose

Rules constrain the assessment and make the demonstration repeatable. They are illustrative PoC rules, not client policy.

## Lifecycle rules

### Quoted
Evidence indicates that a quote was issued, but there is no reliable acceptance evidence.

### Accepted unpaid
Reliable acceptance evidence exists and no reliable completed payment evidence exists.

### Accepted paid
Reliable acceptance and completed payment evidence exist, with no later cancellation.

### In delivery
Acceptance/payment evidence exists and notes indicate work has begun, but completion evidence is absent.

### Completed
Reliable completion evidence exists and no later evidence reverses or invalidates it.

### Cancelled
Reliable withdrawal or cancellation evidence exists and is not superseded by later reinstatement evidence.

### Insufficient evidence
The supplied records do not support one permitted lifecycle status with adequate traceability.

## Precedence
1. Order evidence chronologically.
2. Later reliable evidence can supersede earlier evidence.
3. Structured records and notes may conflict; conflicts must be surfaced, not silently resolved.
4. Missing evidence must be labelled as missing, not treated as proof.
5. A completion recommendation requires explicit completion evidence.

## Confidence policy

### High
- Direct, unambiguous evidence supports the status.
- No material contradiction is present.
- Evidence identifiers are traceable.

### Medium
- Evidence supports the status but contains ambiguity, incompleteness or a minor contradiction.

### Low
- Material conflict, sparse evidence or reliance on indirect language exists.
- Low-confidence cases should carry a review exception.

## Exception types
- `status_mismatch`
- `missing_payment_evidence`
- `contradictory_evidence`
- `low_confidence`
- `insufficient_evidence`
- `context_truncated`
- `assessment_failure`

## Rule management
- Store rules in version-controlled YAML.
- Assign a rules version to every assessment.
- Changes require benchmark reruns.
- Do not modify lifecycle meanings through prompts alone.
