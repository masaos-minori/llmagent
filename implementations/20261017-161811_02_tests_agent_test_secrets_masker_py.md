# Implementation Procedure — `tests/agent/test_secrets_masker.py`

## Goal

Add unit tests for the new JSON secret-masking patterns and regression coverage for the
existing shapes (`REQ-003`, `REQ-004`, `REQ-006`).

## Scope

Modify only `tests/agent/test_secrets_masker.py`. Append parametrized JSON-secret cases, a
non-secret stderr no-op test, and confirm existing-shape regressions and
`test_arbitrary_text_never_raises` still pass. Depends on the code change in
`scripts/agent/secrets_masker.py` (this plan's row 1).

## Assumptions

- The existing file (76 lines) covers the three `key=value` shapes, `Authorization`/`Bearer`,
  no-secret, empty string, and `test_arbitrary_text_never_raises`; append rather than
  rewrite.
- Row 1 adds a quoted-key JSON pattern to `SECRET_PATTERNS`.

## Design decisions

- Parametrize the new cases across key names (`token`, `api_key`, `password`, ...) and both
  `:` and `,` separators.
- Assert both that the masked result contains `***MASKED***` and that the original value
  string is absent from the result.
- Use a representative non-secret stderr sample that contains no known secret key name +
  quoted value, so REQ-003 asserts a true no-op.

## Alternatives considered

- Hardcoding individual assertions vs. parametrization: parametrize to cover multiple key
  names and separators compactly (REQ-004).

## Implementation

### Target file

`tests/agent/test_secrets_masker.py`

### Procedure

1. Add parametrized cases for JSON secret values:
   - `{"token": "abc123"}` (colon separator)
   - `"api_key":"xyz"` (no space)
   - `"password": "pw",` (comma separator)
   - additional known key names.
   Assert each masks to `***MASKED***` with the original value absent.
2. Add a non-secret stderr sample test asserting the sample is returned unchanged (REQ-003).
3. Confirm existing-shape regressions (three `key=value` shapes, `Authorization`, `Bearer`)
   still pass and `test_arbitrary_text_never_raises` still passes with the new pattern.
4. Static-confirm no bare-token pattern was added (REQ-006) — e.g. assert the count of
   patterns in `SECRET_PATTERNS` grew by exactly one, or grep the source.

### Method

Append test functions / extend existing parametrization; reuse existing helpers.

### Details

- Ensure the non-secret sample genuinely exercises a plausible stderr line without a
  known-secret-key + quoted-value construct.

## Compatibility considerations

N/A: test-only change.

## Security considerations

The tests encode a security property (secrets masked); keep samples free of real secrets.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run the masker tests; all pass.
- Command: `uv run pytest tests/agent/test_secrets_masker.py -q`.

## Completion criteria

JSON-secret parametrized cases mask correctly; existing-shape regressions and the
arbitrary-text no-op pass; non-secret sample unchanged.

## Out of scope

`scripts/agent/secrets_masker.py` (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_secrets_masker.py | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-003` (non-secret no-op), `REQ-004` (new-pattern + regression
  tests), `REQ-006` (no bare-token pattern)
- **Source issue**: `issues/20261017-123248_mask01_extend-secret-masking-nonjson-and-header-formats.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-144815_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-161811
- **Related target files**: `tests/agent/test_secrets_masker.py`
