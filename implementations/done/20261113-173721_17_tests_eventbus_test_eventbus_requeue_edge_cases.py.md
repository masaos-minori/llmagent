## Goal
Update `sweep_orphans` call sites and replace every `dlq_requeue_count` and `already_redelivered`-field assertion with status/lineage assertions (REQ-001, REQ-003, REQ-004 / AC-1, AC-3, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Call-site count (2026-11-13 verification): 5 `sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)` sites at lines 145, 206, 232, 276, 307.
- Run after rows 01, 04 (`dlq.py`, `dlq_repo.py`); the `status == "already_redelivered"` string values stay valid (REQ-003 removes only the boolean field, not the status vocabulary).

## Design decisions
- Every removed-counter assertion maps to a descendant-row query (`SELECT COUNT(*) FROM events WHERE redelivered_from = ?`) or a deletion when a descendant query already asserts the same fact — the lineage row is the surviving single requeue fact (Plan Design).

## Alternatives considered
- Deleting the counter-focused tests: rejected — they encode rollback and exactly-once behaviors (failure injection, two-connection race) that must keep regression coverage against the new write path.

## Implementation
### Target file
`tests/eventbus/test_eventbus_requeue_edge_cases.py`

### Procedure
1. Mechanical: all 5 `sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)` calls become `sweep_orphans(db, max_retry=2)`.
2. `test_requeue_valid_dlq_event` (118): at line 157 change `SELECT dlq_at, dlq_requeue_count FROM events WHERE event_id = ?` to `SELECT dlq_at FROM events WHERE event_id = ?` and delete line 161 `assert orig_row["dlq_requeue_count"] == 1`; keep `assert orig_row["dlq_at"] is not None` (160) and the existing descendant block (163-168, `new_row["redelivered_from"] == body["event_id"]` on `data["new_event_id"]`) unchanged — do not add a duplicate descendant assertion.
3. `test_second_requeue_of_same_event_rejected_after_first_redeliver` (170): at 209-218 replace the counter block with `SELECT COUNT(*) FROM events WHERE redelivered_from = ?` on the original id asserted `== 1`; at 242-243 re-run the same count query after the rejected 409 and assert it is still `1`.
4. `TestRequeueFailureInjection` tests (420, 461): replace the `_get_field(client, event_id, "dlq_requeue_count") == 0` assertions (450, 489) with `SELECT COUNT(*) FROM events WHERE redelivered_from = ?` on the original id asserted `== 0` (rolled-back requeue leaves no descendant).
5. `test_redelivered_from_violation_maps_to_already_redelivered` (557): delete line 574 `assert result.already_redelivered is True` (keep `assert result.status == "already_redelivered"` at 573 and the `new_event_id`/`new_seq` None asserts); replace the post-rollback counter block (580-585, `SELECT dlq_requeue_count ... assert count == 0`) with the descendant-count query asserted `== 0`, and adjust the adjacent comment from "UPDATE increment undone" to "INSERT rolled back".
6. `test_two_connections_requeue_same_original_exactly_once` (600): delete the redundant `SELECT dlq_requeue_count ... assert count == 1` block (646-650); the descendant-count `== 1` assertion immediately above (640-645) already proves the fact.

### Method
- Steps 2-6 are text-anchored block replacements per quoted line numbers; verify completeness with `rg -n "dlq_requeue_count|already_redelivered is" tests/eventbus/test_eventbus_requeue_edge_cases.py` returning no match.

### Details
- The `_get_field` helper stays for other columns (`dlq_at`, `dlq_at`-based checks); only its `dlq_requeue_count` call sites are removed.

## Compatibility considerations
- No test name changes in this file; no doc citations reference these tests.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Call sites | Test | `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q` | All pass |
| Residual old signature | Search | `rg -n 'sweep_orphans\(db, str\(' tests/eventbus/test_eventbus_requeue_edge_cases.py` | No match |
| Removed field/column | Search | `rg -n "dlq_requeue_count|already_redelivered is" tests/eventbus/test_eventbus_requeue_edge_cases.py` | No match |

## Completion criteria
- AC-3: the result-object surface is exercised only through `status`/`new_event_id`/`new_seq`; AC-1/AC-4 as for rows 15-16.

## Out of Scope
- The 409/404 response-code expectations and rollback/transaction-state assertions (`conn.in_transaction`), which are behavior-unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261113-214650 | deviation step5: procedure said descendant-count==0 but competitor descendant row makes count 1; applied documented deletion rule (existing n==1 block covers the fact) per Design decisions |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113-214650 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113-214650 | targeted pytest 10 passed; mypy/coverage/full-suite deferred to cycle 18 per group-1 deferral note |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113-214650 | N/A docs out of scope, handled by row 14 regeneration |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-004 / AC-1, AC-3, AC-4
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `tests/eventbus/test_eventbus_requeue_edge_cases.py`