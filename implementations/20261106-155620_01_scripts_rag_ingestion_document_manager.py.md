## Goal

Widen the exception handler in `DocumentManager._invoke_callback` from
`except (TypeError, ValueError)` to `except Exception` (`REQ-001`, `REQ-003`; AC-1, AC-2) so a
callback that raises any other exception type (e.g. `sqlite3.Error` from a DB-reporting
`on_ingest_complete`) is logged and swallowed instead of escaping `check_consistency` and
breaking `RagIngester.ingest_all` after all ingestion already succeeded.

## Scope
**Release unit**: callback-catch-widening (Plan Release units)

## Assumptions
- `_invoke_callback` is a private static method with a single caller (`check_consistency`,
  `document_manager.py:130`), verified by `rg` across `scripts/` and `tests/`.
- `check_consistency` is itself called unguarded inside `RagIngester.ingest_all`
  (`ingester.py:171-175`); widening the catch keeps the "reporting must never break
  ingestion" contract that the surrounding code already follows.
- Catching `Exception` (not `BaseException`) is the intended ceiling: `KeyboardInterrupt` /
  `SystemExit` must still propagate (standard convention).

## Design decisions
- **Change only the except tuple.** Replace `except (TypeError, ValueError):` with
  `except Exception:` on a single line. Keep the body
  `logger.exception("on_ingest_complete callback failed")` byte-identical (AC-2, issue
  Constraint "Keep the `logger.exception` call and its message").
- **Binding-free form.** Use plain `except Exception:` (no `as exc`). `logger.exception`
  renders the traceback and message itself, so no binding is needed. This is also the
  form BLE001 permits — `pyproject.toml:106` selects `BLE001`, which flags only
  *unused bound* exceptions, not the binding-free form.
- **Narrowest boundary.** Do not move the try/except into `check_consistency` or
  `ingest_all`: the contract lives with the callback wrapper, and widening at the
  narrowest existing boundary cannot accidentally swallow ingestion errors (issue
  Constraint 1).

## Alternatives considered
- Moving the try/except into `check_consistency`: rejected — multi-statement-scope change,
  violates the "single handler-scope change" constraint.
- `except BaseException`: rejected — would swallow `KeyboardInterrupt` / `SystemExit`.
- Binding (`except Exception as exc`): rejected — unused binding would trip BLE001; no
  consumer needs the value.

## Implementation
### Target file
- `scripts/rag/ingestion/document_manager.py`

### Procedure
1. In `_invoke_callback`, change line :149 from `except (TypeError, ValueError):` to
   `except Exception:`. Nothing else in the file changes.

### Method
- Locate the method (lines :143-150):
  ```python
  @staticmethod
  def _invoke_callback(callback: Callable[[], None] | None) -> None:
      """Invoke the callback, logging any exception without re-raising."""
      if callback is not None:
          try:
              callback()
          except (TypeError, ValueError):
              logger.exception("on_ingest_complete callback failed")
  ```
- Change only the except line:
  ```python
          except Exception:
              logger.exception("on_ingest_complete callback failed")
  ```

### Details
- The docstring ("logging any exception without re-raising") already describes the new
  behavior; the change makes the code match the docstring. No docstring edit.
- No schema, public-API, or constant change. `scan_change_consumers.py` not required:
  private helper, one caller, no persisted state touched.
- `bump_index_generation` (`ingester.py:181-182`) can no longer be skipped by a callback
  crash — a consequence, not a requirement; no `ingester.py` change is needed.

## Compatibility considerations
`TypeError` catch coverage is a strict superset today, so no existing behavior narrows.
`check_consistency` and the ingestion path are untouched. The only observable change is
that previously-escaping callback exceptions are now logged and swallowed (AC-1).

## Security considerations
N/A: no input-handling, network, or credential change. The `logger.exception` line records
a full traceback at ERROR level, so masked callback failures remain observable (AC-1).

## Rollback considerations
Revert the commit to `document_manager.py`. The change is a single-line except-clause
edit.

## Validation plan
- RED: the new `sqlite3.Error`-callback regression test
  (`tests/rag/ingestion/test_rag_ingester_callback.py`, companion document) fails against
  current code (the exception escapes `ingest_all`) and passes after this change.
- Characterization: existing happy-path test `test_ingest_all_calls_on_ingest_complete`
  stays unchanged and green.
- Static gates: `uv run ruff check scripts/` (no BLE001 finding on the file),
  `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`,
  `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml
  -ll` — clean, no new findings.
- Coverage: changed lines reach ≥ 90% diff-cover (`rules/toolchain.md`).

## Completion criteria
- `_invoke_callback` uses `except Exception:` with the unchanged `logger.exception` body.
- The new regression test passes; happy-path test unchanged.
- ruff reports no BLE001 finding on the file; static gates clean; diff-cover ≥ 90%.

## Out of Scope
- `check_consistency`'s own try/except scope.
- Adding a callback to the CLI path (`ingester.py:409` passes none — unchanged).
- Any `ingester.py` change (consequence note only).
- Consistency report contents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Widen except clause in `scripts/rag/ingestion/document_manager.py` | Pending | — | — | REQ-001, REQ-003 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: `issues/20261106-073538_raging012_ingest-callback-narrow-catch.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-104959_raging012_ingest-callback-narrow-catch.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-155620
- **Related target files**: `scripts/rag/ingestion/document_manager.py`
