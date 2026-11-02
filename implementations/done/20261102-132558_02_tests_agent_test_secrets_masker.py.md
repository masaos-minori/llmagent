# Colon-form masker tests and count update

## Goal

Add the failing-first test coverage for the colon forms and pin the UNK-01 decision in
`tests/agent/test_secrets_masker.py`, and update the pattern-count assertion from 6 to 8 in the
same change (Plan REQ-001 unquoted colon masking, REQ-002 quoted colon masking, REQ-003
decision pinned by tests, REQ-004 existing-form regression).

## Scope

- New class `TestColonFormMasking` (new) with the cases listed in Details.
- Update `test_pattern_count_grew_by_exactly_one` (`tests/agent/test_secrets_masker.py:138-143`):
  rename to `test_pattern_count_matches_inventory` (new) and assert `len(SECRET_PATTERNS) == 8` —
  the old name ("grew by exactly one") describes the 5→6 JSON-key pass and would lie for 6→8.
- Existing `TestMaskSecrets` and `TestJsonSecretMasking` cases (including the pinned
  `token=abc def` expectation) stay untouched: the recorded decision keeps `key=value` behavior.

## Assumptions

- Verified 20261102: classes `TestMaskSecrets` and `TestJsonSecretMasking` exist;
  `test_pattern_count_grew_by_exactly_one` pins `== 6`; `test_masks_secret_values` is a
  parametrized case list including the `token=abc def` pin.
- Phase 1 (tests first): these tests are written before row 01 lands and MUST fail red until it
  does — the red run is the Plan's Phase 1 evidence, not a defect.
- Expected outputs assume row 01's exact pattern set and order (quoted-colon before
  unquoted-colon, both after `Bearer`); if `code-implementation` changes the shapes, the
  assertions here are the contract (AC-1..AC-5), not the implementation text.

## Design decisions

- Assert absence-of-leak for the ordering case (`token: Bearer abc123` → output must not contain
  `abc123`) rather than an exact masked string — pins AC-4 without freezing the accepted
  double-mask artifact (`token: ***MASKED*** ***MASKED***`).
- Pin the decision boundary explicitly (REQ-003/AC-3): unquoted values stop at whitespace and
  newline, so `token: abc def` → `token: ***MASKED*** def` and a colon value followed by a
  second line keeps the next line; quoted values mask across whitespace in full.

## Alternatives considered

- Extend the existing parametrized `test_masks_secret_values` list with colon cases — rejected:
  that list pins pre-existing expectations this Plan must not blur; a separate class keeps the
  decision-boundary tests readable as a unit.

## Implementation
### Target file
`tests/agent/test_secrets_masker.py`

### Procedure
Append `TestColonFormMasking` (new) after `TestJsonSecretMasking`; edit only the count test in
place. No changes to fixtures, imports of `_mask_secrets` already present, or other test bodies.

### Method
Add tests (all calling `_mask_secrets` directly):
- `test_unquoted_colon_forms` (new), parametrized: `password: hunter2` → `password: ***MASKED***`;
  `token: abc123` → `token: ***MASKED***`; `access_token: abc` → `access_token: ***MASKED***`;
  `X-Api-Key: abc` → `X-Api-Key: ***MASKED***`; `PWD : s3cret` → `PWD : ***MASKED***`
  (case-insensitive, spaces around the colon).
- `test_quoted_colon_forms` (new): `api_key: 'abc def'` → `api_key: ***MASKED***`;
  `password: "two words"` → `password: ***MASKED***`; each quoted case also asserts no quote or
  word of the value survives.
- `test_whitespace_decision_pinned` (new): `token: abc def` → `token: ***MASKED*** def`
  (documented decision: unquoted values stop at whitespace, mirroring the `key=value` pin);
  multi-line `password: hunter2\npath=/api/items status=200` → first line
  `password: ***MASKED***`, second line unchanged.
- `test_bearer_ordering_no_partial_leak` (new): `token: Bearer abc123` output must not contain
  `abc123`; `Authorization: Bearer abc123` output starts `Authorization: Bearer` (scheme kept)
  and does not contain `abc123` (AC-4, REQ-004).
- `test_idempotence_double_application` (new): `_mask_secrets(_mask_secrets(x)) ==
  _mask_secrets(x)` for colon, quoted-colon and the existing non-secret stderr sample (AC-5).

### Details
- Update the count test in place:
  ```python
  def test_pattern_count_matches_inventory(self) -> None:
      assert len(SECRET_PATTERNS) == 8
  ```
  Keep the import style the existing test uses: `SECRET_PATTERNS` imported function-locally
  inside the count test body; the module-level `_mask_secrets` import stays unchanged.
- No new no-false-positive prose test is needed beyond the existing
  `test_non_secret_stderr_sample_unchanged` / `test_no_secret_returns_unchanged` (REQ-004, AC-5);
  accepted colon over-masking (`Invalid token: expired`) is documented in row 01's Security
  considerations, not asserted here.

## Compatibility considerations

- The count-test rename touches no other test; `rg test_pattern_count` shows only this one use.
- `tests/agent/test_http_lifecycle_command_validator.py::test_masked_secrets_in_stderr` and the
  startup-mcp starter tests must pass unchanged (reference-file regression).

## Security considerations

- N/A: tests only; the leak itself is covered by row 01.

## Rollback considerations

- N/A: revert the commit; the red-phase evidence lives in the commit history.

## Validation plan

- `uv run pytest tests/agent/test_secrets_masker.py` — expected red after this row alone,
  green after row 01 lands (Plan Phase 1 → Phase 2).
- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py tests/agent/test_startup_mcp_starter.py`
  — unchanged.
- `uv run ruff format`, `uv run ruff check` on the touched file; coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- Colon/quoted-colon/decision-boundary/ordering/idempotence tests exist and pass with row 01
  applied; every pre-existing test in the module still passes; count assertion reads 8.

## Out of Scope

- New key names or other separators (owned by `diagmask001`).
- Changes to `TestMaskSecrets` parametrized expectations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestColonFormMasking` (new) tests (red before row 01 lands) | Completed | 20261102-154927 | 20261102-155107 | Plan Phase 1 3b corrections applied: deduped quoted-colon case; clarified function-local SECRET_PATTERNS import red phase confirmed: 8 colon-form tests failed, 32 pre-existing passed (Plan Phase 1 evidence) |
| 2 | Update/rename the pattern-count assertion to 8 | Completed | — | 20261102-160413 | Same commit as row 01 ruff format/check clean on test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261102-160413 | green state confirmed after proc 01: 40 passed in test_secrets_masker.py; 8 patterns pinned |

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
- **Requirement ID**: REQ-001 (unquoted colon masking), REQ-002 (quoted colon masking), REQ-003 (decision pinned by tests), REQ-004 (existing forms keep working)
- **Source issue**: issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132558
- **Related target files**: tests/agent/test_secrets_masker.py