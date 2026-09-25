# Engineering Method

## Aim

Use agent-assisted engineering without surrendering control of scope, architecture or quality.

## Core loop

```text
Understand -> Specify -> Slice -> Implement -> Run -> Test -> Inspect -> Correct -> Review -> Document
```

## Principles
- Small, bounded tasks.
- Vertical slices over broad technical layers.
- One objective per ticket.
- Explicit acceptance criteria before code.
- Tests at deterministic seams.
- Real execution evidence before completion.
- Stop when acceptance criteria pass.
- Record material decisions.

## Roles

### Human product/engineering owner
- Owns product scope, definitions, architecture and acceptance.
- Approves changes to statuses, rules and cost assumptions.
- Reviews demonstrations and release readiness.

### Coding agent
- Reads governing documentation first.
- States assumptions.
- Implements only the selected ticket.
- Adds and runs tests.
- Reports changed files, commands and results.
- Does not declare success without execution evidence.

### Reviewer agent or human reviewer
- Reviews against the ticket and architecture.
- Looks for scope creep, hidden cost and untested failure paths.
- Does not rewrite the feature during review.

## Workflow per ticket
1. Read `AGENTS.md`, product spec, architecture and relevant ADRs.
2. Restate objective and acceptance criteria.
3. Identify permitted files and expected tests.
4. Implement the smallest vertical change.
5. Run formatter, linter, type checker and tests.
6. Run the affected user journey.
7. Inspect token/cost impact for LLM changes.
8. Correct failures.
9. Produce completion evidence.
10. Review and merge only when the definition of done is satisfied.

## Recommended reusable skills
- Domain modelling.
- Specification creation.
- Ticket decomposition.
- Test-driven development for deterministic logic.
- Bug diagnosis.
- Code review.
- Architecture review at sprint boundaries.

Use skills as composable workflows. Do not add an agent framework to the product merely to support the development process.

## Prompt/change discipline
A prompt change is a product change. It requires:
- version increment;
- benchmark rerun;
- schema-validity check;
- evidence-validity check;
- status-accuracy comparison;
- token and cost comparison;
- recorded result.

## Architecture checkpoints
Hold a lightweight architecture review only:
- before implementation;
- after the first end-to-end slice;
- before demo release.

Avoid continuous redesign.
