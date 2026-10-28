# Procedure: update config-to-principal assertions and add the consumer/topic matrix

## Goal

Assert the pair set built from `consumer_authorization` and `topic_authorization` and that empty mappings stay deny-all (Plan REQ-001, REQ-007).

## Scope

- Modify only `tests/eventbus/test_eventbus_consumer_authorization.py`.
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

`tests/eventbus/test_eventbus_consumer_authorization.py`

### Procedure

- In `test_mapping_loaded_via_config_reaches_consumer_principal`, replace the two set assertions with `principal.consumer_grants == frozenset({("c1", "topicA")})`.
- In `test_empty_mapping_via_config_denies_all`, assert `principal.consumer_grants == frozenset()`.
- Add `test_consumer_authorization_with_empty_topic_list_grants_nothing` (new): `{"c1": []}` yields no grant, so `c1` is rejected.
- Add `test_cross_pair_is_rejected_over_http` (new) using the file's existing client fixture: configure `c-a -> topic-a` and `c-b -> topic-b` and assert 403 for `c-a`/`topic-b` and `c-b`/`topic-a`, 200 for the own pairs.

### Method

Edit the existing tests in place; reuse the file's existing fixtures and helpers.

### Details

- The file's `TestClient` fixtures and config helpers are reused unchanged.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_consumer_authorization.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_consumer_authorization.py`; `uv run ruff check tests/eventbus/test_eventbus_consumer_authorization.py` | No finding |

## Completion criteria

- Assertions use `consumer_grants`.
- The cross-pair HTTP test fails on the pre-change code and passes after.

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
- **Requirement ID**: REQ-001, REQ-007 (grants built from both mappings; deny-all semantics)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: tests/eventbus/test_eventbus_consumer_authorization.py
