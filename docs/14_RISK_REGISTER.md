# Risk Register

| ID | Risk | Impact | Mitigation | Trigger/indicator |
|---|---|---|---|---|
| R1 | LLM cites evidence it was not given | High | Validate every source ID and reject invalid output | Unknown evidence ID |
| R2 | Processing cost grows with long notes | High | Context limits, benchmark by note volume, one-call normal path | Token/cost regression |
| R3 | Synthetic data is too simple | Medium | Include contradictions, sparse evidence and long histories | Near-perfect results with no failures |
| R4 | Prompt changes improve one case but damage others | High | Fixed benchmark suite and version comparison | Benchmark regression |
| R5 | PoC expands into production architecture | Medium | Enforce north-star and V1 exclusions | New framework/service without acceptance need |
| R6 | Cost projection appears definitive | Medium | Show assumptions, sample and model/prompt version | Projection shown without basis |
| R7 | Invalid output is shown as trustworthy | High | Pydantic validation and visible failure state | Schema validation failure |
| R8 | Client information is reused | High | Synthetic-only policy and review | Client names/text detected |
| R9 | Provider pricing becomes stale | Medium | Versioned configuration with effective date | Missing/outdated effective date |
| R10 | Agent-generated code is accepted without execution | High | Definition of done requires command/test evidence | Completion claim without logs |
