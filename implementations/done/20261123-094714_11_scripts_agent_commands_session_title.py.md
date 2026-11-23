## Goal

Use the captured target for the pending state and the fallback title, and stop logging title text and raw failure reasons (REQ-004 target-bound fallback, REQ-005 audit redaction; AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change; row 30 is covered as this document's companion.

## Assumptions
- Current code verified: `commands/session_title.py:27-57` sets pending on the current session, builds a fallback title (truncated first input or "(New Session)"), writes it via `set_title(fallback_title)`, logs "using fallback: %s" with the raw error, and emits an audit line `session_title_fallback session_id=%s fallback=%r reason=%s` carrying the fallback text and exception.

## Design decisions
- Read the captured target (seq 09 context variable) once and use it for `set_title_pending`, the fallback `set_title(target=...)` write, and the finally-clause pending reset — a stale task can no longer flip pending on a newer session (REQ-004).
- Audit and warning lines keep ids and the exception class name only; fallback text and raw reason are dropped (REQ-005, AC-2).

## Alternatives considered
N/A: the captured-target design is fixed by the plan.

## Implementation
### Target file
`scripts/agent/commands/session_title.py`
### Procedure
1. Capture the target at method start; pass it to pending-state calls and the fallback `set_title`.
2. Rewrite the fallback audit line as `session_title_fallback session_id=%s generation=%s error=%s` with `type(exc).__name__` — no fallback text, no raw reason.
3. Rewrite the warning log likewise.
### Method
Target threading through existing branches; display-side truncation constants switch to the display limit (seq 01) for the fallback preview.
### Details
N/A: none beyond the plan text.

### Companion test files
- `tests/agent/commands/test_agent_cmd_session.py`
  - Procedure: assert the fallback title lands on the captured target (not the current session when they differ) and that audit/warning records contain no title text or raw reason.
  - Validation: `uv run pytest tests/agent/commands/test_agent_cmd_session.py -q`.

## Compatibility considerations
- The audit event text changes; any dashboard or test matching the old `fallback=%r reason=%s` shape is in the companion row.

## Security considerations
- AC-2 redaction point: fallback titles echo user input and must not enter logs or audit.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_session.py -q`.

## Completion criteria
Pending state and fallback writes follow the captured target, and neither the audit line nor the warning carries title text or a raw failure reason (AC-2).

## Out of Scope
Service-side save path (seq 10), capture point (seq 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261123-122207 | After seq 01, 09 Changed: scripts/agent/commands/session_title.py |
| 2 | Add or update tests per Validation plan (companion row 30) | Completed | — | 20261123-122207 | Tests written first per plan Phase 4 Changed: tests/agent/commands/test_agent_cmd_session.py. Targeting and redaction tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-122207 | 20261123-123429 | 3e clean (ruff, mypy 608 files, lint-imports, bandit -ll, module size, docstrings, suppression, compat shims, mock patch targets). Full suite 2 failed/13510 passed, failures in out-of-scope tests (see report); diff-cover 98% End-of-batch run passed: 13519 passed, 5 skipped; mypy 608 files clean; lint-imports 6 kept; diff-cover 98% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261123-122207 | N/A for this row N/A: docs handled by procedures 15-20 |

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
- **Requirement ID**: `REQ-004` (target-bound pending and fallback), `REQ-005` (audit and log redaction)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/commands/session_title.py`, `tests/agent/commands/test_agent_cmd_session.py`