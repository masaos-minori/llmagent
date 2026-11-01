# Secrets masker leaves colon-form and whitespace secrets in plaintext

## Priority
Medium

## Summary
`scripts/agent/secrets_masker.py::_mask_secrets()` redacts `key=value`, header, Bearer and quoted-JSON-key forms, but `SECRET_PATTERNS` does not cover unquoted `key: value` (YAML or log style), values that contain whitespace, or multi-line values, so those secrets are still emitted in plaintext to logs. Extend the pattern coverage and keep the existing forms working.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's tool-execution/security-gating subsystem and re-verified against the current code in a later review. The original defect (the substitution `m.group()[:10] + "***MASKED***"` that leaked short secrets and the leading characters of long ones) is already fixed: the substitution now keeps the key group and replaces only the value (`m.group(1) + "***MASKED***"`; `pwd=ab`, `password=hunter2` and `{"password": "abc"}` all mask correctly). Earlier masker work is archived in `issues/done/20261004-160514_secmask001_secrets-masker-leaves-short-secret-values-unmasked.md`, `issues/done/20261013-162325_agmask01_*` and `issues/done/20261017-123248_mask01_*`.

## Problem
Reproduction (pure regex module, no logger or DB): `_mask_secrets("password: hunter2")` and `_mask_secrets("token: abc123")` return the input unchanged. Values containing whitespace (for example `password=two words`) are masked only up to the first whitespace, and multi-line values are not handled. Evidence label: `Explicit in code` plus a direct run.

## Reason for Change
The utility runs before logging subprocess stderr and exception text (`scripts/agent/startup_mcp_starter.py`, `scripts/agent/http_lifecycle.py`, `scripts/agent/http_lifecycle_errors.py`, `scripts/shared/retry_helper.py`) to keep credentials out of persisted logs. Colon-separated forms are common in YAML and log lines, so the residual gap still lets credentials reach logs, though the common `key=value` case is now covered.

## Implementation Intent
Extend `SECRET_PATTERNS` to match `key: value` and `key: "value"` for the same key names, and decide how to treat values that contain whitespace (mask to end of line, or to a delimiter), keeping the existing `key=value` behavior and the capture-group substitution unchanged.

## Target Files or Areas
- `scripts/agent/secrets_masker.py` (`SECRET_PATTERNS`, `_mask_secrets()`)

## Required Changes
- Add regex coverage for unquoted colon-separated `key: value` forms for the existing key names.
- Decide and implement the treatment of whitespace-containing and multi-line values, or record the decision to leave them out.
- Add tests: colon form, colon form with quotes, a value with whitespace, a multi-line value (if covered), plus the existing short and long `key=value` cases as regression, and ordinary text with no secret (no false positive).

## Constraints
- Keep the function's existing signature (`_mask_secrets(text: str) -> str`) and call sites unchanged.
- Do not change the set of key names considered sensitive beyond what is needed to add colon-separated matching for the same keys.

## Acceptance Criteria
- `password: hunter2` and `token: abc123` are masked like their `key=value` forms.
- No value matched by `SECRET_PATTERNS` appears, in whole or in part, in the output.
- Existing call sites continue to receive masked text with no code change.

## Testing Expectations
Unit tests in the module covering: short secret (≤10 chars total match), long secret, colon-separated form, and a case with no secret present (no false-positive masking of ordinary text). Run the full existing `secrets_masker` test module (if any) plus `tests/agent/test_startup_mcp_starter.py`/`tests/agent/test_http_lifecycle*.py` after the change to confirm no call-site regression.

## Documentation Impact
N/A: no operator-facing documentation describes this masking utility's exact behavior today; this is an internal correctness fix.

## Out of Scope
- `scripts/agent/diagnostic_store.py`'s separate, independent secret-detection regex (tracked separately — see Dependencies).
- `scripts/agent/tool_result_formatter.py::mask_args()`'s key-name-based audit masking (tracked separately).

## Dependencies
Related to `issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md`, which recommends consolidating `diagnostic_store.py`'s own secret-pattern allowlist with this module's patterns once this fix lands. Implement this issue first.

## Unresolved Questions
- How far the whitespace and multi-line coverage should go without producing false positives on ordinary text: a design choice for the owner.

## AI Implementation Instruction
Change only `SECRET_PATTERNS` coverage in `secrets_masker.py` and its tests; do not touch the substitution logic that already works or any call site. Add the tests above before considering this done. Do not attempt the consolidation with `diagnostic_store.py` in this issue.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180324
- **Related target files**: scripts/agent/secrets_masker.py
