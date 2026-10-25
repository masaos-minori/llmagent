# Decide and document the diagnostics storage encryption posture

## Priority
Medium

## Summary
Make the `session_diagnostics` storage encryption posture an explicit, documented decision: `DiagnosticStore` supports Fernet encryption, but every shipped config sets `encryption_key = ""` and `save()` defaults to `encrypt=False`, so diagnostic rows are persisted in plaintext for the full retention window. Review finding F-006.

## Background
Explicit in code and config: `scripts/agent/diagnostic_store.py` — `DiagnosticStore.save()` takes `encrypt: bool = False`; `_encrypt_content` is a documented no-op when the key is empty; when no key is configured and the sensitive-pattern scan hits, the store logs "Sensitive information detected in diagnostic content without encryption enabled." and persists the content anyway; the read path only decrypts rows with the Fernet prefix. `config/agent.toml` `[diagnostics] encryption_key = ""` (comment: '"" disables encryption (opt-in)') and the deployed `/opt/llm/config/agent.toml` ship the same empty key, with `retention_days = 30`. Protection of stored diagnostics therefore rests on `_SENSITIVE_FIELDS` filtering plus best-effort `_SENSITIVE_PATTERNS` regex redaction. Confirmed by review (python-code-review finding F-006, High confidence; this opt-in behavior is documented in the config comment, but no operational decision endorsing it exists in `docs/`).

## Problem
Diagnostic rows (including transport-failure payloads) are stored in plaintext; the store can detect sensitive-looking content yet still writes it unredacted-by-encryption, and whether that is accepted for production is nowhere stated.

## Reason for Change
A security-relevant config posture currently exists only as a code default plus a config comment. Whether to enable encryption in production or formally accept plaintext-with-redaction needs a decision an implementer and operator can both rely on.

## Implementation Intent
This issue is primarily a decision plus its documentation, not a code patch. Option A: enable a Fernet key in the production config (key generated and installed out-of-band, never committed) and verify the encrypt/read round-trip. Option B: formally accept the current posture and record it as an operational note / Known Issue with the residual risk (regex redaction is best-effort; detected-sensitive rows are persisted). A decision on rows already stored in plaintext under the retention window is part of the outcome.

## Target Files or Areas
- `config/agent.toml` `[diagnostics]` (repo-side posture documentation)
- Production config `/opt/llm/config/agent.toml` `[diagnostics]` (only if Option A is chosen)
- `scripts/agent/diagnostic_store.py` (behavior reference; unchanged unless the decision requires it)
- Agent diagnostics documentation under `docs/23_agent/`

## Required Changes
- Obtain the owner decision: enable encryption in production, or accept plaintext-with-redaction.
- Option A: provision a Fernet key in the production config (generation and placement out-of-band; never committed or pasted), then verify save/decrypt round-trip on real rows.
- Option B: record the accepted-risk posture in the diagnostics docs as an operational note / Known Issue.
- State the handling of existing plaintext rows (re-encrypt, expire via retention, or leave).

## Constraints
- `skills/DESIGN.md` No secrets in output: no generated or real key value may appear in any committed file, issue, or doc.
- `DiagnosticStore` behavior (redaction pipeline, lazy purge, read-side decrypt) must not regress.
- Config changes to `/opt/llm/config/` are shared-infrastructure changes and require explicit approval.

## Acceptance Criteria
- The posture decision is recorded: either the production config carries a key with a verified round-trip, or the accepted risk is documented in the diagnostics docs.
- The chosen handling of pre-existing plaintext rows is stated.
- Full test suite passes with no behavior change to `DiagnosticStore` unless the decision required one.

## Testing Expectations
- If Option A: a round-trip check (save with key configured → stored value decrypts to the redacted original) via existing encryption tests or a targeted integration check.
- Regression: existing `DiagnosticStore` tests (redaction, purge, decrypt-on-read) pass unchanged.

## Documentation Impact
Required: record the posture in the agent diagnostics documentation — intent (opt-in encryption), constraints (key handling), failure behavior (detected-sensitive-but-unencrypted warning path), and operational notes; Known Issue entry if Option B.

## Out of Scope
- Redesigning `_SENSITIVE_PATTERNS` redaction or the field-filter list.
- Changing `save()`'s default `encrypt` flag.
- Encryption of other tables (messages, memories).

## Dependencies
N/A: none

## Unresolved Questions
- Owner decision (不明): enable encryption in production or formally accept plaintext-with-redaction.
- Disposition of already-stored plaintext rows within the 30-day retention window.

## AI Implementation Instruction
Do not generate, commit, or paste any encryption key. Present both options with their operational cost for the owner's decision before changing production config; docs updates must follow `skills/DESIGN.md` docs policy and contain no secrets.

## Traceability
- **Workflow phase**: python-code-review (finding F-006)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-210357
- **Related target files**: `config/agent.toml`, `/opt/llm/config/agent.toml`, `scripts/agent/diagnostic_store.py`, `docs/23_agent/`
