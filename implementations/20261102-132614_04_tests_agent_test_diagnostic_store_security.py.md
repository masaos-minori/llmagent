# Guard tests for the shared detector and carve-outs

## Goal

Add refusal and no-false-positive tests for the shared-detector guard in
`tests/agent/test_diagnostic_store_security.py`, covering new shapes, short values, the encrypted
path, the `_filter_failed` carve-out and the already-masked/empty exemptions (Plan REQ-002 old
shapes still refused, REQ-003 new shapes refused, REQ-004 contract and exemptions / AC-2..AC-4).

## Scope

- New class `TestSharedDetectorGuard` (new) reusing the file's existing `MockConnection` /
  `MockContext` fixtures and the `DiagnosticStore()` + `tmp_path` pattern of
  `TestSensitiveDataRefusal` (`tests/agent/test_diagnostic_store_security.py:255-293`).
- New carve-out test for the `_filter_failed` path (none exists today — verified 20261102).
- Pre-existing tests, including the six parametrized refusal cases and
  `test_save_with_encrypt_but_no_key_raises_on_sensitive_data` (:219, content
  `{"api_key": "abcdefghijklmnop"}`; the `sk-...` cases live in
  `tests/agent/test_diagnostic_store.py:557-602`), stay untouched: they are the REQ-002 regression.

## Assumptions

- Refusal assertions follow the existing style: `pytest.raises(RuntimeError)` with the exact
  message and `len(mock_conn.executed_calls) == 0` (no INSERT executed).
- Tests written red-first (Plan Phase 1) against the pre-consolidation guard: new-shape cases
  fail until rows 01-02 land; the exemption cases (`{"token": ""}`, short values) fail against
  the OLD guard only where the old 16-char minimum lets a short secret through — pin short-value
  refusal (`{"private_key": "abc"}`) which the old guard allows today.
- Detection equivalence (AC-1 "refuses content for which the shared function is true") is asserted
  by calling `detects_secrets` (new) in the test and comparing with `save()`'s behavior for the same
  string.

## Design decisions

- Parametrize one refusal case list shared by the guard test and a masker-side equivalence assert
  in the same class — one source of truth for the AC-3 shape inventory across guard and masker.
- Keep exemption tests as saves (no raise, INSERT present) rather than `detects_secrets` (new) unit
  calls only: the AC-4 contract is about `save()` behavior.

## Alternatives considered

- Extend `TestSensitiveDataRefusal`'s parametrize list — rejected: that list pins the
  pre-consolidation baseline (REQ-002); mixing new expectations into it blurs the regression
  signal.

## Implementation
### Target file
`tests/agent/test_diagnostic_store_security.py`

### Procedure
Append `TestSharedDetectorGuard` (new) after `TestSensitiveDataRefusal`.

### Method
- `test_refuses_new_shapes_without_key` (new), parametrized:
  `{"authorization": "Bearer eyJhbGciOiJIUzI1Ni01234567890abcdef.abcdefghijklmnopqrstuv"}`,
  `{"credential": "hunter2"}` (short value — UNK-01 fail-closed),
  `{"private_key": "abc"}` (16-char minimum gone),
  `{"passwd": "topsecret99"}`, `plain text api_key => sec35`,
  `{"note": "see postgres://admin:s3cr3tpw@db:5432/x"}`,
  bare JWT as whole content; each: `pytest.raises(RuntimeError)` with the exact message and no
  INSERT.
- `test_guard_matches_shared_detector` (new): for the parametrized list plus the exemption list,
  `save()` raises exactly when `detects_secrets(content)` (new) is True (AC-1).
- `test_saves_exemptions_without_raise` (new): `{"message": "hello world"}`,
  `[INCOMPLETE: timeout]`, `token=***MASKED***`, `{"token": ""}`,
  `https://example.com/api/items` — saved, INSERT executed, content unchanged.
- `test_encrypted_path_still_saves_new_shapes` (new): with a patched encryption key,
  `save(..., encrypt=True)` on two AC-3 shapes stores ciphertext without raising (AC-4).
- `test_filter_failed_carve_out_preserved` (new): patch `_filter_sensitive_fields` to raise; a
  secret-bearing payload is saved unencrypted without `RuntimeError` and a warning is logged
  (caplog on logger `agent.diagnostic_store`) (AC-4 carve-out).

### Details
- Import `detects_secrets` (new) from `agent.secrets_masker` function-locally, matching the file's
  existing import style.

## Compatibility considerations

- The six existing parametrized refusals must keep passing after the consolidation (REQ-002);
  they exercise the widened masker JSON pattern (row 01), not the deleted private patterns.

## Security considerations

- N/A: tests only; the coverage they pin is the security contract.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_diagnostic_store_security.py tests/agent/test_diagnostic_store.py
  tests/agent/test_regression_diagnostic_persist.py` — red for new shapes until rows 01-02 land.
- `uv run ruff format`, `uv run ruff check` on the touched file; coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- Every AC-3 shape refuses with zero INSERTs; every AC-4 exemption saves; the carve-out and
  encrypted-path tests pass; the pre-existing refusal/save tests are green unchanged.

## Out of Scope

- Masker-side masking detail (row 03); caller-level `RuntimeError` handling (UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestSharedDetectorGuard` (new) tests (red before rows 01-02 land) | Completed | — | — | Plan Phase 1 TestSharedDetectorGuard added (17 tests); red evidence 12 failed/32 passed recorded; green after row 02 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check, mypy, bandit -ll -r scripts/, lint-imports (6 kept), check_module_size, full suite 11276 passed/8 skipped, diff-cover 100%, docs checkers exit 0 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-002 (old shapes keep being refused), REQ-003 (new shapes refused), REQ-004 (contract, carve-out, exemptions)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140448_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132614
- **Related target files**: tests/agent/test_diagnostic_store_security.py