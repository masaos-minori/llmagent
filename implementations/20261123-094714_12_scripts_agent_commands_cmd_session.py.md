## Goal

Load sessions through the transition service, report the four separate counts, and show title pending per session (REQ-002 load via service, REQ-009 separate counts; AC-1, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change. Its behavioral tests are carried by rows 21 and 30 (covered in seq 02 and seq 11 documents), per this row's Related Tests cell.

## Assumptions
- Current code verified: `_load_session` calls `restore_session` directly and prints one count (`cmd_session.py:254-269`); the list view shows "(generating...)" via `is_title_pending()` for the current row (`cmd_session.py:118`) and truncates titles with `SESSION_TITLE_TRUNCATE_AT`/`SESSION_TITLE_MAX_CHARS`.
- `SessionRestoreResult` already carries the four counts (seq 05) and the service exists (seq 02) when this row runs.

## Design decisions
- Replace the direct `restore_session` call with the seq 02 transition service load method, including refusal-message handling for the idle check (REQ-002).
- Success message reports fetched, synthesized, dropped, and restored separately (REQ-009).
- Per-session pending display uses the seq 01 per-session pending state: current row keeps its check; non-current rows consult the per-session set so a stale generating session shows correctly (plan row 12).

## Alternatives considered
N/A: service routing is fixed by REQ-002.

## Implementation
### Target file
`scripts/agent/commands/cmd_session.py`
### Procedure
1. Rewire `_load_session` to call the transition service and print the four counts.
2. Update the list view's title-state and truncation logic to the per-session pending state and the display-limit constant (seq 01).
3. Keep lazy-import style for the service import, matching the module's existing pattern.
### Method
Call-site replacement; display helpers adjusted, table structure unchanged.
### Details
- `cmd_session.py` is also named by open Issues cliplc003/cliplc011; this plan lands first (plan Assumptions) — keep changes confined to `_load_session` and the list view to reduce overlap.

## Compatibility considerations
- User-visible success string changes (four counts); companion tests in rows 21/30 assert behavior, row 30 lives in the seq 11 document.

## Security considerations
N/A: display-only changes.

## Rollback considerations
N/A: revert the commit (depends on seq 02, 05).

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_session.py tests/agent/services/test_session_transition.py -q`.

## Completion criteria
/session load either commits atomically via the service or leaves the old session untouched, reports four counts, and pending title state is shown per session (AC-1, AC-5).

## Out of Scope
Service internals (seq 02), per-session pending storage (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | After seq 02, 05 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Behavioral tests in rows 21/30 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs via seq 15 |

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
- **Requirement ID**: `REQ-002` (load through the service), `REQ-009` (four separate counts)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/commands/cmd_session.py`
