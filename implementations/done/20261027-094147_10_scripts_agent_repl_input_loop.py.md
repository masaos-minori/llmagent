## Goal

Surface ConversationPersistenceError distinctly in the REPL loop instead of letting it be handled by the generic per-turn exception handler (`REQ-007`). The current `_repl_loop` catches all per-turn errors with a single `except Exception` and routes them through `_surface_turn_error`; this row adds a narrower branch ahead of that handler so a compensated persistence failure prints a dedicated "turn not persisted, history rolled back" message while the loop continues with consistent state.

## Scope

- **In-Scope** (`scripts/agent/repl_input_loop.py`, plus the view output chain that carries the distinct message):
  - In `repl_input_loop.py`, add an `except ConversationPersistenceError` clause to `_repl_loop`, placed before the existing `except Exception as exc` (repl_input_loop.py:318), that calls `self._view.write_turn_not_persisted()` and re-enters the loop (`REQ-007`).
  - Add the `write_turn_not_persisted()` method across the view output chain so the call type-checks and renders: `WriterBase` (ABC, `NotImplementedError` default) and `CLIView` (delegates to port) in `cli_view.py`, and `OutputPort` (Protocol) + `CliOutputPort` (prints the `[non-fatal] turn not persisted, history rolled back` line) in `commands/output_port.py`.
  - Preserve the existing `SchemaMissingError` / `RuntimeError` / `sqlite3.Error` branches in `run` and the `TimeoutError` handling in `_repl_loop` unchanged.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The ConversationPersistenceError body and its compensation/restore (turn_persistence.py, seq 01).
  - The orchestrator's narrow branch that sets the persistence `error_kind` (orchestrator.py, seq 05).

## Assumptions

- The orchestrator (seq 05) re-raises ConversationPersistenceError after the boundary compensates and restores, so it propagates to the REPL as a distinct type.
- ConversationPersistenceError (seq 01) subclasses `Exception`, so the new branch must precede the generic `except Exception` handler to take effect.

## Design decisions

- **Narrow branch ahead of the generic handler.** Python evaluates `except` clauses top-to-bottom; placing the ConversationPersistenceError branch before `except Exception` ensures persistence failures are distinguished from other per-turn errors (`REQ-007`).
- **Keep the loop alive.** After surfacing the message, the loop proceeds to the next input exactly as it does for other contained errors, so the interactive session stays usable (`AC-007`).

## Alternatives considered

- **Handle persistence errors in `_surface_turn_error`.** Rejected: that method takes a generic `Exception` and formats `{name}: {exc}`; special-casing there would mix persistence formatting into the generic path. A dedicated branch keeps the messages separable and testable.

## Implementation

### Target file

`scripts/agent/repl_input_loop.py` (existing; extended)

### Procedure

1. Import ConversationPersistenceError (seq 01) at module scope.
2. In `_repl_loop` (repl_input_loop.py:230), add `except ConversationPersistenceError:` before `except Exception as exc:` (repl_input_loop.py:318); call `self._view.write_turn_not_persisted()` and let the loop continue.
3. Run the validation sequence.

### Method

`ReplInputLoop` (repl_input_loop.py:38) owns the interactive loop. `_repl_loop` (repl_input_loop.py:230) runs the read/dispatch loop; its per-turn wrapper ends with `except TimeoutError` branches (repl_input_loop.py:311-315) followed by a catch-all `except Exception as exc:  # noqa: BLE001` (repl_input_loop.py:318) that calls `self._surface_turn_error(exc)` (repl_input_loop.py:319) inside a `finally` that clears the turn-active flags. `_surface_turn_error` (repl_input_loop.py:129) writes `{exc.__class__.__name__}: {exc}` via `self._view.write_fatal`. The new branch sits ahead of repl_input_loop.py:318.

