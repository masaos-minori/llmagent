## Goal
Update the `_promote` helper and its call sites to the new `promote_single` signature (REQ-001 / AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Verified 2026-11-13: the only `promote_single` use is the `_promote` helper (`tests/eventbus/test_eventbus_dlq_outbox.py` lines 97-101, call at 101); 8 call sites invoke `_promote(db, deadletter, ...)` at lines 216, 268, 310, 386, 412, 454, 499, 619 (one passes `str(tmp_path / "deadletter")` inline).
- `deadletter`/`deadletter_dir` remain in use by `process_outbox` and the `_worker`/`_base_cfg` helpers (lines 33, 67-92) — those signatures are unchanged by this plan.
- Run after row 01 (`dlq.py`).

## Design decisions
- Change the helper rather than each call site's inner call: the helper is the single seam between this file and `promote_single`, so dropping its now-unused `deadletter_dir` parameter keeps the helper honest (it no longer routes an argument the function ignores cannot receive).

## Alternatives considered
- Keeping the helper's `deadletter_dir` parameter to minimize the diff: rejected — an unused parameter is exactly the leftover-class the plan removes (REQ-005's naming/reachability intent).

## Implementation
### Target file
`tests/eventbus/test_eventbus_dlq_outbox.py`

### Procedure
1. `_promote` (line 97): change to `def _promote(db: Any, event_id: str) -> None` and the body to `assert promote_single(db, event_id) is True`.
2. Update all 8 call sites: `_promote(db, deadletter, ev["event_id"])` (and the `str(tmp_path / "deadletter")` variant at 386) become `_promote(db, ev["event_id"])`.

### Method
- Uniform textual transform; verify with `rg -n "_promote\(db, " tests/eventbus/test_eventbus_dlq_outbox.py` showing only single-event-argument calls.

### Details
- The surrounding fixture variables (`deadletter = str(tmp_path / "deadletter")`) stay: they feed `_worker`/`process_outbox`.

## Compatibility considerations
- None beyond row 01's signature change.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Outbox tests | Test | `uv run pytest tests/eventbus/test_eventbus_dlq_outbox.py -q` | All pass |
| Residual old call shape | Search | `rg -n 'promote_single\(db, [^e]' tests/eventbus/test_eventbus_dlq_outbox.py` | No match |

## Completion criteria
- AC-1: no `promote_single` call in this file passes a directory.

## Out of Scope
- `process_outbox`, `reconcile_missing_dlq_files`, `archive_dlq_record` usage and the outbox-status assertions (unchanged behavior).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 / AC-1
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `tests/eventbus/test_eventbus_dlq_outbox.py`
