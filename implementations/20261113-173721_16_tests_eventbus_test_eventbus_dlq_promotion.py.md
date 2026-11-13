## Goal
Update `sweep_orphans` call sites, rename the requeue audit test to its lineage name (cited by ADR-006 INV-08), and replace the unreachable-OSError nack test with a DB-only promotion test (REQ-001, REQ-002, REQ-004 / AC-1, AC-2, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Call-site count (2026-11-13 verification): 11 `sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)` sites at lines 164, 195, 229, 276, 300, 331, 400, 415, 429, 443, 701.
- `TestRequeueAuditField::test_dlq_requeue_increments_dlq_requeue_count_not_consumer_delivery_failure_count` (line 205) is the test ADR-006's INV-08 verification row cites; the new name is fixed by this document and consumed by row 10 (`20261113-173721_10_docs_10_adr_...md`), which must run after this one.
- Run after rows 01-02 (`dlq.py`, `ack_route.py`).

## Design decisions
- The renamed test keeps its second proof obligation (requeue must not touch `consumer_delivery_failure_count`) and swaps only its first: counter increment → `redelivered_from` descendant lineage (Plan Design: requeue history is carried by lineage).
- The `OSError`-patch test is rewritten rather than deleted: its post-dlqbox001 message ("promotion is DB-only; a failing artifact writer cannot defer it") is now the normal path, so the patch is meaningless but the assertion sequence still proves AC-2's outcome (promotion + outbox-generated artifact).

## Alternatives considered
- Deleting the OSError test: rejected — it is this file's only end-to-end proof that `/nack` promotion never writes inline and the outbox worker completes the artifact; REQ-002 explicitly says the test is "updated", not removed.

## Implementation
### Target file
`tests/eventbus/test_eventbus_dlq_promotion.py`

### Procedure
1. Mechanical: all 11 `sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)` calls become `sweep_orphans(db, max_retry=2)`. Leave `_drain_outbox(db, str(tmp_path / "deadletter"))` calls unchanged.
2. `TestDLQPromotionSemantics` (the test at line 205): rename the test to `test_dlq_requeue_records_lineage_not_consumer_delivery_failure_count` (new); update its docstring to "DLQ requeue records the descendant lineage but does NOT modify consumer_delivery_failure_count."; replace the `SELECT dlq_requeue_count FROM events ...` / `assert orig_row["dlq_requeue_count"] == 1` block (lines 215-218) with the descendant assertion `SELECT redelivered_from FROM events WHERE event_id = ?` on `new_event_id`, `assert new_row["redelivered_from"] == body["event_id"]`, plus `SELECT COUNT(*) FROM events WHERE redelivered_from = ?` on the original id == 1; keep the unchanged `consumer_delivery_failure_count == 2` assertion and the original row's `dlq_at is not None` assertion.
3. `TestPromotionFailurePaths::test_nack_with_failing_writer_still_promotes_and_outbox_generates` (lines 531-597): rename to `test_nack_promotes_db_only_and_outbox_generates_artifact` (new); remove the `monkeypatch` fixture parameter, the `dlq._atomic_write` capture, the `_raise` writer, and both `monkeypatch.setattr` calls; keep the two-nack sequence, `dlq_promoted is True`, `dlq_at is not None`, outbox row `status == "pending"`, "no inline file" and post-`_drain_outbox` file-exists assertions unchanged; update the docstring to state promotion is DB-only by design (no writer-failure scenario remains to patch).

### Method
- Step 1 is the same uniform textual transform as row 15; verify with `rg -n 'sweep_orphans\(db, str\(' tests/eventbus/test_eventbus_dlq_promotion.py` returning no match.

### Details
- The `from eventbus import dlq` import and `pytest.MonkeyPatch` typing are dropped only where step 3 removes their last use; other tests in `TestPromotionFailurePaths` keep their own patches.

## Compatibility considerations
- Row 10 (ADR-006) cites the step-2 test name; keep the exact name `test_dlq_requeue_records_lineage_not_consumer_delivery_failure_count` (new).

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Call sites | Test | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py -q` | All pass |
| Residual old signature | Search | `rg -n 'sweep_orphans\(db, str\(' tests/eventbus/test_eventbus_dlq_promotion.py` | No match |
| Column removal | Search | `rg -n "dlq_requeue_count" tests/eventbus/test_eventbus_dlq_promotion.py` | No match |
| Renamed test exists | Search | `rg -n "test_dlq_requeue_records_lineage_not_consumer_delivery_failure_count" tests/eventbus/test_eventbus_dlq_promotion.py` | One match |

## Completion criteria
- AC-2: the nack failure-path test exercises the DB-only path without patching; AC-1/AC-4 as for row 15; renamed test matches row 10's citation exactly.

## Out of Scope
- `test_dlq_list_snapshot_consistent_during_promotion` internals (no removed-field usage; only its sweep call changes in step 1), `_drain_outbox` helper signature.

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004 / AC-1, AC-2, AC-4
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `tests/eventbus/test_eventbus_dlq_promotion.py`
