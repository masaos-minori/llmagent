## Goal

Save the generated title to the captured target session, reject a stale generation, and keep title text out of logs (REQ-004 target-checked save, REQ-005 log redaction; AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change; row 29 is covered as this document's companion.

## Assumptions
- Current code verified: `services/session_title.py:56-57` calls `ctx.session.set_title(title)` unconditionally and logs `logger.info("Session title generated: %r", title)`.
- The captured target reaches this module through the context variable set by seq 09.

## Design decisions
- Read the captured target and pass it as `set_title(..., target=...)` (seq 01); when the write is refused (stale target), log a redacted rejection (class name and ids only) and return a result marked stale instead of writing (REQ-004).
- Replace the `%r` title-text log with a title-free line (session id and generation only) (REQ-005).

## Alternatives considered
N/A: the plan fixes the captured-target design.

## Implementation
### Target file
`scripts/agent/services/session_title.py`
### Procedure
1. Read the context variable target; call `set_title` with that target.
2. On a refused (stale) write, log without title text and surface the rejection in `SessionTitleResult`.
3. Remove `%r` title interpolation from the success log.
### Method
Read-target-then-target-checked-write; result type unchanged (stale case logged, not raised) unless the companion tests need a flag field — keep it minimal.
### Details
N/A: none beyond the plan text.

### Companion test files
- `tests/agent/services/test_session_title.py`
  - Procedure: assert a stale-generation title is rejected (no write) and that caplog records contain no title text.
  - Validation: `uv run pytest tests/agent/services/test_session_title.py -q`.

## Compatibility considerations
- `SessionTitleResult` behavior for stale writes must not break `commands/session_title.py` handling (its own row, seq 11).

## Security considerations
- Redacting title text from logs is the AC-2 requirement: titles may contain user input.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_session_title.py -q`.

## Completion criteria
A title completes only into the session that created the task, stale results are refused with redacted logs, and no log line carries title text (AC-2).

## Out of Scope
Target capture (seq 09), fallback-title path (seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261123-122206 | After seq 01, 09 Changed: scripts/agent/services/session_title.py |
| 2 | Add or update tests per Validation plan (companion row 29) | Completed | — | 20261123-122206 | Tests written first per plan Phase 4 Changed: tests/agent/services/test_session_title.py. Stale-generation and no-title-log tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-122206 | 20261123-123429 | 3e clean (ruff, mypy 608 files, lint-imports, bandit -ll, module size, docstrings, suppression, compat shims, mock patch targets). Full suite 2 failed/13510 passed, failures in out-of-scope tests (see report); diff-cover 98% End-of-batch run passed: 13519 passed, 5 skipped; mypy 608 files clean; lint-imports 6 kept; diff-cover 98% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261123-122207 | Generated docs via seq 18 N/A: docs handled by procedures 15-20 |

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
- **Requirement ID**: `REQ-004` (target-checked title save), `REQ-005` (title text out of logs)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/services/session_title.py`, `tests/agent/services/test_session_title.py`