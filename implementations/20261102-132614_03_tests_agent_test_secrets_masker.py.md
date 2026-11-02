# Masker tests for the extended shapes and final count

## Goal

Extend `tests/agent/test_secrets_masker.py` with the extended-shape masking tests and update the
pattern-count assertion to the diagmask final count (Plan REQ-003 new coverage in log text,
REQ-005 idempotence and count / AC-3, AC-5).

## Scope

- New class `TestExtendedShapeMasking` (new) covering the row-01 pattern inventory.
- Update the count assertion `test_pattern_count_matches_inventory` (new), created by secmask001,
  from 8 → the diagmask final literal (14 under row 01's designed inventory; if
  `code-implementation` consolidates patterns, the literal is set to the final
  `len(SECRET_PATTERNS)` in the same commit).
- Pin the empty-JSON-value exemption (`{"token": ""}` unchanged) — the `*`→`+` behavior change
  row 01 makes (UNK-01).
- Existing classes untouched except the count test.

## Assumptions

- Verified 20261102: no existing test pins masking of an empty JSON value; the count test at
  :138-143 (post-secmask001 `test_pattern_count_matches_inventory` (new)) is the only count pin.
- Tests are written red-first (Plan Phase 1) before row 01 lands; red is expected evidence.
- `test_pattern_count_matches_inventory` (new) and `TestColonFormMasking` (new) are created by secmask001
  (batch step 1, implemented before this Plan) and exist when this row executes — accepted
  earlier-seq references, not stale.
- Expected outputs assume row 01's exact inventory (JWT pattern masks the whole token; URL pattern
  masks only the password segment).

## Design decisions

- Assert leak-absence for JWT/URL (output must not contain the password/secret substring) in
  addition to exact-shape asserts where the substitution is deterministic.
- Ordering/idempotence cases pin the cross-plan constraint secmask001 recorded (colon + Bearer)
  and the new bare-JWT independence from key patterns (AC-3 "no part left", AC-5 "twice equals
  once").

## Alternatives considered

- Parametrize into `TestMaskSecrets` — rejected: the new inventory (JWT, URL, `=>`, new keys) is a
  distinct feature set from the original shapes; a new class keeps failure triage clear.

## Implementation
### Target file
`tests/agent/test_secrets_masker.py`

### Procedure
Append `TestExtendedShapeMasking` (new) after `TestColonFormMasking` (new); update the count literal in
place.

### Method
New tests (calling `_mask_secrets` directly):
- `test_new_key_names_masked` (new), parametrized over `authorization=xyz`, `credential=xyz`,
  `private_key=xyz`, `bearer=xyz`, `authorization: xyz`, `credential: abc`, `private_key: abc`,
  `{"authorization": "xyz"}`, `{"credential": "xyz"}`, `{"private_key": "xyz"}` — value absent
  from output.
- `test_arrow_separator` (new): `api_key => topsecretxyz` masked (REQ-003 separator case).
- `test_bare_jwt_masked` (new): a three-segment `eyJhbGciOi...` token in prose is fully masked,
  no segment survives; a word starting with eyJ shorter than the shape stays unchanged.
- `test_url_credential_masked` (new): `postgres://admin:s3cr3tpw@db:5432/x` → scheme, user and
  host kept, `s3cr3tpw` absent; negative: `https://example.com/api/items` unchanged (Plan Risks 3).
- `test_scheme_preserved_with_authorization_key` (new): `Authorization: Bearer abc123` keeps
  `Authorization: Bearer` and drops `abc123` (secmask001 AC-4 stays green after the
  authorization-key additions).
- `test_empty_json_value_not_masked` (new): `{"token": ""}` and `{"password": ""}` returned
  unchanged (UNK-01 exemption).
- `test_extended_idempotence` (new): double application equals single application for each new
  shape (AC-5).
- `test_large_input_terminates` (new): a 10 000-char mixed payload finishes in bounded time
  (Plan Risks 4 — assert completion, not duration).
Count test: assert `len(SECRET_PATTERNS) == 14` (or the final consolidated count, see Scope).

### Details
- Keep the module's existing function-local import style.

## Compatibility considerations

- The count literal couples this file with diagmask row 01 and secmask001 rows 01-02: the value
  changes twice across the batch (6 → 8 → 14); each bump lands in the commit of the pattern change
  it belongs to.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_secrets_masker.py` — red until row 01 lands, then green.
- `uv run ruff format`, `uv run ruff check` on the touched file; coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- Every AC-3 shape masks with no secret fragment left; every AC-4 exemption returns unchanged;
  idempotence holds; count assertion equals the final pattern count.

## Out of Scope

- Guard-side refusal tests (row 04); docs (rows 05-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestExtendedShapeMasking` (new) tests (red before row 01 lands) | Pending | — | — | Plan Phase 1 |
| 2 | Update the pattern-count literal to the final count | Pending | — | — | Same commit as row 01 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (new coverage masked in logs), REQ-005 (idempotence, count update)
- **Source issue**: issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140448_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132614
- **Related target files**: tests/agent/test_secrets_masker.py
