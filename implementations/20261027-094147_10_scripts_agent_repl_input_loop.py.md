## Goal

Surface ConversationPersistenceError distinctly in the REPL loop instead of letting it be handled by the generic per-turn exception handler (`REQ-007`). The current `_repl_loop` catches all per-turn errors with a single `except Exception` and routes them through `_surface_turn_error`; this row adds a narrower branch ahead of that handler so a compensated persistence failure prints a dedicated "turn not persisted, history rolled back" message while the loop continues with consistent state.

## Scope

- **In-Scope** (`scripts/agent/repl_input_loop.py` only):
  - Add an `except ConversationPersistenceError` clause to `_repl_loop`, placed before the existing `except Exception as exc` (repl_input_loop.py:315), that writes a distinct message via the view and re-enters the loop (`REQ-007`).
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
2. In `_repl_loop` (repl_input_loop.py:229), add `except ConversationPersistenceError:` before `except Exception as exc:` (repl_input_loop.py:315); write a distinct message via `self._view` and let the loop continue.
3. Run the validation sequence.

### Method

`ReplInputLoop` (repl_input_loop.py:38) owns the interactive loop. `_repl_loop` (repl_input_loop.py:229) runs the read/dispatch loop; its per-turn wrapper ends with `except TimeoutError` branches (repl_input_loop.py:310-314) followed by a catch-all `except Exception as exc:  # noqa: BLE001` (repl_input_loop.py:315) that calls `self._surface_turn_error(exc)` (repl_input_loop.py:316) inside a `finally` that clears the turn-active flags. `_surface_turn_error` (repl_input_loop.py:128) writes `{exc.__class__.__name__}: {exc}` via `self._view.write_fatal`. The new branch sits ahead of repl_input_loop.py:315.

```python
# repl_input_loop.py — distinct persistence error (REQ-007)  (new)
            except TimeoutError:
                if ctx.conv.shutdown_requested:
                    self._log_graceful_shutdown_timeout()
                    break
                raise
            except ConversationPersistenceError:                 # (new) seq 01
                self._view.write_turn_not_persisted()
            except Exception as exc:  # noqa: BLE001 — contain unexpected per-turn errors so the interactive session stays usable after a failing turn
                self._surface_turn_error(exc)
            finally:
                self._turn_active = False
                ctx.conv.is_processing = False
```

### Details

- **`REQ-007` (distinct surfacing):** the new branch calls a dedicated view method (e.g. `write_turn_not_persisted` (new)) producing "turn not persisted, history rolled back", distinct from the generic `{name}: {exc}` format.
- **`AC-007` (loop continues):** after surfacing, the `finally` resets turn state and the loop reads the next input; existing REPL error tests still pass.
- **Ordering:** the branch MUST precede the `except Exception` handler (repl_input_loop.py:315), else the generic handler consumes it.

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
| 1 | Add distinct ConversationPersistenceError branch in `scripts/agent/repl_input_loop.py` | Pending | — | — | Before generic except at L315 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Extend `tests/agent/test_repl_error_handling.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
