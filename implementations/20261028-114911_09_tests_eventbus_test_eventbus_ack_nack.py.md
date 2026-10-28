# Procedure: update Principal fixtures and add cross-consumer and cross-topic NACK tests

## Goal

Move the `principal_client` fixture to `consumer_grants` and prove NACK rejects another consumer's id and a non-granted event topic without changing state (Plan REQ-004).

## Scope

- Modify only `tests/eventbus/test_eventbus_ack_nack.py`.
- Test-only change; no source file is edited.

## Assumptions

- The source procedures with a lower `seq` have landed: `Principal` carries `consumer_grants` and the shared decision exists (they are created by earlier rows of the same Plan).
- Overlap (compatible): `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` also targets `scripts/eventbus/ack_route.py` and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits the promotion block of `_nack_and_promote` and one transition-table row, which this procedure does not touch. `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/app.py` (`_shutdown_lifespan` only).

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert on observable HTTP status and delivery state, not on state the test assigned to a mock.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure

- In the `principal_client` fixture (both construction sites), replace the removed fields with `consumer_grants` for `consumer-A` on the topic the file publishes to.
- Add `test_nack_with_other_consumers_id_returns_403` (new) and `test_nack_for_event_of_ungranted_topic_returns_403` (new); assert the `consumer_delivery` table is unchanged afterwards.
- Add `test_nack_for_unknown_event_still_returns_404` (new) for the unchanged not-found behavior.

### Method

Edit the existing tests in place; reuse the file's existing fixtures and helpers.

### Details

- The table-level assertions reuse the file's existing `db` fixture.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_ack_nack.py`; `uv run ruff check tests/eventbus/test_eventbus_ack_nack.py` | No finding |

## Completion criteria

- The new tests fail on the pre-change code (no topic check) and pass after.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (pair bound to the event topic for ACK and NACK)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py
