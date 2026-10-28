# Procedure: update the principal override and add a wrong-topic ACK test

## Goal

Move the principal override to `consumer_grants` and prove ACK rejects a non-granted event topic (Plan REQ-004).

## Scope

- Modify only `tests/eventbus/test_eventbus_ack_endpoint.py`.
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

`tests/eventbus/test_eventbus_ack_endpoint.py`

### Procedure

- In the `principal_client` fixture, replace the removed fields with `consumer_grants`; update the comment that mentions `allowed_consumer_ids`.
- In `test_ack_event_principal_ownership_validation`, update the comment about where the principal's authorization comes from.
- Add `test_ack_for_event_of_ungranted_topic_returns_403_and_changes_nothing` (new): publish to an ungranted topic, ACK with a granted `consumer_id`, expect 403 and no `consumer_delivery` or `consumer_offsets` row.

### Method

Edit the existing tests in place; reuse the file's existing fixtures and helpers.

### Details

- Reuses the file's `principal_client` and publish helpers.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_ack_endpoint.py`; `uv run ruff check tests/eventbus/test_eventbus_ack_endpoint.py` | No finding |

## Completion criteria

- The wrong-topic ACK test passes and leaves delivery and offset state untouched.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | 20261028-130500 | 20261028-130500 | Out-of-scope support: tests/eventbus/eventbus_helpers.py TEST_TOPICS, test_eventbus_crash_ack.py and test_eventbus_dlq_pagination.py consumer_authorization |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-130500 | 20261028-130500 |  |

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
- **Requirement ID**: REQ-004 (ACK pair authorization)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: tests/eventbus/test_eventbus_ack_endpoint.py