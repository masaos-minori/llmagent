## Goal

Expand `http_augment.py`'s `HttpAugment.run()` docstring to explain the identity-vs-truthiness contract, and add a runtime assertion enforcing it, per REQ-003.

## Scope

- In-Scope: Expanding `run()`'s one-line docstring and adding `assert result is not None or result == ""` after `call_rag_service()` returns
- Out-of-Scope: Modifying any other file; changing behavior; adding new methods

## Assumptions

- The current codebase's runtime handling of `None` vs `""` in `http_augment.py` is already correct — only a defensive assertion is being added, not a behavior change
- The `result` variable after `call_rag_service()` returns is always `str | None`
- The `_http_result_kind` classification (lines 108-116) already correctly distinguishes `None`/`""`/non-empty but is unasserted

## Design decisions

1. Expand the docstring to explicitly document the `None`/`""`/non-empty-string contract before adding the assertion — documentation should precede enforcement
2. Place the assertion immediately after `call_rag_service()` returns, so it catches the case where `result` is neither `None` nor a valid string
3. Include a descriptive error message in the assertion to aid debugging when it fires

## Alternatives considered

- Using `if result is not None and result != "":` instead of `assert` — rejected because the existing pattern in this codebase uses assertions for this class of contract enforcement
- Adding a return-type guard in `call_rag_service()` — rejected because the existing contracts already encode the distinction correctly

## Implementation
### Target file
`scripts/rag/http_augment.py`

### Procedure
1. Expand `run()`'s docstring to explain the identity-vs-truthiness contract
2. Insert an assertion after `call_rag_service()` returns

### Method
Docstring expansion + inline assertion in `run()` method body.

### Details
1. Locate `HttpAugment.run()` at lines 84-122
2. Expand the docstring (currently a single line at line 85) to include:
   - Return value contract: `str` (non-empty), `""` (valid empty), `None` (triggers fallback)
   - Identity-vs-truthiness note: distinguish `None` from empty string
3. After `call_rag_service()` returns (around line 108), insert:
   ```python
   assert result is not None or result == "", (
       f"call_rag_service() returned unexpected falsy value: {result!r}; "
       "expected str (non-empty or empty) or None"
   )
   ```
4. This assertion enforces the same contract as in `pipeline.py`, ensuring consistency across the two call sites

## Compatibility considerations

- Assertions are stripped under `python -O` — this is a known, accepted trade-off; the assertions are a development-time safety net, not a production guarantee
- The existing docstrings and correct current logic are the actual production-time contract
- No behavioral change — the assertion only fires if a future regression introduces an invalid return value
- The docstring expansion adds clarity without changing the API surface

## Security considerations

N/A: Defensive assertion and documentation only, no security impact.

## Rollback considerations

Simple revert of the docstring expansion and assertion insertion — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/http_augment.py | Unit — verify HttpAugment classification and assertion | `pytest tests/rag/ -k http` | Classifies `""` as `"remote_empty"` without raising; `None` triggers fallback without raising |

## Completion criteria

- [ ] `http_augment.py`'s `HttpAugment.run()` docstring explicitly states the None/""/non-empty-string contract
- [ ] `HttpAugment.run()` raises an `AssertionError` if `call_rag_service()` returns an unexpected falsy value
- [ ] All existing tests pass after changes
- [ ] `pytest tests/rag/ -k http` runs without errors

## Out of scope

- Modifying `pipeline.py` (separate document)
- Modifying `stage.py` (separate document)
- Changing the fallback order
- Adding new fallback stages
- Changing HttpAugment's return values
- Implementing sentinel objects like `_NO_RESULT`
- Modifying `pipeline_service.py` (docstring already fully documents the contract)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify `result` variable type after `call_rag_service()` returns | Completed | — | — | Confirm `str | None` |
| 2 | Expand docstring in `HttpAugment.run()` | Completed | — | — | Add identity-vs-truthiness explanation |
| 3 | Add assertion after `call_rag_service()` returns | Completed | — | — | Insert around line 108 |
| 4 | Run validation sequence (`rules/toolchain.md`) | Completed | — | — | `pytest tests/rag/` |

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
- **Requirement ID**: REQ-003 — document and enforce identity-vs-truthiness contract in HttpAugment.run()
- **Source issue**: issues/20260913-163623_bugs001_http_augment_fallback_truthiness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-175907_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-202920
- **Related target files**: scripts/rag/http_augment.py
