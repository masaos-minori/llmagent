## Goal

Give `AgentSession` a monotonically increasing session generation and an immutable `SessionTarget` (new), make `set_title` target-checked, make title pending per session id, and split the title storage and display limits (REQ-001 session generation, REQ-004 title targeting, REQ-009 separate limits; AC-2, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change to the session state owner. Foundation for the transition service (seq 02) and the title-task binding (seq 09-11).

## Assumptions
- `session_id` stays a plain attribute bumped by `start()`; `generation` is runtime state only, no schema change (Plan Assumptions).
- Current helpers verified against source: `_title_pending` bool at `session.py:80`, `is_title_pending`/`set_title_pending` at `session.py:207-213`, `set_title` truncating to `SESSION_TITLE_MAX_CHARS` and writing to the current session id at `session.py:215-230`.

## Design decisions
- `generation` (new) starts at 0 and increments inside `start()` and in the transition commit (seq 02 calls a bump hook); it changes on every session id change (REQ-001).
- `capture_target()` returns `SessionTarget` (new) — a frozen dataclass of `session_id` and `generation`; `set_title(title, *, target=None)` writes only when the target matches the current id and generation, else returns False without writing; `title_pending` becomes a per-session-id set (REQ-004).

## Alternatives considered
- Versioned attribute on the DB row: rejected — generation is runtime state (Plan Assumptions: no schema change).

## Implementation
### Target file
`scripts/agent/session.py`
### Procedure
1. Add the `generation` (new) attribute init and its increment in `start()`; add the commit-side bump helper for the transition service.
2. Add `SessionTarget` (new) and `capture_target()` (new).
3. Rework `set_title(title, *, target=None)`: target match required; keep returning False when session_id is None and raising `sqlite3.Error` on DB failure.
4. Replace the single `_title_pending` bool with per-session-id pending state; `set_title_pending(pending, session_id=None)` / `is_title_pending(session_id=None)` keep the current call sites working when no id is passed.
5. Split `SESSION_TITLE_MAX_CHARS` into `SESSION_TITLE_STORAGE_MAX_CHARS` (new), used for truncation in `set_title`, and `SESSION_TITLE_DISPLAY_MAX_CHARS` (new), used for display truncation by command rows; keep re-exports where consumers import the old name only if `tools/generate_reference_table.py --check` requires the transition.
### Method
Field and constant additions plus signature widening with keyword-only `target`; existing callers (no target) keep the write-to-current behavior.
### Details
- `set_title` currently shares one 32-char constant for storage and display (`session.py:34`); display callers use `SESSION_TITLE_TRUNCATE_AT` for the ellipsis — keep that helper, change only the limit constants (REQ-009).

### Companion test files
- `tests/agent/test_agent_session.py`
  - Procedure: add generation-increment-on-start, `capture_target` (new) immutability, target-checked `set_title` (stale target returns False, no write), per-session pending, and storage/display limit tests.
  - Validation: `uv run pytest tests/agent/test_agent_session.py -q`.

## Compatibility considerations
- `set_title` gains a keyword-only parameter; all current call sites (`conversation_service.py`, both title modules, `cmd_session.py`) pass positionally and stay valid until their own rows switch to targets (Plan consumer scan).
- `is_title_pending()`/`set_title_pending()` keep working with no arguments.

## Security considerations
N/A: no new input handling; title truncation preserved.

## Rollback considerations
N/A: revert the commit; dependent rows (seq 02, 09-12) land after this one.

## Validation plan
- `uv run pytest tests/agent/test_agent_session.py -q`.
- Full sequence per `rules/toolchain.md`; `uv run python tools/generate_reference_table.py --check` after the constant split.

## Completion criteria
Generation changes on every session id change; a stale target cannot write a title; pending state is per session; storage and display limits are separate constants; the companion tests pass (AC-2, AC-5).

## Out of Scope
The transition service (seq 02), title-task capture (seq 09-11), command display changes (seq 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261123-120528 | Changed: scripts/agent/session.py (+ UNK-03 marker memory_finalized_count/record_memory_finalized; temporary SESSION_TITLE_MAX_CHARS alias removed at seq 12) |
| 2 | Add or update tests per Validation plan (companion row 22) | Completed | — | 20261123-120528 | Changed: tests/agent/test_agent_session.py; targeted tests pass (testmon not usable on cold data; rg-selected tests/agent files, 508+ passed) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-120528 | 20261123-123425 | 3e: ruff, mypy (607 files), lint-imports, bandit, module size, docstrings, suppression, compat shims clean; awaiting end-of-batch full run End-of-batch run passed: 13519 passed, 5 skipped; mypy 608 files clean; lint-imports 6 kept; diff-cover 98% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261123-120528 | Docs handled by seq 15-20 N/A: docs handled by procedures 15-20 |

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
- **Requirement ID**: `REQ-001` (generation and target), `REQ-004` (target-checked title writes), `REQ-009` (separate title limits)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/session.py`, `tests/agent/test_agent_session.py`