## Goal

Record the `ProcessInfoSnapshot.stderr_log` field semantics as a logical identifier while keeping
the field name (REQ-007 — public snapshot field carries a logical identifier).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Field name is preserved; only the documented value semantics change, so dict-shape consumers and
  pinned tests are unaffected (Plan Assumptions).
- No overlap with a sibling Plan on this file.

## Design decisions

- Document the field as a logical identifier in the dataclass docstring/comment; no runtime
  behavior change in this module — the value is produced by `scripts/agent/http_lifecycle.py`
  (document 05).

## Alternatives considered

- Changing the field type to a dedicated identifier type — rejected: no public-contract benefit and
  it would break dict-shape consumers.

## Implementation
### Target file
`scripts/agent/services/models.py`
### Procedure
- Update the `stderr_log` field description in `ProcessInfoSnapshot` to state that it holds a
  logical identifier, not an absolute path.
### Method
- Comment/docstring-only change at line 47; no code path change.
### Details
- The value is produced by document 05; this document records the contract the producer must honor.

### Companion test files
- `tests/agent/test_lifecycle.py`
  - Procedure: update snapshot dict expectations at lines 973, 1380-1402, 1625 to the logical
    identifier.
  - Validation: `uv run pytest tests/agent/test_lifecycle.py`.
  - Step 3b correction: the cited lines are not snapshot expectations. Lines 973 and 1380-1402 seed
    `_log_paths` and assert cleanup behavior; the `stderr_log=""` expectations at 1625 and the two
    neighbouring cases describe an untracked server, which still renders an empty string. No update
    was needed. One contract test was added in `TestHttpLifecycleStderrLog` asserting the field holds
    the logical identifier while the manager keeps the real path.

## Compatibility considerations

- No consumer code changes; `scripts/agent/lifecycle_router.py` is a reference file only.

## Security considerations

- N/A: no new disclosure surface; the change documents the AC-4 boundary.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_lifecycle.py`.
- Sequence: format → lint → type.

## Completion criteria

- The field description states a logical identifier and the updated test expectations pass.

## Out of Scope

- Producing the identifier value (document 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-014000 | field comment states the value is a logical identifier, never an absolute path; no runtime change |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-014000 | companion `tests/agent/test_lifecycle.py` cited lines are seeding/cleanup assertions, not snapshot expectations: no update needed; 1 contract test added; 91 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-095216 | 20261127-095216 | gates pass; mypy baseline 33 errors in tests/agent/test_lifecycle.py unchanged; changed files: scripts/agent/services/models.py, tests/agent/test_lifecycle.py; awaiting end-of-batch full suite gates pass; mypy baseline 33 errors in tests/agent/test_lifecycle.py unchanged; changed files: scripts/agent/services/models.py, tests/agent/test_lifecycle.py; awaiting end-of-batch full suite |

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
- **Requirement ID**: `REQ-007` (public process snapshots omit internal log paths)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/services/models.py`, `tests/agent/test_lifecycle.py`