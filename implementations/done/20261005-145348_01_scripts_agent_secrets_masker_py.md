## Goal

Replace the `match[:10]` prefix-keep in `secrets_masker.py`'s `_mask_secrets()` with whole-value masking so no character of any secret value leaks into logs or error reports, regardless of value length (`REQ-001`). Keep only the key name and separator in the output, preserving the helper's public contract and every call-site signature.

## Scope

**In**:
- Modify `scripts/agent/secrets_masker.py` only — change the replacement expression inside `_mask_secrets()` so the entire matched value is masked while the key name and separator are preserved.

**Out**:
- No changes to the three existing `SECRET_PATTERNS` (A-01).
- No new secret patterns beyond the four `key=value` families (`password`/`passwd`/`pwd`, `api_key`/`apikey`, `secret`, `token`, case-insensitive) — REQ-002.
- No changes to call sites (`http_lifecycle.py`, `http_lifecycle_errors.py`, `startup_mcp_starter.py`, `retry_helper.py`).
- No test authoring here — tests owned by the paired doc `20261005-145348_02_tests_agent_test_secrets_masker_py.md`.

## Assumptions

1. The three existing `SECRET_PATTERNS` remain the authoritative set; only the replacement expression changes, not the patterns themselves (A-01).
2. "Keep only the key name" means preserve everything up to and including the value delimiter (key name + optional whitespace + `=`) and replace only the value portion with the masked sentinel (A-02).
3. Retaining the `***MASKED***` sentinel is required so downstream consumers and the existing regression test (which asserts `"MASKED" in msg`) continue to work (A-03).

## Design decisions

- Convert each existing pattern from a non-capturing match over the whole `key=value` fragment into a capturing group around the value (`\S+`). Replace with a lambda that keeps `m.group(1)` (the captured key-name + separator prefix) and appends the `***MASKED***` sentinel, discarding the captured value.
- This makes masking independent of value length, preserves the public contract and call-site signatures, keeps one regex pass per pattern, and introduces no new imports or patterns.
- `retry_helper._mask_secrets` already delegates to this helper, so the fix propagates transitively to its callers.

## Alternatives considered

- **Sentinel-only replacement**: Replace the entire match with `***MASKED***` without preserving the key name. Rejected — loses useful context (which key was found) and breaks downstream consumers that parse the masked output.
- **Different sentinel format**: Use a different sentinel string. Rejected — the existing regression test asserts `"MASKED" in msg`; changing the sentinel would require updating that test and all downstream consumers.
- **Multiple regex passes**: Run separate passes for key extraction and value masking. Rejected — unnecessary complexity; a single lambda replacement achieves the same result.

## Implementation

### Target file

`scripts/agent/secrets_masker.py`

### Procedure

Change the `pattern.sub(...)` replacement so the entire matched value is masked regardless of length while the key name/separator is preserved; retain the `***MASKED***` sentinel; ensure no raise on empty/arbitrary text; keep one regex pass per pattern. Do not add patterns.

### Method

Convert each existing pattern from a non-capturing match over the whole `key=value` fragment into a capturing group around the value (`\S+`). Replace with a lambda that keeps `m.group(1)` (the captured key-name + separator prefix) and appends the `***MASKED***` sentinel, discarding the captured value.

### Details

Before:
```python
masked = pattern.sub(lambda m: m.group()[:10] + "***MASKED***", masked)
```

After (for each pattern):
```python
masked = pattern.sub(lambda m: m.group(1) + "***MASKED***", masked)
```

Each pattern must be updated to capture the value separately:

```python
SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(password|passwd|pwd)\s*=\s*(\S+)"),
    re.compile(r"(?i)(api[_-]?key|apikey)\s*=\s*(\S+)"),
    re.compile(r"(?i)(secret|token)\s*=\s*(\S+)"),
]
```

The lambda receives the full match via `m.group()` (unchanged) but uses `m.group(1)` which captures only the key-name + separator prefix (everything before `\S+`), then appends `***MASKED***`. The captured value (`m.group(2)`) is discarded.

Behavior after the change:
- Short values (`token=abc`, `secret=x`) → fully masked (no value characters survive).
- Long values (`api_key=sk-1234567890abcdef`) → fully masked (no value characters survive).
- Mixed-case keys (`PASSWORD=hunter2`) → fully masked, key name preserved.
- Text with no secrets → returned unchanged.
- Empty string → returned unchanged.
- Arbitrary text → never raises.

## Compatibility considerations

- No public-API change: `_mask_secrets()` signature and return contract are unchanged.
- The `***MASKED***` sentinel is retained, so downstream consumers/tests that look for `"MASKED"` continue to work.
- The masked output format changes slightly: previously `password=h***MASKED***` (one value char leaked); now `password=***MASKED***` (zero value chars). Callers that parse the masked output by splitting on `=` will see the value portion replaced entirely — this is the intended behavior.
- `retry_helper._mask_secrets` delegates to this helper; its callers inherit the fix transitively.

## Security considerations

- This change directly addresses a security concern: short secret values were not masked at all, giving a false sense of protection. The fix ensures ALL values are masked regardless of length.
- No new attack surface introduced — the patterns and sentinel are unchanged; only the replacement expression is modified.
- The fix does not introduce any new dependencies or external calls.

## Rollback considerations

- If the change causes unexpected issues, reverting the replacement expression restores the original behavior. The patterns themselves are unchanged, so the rollback is a single-line revert.
- Downstream consumers that rely on the old masked format (e.g., parsing the masked output) may need adjustment if they expect the partial-value leakage.

## Validation plan

- Run the validation sequence on `scripts/agent/secrets_masker.py`: `ruff format/check`, `mypy`, `bandit`.
- Run the new test module: `uv run pytest tests/agent/test_secrets_masker.py -v`.
- Confirm existing regression test still passes: `uv run pytest tests/agent/test_http_lifecycle_command_validator.py::test_masked_secrets_in_stderr -v`.

## Completion criteria

- All secret values (short and long) are fully masked — no character of the value appears in the output.
- The key name and separator are preserved in the output.
- The `***MASKED***` sentinel is present in the output.
- Text with no secrets is returned unchanged.
- Empty string returns empty string.
- Arbitrary text never raises.
- Existing regression test `test_masked_secrets_in_stderr` still passes.
- `ruff format/check`, `mypy`, `bandit` clean on `scripts/agent/secrets_masker.py`.

## Out of scope

- Adding patterns for non-`key=value` credential forms (`Authorization: Bearer ...`, `Cookie`, etc.).
- Introducing a general log-redaction framework.
- Changes to call sites (`http_lifecycle.py`, `http_lifecycle_errors.py`, `startup_mcp_starter.py`, `retry_helper.py`).
- Test authoring — covered by the paired doc `20261005-145348_02_tests_agent_test_secrets_masker_py.md`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests owned by paired doc |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `TestStartupOrchestratorRecoverPendingApprovals` | Pending | — | — | Cross-row dependency: implement paired test doc first so assertions reflect gated behavior |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: doc update covered by paired doc `20261005-145348_03_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health_md.md` |

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
- **Requirement ID**: `REQ-001` — masking must cover the entire secret value regardless of length; `REQ-002` — masking scoped to the four existing `key=value` families only
- **Source issue**: issues/20261004-160514_secmask001_secrets-masker-leaves-short-secret-values-unmasked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-194533_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-145348
- **Related target files**: scripts/agent/secrets_masker.py
