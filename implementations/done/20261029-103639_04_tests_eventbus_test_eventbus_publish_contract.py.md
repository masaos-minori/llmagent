# Implementation Procedure: tests/eventbus/test_eventbus_publish_contract.py (Published-at ownership procedure 4)

## Goal

Flip the contract test that asserts malformed `published_at` is accepted to assert it is
rejected with 422, and add the future-value acceptance case required by the plan row.

## Scope

- Update `test_published_at_format_not_validated_by_jsonschema` to expect 422 after the
  FormatChecker change (row 2).
- Add a future-`published_at` acceptance case (no skew limit per plan UNK-02 decision).
- Confirm `test_missing_required_published_at_rejected` (`:99`) stays green.

## Assumptions

- The current test (`test_published_at_format_not_validated_by_jsonschema`,
  `:146-159`) asserts a 200 response plus server-computed `published_at` for the value
  `"not-a-date"`; after the FormatChecker change it must assert 422.

## Design decisions

- Rename the test to `test_published_at_bad_format_returns_422` (new) so the test name states
  the new contract (the old name describes the removed behavior).

## Alternatives considered

- Delete the test instead of flipping it (rejected: the malformed-input contract needs
  explicit regression coverage).

## Implementation
### Target file
`tests/eventbus/test_eventbus_publish_contract.py`

### Procedure
1. Rename `test_published_at_format_not_validated_by_jsonschema` to
   `test_published_at_bad_format_returns_422` (new).
2. Change the assertion from status 200 to status 422 (matching the module's existing
   422 contract-test style).
3. Remove the server-computed-`published_at` assertions (the response is no longer a
   stored event).
4. Keep `test_missing_required_published_at_rejected` unchanged.
5. Add `test_published_at_future_value_accepted(new)`: a valid RFC 3339 timestamp in the
   future returns 200 and is stored unchanged (no skew limit per plan UNK-02 decision;
   REQ-004/AC-3).

### Method
Inline test edit; reuse the module's existing client/header fixtures.

### Details
- Malformed fixture value stays the existing `"not-a-date"`.
- Update the test docstring: the old text documents that jsonschema ignores `format`
  without a checker; the new text states the checker is attached and rejects bad
  timestamps.

## Compatibility considerations

- This test encodes a deliberate contract change from the plan; other suites asserting
  the old behavior are covered by rows 5 and 7.

## Security considerations

- None specific.

## Rollback considerations

- Restore the previous test body and name together with the row 2 rollback.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_publish_contract.py -q`

## Completion criteria

- Malformed `published_at` produces 422 in tests; missing `published_at` produces 422;
  all contract tests green.

## Out of Scope

- Route implementation (row 2), valid-path behavior tests (row 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261029-154000 | 20261029-160102 | Stored-unchanged assertion reads the DB directly: the publish response body only returns event_id+seq. |
| 2 | Add or update tests per Validation plan | Completed | 20261029-154000 | 20261029-160102 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-154000 | 20261029-160102 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261029-154000 | 20261029-160102 |  |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261028-122454_ebpubat006_published-at-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-233320_ebpubat006_published-at-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-103639
- **Related target files**: tests/eventbus/test_eventbus_publish_contract.py