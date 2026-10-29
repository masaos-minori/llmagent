# Implementation Procedure: tests/eventbus/test_eventbus_publish.py (Published-at ownership procedure 5)

## Goal

Lock the new publish behavior with valid-path tests and pin the existing duplicate-
retention behavior (plan UNK-03: current behavior maintained, no dedup change).

## Scope

- Add tests asserting supplied `published_at` values are stored exactly as sent.
- Add a duplicate-publish retention test pinning the current seq/idempotency behavior.

## Assumptions

- Existing tests `test_identical_content_retry_returns_same_seq` (`:216`) and
  `test_conflicting_content_retry_returns_409` (`:230`) already pin dedup behavior; the
  new test pins that both rows keep their own `published_at` (no rewrite on retry).

## Design decisions

- Follow the plan's UNK-03 decision: pin existing duplicate-retention behavior rather
  than changing it.

## Alternatives considered

- Add dedup-on-timestamp semantics (rejected by plan UNK-03 decision).

## Implementation
### Target file
`tests/eventbus/test_eventbus_publish.py`

### Procedure
1. Add a test that publishes an event with an explicit RFC 3339 `published_at` and
   asserts the stored/returned `published_at` equals the sent value (no server rewrite).
2. Add a test publishing identical content twice with different `published_at` values
   and asserting the retry returns the original seq and original `published_at`
   (current duplicate-retention shape).
3. Reuse the module's existing client fixtures; append the new tests after the existing
   idempotency tests.

### Method
Inline test additions; no fixture changes.

### Details
- These are new test names (no existing symbols with these names); the stale detector
  treats them as `(new)` via the template marker.

## Compatibility considerations

- New tests must not assume the removed schema default; all fixtures must send
  `published_at` explicitly.

## Security considerations

- None specific.

## Rollback considerations

- Remove the added tests together with the row 1-3 rollbacks.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_publish.py -q`

## Completion criteria

- New tests pass and pin stored-value equality plus duplicate retention.

## Out of Scope

- Contract-level malformed-input tests (row 4).
- Schema version pin (row 7).

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
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: issues/20261028-122454_ebpubat006_published-at-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-233320_ebpubat006_published-at-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-103639
- **Related target files**: tests/eventbus/test_eventbus_publish.py
