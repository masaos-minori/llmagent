## Goal

Own the write-or-skip decision in exactly one component (REQ-003): gate both
persist methods on `ctx.session.session_id`, skipping (no `DiagnosticStore.save`,
no `memory.on_session_stop`) and logging the reason when no session was started.
Contain persistence failures so a defect in the payload-building body is reported
as non-fatal instead of escaping the method (REQ-004, REQ-005). State the new
contract in the module, class, and method docstrings (REQ-009).

## Scope

Production behavior change to `scripts/agent/session_persister.py` only. Reference
reads: `scripts/agent/context.py` (`ctx.session`, `AgentSession` at
`scripts/agent/session.py:148`), `scripts/agent/cli_view.py` (`write_warning`,
`OutputTag.NON_FATAL`), `scripts/agent/memory/ingestion.py` (`on_session_stop`
no-ops on empty history, `:87-89`). Dependent tests:
`tests/agent/test_session_persister.py` (rows 5), `tests/agent/test_repl.py`
(row 4).

## Assumptions

- `session_id` is the sole session-existence state in the code
  (`scripts/agent/session.py:148` is the only assignment; `AgentSession` has no
  `started` flag, no `end()`, no factory). The gate keys on it (UNK-02).
- `DiagnosticStore.save(session_id=None, …)` must keep working — it is tested as
  intended (`tests/agent/test_regression_diagnostic_persist.py:114-123`) and used
  by `session.py:94` and the turn recorders after a session exists. The gate lives
  **above** the store, not inside it (REQ-006).
- `memory.on_session_stop` already no-ops on an empty history (`ingestion.py:87-89`);
  the gate prevents the call rather than changing it (UNK-03).

## Design decisions

- **Gate both methods with an early return (REQ-003).** At the very top of each
  method, before any payload work:
  ```python
  if self._ctx.session.session_id is None:
      logger.info("Skipping session persistence: no started session")
      return
  ```
  A skip performs no `save` and no `on_session_stop` and records its reason in the
  log. This is an early return, not a nested branch around the body.
- **Widen the containment of `persist_session_diagnostics` (REQ-004, REQ-005).**
  The outer guard at `:154` currently catches only `(OSError, sqlite3.Error)`, so
  a payload-defect exception (e.g. `TypeError` from `json.dumps` on a
  non-serializable stat value) escapes. Change that clause to catch the whole
  step and route the failure through the non-fatal channel:
  ```python
  except Exception as e:
      logger.debug("Failed to persist session diagnostics", exc_info=True)
      self._view.write_warning(
          f"{OutputTag.NON_FATAL} Session persistence failed: {type(e).__name__}: {e}"
      )
  ```
  This broadens the existing single clause (no new `except` branch), so it does
  not add a counted branch.
- **Import `OutputTag`.** Add `from agent.output_tags import OutputTag` (the same
  module `repl.py` uses for the same tag). The current `write_warning` at `:152`
  carries no tag; the widened guard now does (REQ-004).
- **Update the docstrings (REQ-009).** Module docstring (`:2-9`), class
  docstring (`:32-37`), `persist_session_diagnostics` docstring (`:51`), and
  `persist_session_memories` docstring (`:159`) each state that the step skips
  (logging the reason) when `ctx.session.session_id` is None and otherwise writes
  before resource close.

## Alternatives considered

- Putting the gate in `AgentREPL.run()` instead of `SessionPersister` — rejected:
  the decision is a policy about when session state is meaningful, and the
  component that performs the writes is the only one that knows which values
  depend on a `sessions` row (Design → Why the decision belongs to
  `SessionPersister`). Keeping it in `AgentREPL` would force any future non-REPL
  caller to re-derive it.
- Containing only the DB call (leaving the payload body unguarded) — rejected:
  the measured `TypeError` escaped through the payload body, not the `save` call
  (Background); REQ-005 requires the whole step contained.

## Implementation

### Target file

`scripts/agent/session_persister.py`

### Procedure

1. **Add the import.** Insert
   `from agent.output_tags import OutputTag` alongside the other
   `from agent.*` imports (after `:24`).
2. **Gate `persist_session_diagnostics`.** Insert the early return at the top of
   the method, before the `try` at `:52`:
   ```python
   if self._ctx.session.session_id is None:
       logger.info("Skipping session diagnostics: no started session")
       return
   ```
3. **Widen the outer guard.** Replace the clause at `:154-155`
   (`except (OSError, sqlite3.Error): logger.debug(...)`) with the `Exception`
   clause shown in Design decisions. Keep the `logger.debug` line for
   observability; add the `write_warning` line (REQ-004).
4. **Gate `persist_session_memories`.** Insert the same early return at the top of
   the method, before the `if self._ctx.services ...` guard at `:159`:
   ```python
   if self._ctx.session.session_id is None:
       logger.info("Skipping session memories: no started session")
       return
   ```
5. **Update the four docstrings** per Design decisions.

