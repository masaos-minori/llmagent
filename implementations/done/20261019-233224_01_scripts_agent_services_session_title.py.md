## Goal

Add an explicit `except (sqlite3.Error)` clause to `SessionTitleService.generate` in `scripts/agent/services/session_title.py` so that a database failure raised by `ctx.session.set_title(...)` is converted into `SessionTitleGenerationError` (chained with `from e`) instead of escaping the `try` uncaught. This restores the single, consistent failure contract that every other failure type already funnels through, so the command-layer fallback (`SessionTitleGen.generate`) triggers on DB errors exactly as it does on LLM/HTTP failures.

## Scope

- **In scope:**
  - Add `import sqlite3` to `scripts/agent/services/session_title.py`.
  - Insert one `except sqlite3.Error as e:` clause in `SessionTitleService.generate`, placed immediately before the existing `except (RuntimeError, OSError)` handler, raising `SessionTitleGenerationError(f"DB error: {e}") from e`.
- **Out of scope:**
  - Changing `AgentSession.set_title` (`scripts/agent/session.py`) — its `title[:SESSION_TITLE_MAX_CHARS]` storage cap (Issue sess002) and its `sqlite3.Error` propagation are intentionally preserved.
  - Changing `SessionTitleGen.generate` (`scripts/agent/commands/session_title.py`) or its fallback logic.
  - Changing which failures are retryable; only ensuring DB errors funnel through `SessionTitleGenerationError`.

## Assumptions

- `sqlite3.Error` is not a subclass of `RuntimeError`, `OSError`, or `ValueError` (its MRO is `sqlite3.Error -> Exception -> BaseException -> object`), so the generic handler never matched it and still will not — the new clause is required, not redundant in effect.
- `sqlite3.Error` is importable at module load with no side effects (stdlib), so `import sqlite3` is safe at the top of the file.
- Any `sqlite3.Error` raised anywhere inside the `try` during generation is legitimately a generation failure worth converting; the issue frames the fix as "a database error ... during generation," so broad capture within the `try` is intended.
- The retryability decision lives in callers of `SessionTitleGen`/`SessionTitleService`, so wrapping does not alter retry semantics.

## Design decisions

- **Dedicated clause vs. extending the generic handler.** A dedicated `except sqlite3.Error` clause is preferred over adding `sqlite3.Error` to the `(RuntimeError, OSError)` tuple. `sqlite3.Error` is not a `RuntimeError`/`OSError`, so the generic handler never caught it; widening the tuple would muddy the generic handler's "unexpected runtime errors" meaning. A dedicated clause documents intent and mirrors the existing per-type clauses (`httpx`, `ValueError`).
- **Placement immediately before the generic handler.** Insert the clause right after the `except ValueError` clause and directly before `except (RuntimeError, OSError)`. It is reached before the generic branch and reads as a distinct, intentional DB-error case.
- **Ordering is safe.** `SessionTitleGenerationError(RuntimeError)` (exceptions.py line 13) is re-raised first (`except SessionTitleGenerationError: raise`, line 61), so it never shadows the new clause. `sqlite3.Error` is unrelated to `httpx`, `ValueError`, `RuntimeError`, and `OSError`, so no two clauses overlap. Resulting order: `SessionTitleGenerationError` → `httpx` → `ValueError` → `sqlite3.Error` → `(RuntimeError, OSError)`.
- **Cause chaining.** Raise `SessionTitleGenerationError(f"DB error: {e}") from e` so the original `sqlite3.Error` is preserved in `__cause__`, matching the `from e` style of the surrounding clauses.
- **Message shape.** Use a DB-specific prefix `f"DB error: {e}"`, consistent with the ValueError clause's `f"Response parse error: {e}"` and the generic clause's `f"Unexpected error: {e}"`. (The httpx clause uses bare `str(e)`; the DB clause follows the descriptive-prefix convention used by the other two.)

## Alternatives considered

- **Extend the generic `(RuntimeError, OSError)` tuple to `(RuntimeError, OSError, sqlite3.Error)`.** Works functionally but conflates genuine runtime/OS errors with DB errors under one catch-all, reducing clarity. Rejected in favor of the dedicated clause.
- **Place the clause after the generic handler.** Would never be reached because `sqlite3.Error` is not a `RuntimeError`/`OSError` — the generic handler's tuple does not include it, so placement relative to the generic handler is about readability/intent, not reachability. Placed before the generic handler to make the DB-error case explicit and ordered.

## Implementation

### Target file

`scripts/agent/services/session_title.py` (modify).

### Procedure

1. **Add the import.** In the stdlib import group at the top of the file, add `import sqlite3`. Current imports are:
   ```python
   from __future__ import annotations

   import logging
   from typing import TYPE_CHECKING

   import httpx
   from shared.json_utils import extract_llm_content, parse_http_json
   from shared.llm_client import build_llm_url

   from agent.services.exceptions import SessionTitleGenerationError
   from agent.services.models import SessionTitleResult
   ```
   Insert `import sqlite3` alongside `import logging`:
   ```python
   import logging
   import sqlite3
   from typing import TYPE_CHECKING
   ```
