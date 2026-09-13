## Goal

Add runtime assertions enforcing the identity-vs-truthiness contract in `pipeline.py`'s `augment()` method, per REQ-002.

## Scope

- In-Scope: Adding `assert result is not None or result == ""` in `pipeline.py`'s `augment()` HTTP-mode branch after the existing `if result is not None:` check resolves
- Out-of-Scope: Modifying any other file; changing behavior; adding new methods

## Assumptions

- The current codebase's runtime handling of `None` vs `""` in `pipeline.py` is already correct — only a defensive assertion is being added, not a behavior change
- The `result` variable at line 298 is always `str | None` at the point the assertion is inserted
- The fallback chain order (HTTP → cache → search → refiner → raw) remains unchanged

## Design decisions

1. Use assertions rather than runtime `if`/raise checks — consistent with how this class of defensive check is used elsewhere in the target files
2. Place the assertion immediately after the existing `if result is not None:` check fails to short-circuit, so it catches the case where `result` is neither `None` nor a valid string
3. Do not introduce a sentinel object (e.g. `_NO_RESULT`) — deferred since the current `None`/`""` approach already works correctly

## Alternatives considered

- Using `if result is not None and result != "":` instead of `assert` — rejected because the existing pattern in this codebase uses assertions for this class of contract enforcement
- Adding a return-type guard in `call_rag_service()` — rejected because the existing contracts already encode the distinction correctly

## Implementation
### Target file
`scripts/rag/pipeline.py`

### Procedure
Insert an assertion after the existing `if result is not None:` check at line 298 fails to short-circuit.

### Method
Inline assertion in `augment()` method body.

### Details
1. Locate the `if result is not None:` check at line 298 in `augment()`
2. After the block that handles the `None` case (fallback logic), insert:
   ```python
   assert result is not None or result == "", (
       f"HTTP augment returned unexpected falsy value: {result!r}; "
       "expected str (non-empty or empty) or None"
   )
   ```
3. This assertion enforces the contract described in the existing docstring (lines 261-263): `is not None` means success with result, even if empty string

## Compatibility considerations

- Assertions are stripped under `python -O` — this is a known, accepted trade-off; the assertions are a development-time safety net, not a production guarantee
- The existing docstrings and correct current logic are the actual production-time contract
- No behavioral change — the assertion only fires if a future regression introduces an invalid return value

## Security considerations

N/A: Defensive assertion only, no security impact.

## Rollback considerations

Simple revert of the single assertion insertion — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/pipeline.py | Unit — verify augment() does not raise on `""` or non-empty result, falls back on `None` | `pytest tests/rag/ -k augment` | No `AssertionError`; correct fallback behavior preserved |

## Completion criteria

- [ ] `pipeline.py`'s `augment()` method raises an `AssertionError` if the HTTP-mode branch's result is neither `None` nor an empty/non-empty string
- [ ] All existing tests pass after changes
- [ ] `pytest tests/rag/ -k augment` runs without errors

## Out of scope

- Modifying `http_augment.py` (separate document)
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
| 1 | Verify `result` variable type at assertion insertion point | Pending | — | — | Confirm `str | None` |
| 2 | Add assertion in `augment()` HTTP-mode branch | Pending | — | — | Insert after line 298 |
| 3 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | `pytest tests/rag/` |

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
- **Requirement ID**: REQ-002 — enforce identity-vs-truthiness contract with runtime assertion
- **Source issue**: issues/20260913-163623_bugs001_http_augment_fallback_truthiness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-175907_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-202920
- **Related target files**: scripts/rag/pipeline.py