### Method

Read-only reference reads of `scripts/agent/session.py` (`session_id` at `:148`,
silent-skip precedents at `:80-84`/`:89-93`), `scripts/agent/memory/ingestion.py`
(`:87-89`), and `scripts/db/schema_sql.py` (`session_diagnostics` DDL, `:140-150`)
confirm the gate reads `session_id` and follows the existing skip pattern; neither
file changes.

### Details

- **AC-9 / radon budget.** `persist_session_diagnostics` is radon C (18) at HEAD.
  Step 2 adds one counted branch (`if`), which would raise it to C (19). Re-run
  `uv run radon cc scripts/agent/session_persister.py` after steps 2-4. If the
  method exceeds complexity 18, extract the payload-building body (`:53-142`) into
  a private helper (e.g. `_build_session_summary(self) -> dict`) so the extracted
  method holds the branches and `persist_session_diagnostics` stays within budget.
  Do not compensate by nesting the gate — REQ-003 must stay an early return.
- The widened `except Exception` does not add a branch (it replaces the existing
  clause), so it does not affect the radon count on its own.
- REQ-006 holds automatically: the gate reads `session_id` and returns above
  `DiagnosticStore.save`; calling `save(session_id=None, …)` directly still writes
  a row. The new mirror test asserts this contrast (row 5).

## Compatibility considerations

- No signature changes. The payload (`:111-134`), the `StateStore`/RAG enrichment
  (`:72-109`), and the inner `save` error path (`:144-152`) are unchanged.
- On the normal-exit path both methods still run, in the same order, with the same
  payload, before any resource is closed (REQ-010): `test_repl_error_handling.py:20`
  sets `session_id = 123` and `TestPersistSessionDiagnostics` sets `session_id = 1`,
  so both pass through the gate.

## Security considerations

- N/A: no auth, secret, or permission change. Containment widens the caught
  exception type, which is an operational-robustness change, not a privilege
  change.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/session_persister.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_session_persister.py tests/agent/test_repl.py
  tests/agent/test_repl_error_handling.py tests/agent/test_regression_diagnostic_persist.py
  tests/agent/test_import_smoke.py -q` (AC-3, AC-4, AC-7).
- `grep -rn "persister_callback" scripts/ tests/` → empty (AC-5).
- `uv run ruff check scripts/agent/session_persister.py tests/agent/test_session_persister.py`
  (no `F401` from the `OutputTag` import unless unused), `uv run mypy
  --no-namespace-packages scripts/agent/session_persister.py`, `uv run vulture
  scripts/agent/session_persister.py --min-confidence 80`.
- `uv run radon cc scripts/agent/session_persister.py` and
  `uv run python tools/check_module_size.py` (AC-9): `persist_session_diagnostics`
  not above C (18); `check_module_size.py` reports no new violation.
- `uv run python tools/check_docstrings.py` (AC-9, REQ-009).

## Completion criteria

Both persist methods skip (logging the reason) when `ctx.session.session_id` is
None and write otherwise; a persistence failure — including a payload-body defect —
is reported via `write_warning` with `OutputTag.NON_FATAL` and does not escape;
docstrings state the gate; AC-3/AC-4/AC-7/AC-9 hold.

## Out of Scope

- The persist step's new call site in `AgentREPL.run()` — row 1. The
  `ReplInputLoop.run()` parameter/`finally` removal — row 2. Test-file changes —
  rows 4/5. Docs — rows 6/7. `DiagnosticStore` itself (REQ-006) and
  `scripts/agent/session.py` / `context.py` (the gate reads, does not edit).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import `OutputTag` | Pending | — | — | REQ-004 |
| 2 | Gate `persist_session_diagnostics` with early return (REQ-003) | Pending | — | — | REQ-003, REQ-009 |
| 3 | Widen outer guard to `Exception` + `write_warning` (REQ-004, REQ-005) | Pending | — | — | REQ-004, REQ-005, AC-9 |
| 4 | Gate `persist_session_memories` with early return | Pending | — | — | REQ-003 |
| 5 | Update module/class/method docstrings (REQ-009) | Pending | — | — | REQ-009 |
| 6 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2-5 | Shared file with `repl001` (`plans/20261022-030840_plan.md`)? No — `session_persister.py` is not in `repl001`'s region. This Plan is ordered after `repl001`/`repl002`/`repl003`/`shutdown001` only for the shared `test_repl.py`/docs; this file itself has no cross-plan edit. | No | — |
| 3 | AC-9 radon budget: adding the REQ-003 gate may push `persist_session_diagnostics` above C (18); extract the payload body if so (see Details). | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | 3 | Complexity | Open | implementer | Phase 2, if radon > C(18) |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004, REQ-005, REQ-009
- **Source issue**: `issues/20261021-093421_shutdown002-session-persistence-skipped-on-startup-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-071052_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-093504
- **Related target files**: `scripts/agent/session_persister.py`