2. **Insert the new `except` clause.** In `SessionTitleService.generate`, locate the existing `except` chain (lines 61-67):
   ```python
           except SessionTitleGenerationError:
               raise
           except (httpx.HTTPStatusError, httpx.RequestError) as e:
               raise SessionTitleGenerationError(str(e)) from e
           except ValueError as e:
               raise SessionTitleGenerationError(f"Response parse error: {e}") from e
           except (RuntimeError, OSError) as e:
               raise SessionTitleGenerationError(f"Unexpected error: {e}") from e
   ```
   Insert a new clause **between** the `except ValueError` clause (lines 65-66) and the `except (RuntimeError, OSError)` clause (line 67):
   ```python
           except sqlite3.Error as e:
               raise SessionTitleGenerationError(f"DB error: {e}") from e
   ```
   The parenthesized form `except (sqlite3.Error) as e:` is equivalent and acceptable if strict parity with the plan's REQ-001 wording is desired; the unparenthesized form is recommended for readability.
3. **Verify indentation.** The new clause must sit at the same indentation level as the sibling `except` clauses (8 spaces under the `try`). The `set_title` call it now guards is at line 58 (`ctx.session.set_title(title)`), inside the same `try`.

### Details

- The resulting `except` order is: `SessionTitleGenerationError` (re-raise) → `httpx` → `ValueError` → `sqlite3.Error` (new) → `(RuntimeError, OSError)`. No already-handled type stops being handled; none change their wrapping-message shape.
- `sqlite3.Error` is the base class of all SQLite exceptions (e.g. `sqlite3.IntegrityError`, `sqlite3.OperationalError`), so catching it captures the full family of DB failures, matching the intent of "a database error ... during generation."
- No signature, interface, schema, config, or deploy change. `set_title`'s behavior and `sqlite3.Error` propagation are untouched.

## Compatibility considerations

- Existing consumers of `SessionTitleService.generate` already expect `SessionTitleGenerationError`; this only widens the set of inputs that produce it. `SessionTitleGen.generate` (`scripts/agent/commands/session_title.py` line 31) catches `SessionTitleGenerationError` and applies its input-based fallback (lines 33-41), so the DB-failure case now degrades gracefully to the fallback title exactly as LLM/HTTP failures do.
- The new exception message `"DB error: ..."` is a new string shape but is only produced on a previously-unhandled path, so no existing test or caller depends on it.

## Security considerations

- No new secrets, permissions, or attack surface. The `sqlite3.Error` message is included in the wrapper message via `{e}`; SQLite error strings do not typically contain user-controlled data beyond the query/column names, and the value is logged/wrapped, not returned to end users as a raw traceback. This matches the handling of the other clauses.

## Rollback considerations

- The change is a single additive clause plus one import line. To revert, delete the `import sqlite3` line and the new `except sqlite3.Error` clause, restoring the original four-clause chain. No migration, config, or data change accompanies it.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/session_title.py` (DB error -> wrapped) | Unit: drive `SessionTitleService.generate` past the HTTP path with `set_title` raising `sqlite3.Error`; assert `SessionTitleGenerationError` is raised and chained. | `uv run pytest tests/agent/services/test_session_title.py` | Covered by the regression test added in the companion doc (`test_session_title.py`). |
| Touched file (lint/type) | Static: `ruff` + `mypy` on `scripts/agent/services/session_title.py`. | `uv run ruff check` / `uv run mypy` | Clean (zero findings); `sqlite3` resolves. |
| Deployment | No deploy artifact changes (exception handling only). | Inspect `deploy/` for session-title references | No deploy script references the changed handling; nothing to redeploy beyond normal code rollout. |

The regression test asserting the conversion itself is authored in the companion implementation procedure for `tests/agent/services/test_session_title.py` (REQ-003); this document covers only the source change and its own lint/type/deployment validation.

## Completion criteria

- `scripts/agent/services/session_title.py` contains `import sqlite3` and an `except sqlite3.Error as e:` clause raising `SessionTitleGenerationError(f"DB error: {e}") from e`, placed immediately before the `except (RuntimeError, OSError)` handler.
- Re-raise ordering is `SessionTitleGenerationError` → `httpx` → `ValueError` → `sqlite3.Error` → `(RuntimeError, OSError)`.
- `ruff check` and `mypy` pass cleanly on the touched file.
- The REQ-003 regression test (companion doc) passes, confirming the conversion.

## Out of Scope

- `scripts/agent/session.py` (`set_title` storage cap and `sqlite3.Error` propagation).
- `scripts/agent/commands/session_title.py` (`SessionTitleGen.generate` fallback).
- Retryability semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261020-121334 | 20261020-121334 | Add `import sqlite3` + `except sqlite3.Error` clause before the generic handler Added import sqlite3; inserted except sqlite3.Error clause before except (RuntimeError, OSError); raises SessionTitleGenerationError(f'DB error: {e}') from e. |
| 2 | Add or update tests per Validation plan | Completed | 20261020-121334 | 20261020-121334 | Regression test authored in companion doc (`test_session_title.py`) N/A (source change; regression test is proc 08). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-121334 | 20261020-121334 | ruff/mypy on `session_title.py` ruff/mypy(438)/lint-imports(6/6)/bandit clean; combined Plan C suite 9614 passed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020-121334 | 20261020-121334 | N/A — no `docs/*.md` describes this contract N/A. |

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
- **Source issue**: `issues/20261019-202210_sess003_sessiontitleservice-primary-path-lets-sqlite3.error-from-set_title-propagate-uncaught-instead-of-triggering-fallback.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-221335_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-233224
- **Related target files**: `scripts/agent/services/session_title.py`