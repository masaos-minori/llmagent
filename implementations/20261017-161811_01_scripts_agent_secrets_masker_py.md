# Implementation Procedure — `scripts/agent/secrets_masker.py`

## Goal

Broaden `_mask_secrets()` so it masks secrets in common modern formats beyond the three
existing shapes (`key=value`, `Authorization:` header lines, standalone `Bearer` tokens) —
at minimum JSON object values for known secret key names (`"token"`, `"api_key"`,
`"password"`, ...) with `:` and `,` separators — while preserving the existing patterns
verbatim and avoiding false positives (`REQ-001`, `REQ-002`).

## Scope

Modify only `scripts/agent/secrets_masker.py`. Append narrow, high-confidence quoted-key
JSON patterns to `SECRET_PATTERNS` for known secret key names covering `:`/`,` separators.
Keep the existing five patterns verbatim. Do NOT change call sites or `_mask_secrets`'s
substitution logic.

## Assumptions

- `SECRET_PATTERNS` (lines 6–12) holds exactly five patterns; `_mask_secrets` (lines 15–20)
  applies each via `pattern.sub(lambda m: m.group(1) + "***MASKED***")`.
- New patterns follow the same two-group convention: group 1 preserved by substitution,
  group 2 redacted.

## Adversarial verification findings (plan discrepancies)

- **No discrepancy.** Verified the proposed quoted-key pattern against representative
  inputs:
  - `{"token": "abc123"}` → `{"token": "***MASKED***"}` ✓
  - `"api_key":"xyz"` and comma-separated `"password": "pw",` → masked ✓
  - multi-field JSON masks only the known-secret field; `"name": "John"` is untouched
    (no false positive) ✓
  - existing `Authorization:`/`Bearer` shapes are unaffected by the new pattern ✓
  - malformed input `{"token": }` does not raise and simply does not match ✓
  - the value capture `[^"\']*` stops at the next quote (no over-consumption) ✓

## Design decisions

- Prefer approach (a) — quoted-key JSON patterns. Group 1 = `"token": "` (key + separator +
  opening quote); group 2 = value via `[^"\']*`; substitution yields
  `"token": "***MASKED***"`. Restricting to known secret key names with quoted keys limits
  false positives (REQ-003).
- Approach (b) (unquoted-key `:`/`,` variants) is higher false-positive risk; defer unless
  coverage demand warrants it (UNK-01). Implement exactly one.
- Add the new pattern(s) AFTER the existing five; do not reorder or modify them (REQ-002).

## Alternatives considered

- Unquoted-key `:`/`,` patterns (approach b): rejected as primary due to higher false-positive
  risk; kept as an optional future addition.
- Structured secret detector: rejected — out of scope; the plan keeps the regex approach.

## Implementation

### Target file

`scripts/agent/secrets_masker.py`

### Procedure

1. In `SECRET_PATTERNS`, append a quoted-key JSON pattern after the existing five:
   ```python
   re.compile(
       r'(?i)("(?:password|passwd|pwd|api[_-]?key|apikey|secret|token)"\s*[:,]\s*["\'])([^"\']*)'
   ),
   ```
2. Verify the existing five patterns are byte-for-byte unchanged.
3. Confirm `_mask_secrets` is untouched (still `m.group(1) + "***MASKED***"`).
4. Static-check that no bare high-entropy token pattern was added (REQ-006).

### Method

Append the compiled pattern to the list literal; re-run the masker tests.

### Details

- The value capture `[^"\']*` stops at the next quote, so a missing closing quote does not
  raise and does not over-consume.
- Keep the key-name alternation exactly as listed; adding a name later is a one-pattern
  addition (UNK-02).

## Compatibility considerations

Only ADD a pattern; the existing five are verbatim and all four call sites
(`startup_mcp_starter.py`, `retry_helper.py`, `http_lifecycle.py`,
`http_lifecycle_errors.py`) import/use `_mask_secrets`, so this is backward compatible.
Verify imports still succeed (validation plan).

## Security considerations

Fail closed on the newly covered format; ensure the non-secret sample stays unmodified
(REQ-003) so legitimate output is not corrupted.

## Rollback considerations

Revert the commit to `scripts/agent/secrets_masker.py`.

## Validation plan

- Unit (`tests/agent/test_secrets_masker.py`):
  - Parametrized JSON cases: `{"token": "abc123"}`, `"api_key":"xyz"`, comma-separated
    variant, multiple known key names → all masked (REQ-001).
  - Regression of existing shapes (REQ-002).
  - Non-secret stderr sample returned unchanged (REQ-003).
  - `test_arbitrary_text_never_raises` still passes (REQ-004).
- Static: confirm no bare-token pattern in `SECRET_PATTERNS` (REQ-006).
- Command: `uv run pytest tests/agent/test_secrets_masker.py -q`.
- Import smoke: `uv run python -c "import agent.startup_mcp_starter, agent.shared.retry_helper, agent.http_lifecycle, agent.http_lifecycle_errors"`.
- Lint/type: `uv run ruff check scripts/agent/secrets_masker.py` and `uv run mypy
  scripts/agent/secrets_masker.py` clean.

## Completion criteria

`_mask_secrets()` masks JSON-style secret values for known key names with `:`/`,` separators;
the existing five patterns and their behavior are unchanged; non-secret output is unmodified.

## Out of scope

Unquoted-key variants, bare high-entropy tokens, base64/hex keys, call sites, the test file
(separate row), and the doc update (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append quoted-key JSON pattern to SECRET_PATTERNS | Pending | — | — | approach (a) |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: test file is a separate row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: doc is a separate row |

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
- **Requirement ID**: `REQ-001` (mask JSON secret values, `:`/`,`), `REQ-002` (existing
  patterns unchanged), `REQ-006` (no bare-token pattern)
- **Source issue**: `issues/20261017-123248_mask01_extend-secret-masking-nonjson-and-header-formats.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-144815_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-161811
- **Related target files**: `scripts/agent/secrets_masker.py`
