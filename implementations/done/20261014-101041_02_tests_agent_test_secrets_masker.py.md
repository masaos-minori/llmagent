## Goal

Add parametrized unit tests for the new bearer-header secret shapes to `tests/agent/test_secrets_masker.py` (REQ-006) while retaining every existing `key=value`, no-secret, empty-string, and arbitrary-text case as regression coverage.

## Scope

**In:**
- Append new parametrized cases covering `Authorization: Bearer <token>` (REQ-002), a generic `Authorization: <scheme> <token>` header (REQ-003), and a standalone `Bearer <token>` (REQ-004) to `tests/agent/test_secrets_masker.py`.

**Out:**
- No modification to existing test cases or the source file (`scripts/agent/secrets_masker.py`) — those are owned by the paired docs.
- No new imports beyond what the module already uses (`pytest`, `_mask_secrets`).

## Assumptions

1. The new cases assert the exact masked output produced by the two appended patterns (see the paired doc `20261014-101041_01_scripts_agent_secrets_masker.py.md` for the patterns), so expected strings are computed from those patterns' replacement convention.
2. Existing cases — including the secmask001 short-value regression cases in `test_masks_secret_values` and `test_short_value_full_masking` — remain authoritative and must not be altered.

## Design decisions

- Add one new parametrized method `test_bearer_header_shapes` to the existing `TestMaskSecrets` class, reusing the `@pytest.mark.parametrize` pattern already in the file so the style is consistent and the cases run under the same collection.
- Keep the new cases additive: they append to the file without touching existing methods, so the secmask001 regression coverage is preserved byte-for-byte.

## Alternatives considered

- **One assertion method per shape**: More verbose; rejected in favor of a single parametrized table that mirrors the existing `test_masks_secret_values` style.
- **Extend the existing `test_masks_secret_values` table**: Would mix `key=value` and bearer shapes in one table; rejected to keep bearer coverage self-documenting and isolated to REQ-002/003/004.

## Implementation

### Target file

`tests/agent/test_secrets_masker.py`

### Procedure

Append a new parametrized test method inside the `TestMaskSecrets` class (after `test_masks_secret_values`, before the non-parametrized helpers). Do not modify any existing method.

### Method

Parametrize over `(input_text, expected)` pairs. Each expected value follows the `group(1) + "***MASKED***"` convention: the `Authorization:`/`Bearer` keyword and scheme are preserved, only the token is replaced.

### Details

Add this method to the `TestMaskSecrets` class:
```python
    @pytest.mark.parametrize(
        "input_text,expected",
        [
            # REQ-002: Authorization: Bearer <token>
            ("Authorization: Bearer dGhpczBzZWNyZXQ=", "Authorization: Bearer ***MASKED***"),
            # REQ-003: generic Authorization: <scheme> <token>
            ("Authorization: Basic YWxsb246cGFzcw==", "Authorization: Basic ***MASKED***"),
            ("Authorization: Digest abc123def", "Authorization: Digest ***MASKED***"),
            # REQ-004: standalone Bearer <token> (no Authorization: prefix)
            ("Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig", "Bearer ***MASKED***"),
        ],
    )
    def test_bearer_header_shapes(self, input_text: str, expected: str) -> None:
        """Bearer-header and standalone bearer-token shapes are masked."""
        result = _mask_secrets(input_text)
        assert result == expected
```

Expected-output derivation (verified against the appended patterns):
- `Authorization: Bearer dGhpczBzZWNyZXQ=` → pattern 4 keeps `Authorization: Bearer ` and masks the token → `Authorization: Bearer ***MASKED***`.
- `Authorization: Basic YWxsb246cGFzcw==` / `Authorization: Digest abc123def` → pattern 4 keeps `Authorization: <scheme> ` and masks the token.
- `Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig` → pattern 5 keeps `Bearer ` and masks the token → `Bearer ***MASKED***`.

The existing `test_arbitrary_text_never_raises` (random latin-1 bytes) already exercises the no-raise contract against the expanded pattern set; it remains sufficient, but the new bearer cases add positive coverage.

## Compatibility considerations

N/A: test-only change; no production code, public API, or behavior is altered.

## Security considerations

N/A: this document asserts security behavior defined by the paired source doc; it introduces no security surface itself.

## Rollback considerations

N/A: revert the commit to remove the added cases; existing cases are untouched.

## Validation plan

- Run the updated module: `uv run pytest tests/agent/test_secrets_masker.py -v`.
- Confirm the four new bearer cases pass and that every pre-existing case (short/long/mixed-case `key=value`, no-secret, empty, arbitrary-text) still passes unchanged.

## Completion criteria

- `test_bearer_header_shapes` exists and its four parametrized cases pass.
- All previously existing test cases still pass with identical assertions (no regression).
- `uv run pytest tests/agent/test_secrets_masker.py` exits clean.

## Out of scope

- Modifying the source masker (`scripts/agent/secrets_masker.py`) — owned by the paired doc.
- Adding tests for out-of-scope shapes (JSON `"key": "value"`, bare hex/base64).
- Documentation updates — owned by the paired doc.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | N/A | — | — | No source change; source owned by paired doc `20261014-101041_01_scripts_agent_secrets_masker.py.md` |
| 2 | Add or update tests per Validation plan | Completed | 20261014-114805 | 20261014-114805 | REQ-006: add bearer cases, retain regression cases |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-114805 | 20261014-114805 | `uv run pytest tests/agent/test_secrets_masker.py` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Doc update owned by paired doc `20261014-101041_03_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md` |

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
- **Requirement ID**: `REQ-006` — unit tests cover the new bearer shapes plus regression of the existing `key=value` cases
- **Source issue**: issues/20261013-162325_agmask01_mask-alternate-secret-shapes-in-the-agent-secret-masker.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-093347_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-101041
- **Related target files**: tests/agent/test_secrets_masker.py