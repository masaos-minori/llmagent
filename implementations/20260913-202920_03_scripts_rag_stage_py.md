## Goal

Correct `PipelineContext.reranked`'s field-level comment to state it is never `None` — always a `list`, possibly empty — correcting the original Plan draft's mistaken nullable assumption, per REQ-004.

## Scope

- In-Scope: Adding an inline comment above `PipelineContext.reranked` (line 44) stating it is never `None`
- Out-of-Scope: Modifying any other file; changing behavior; adding new methods

## Assumptions

- `PipelineContext.reranked` is never assigned `None` anywhere in the codebase (its declared type and default factory are the evidence; no assignment site sets it to `None`)
- The inline comment will be read by developers who need to understand the field's contract

## Design decisions

1. Add an inline comment directly above the field declaration rather than modifying the type annotation — the type itself proves non-nullability, but a comment makes the intent explicit for readers
2. Use clear language that distinguishes this field from the identity-checked `result` variables in `pipeline.py`/`http_augment.py`: "no identity check applies to this field"

## Alternatives considered

- Modifying the type annotation to `list[RagHit]` with a comment — rejected because the type annotation already implies non-nullability; a comment is sufficient and less invasive
- Adding a property getter/setter — rejected because there is no behavioral reason to do so; the field is accessed directly throughout the codebase

## Implementation
### Target file
`scripts/rag/stage.py`

### Procedure
Add an inline comment above `PipelineContext.reranked` (line 44) stating it is never `None`.

### Method
Inline comment addition above the field declaration.

### Details
1. Locate `PipelineContext.reranked` at line 44 in `stage.py`
2. Above the field declaration, add:
   ```python
   # Never None — always a list, possibly empty; no identity check applies to this field.
   reranked: list[RagHit] = dataclasses.field(default_factory=list)
   ```
3. This clarifies that unlike the `result` variables in `pipeline.py`/`http_augment.py`, `reranked` is guaranteed non-null by its type and default factory

## Compatibility considerations

- Comment-only change — no behavioral impact
- The comment is visible to IDEs and linters but does not affect runtime behavior
- The clarification prevents future developers from incorrectly assuming `reranked` can be `None`

## Security considerations

N/A: Documentation correction only, no security impact.

## Rollback considerations

Simple revert of the comment addition — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/stage.py | Manual review — verify comment clarity | Manual inspection | Comment clearly states `reranked` is never `None` |

## Completion criteria

- [ ] `PipelineContext.reranked`'s inline comment states it is never `None`
- [ ] Comment includes "no identity check applies to this field" to distinguish from `result` variables
- [ ] No unintended modifications to other parts of the file

## Out of scope

- Modifying `pipeline.py` (separate document)
- Modifying `http_augment.py` (separate document)
- Changing the type annotation
- Adding new fields or methods
- Changing the fallback order

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add inline comment above `reranked` field declaration | Pending | — | — | Clarify never-None contract |
| 2 | Manual review of comment clarity | Pending | — | — | Ensure wording is precise |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 — document PipelineContext.reranked as never-None (always a list, empty or non-empty)
- **Source issue**: issues/20260913-163623_bugs001_http_augment_fallback_truthiness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-175907_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-202920
- **Related target files**: scripts/rag/stage.py
