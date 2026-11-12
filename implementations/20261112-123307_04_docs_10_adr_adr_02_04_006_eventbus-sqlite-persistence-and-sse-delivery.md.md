## Goal
Make ADR-006 INV-13 say `>= max_retry`, re-map the INV-04, INV-07, and publish-retry test rows to the invariants they verify, and name the requeue API's HTTP 409 text (`REQ-002`, `REQ-003`, `REQ-008` / `AC-2`, `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Implementation Notes already say `>= max_retry` and the cited test is `..._gte_max_retry`; `scripts/eventbus/dlq.py` `is_promotable` promotes at the max_retry boundary — only INV-13's text is stale.
- Current rows (checked): INV-04 cites `test_eventbus_crash_ack.py::...test_unacked_event_replayed_on_reconnect` (it verifies the at-least-once baseline, INV-07); INV-07 cites the publish-retry idempotency tests (INV-06, Event IDs for idempotent processing, UNK-03).
- `already_redelivered` and `not_in_dlq` both map to HTTP 409 with `ERR_EVENT_NOT_IN_DLQ` (`event is not in DLQ`) in `scripts/eventbus/dlq_route.py`; `route_helpers.py` defines the text.
- Overlap: adrrev014 (Scope, Data Ownership, Replay Contract), adrrev016 (front matter, INV-15), and `plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md` edit other regions; this document edits INV-13, the test rows, and the requeue paragraph only — compatible. Locate by text, not line number.

## Design decisions
- Change wording only; no invariant is renumbered, so index citations by `ADR-NNN INV-NN` stay valid.
- INV-04 gets the restart-resume tests; the unacked-replay test moves to INV-07; the publish-retry tests move to INV-06.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. INV-13 (Invariants list): replace `has exceeded max_retry` with `has reached max_retry (>= max_retry)`.
2. Automated Tests: re-map the INV-04, INV-07, and publish-retry rows.
3. Requeue paragraph (the `Redelivery uniqueness` bullet): name the HTTP 409 error text.
4. Append one `Current Decision Approval (pending)` line to the Approval Record.

### Method
- INV-04 row: tests `tests/eventbus/test_eventbus_restart_resume.py::test_same_consumer_id_resumes_from_last_acked_offset` and `::test_resume_from_sqlite_offset` (consumer IDs and persisted ACK offsets across restarts).
- INV-07 row: `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_unacked_event_replayed_on_reconnect` (the at-least-once baseline).
- Publish-retry row: `test_identical_content_retry_returns_same_seq` and `test_conflicting_content_retry_returns_409` map to INV-06 (confirm at approval, UNK-03).
- Requeue paragraph: add that `already_redelivered` is returned to the caller as HTTP 409 with the text `event is not in DLQ`, the same text as for an event not in the DLQ.
- Approval line wording: `Current Decision Approval (pending)`: the INV-13 wording and Verification re-mapping await maintainer approval; approver, date, and scope are 不明; tracked by adrrev012.

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); none is written on a maintainer's behalf (UNK-04).
- Count Automated Tests rows before and after the edit; no row is dropped. Do not edit the requeue API's 409 text (a behavior question, out of scope).

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` (only the intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.

## Completion criteria
- INV-13, the Implementation Notes, and the cited test agree on `>= max_retry`.
- Each test row verifies the invariant it names; the requeue paragraph names the 409 text; a marked pending approval line exists.

## Out of Scope
- Scope, Data Ownership, and Replay Contract text (adrrev014); front matter and INV-15 (adrrev016); changing the API's 409 text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` / `REQ-003` / `REQ-008` — INV-13 `>=` wording; test rows verify their invariants; requeue 409 text; pending approval
- **Source issue**: issues/20261109-113220_adrrev015_adr-index-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104147_adrrev015_adr-index-matrix.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123307
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
