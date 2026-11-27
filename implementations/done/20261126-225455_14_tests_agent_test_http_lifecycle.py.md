## Goal

Assert the two changed behaviors this test file covers: safe public error summaries (REQ-002) and
snapshots that carry a logical identifier instead of an internal log path (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- This row is not a companion: two Plan rows name it in `Related Tests` (`scripts/agent/http_lifecycle_errors.py`
  and `scripts/agent/http_lifecycle.py`), so it keeps its own document per the companion conditions.
- Existing assertions already match error text through `pytest.raises(..., match=...)` at lines 243,
  264, 343; those match strings must be updated to the code-plus-redacted-summary form.
- Step 3b correction: the update is not required for these assertions to pass. `match=` is a substring
  search against the rendered string, and each listed match string is a substring of the unchanged
  `reason`, so all three still pass against the changed producer. The contract is pinned instead by a
  new assertion on the full rendered form (`server_key: code: redacted reason`).
- The snapshot fixture at line 41 supplies `stderr_log`; its expected value becomes the logical
  identifier produced by document 05.
- Step 3b correction: the fixture supplies `stderr_log=None`, so it carries no expectation to update.
  The snapshot expectation lives in the added `TestSnapshotLogicalIdentifier` class (document 05's
  companion tests); this document adds the rendering assertion only.

## Design decisions

- Assert the rendered `str(HttpStartupError(...))` rather than the `reason` field, since the field
  itself is unchanged and only the rendering is the public contract.

## Alternatives considered

- N/A: no alternative test structure is needed; the file's existing fixture pattern is reused.

## Implementation
### Target file
`tests/agent/test_http_lifecycle.py`
### Procedure
- Update the error-text match assertions to the stable code plus redacted summary. (Per the Step 3b
  correction these pass unchanged; the rendered form is pinned by the new assertion instead.)
- Add an assertion that a `reason` containing the log directory renders without an absolute path.
- Update the snapshot expectation to the logical identifier.

### Method
- Build a `StartupFailure` whose `reason` embeds the log directory and assert the rendered string
  contains the code and no `/`-prefixed path.
- Assert the snapshot's `stderr_log` equals the logical identifier for the same path.

### Details
- Keep the existing `open_log` patching pattern; no new fixture is introduced.

## Compatibility considerations

- Test-only change; the assertions must be updated together with documents 02 and 05, otherwise the
  suite fails against the pre-change code.

## Security considerations

- These are the regression guards for AC-1 and AC-4.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_http_lifecycle.py`.
- Sequence: format → lint → type.

## Completion criteria

- The suite passes against the changed producer code and fails if a rendered error or snapshot
  contains an absolute path.

## Out of Scope

- The producer changes themselves (documents 02 and 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-032000 | TestErrorRenderingCharacterization added, 2 tests; Step 3b: the three match assertions pass unchanged because match= is a substring search, and the fixture at line 41 supplies stderr_log=None so no snapshot expectation was updated |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-032000 | 21 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-095216 | 20261127-095216 | format and lint clean; mypy 14 baseline errors in this file unchanged; gates pass; awaiting end-of-batch full suite format and lint clean; mypy 14 baseline errors in this file unchanged; gates pass; awaiting end-of-batch full suite |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | test-only change; no documentation in scope |

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
- **Requirement ID**: `REQ-002` (stable public error codes) and `REQ-007` (snapshots carry a logical identifier)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `tests/agent/test_http_lifecycle.py`