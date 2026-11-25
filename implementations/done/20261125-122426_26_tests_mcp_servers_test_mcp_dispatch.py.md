## Goal

Move the dispatcher tests to the context-based signature and replace the marker-era dry-run and keyless cases with mode-based ones (REQ-003, REQ-004, REQ-006, REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The file has about 100 call sites using `idempotency_key=`; the change is mechanical through one local helper.
- Verified cases that change meaning: `test_dry_run_result_not_cached` (marker style, line 326), `test_error_and_dry_run_do_not_leave_replayable_state` (1156), `test_dry_run_clears_pending_row` (1220), and `test_keyless_and_empty_key_always_execute` (158), which pins the behavior this Plan removes.

## Design decisions

- One module-level helper builds an `ExecutionContext` from a key and an optional mode, so the call-site edit is a rename, not a rewrite.

## Alternatives considered

Keeping a compatibility shim in `dispatch_tool` for the old keyword was rejected: it would keep the second way of supplying a key alive.

## Implementation
### Target file
`tests/mcp_servers/test_mcp_dispatch.py`

### Procedure
Replace the keyword argument with the helper everywhere and rewrite the four cases above.

### Method
- Add a helper `_ctx` (new) taking `(key="", mode="applied")` returning `ExecutionContext(request_id="", session_id="", idempotency_key=key, execution_mode=mode)`.
- Replace each `idempotency_key=X` with `context=_ctx(X)`.
- Rewrite the two marker-based dry-run cases to dispatch with `_ctx(key, "preview")` and assert no cache entry and no durable row, with the handler returning plain text.
- Replace the keyless-always-executes case with: a keyless side-effecting call returns idempotency_key_required and runs no handler; a keyless read-only call executes.
- Add: a replay result reports `execution_mode == "no_op"`; an applied success reports `side_effect_applied is True`.

### Details
- Do not change the durable-store fixtures or the concurrency pins.

## Compatibility considerations

Test-only.

## Security considerations

N/A: test code.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- No `idempotency_key=` argument is passed to `dispatch_tool`.
- No test depends on output-marker detection.

## Out of Scope

- The new cross-server contract test (its own document).
- The concurrency test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test file described in Implementation > Procedure/Method/Details | Completed | 20261125-175203 | 20261125-175203 | changed; module-level _ctx helper, 47 call sites converted, 4 marker-era cases rewritten (keyless pair, preview-not-cached, error+preview, preview-leaves-no-row) plus the replay/applied-flag case; also fixed a pre-existing mypy no-any-return in _seed_interrupted (int(row.attempt_number)) so the changed-file gate passes; no idempotency_key= call site remains |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-180342 | 20261125-180342 | — plan batch: end-of-batch full-suite run pending; targeted run 45 passed, ruff/mypy/lint-imports clean. This procedure has 2 rows (test-only), so the validation row is Step 2, not Step 3 end-of-batch full-suite run: 14369 passed, 4 skipped; diff-cover 92% (>=90) on changed lines; run_validation_gates.py passes |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-006, REQ-010
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `tests/mcp_servers/test_mcp_dispatch.py`