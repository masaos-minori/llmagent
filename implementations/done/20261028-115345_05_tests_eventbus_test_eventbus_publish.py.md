# Procedure: add the duplicate-publish-after-JSONL-failure test

## Goal

Prove a retry of the same event after a failed JSONL append returns the same `seq` and does not backfill JSONL (Plan REQ-006).

## Scope

- Modify only `tests/eventbus/test_eventbus_publish.py`.
- Test-only change; no source file is edited.

## Assumptions

- Independent of the code rows; it documents existing behavior.
- Overlap (compatible): `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived, procedures pending) also targets `scripts/eventbus/ack_route.py` (authorization at the start of the routes) and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (Authentication section and error table); this procedure edits only the promotion block of `_nack_and_promote` and one transition-table row.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_publish.py`

### Procedure

- Add `test_duplicate_publish_after_jsonl_failure_returns_same_seq_and_does_not_backfill` (new): patch `Path.open` to fail for `events.jsonl` as `test_publish_succeeds_if_jsonl_append_fails` does, publish an event, then publish the identical event again without the patch; assert both responses carry the same `seq`, `events.jsonl` does not contain the event id, and the `/replay` result lists the event once.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- No production change is needed: JSONL is appended only when the insert reports `inserted`; this test documents the accepted divergence.
- The file's `client` fixture, `_event` helper and `patch` import are reused.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_publish.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_publish.py`; `uv run ruff check tests/eventbus/test_eventbus_publish.py` | No finding |

## Completion criteria

- The test passes on the current code and pins the documented no-backfill behavior.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | 2026-10-28 | 2026-10-28 | Test added as specified; 15 tests pass |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-28 | 2026-10-28 | pytest + ruff clean; full suite 10372 passed; diff-cover 100% |

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
- **Requirement ID**: REQ-006 (idempotent duplicate publish after a failed JSONL append)
- **Source issue**: issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115345
- **Related target files**: tests/eventbus/test_eventbus_publish.py
