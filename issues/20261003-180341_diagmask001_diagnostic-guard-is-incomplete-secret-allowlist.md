# Diagnostic guard is incomplete secret allowlist

## Priority
Medium

## Summary
`DiagnosticStore.save()` guards unencrypted diagnostic persistence with its own single regex (`_SENSITIVE_PATTERNS`), independent of `secrets_masker.py`'s separate pattern set. A secret under a key name outside its list, a value introduced by a separator it does not expect, or a bare value with no key (a raw JWT, a `scheme://user:pass@host` URL) is persisted to `session_diagnostics` in plaintext whenever encryption is unset, which is the default because encryption is opt-in.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's session-state subsystem (`scripts/agent/diagnostic_store.py`), compared against the separate, also-narrow pattern set in `scripts/agent/secrets_masker.py` used for log-line masking.

## Problem
`scripts/agent/diagnostic_store.py` defines `_SENSITIVE_PATTERNS`, one regex matching a fixed key list (`api_key`, `secret`, `token`, `password`, `access_token`, `auth_token`, `bearer`, `client_secret`) followed by an optional quote, whitespace, `:` or `=`, and a value of at least 16 characters from `[a-zA-Z0-9_\-\.]`. It runs only when `encryption_key` is empty and the earlier `sensitive_fields` redaction did not fail (`_filter_failed`). Because the value group matches any 16-character prefix, a `token: eyJ...` JWT under a listed key name is detected; the real gaps are: key names not in the list (for example `authorization`, `passwd`, `credential`, `private_key`), other separators, and bare values with no key (a raw JWT, `scheme://user:pass@host`). `scripts/agent/secrets_masker.py` keeps an independent pattern set (`SECRET_PATTERNS`), so the two implementations diverge.

## Reason for Change
A secret whose shape doesn't match `_SENSITIVE_PATTERNS` is persisted to `session_diagnostics` in plaintext whenever `diagnostics.encryption_key` is unset. The guard gives a false sense of safety for secret shapes it doesn't cover, and maintaining two divergent secret-detection implementations means a fix to one does not benefit the other.

## Implementation Intent
Consolidate on one shared secret-detection utility used by both log masking and diagnostic persistence, and treat the regex as defense in depth. Widen coverage to additional key names, bare JWT-shaped values and `scheme://user:pass@` connection strings.

## Target Files or Areas
- `scripts/agent/diagnostic_store.py` (`_SENSITIVE_PATTERNS`, `DiagnosticStore.save()`)
- `scripts/agent/secrets_masker.py` (the consolidation target, once its own value-leak bug is fixed)

## Required Changes
- Replace `diagnostic_store.py`'s standalone `_SENSITIVE_PATTERNS` with a call into the shared `secrets_masker` detection logic (or a common module both import from).
- Extend the shared pattern set to cover the gaps listed in Problem.
- Add tests asserting that a bare JWT-shaped value, a `user:pass@host` connection string and a secret under an unlisted key name are detected by `DiagnosticStore.save()`'s guard when encryption is unset.

## Constraints
- Do not change `DiagnosticStore.save()`'s behavior when `diagnostics.encryption_key` is set (encrypted path is unaffected by this fix).
- Do not change the `RuntimeError`-on-detection behavior itself — only widen what triggers it.

## Acceptance Criteria
- `diagnostic_store.py` and `secrets_masker.py` share one secret-detection implementation.
- A bare JWT-shaped value, a `user:pass@host` connection string and a secret under an unlisted key name are detected and blocked from unencrypted diagnostic persistence.

## Testing Expectations
Unit tests covering the new coverage in addition to existing `_SENSITIVE_PATTERNS` cases, including the `sensitive_fields` redaction path that runs first. Run `tests/agent/test_diagnostic_store.py` after the change.

## Documentation Impact
N/A: no operator-facing documentation describes the exact secret-shape coverage of this guard today.

## Out of Scope
- `diagnostics.encryption_key`'s own encryption implementation (not touched — this issue concerns only the plaintext-path detection guard).
- `tool_result_formatter.py::mask_args()`'s key-based audit masking (tracked separately).

## Dependencies
Depends on `issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md` (colon-form coverage of the shared masker): implement that first so the consolidated logic does not inherit its gap.

## Unresolved Questions
N/A: none for the gap itself; confirmed by reading `diagnostic_store.py` and `secrets_masker.py`.

## AI Implementation Instruction
Consolidate onto one shared detection utility rather than patching `diagnostic_store.py`'s pattern list in isolation. Implement `secmask001` first. Add the regression tests described above before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180341
- **Related target files**: scripts/agent/diagnostic_store.py, scripts/agent/secrets_masker.py