```python
# repl_input_loop.py — distinct persistence error (REQ-007)  (new)
            except TimeoutError:
                if ctx.conv.shutdown_requested:
                    self._log_graceful_shutdown_timeout()
                    break
                raise
            except ConversationPersistenceError:  # seq 10: compensated turn; surface distinctly before the generic handler
                self._view.write_turn_not_persisted()
            except Exception as exc:  # noqa: BLE001 — contain unexpected per-turn errors so the interactive session stays usable after a failing turn
                self._surface_turn_error(exc)
            finally:
                self._turn_active = False
                ctx.conv.is_processing = False
```

### Details

- **`REQ-007` (distinct surfacing):** the new branch calls the dedicated `self._view.write_turn_not_persisted()` (added to the view output chain: `WriterBase`/`CLIView` in `cli_view.py`, `OutputPort`/`CliOutputPort` in `commands/output_port.py`), which prints "[non-fatal] turn not persisted, history rolled back" — distinct from the generic `{name}: {exc}` format written by `_surface_turn_error`.
- **`AC-007` (loop continues):** after surfacing, the `finally` resets turn state and the loop reads the next input; existing REPL error tests still pass.
- **Ordering:** the branch MUST precede the `except Exception` handler (repl_input_loop.py:318), else the generic handler consumes it.

## Compatibility considerations

- Additive branch; `_surface_turn_error` and other handlers unchanged. Requires a new view method for the distinct message (Phase 1 view-surface detail).

## Security considerations

- No new input surface; the message names the failure category, not any sensitive value.

## Rollback considerations

- Revert the `repl_input_loop.py` edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| distinct surfacing | Unit: inject ConversationPersistenceError, assert distinct message | `uv run pytest tests/agent/test_repl_error_handling.py` | Dedicated message printed |
| loop continues | Behavior: loop accepts next input after persistence error | `uv run pytest tests/agent/test_repl_error_handling.py` | Loop consistent (`AC-007`) |
| backward compat | Regression: existing REPL error tests | `uv run pytest tests/agent/test_repl_error_handling.py` | Unchanged |
| static | ruff / mypy / bandit / vulture | `uv run ruff check scripts/`; `uv run mypy scripts/`; `uv run bandit -r scripts/ -c pyproject.toml`; `uv run vulture scripts/` | Clean |

## Completion criteria

- `_repl_loop` has an `except ConversationPersistenceError` branch ahead of the generic `except Exception` handler that surfaces a distinct message and keeps the loop alive.
- Existing REPL error tests pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body + compensation/restore (turn_persistence.py, seq 01).
- Orchestrator narrow branch (orchestrator.py, seq 05).
- Generic `_surface_turn_error` formatting (repl_input_loop.py, seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add distinct ConversationPersistenceError branch in `scripts/agent/repl_input_loop.py` + `write_turn_not_persisted` across the view output chain | Complete | 2026-10-27 | 2026-10-27 | Imported ConversationPersistenceError; added `except ConversationPersistenceError:` at L316 before generic except at L318; added write_turn_not_persisted to cli_view.py (WriterBase+CLIView) and commands/output_port.py (OutputPort+CliOutputPort, [non-fatal] tag) |
| 2 | Add or update tests per Validation plan | Complete | 2026-10-27 | 2026-10-27 | Added test_repl_surfaces_persistence_error_distinctly (test_repl_error_handling.py); added write_turn_not_persisted coverage to test_output_port.py (protocol parametrize + mock + stdout) and test_cli_view.py (delegation) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Complete | 2026-10-27 | 2026-10-27 | ruff check/format clean, mypy --no-namespace-packages clean (441 files), lint-imports 6/6, bandit High/Medium 0, vulture @80 exit 0 (pre-existing TYPE_CHECKING false-positives only); full suite 10235 passed, 12 skipped |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Complete | 2026-10-27 | 2026-10-27 | Corrected Scope (view output chain now in-scope), Procedure/Method/Details line numbers (shifted +1 from import), pseudocode comment, Execution Status |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `scripts/agent/repl_input_loop.py`
