## Goal

Contain the best-effort `DiagnosticStore.save()` sensitive-pattern refusal in
`scripts/agent/llm_turn_runner.py._handle_llm_error` so a raised `RuntimeError` (or any
exception from a diagnostic save) degrades to a logged warning and never escapes the
interactive LLM turn; the method still returns its normal fail `TurnResult`. Implements
`REQ-001` (no exception escapes the caller) and `REQ-002` (refusal logged at warning level
with `session_id` and `kind`) of the source plan.

## Scope

- Modify `_handle_llm_error` (`scripts/agent/llm_turn_runner.py` lines 189-244). Contain
  every raising diagnostic-save call on the turn path:
  - Partial-text branch (lines 201-216): wrap the `ctx.diagnostics.save(...)` at line 202
    (kind `"llm_transport_error"`) AND the `ctx.diagnostics.save_partial_completion(...)` at
    line 209 (which internally calls `self.save()`, kind `"partial_completion"`).
  - Mid-turn branch (lines 217-231): wrap the `ctx.diagnostics.save(...)` at line 218
    (kind `"mid_turn_error"`).
- Each wrapper logs a warning with `session_id` and the diagnostic `kind`, then execution
  continues to build and return the fail `TurnResult` (lines 237-244).

## Assumptions

- The wrappers mirror the existing `save()` filter-failure handling in
  `scripts/agent/diagnostic_store.py` lines 157-166 (`except Exception` with
  `# noqa: BLE001` and `logger.warning(..., exc_info=True)`).
- Both branches are already inside `if ctx.diagnostics is not None:` guards; the wrappers
  go inside those blocks around the save calls only.
- A module-level `logger` exists and is already used in this method (lines 216, 232).
- `session_id` is available as `ctx.session.session_id`; the diagnostic `kind` is the
  literal passed to each `save()` call.

## Design decisions

- Contain at the caller (source-plan option a): minimal blast radius, preserves the unit
  raise contract asserted by `tests/agent/test_diagnostic_store_security.py` (`REQ-004`).
- Contain `save_partial_completion` at line 209 as well, not just the two direct `save()`
  calls named in the plan row. `save_partial_completion` calls `self.save()`, which can
  raise `RuntimeError` (sensitive pattern) or an I/O error on its own DB write; leaving it
  unguarded would let a `RuntimeError` escape `_handle_llm_error`, violating `REQ-001`.
  This resolves the open choice in the source plan's Phase 2 step 2 ("note that option (a)
  leaves it to `save()`'s own contract"), which would otherwise leave an escape path.
- Wrap each raising call individually (not the whole `if` block) so the non-diagnostic
  bookkeeping — `stat_partial_completions += 1` (line 215), the post-save `logger.warning`
  (lines 216, 232), and the final `TurnResult` return — still runs after a swallowed save
  failure.
- Use `except Exception` to also contain I/O failures on the best-effort channel
  (`REQ-001`: "or any exception").

## Alternatives considered

- Wrapping the entire `if ctx.diagnostics is not None:` block: rejected — it would also
  swallow the `stat_partial_completions` increment and the post-save `logger.warning`;
  per-call wrapping keeps those running.
- Centralized fix in `save()` (source-plan option b): rejected by the frozen scope — it
  changes a broadly-referenced symbol's contract (~42 call sites) and requires updating
  `tests/agent/test_diagnostic_store_security.py`; owner-gated (`UNK-01`).

## Implementation
### Target file

`scripts/agent/llm_turn_runner.py`

### Procedure

1. Partial-text branch (lines 201-216): wrap line 202 in its own `try/except`:

   ```python
   try:
       ctx.diagnostics.save(
           ctx.session.session_id,
           "llm_transport_error",
           incomplete_msg,
           workflow_id=workflow_id,
           task_id=task_id,
       )
   except Exception:  # noqa: BLE001 — best-effort diagnostic; a refusal or I/O failure must not break the turn
       logger.warning(
           "Failed to persist llm_transport_error diagnostic for %s (kind=llm_transport_error)",
           ctx.session.session_id,
           exc_info=True,
       )
   ```

2. In the same branch, wrap line 209 `save_partial_completion` in a separate `try/except`
   logging `(kind=partial_completion)`. Keep `stat_partial_completions += 1` (line 215)
   and `logger.warning` (line 216) OUTSIDE both handlers so they still run.
3. Mid-turn branch (lines 217-231): wrap line 218 in its own `try/except` logging
   `(kind=mid_turn_error)`.
4. Confirm the final `return TurnResult(...)` (lines 237-244) is reached regardless of a
   swallowed save failure.

### Method

Inline edits to one async method. No new symbols, no signature change, no import change
(`logger` already imported).

### Details

- Keep each handler narrow: only the corresponding save call sits inside `try`.
- Each warning carries `session_id` and the diagnostic `kind` for observability (`REQ-002`).
- `# noqa: BLE001` justified like `diagnostic_store.py` line 159.
- `save_partial_completion` is contained at its call site (line 209); its definition in
  `diagnostic_store.py` (lines 244-259) is NOT modified (reference file).

## Compatibility considerations

- `_handle_llm_error` is called from the turn path; its return type (`TurnResult`) and
  semantics are unchanged — a normal (non-raising) save is still recorded, and the fail
  `TurnResult` is still returned.
- No other caller or file is touched.

## Security considerations

- The security boundary is preserved, not bypassed: `save()` still refuses to persist
  detected-sensitive content unencrypted (`diagnostic_store.py` lines 168-174). This
  change only stops the resulting `RuntimeError` from escaping the turn.

## Rollback considerations

- Revert the single file (`git checkout -- scripts/agent/llm_turn_runner.py`): the change
  is localized wrappers; reverting restores the pre-change behavior.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_llm_turn_runner.py -x -q`.
- New regression test lands in row 4 (`tests/agent/test_llm_turn_runner.py`): raising
  `save()` / `save_partial_completion()` must not propagate and must emit a warning record;
  `_handle_llm_error` must still return a `TurnResult`.
- Full sequence per `rules/toolchain.md`: `ruff check`, `ruff format --check`,
  `uv run mypy scripts/`, `bandit -ll`, `radon cc -nc`, `vulture`.

## Completion criteria

- `REQ-001`: a `RuntimeError` from any diagnostic save no longer escapes
  `_handle_llm_error`; a fail `TurnResult` is still returned.
- `REQ-002`: the refusal is logged at warning level with `session_id` and `kind`.
- Existing `_handle_llm_error` tests pass unmodified; the new regression test passes.
- Lint/type/security gates clean with no new suppressions beyond the three justified
  `BLE001` noqa comments.

## Out of Scope

- `scripts/agent/diagnostic_store.py` `save()` / `save_partial_completion` (reference
  files; unchanged under option a).
- `tests/agent/test_diagnostic_store_security.py` (unchanged under option a; source plan
  row 4).
- The same-pattern sites in `scripts/agent/llm_transport_errors.py` and
  `scripts/agent/error_injection_service.py` (test-only, out of scope).
- Source-plan option b (centralized `save()` fix) — owner-gated.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Contain save calls at L202/L209/L218; REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Regression test in row 4 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs change |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20261101-111720_diagstore001_diagnostic-save-crashes-turn.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-120804_diagstore001_diagnostic-save-crashes-turn.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-122726
- **Related target files**: scripts/agent/llm_turn_runner.py
