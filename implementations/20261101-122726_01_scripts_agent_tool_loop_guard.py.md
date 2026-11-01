## Goal

Contain the best-effort `DiagnosticStore.save()` sensitive-pattern refusal in
`scripts/agent/tool_loop_guard.py._save_guard_hint` so a raised `RuntimeError` (or any
exception from the save) degrades to a logged warning and never escapes the interactive
LLM turn. Implements `REQ-001` (no exception escapes the caller) and `REQ-002` (refusal
logged at warning level with `session_id` and `kind`) of the source plan.

## Scope

- Modify `_save_guard_hint` (`scripts/agent/tool_loop_guard.py` lines 137-151): wrap the
  single `ctx.diagnostics.save(ctx.session.session_id, "guard_hint", json_dumps(payload))`
  call at line 151 in a narrow `try/except Exception` that logs a warning including
  `session_id` and `kind="guard_hint"` and returns without propagating on any exception.
- All six callers (`check_empty_result_repeat`, `check_unavailable_repeat`, `check_cycle`,
  `_check_progress_stagnation`, `check_dedup`, `check_retry`) inherit the containment with
  no per-caller change. `check_unavailable_repeat` is also reached directly from
  `LLMTurnRunner.run()` (`scripts/agent/llm_turn_runner.py` line 173), so containing here
  covers that turn path too.

## Assumptions

- The narrow handler mirrors the existing `save()` filter-failure handling in
  `scripts/agent/diagnostic_store.py` lines 157-166 (`except Exception` with
  `# noqa: BLE001` and a `logger.warning(..., exc_info=True)`), consistent with the
  best-effort-diagnostics convention.
- `session_id` is available as `ctx.session.session_id`; the diagnostic `kind` is the
  literal `"guard_hint"` passed at line 151.
- A module-level `logger = logging.getLogger(__name__)` exists (`tool_loop_guard.py` line
  32).
- The early `if ctx.diagnostics is None: return` guard at line 144 stays above the wrapper;
  the wrapper only guards the save itself.

## Design decisions

- Contain at the single choke point `_save_guard_hint` rather than per-caller: every guard
  event funnels through this one static method, so one wrapper contains all six callers
  (and the direct `check_unavailable_repeat` path from the runner). Per-caller wrapping
  would duplicate the handler six times.
- Use `except Exception` (not `except RuntimeError`) to also contain I/O failures on the
  best-effort channel, matching `save()`'s own handler and satisfying `REQ-001` ("or any
  exception").

## Alternatives considered

- Per-caller wrapping in each of the six callers: rejected — duplicates the wrapper and
  misses any future caller; the choke point is one method.
- Centralized fix in `save()` (source-plan option b): rejected by the frozen scope — it
  changes a broadly-referenced symbol's contract (~42 call sites) and requires updating
  `tests/agent/test_diagnostic_store_security.py`; owner-gated (`UNK-01` of the source
  plan).

## Implementation
### Target file

`scripts/agent/tool_loop_guard.py`

### Procedure

1. Locate `_save_guard_hint` (lines 137-151); the diagnostic save is line 151.
2. Replace line 151 with a guarded form:

   ```python
   try:
       ctx.diagnostics.save(ctx.session.session_id, "guard_hint", json_dumps(payload))
   except Exception:  # noqa: BLE001 — best-effort diagnostic; a refusal or I/O failure must not break the turn
       logger.warning(
           "Failed to persist guard_hint diagnostic for %s (kind=guard_hint)",
           ctx.session.session_id,
           exc_info=True,
       )
   ```

3. No explicit `return` is needed: the method returns `None` and the handler swallows the
   exception, so callers continue normally.

### Method

Inline edit to one static method. No new symbols, no signature change, no import change
(`logger` already imported at line 32).

### Details

- Keep the handler narrow: only the `ctx.diagnostics.save(...)` call sits inside `try`;
  nothing else in the method is affected.
- The warning carries `session_id` and the diagnostic `kind` for observability (`REQ-002`).
- `# noqa: BLE001` is justified identically to `diagnostic_store.py` line 159 (the filter
  must never block diagnostic persistence; a save failure is logged and deferred).
- The `payload` dict (lines 146-150) is built before the `try`; leave it unchanged.

## Compatibility considerations

- All six callers inherit the containment unchanged; none is edited.
- `check_unavailable_repeat` (also called directly from `LLMTurnRunner.run():173`) inherits
  the containment.
- No behavior change for the normal (non-raising) case: a successful save is recorded as
  before.

## Security considerations

- The security boundary is preserved, not bypassed: `save()` still refuses to persist
  detected-sensitive content unencrypted (`diagnostic_store.py` lines 168-174). This change
  only stops the resulting `RuntimeError` from escaping the turn; it does not relax
  detection.

## Rollback considerations

- Revert the single file (`git checkout -- scripts/agent/tool_loop_guard.py`): the change
  is a localized wrapper; reverting restores the pre-change behavior.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_tool_loop_guard.py -x -q`.
- New regression test lands in row 3 (`tests/agent/test_tool_loop_guard.py`): raising
  `save()` must not propagate and must emit a warning record.
- Full sequence per `rules/toolchain.md`: `ruff check`, `ruff format --check`,
  `uv run mypy scripts/`, `bandit -ll`, `radon cc -nc`, `vulture`.

## Completion criteria

- `REQ-001`: a `RuntimeError` from `save()` no longer escapes `_save_guard_hint`.
- `REQ-002`: the refusal is logged at warning level with `session_id` and `kind`.
- Existing guard tests pass unmodified; the new regression test passes.
- Lint/type/security gates clean with no new suppressions beyond the one justified
  `BLE001` noqa comment.

## Out of Scope

- `scripts/agent/diagnostic_store.py` `save()` (reference file; unchanged under option a).
- `tests/agent/test_diagnostic_store_security.py` (unchanged under option a; row 4 of the
  source plan).
- The same-pattern sites in `scripts/agent/llm_transport_errors.py` and
  `scripts/agent/error_injection_service.py` (test-only, out of scope).
- Source-plan option b (centralized `save()` fix) — owner-gated.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Contain in `_save_guard_hint` (line 151); REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Regression test in row 3 |
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
- **Related target files**: scripts/agent/tool_loop_guard.py
