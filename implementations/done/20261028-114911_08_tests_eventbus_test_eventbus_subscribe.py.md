# Procedure: update Principal fixtures and add omitted-topic tests for subscribe

## Goal

Move the subscribe fixtures to `consumer_grants` and prove an omitted topic never widens access (Plan REQ-002).

## Scope

- Modify only `tests/eventbus/test_eventbus_subscribe.py`.
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

`tests/eventbus/test_eventbus_subscribe.py`

### Procedure

- In the `principal_client` fixture, build the consumer principal with `consumer_grants=frozenset({("consumer-A", "t")})`-style pairs matching the topics the file's tests publish.
- In `test_subscribe_with_restricted_topic_rejects_disallowed_topic`, replace `allowed_consumer_ids=None` and `allowed_topics=...` with grants and keep the 403 assertion.
- Add `test_subscribe_without_topic_receives_only_granted_topics` (new): grants for `topic-a` only; publish to `topic-a` and `topic-b`; subscribe without `topic`; assert only the `topic-a` event is delivered, both live and in replay.
- Add `test_subscribe_without_topic_and_without_grants_returns_403` (new).
- Keep `test_subscribe_principal_ownership_validation` and update its comment about `allowed_consumer_ids`.

### Method

Edit the existing tests in place; reuse the file's existing fixtures and helpers.

### Details

- Existing SSE helper functions in the file collect events without sleeps; reuse them.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_subscribe.py tests/eventbus/test_eventbus_replay_subscribe.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_subscribe.py`; `uv run ruff check tests/eventbus/test_eventbus_subscribe.py` | No finding |

## Completion criteria

- The omitted-topic tests fail on the pre-change code and pass after.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | 20261028-130500 | 20261028-130500 |  |
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
- **Requirement ID**: REQ-002 (omitted topic narrows to granted topics)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: tests/eventbus/test_eventbus_subscribe.py