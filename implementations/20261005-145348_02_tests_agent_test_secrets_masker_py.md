## Goal

Add a dedicated unit-test module for `_mask_secrets()` covering short values (fully masked), long values (fully masked), mixed-case keys, text with no secrets (returned unchanged), empty string (returned unchanged), and arbitrary text (never raises) (`REQ-003`).

## Scope

**In**:
- Create `tests/agent/test_secrets_masker.py` as a new file with unit tests for `_mask_secrets()`.

**Out**:
- No source change to `scripts/agent/secrets_masker.py` — that is the paired doc `20261005-145348_01_scripts_agent_secrets_masker_py.md`. The new tests assert behavior implemented there.
- No changes to existing tests (`tests/agent/test_http_lifecycle_command_validator.py::test_masked_secrets_in_stderr` is a regression guard, not part of this module).

## Assumptions

1. The recovery module gates the overwrite (paired doc applied): differing current value → keep + log "Keeping existing"; `None` or equal → set (+ "Overwriting" when equal). This doc assumes that change exists; running these tests before it produces false failures.
2. `_mask_secrets()` delegates to `agent.secrets_masker._mask_secrets`, so patching `agent.workflow.approval_ops.find_all_pending_approvals` is not needed here — the function is imported directly from `agent.secrets_masker`.

## Design decisions

- Use `pytest` parametrization for the core masking cases (short value, long value, mixed-case key) to avoid code duplication.
- Use explicit assertions for each case rather than relying on `assertIn`/`assertNotIn` — assert the FULL value is absent for short values (the case the old code leaked).
- Keep the test module self-contained with no fixtures beyond `pytest`'s built-in ones.

## Alternatives considered

- **Fixture-based approach**: Define a fixture for the masker instance. Rejected — `_mask_secrets` is a pure function; no instance setup needed.
- **Property-based testing**: Use `hypothesis` for fuzzing. Rejected — the scope is well-defined and finite; property-based testing adds complexity without proportional benefit for this narrow scope.
- **Integration-style tests**: Test through call sites (e.g., subprocess error logging). Rejected — unit-level isolation is sufficient and faster; integration coverage is handled by the existing regression test.

## Implementation

### Target file

`tests/agent/test_secrets_masker.py`

### Procedure

Create `tests/agent/test_secrets_masker.py` covering short/long/mixed-case/no-secret/empty cases; assert the FULL value is absent for short values (the case the old code leaked).

### Method

Write a test class `TestMaskSecrets` with parametrized and individual test methods. Each test imports `_mask_secrets` from `agent.secrets_masker` and asserts the expected behavior.

### Details

```python
"""Unit tests for agent.secrets_masker._mask_secrets."""

import pytest
from agent.secrets_masker import _mask_secrets


class TestMaskSecrets:
    """Tests for _mask_secrets masking behavior."""

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            # Short values — the case the old code leaked
            ("token=abc", "token=***MASKED***"),
            ("secret=x", "secret=***MASKED***"),
            # Long values
            ("api_key=sk-1234567890abcdef", "api_key=***MASKED***"),
            ("GITHUB_TOKEN=ghp_abcdef123", "GITHUB_TOKEN=***MASKED***"),
            # Mixed-case keys
            ("PASSWORD=hunter2", "PASSWORD=***MASKED***"),
            ("Api_Key=abc123", "Api_Key=***MASKED***"),
            # Value with spaces (should NOT be masked — \S+ stops at whitespace)
            ("token=abc def", "token=abc***MASKED***"),
        ],
    )
    def test_masks_secret_values(self, input_text: str, expected: str) -> None:
        """Secret values are fully masked regardless of length."""
        result = _mask_secrets(input_text)
        assert result == expected

    def test_no_secret_returns_unchanged(self) -> None:
        """Text with no secrets is returned unchanged."""
        text = "hello world"
        assert _mask_secrets(text) == text

    def test_empty_string_returns_unchanged(self) -> None:
        """Empty string returns empty string."""
        assert _mask_secrets("") == ""

    def test_arbitrary_text_never_raises(self) -> None:
        """Arbitrary text never raises."""
        import os
        random_text = os.urandom(100).decode("latin-1")
        result = _mask_secrets(random_text)
        assert isinstance(result, str)

    def test_short_value_full_masking(self) -> None:
        """Short values must have NO characters of the secret value survive."""
        for short_val in ["abc", "x", "1", "a"]:
            result = _mask_secrets(f"token={short_val}")
            assert short_val not in result, f"Value '{short_val}' leaked in: {result}"
            assert "***MASKED***" in result
```

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
- Source code changes — covered by the paired doc `20261005-145348_01_scripts_agent_secrets_masker_py.md`.

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
- **Requirement ID**: `REQ-003` — new unit-test module covering short, long, mixed-case, no-secret, and empty inputs
- **Source issue**: issues/20261004-160514_secmask001_secrets-masker-leaves-short-secret-values-unmasked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-194533_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-145348
- **Related target files**: tests/agent/test_secrets_masker.py
