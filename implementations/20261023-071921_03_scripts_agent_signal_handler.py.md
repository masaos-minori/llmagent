## Goal

Delete the now-unreachable `SignalHandler.set_shutdown_event()` rebinding hook and rewrite the two responsibility bullets that described it, so `SignalHandler` is documented as receiving the shutdown event owned by `AgentREPL` at construction. Keeps signal registration, the non-POSIX fallback, and the class-docstring first line byte-identical.

## Scope

Only `scripts/agent/signal_handler.py`: the `set_shutdown_event()` method (`:136-138`) and the two responsibility bullets in the module docstring (`:9`) and class docstring (`:34`). The call site (`repl.py:113`) is deleted in the sibling `repl.py` row. No other source file, and no `docs/*.md` edit.

## Assumptions

- The sibling `repl.py` row deletes the only call site (`repl.py:113`) before or with this row, so the method has no caller once both land.
- `docs/23_agent/agent_13_reference-api-generated.md:126` copies the class-docstring first line, which must stay byte-identical, so only the third responsibility bullet is reworded, never the first line.

## Design decisions

- Delete rather than re-parent. The hook exists only because the event was created after construction (`repl.py:112-113`); `REQ-001` removes that reason, leaving the method with no caller. Deleting it (not duplicating a setter on `ReplInputLoop`) is what closes the two-state-init defect (`REQ-005`).
- Rewrite the two bullets to describe the post-fix contract: `SignalHandler` receives the `asyncio.Event` owned by `AgentREPL` at construction and sets it on SIGTERM. This matches the measured behavior in `register()` (`:54-59`) and the constructor (`:37-49`).
- Keep the class-docstring first line (`:29`) byte-identical because `agent_13_reference-api-generated.md:126` copies it; keep the non-POSIX fallback (`:64-134`) and `register()` unchanged.

## Alternatives considered

- Renaming `set_shutdown_event()` to a no-op or raising `NotImplementedError`: rejected — dead code should be removed, not preserved as a stub.
- Rewording only the module docstring bullet and not the class docstring bullet: rejected — both describe the same hook and both would be stale.

## Implementation
### Target file
`scripts/agent/signal_handler.py`

### Procedure
1. Locate the method and bullets via grep (line numbers shift by ±1 vs the plan — content-based grep, UNK-03): `grep -n "def set_shutdown_event\|Coordinating shutdown\|Setting shutdown_event\|class SignalHandler" scripts/agent/signal_handler.py`.
2. Confirm the only call site is `repl.py:113` (deleted in the sibling row): `grep -rn "set_shutdown_event" scripts/ tests/` returns nothing after that row lands.
3. Delete the `set_shutdown_event` method body (`:136-138`).
4. Reword the module docstring bullet (`:9`) and the class docstring third bullet (`:34`) to describe receiving the event owned by `AgentREPL`; leave the class-docstring first line (`:29`) untouched.

### Method
- Verify the class-docstring first line before editing: read the three lines of the class docstring (`:29-35`) and confirm `:29` is `"""Encapsulates platform-specific signal handling for graceful shutdown.` — copy it verbatim into the rewritten docstring so it stays byte-identical.
- Verify `register()` (`:51-...`) and the non-POSIX fallback (`:64-134`) are unchanged after the edit.
- After editing, confirm no dangling reference: `grep -rn "set_shutdown_event" scripts/ tests/` returns nothing (the test-method-name substring in `test_startup_mcp_lifecycle.py:181` is unrelated and may remain; if a reviewer's grep is strict, rename that test method — see AC-2 caveat).

### Details
- Module docstring (`:9`): `- Coordinating shutdown with ReplInputLoop via shutdown_event` → `- Receiving the shutdown_event owned by AgentREPL at construction and setting it on SIGTERM to coordinate with ReplInputLoop`.
- Class docstring (`:34`): `- Setting shutdown_event to coordinate with ReplInputLoop shutdown watcher` → `- Receiving the shutdown_event owned by AgentREPL at construction to coordinate with the ReplInputLoop shutdown watcher`.
- Delete the method (`:136-138`):
  ```python
  def set_shutdown_event(self, event: asyncio.Event | None) -> None:
      """..."""
      self._shutdown_event = event
  ```
- Leave `__init__` (`:37-49`, accepts `asyncio.Event | None`), `register()` (`:51-59`), and the Windows fallback (`:64-134`) byte-identical.

## Compatibility considerations
`docs/23_agent/agent_13_reference-api-generated.md:126` copies the class-docstring first line, which is kept byte-identical, so no regeneration with `tools/generate_reference_table.py --type agent` is needed (AC-6). The public contract change (no more setter) is covered by REQ-005/AC-2.

## Security considerations
N/A: deleting a setter and rewording docstrings carries no security impact. Signal registration is unchanged.

## Rollback considerations
Revert the single commit; the setter and original bullets return, restoring the pre-change state exactly.

## Validation plan
- `uv run pytest tests/agent/test_signal_handler.py tests/agent/test_signal_handler_race.py -q` passes unchanged (AC-6).
- `uv run vulture scripts/agent/signal_handler.py --min-confidence 80` reports nothing (no unused member left) (AC-6).
- `uv run python tools/generate_reference_table.py --check --type agent` exits 0 (reference table not drifted) (AC-6).
- `grep -rn "set_shutdown_event" scripts/ tests/` returns nothing after the sibling row lands (AC-2).
- `git diff --stat scripts/agent/signal_handler.py` lists only this file among the production rows.

## Completion criteria
`set_shutdown_event()` is deleted with its only call site gone, the two responsibility bullets describe receiving the `AgentREPL`-owned event, the class-docstring first line is byte-identical, and signal registration plus the non-POSIX fallback are unchanged.

## Out of Scope
`scripts/agent/repl.py` (call site deleted in its row), `scripts/agent/repl_input_loop.py` (bound added in its row), `tests/agent/test_repl.py`, and all `docs/*.md` — byte-identical except the rows that correct them.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `set_shutdown_event()` and rewrite the two responsibility bullets | Pending | — | — | REQ-001, REQ-005; AC-2, AC-6 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No new test module (REQ-005) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | vulture, generate_reference_table --check, existing signal tests |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No `docs/*.md` edit in scope (REQ-008) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | AC-2's `grep -rn "set_shutdown_event"` may still match the unrelated test-method-name substring in `test_startup_mcp_lifecycle.py:181`; if a strict reviewer requires zero matches, rename that test method. Non-blocking — noted for implementation. | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: `issues/20261021-093421_repl001_sigint-sigterm-never-reach-repl-input-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-030840_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-071921
- **Related target files**: `scripts/agent/signal_handler.py`
