# Procedure: update Principal construction and add pairwise decision tests

## Goal

Move direct `Principal(...)` construction to `consumer_grants` and cover the four-cell matrix and control-plane rejection (Plan REQ-001, REQ-005).

## Scope

- Modify only `tests/eventbus/test_eventbus_auth.py`.
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

`tests/eventbus/test_eventbus_auth.py`

### Procedure

- In `_make_test_app`, replace the consumer principal's `allowed_consumer_ids` and `allowed_topics` with `consumer_grants`; update the explanatory comment that mentions `None` meaning unrestricted.
- In `_make_test_app`'s local `resolve_subscribe_identity` copy, keep the shape but call the production dependency the way `app.py` does.
- Rewrite `test_principal_without_topic_binding_is_rejected` for a principal with empty `consumer_grants`, and `test_non_empty_topic_restriction_is_enforced_and_returned` to assert a granted pair is accepted and an ungranted pair gets 403.
- Add `test_pairwise_matrix_rejects_cross_pairs` (new): grants `(consumer_a, topic_a)` and `(consumer_b, topic_b)`; the two own pairs pass and the two cross pairs return 403.
- Add `test_control_plane_token_cannot_use_consumer_routes` (new): the shared `auth_token` and `admin_token` get 403 on subscribe, ACK and NACK.

### Method

Edit the existing tests in place; reuse the file's existing fixtures and helpers.

### Details

- The test-local `resolve_subscribe_identity` mirrors production wiring, so a production wiring change must be reflected here; compare with `app.py` when editing.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_auth.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_auth.py`; `uv run ruff check tests/eventbus/test_eventbus_auth.py` | No finding |

## Completion criteria

- No test constructs `Principal` with the removed fields.
- The matrix and control-plane tests pass.

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
- **Requirement ID**: REQ-001, REQ-003, REQ-005 (grant model, shared decision, control-plane rejection)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: tests/eventbus/test_eventbus_auth.py
