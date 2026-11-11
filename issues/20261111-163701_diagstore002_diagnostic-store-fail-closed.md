# Make DiagnosticStore configuration and persistence fail closed

## Priority
High

## Summary
Make `DiagnosticStore` use a validated, injected diagnostics configuration and make its persistence path fail closed: no original content is written when filtering fails, and encryption is applied by policy instead of by caller choice.

## Background
Source: `memo-issue.md` (Revised Implementation Issues A-H, Issue G), re-verified against current source on 2026-11-11.

- `Explicit in code`: `DiagnosticStore.save()` calls `_filter_sensitive_fields()` inside a try block. On exception it logs "proceeding without filtering" and continues with the original content.
- `Explicit in code`: secret detection (`detects_secrets`) runs only when no encryption key is configured and the filter did not fail. After a filter failure it is skipped.
- `Explicit in code`: encryption happens only when the caller passes `encrypt=True` and a key is configured. The default is `encrypt=False`.
- `Explicit in code`: `fetch()` treats content that starts with the Fernet prefix as ciphertext when a key is configured.
- `Explicit in code`: `_load_diagnostics_config()` is called per `save()` and per `fetch()` and re-reads `agent.toml`.
- `Needs confirmation`: the remaining memo items were not re-read in this pass: non-dict section becoming `{}`, non-list `sensitive_fields` becoming an empty set, `int()` coercion of `retention_days`, missing `__post_init__` validation in `DiagnosticsConfig`, redaction limited to list-valued fields, fetch returning ciphertext on decrypt failure, and the LLM partial-text and transport-error save path.
- Related archived work: `issues/done/20261025-115935_sess006_diagnostic-store-config-reload.md` (config reload cost) and `plans/done/20261101-120804_diagstore001_diagnostic-save-crashes-turn.md` (non-fatal save). This issue must be re-verified against current source for any claim those items may already have changed.

## Problem
A failure in the redaction step results in unredacted diagnostic content (LLM partial text, transport-error details) being persisted to `session_diagnostics`. When an encryption key is configured, plaintext is still stored unless every caller opts in. Configuration is re-read on every operation and is not validated at the type level, so a malformed diagnostics section silently weakens protection (for example, a non-positive retention disables purge).

## Reason for Change
This is a data-protection defect on a persistence path that stores model output and error details, and it fails open on the exact condition (a redaction error) that the protection exists for. No time-sensitive deadline is stated; severity is High because of the security-sensitive behavior.

## Implementation Intent
- Resolve and validate the diagnostics configuration once, at startup or reload, in the canonical config-building and validation layer. Inject the validated snapshot into `DiagnosticStore` at construction.
- Make the persistence policy a store responsibility, not a caller option: with a key, every record is encrypted; without a key, every record is filtered and secret-checked before storage.
- On filter failure, either reject persistence or store a fixed redacted marker. The original content is never written.
- Make the stored form explicit (encrypted, redacted plaintext) so retrieval can report a decrypt-failed state instead of presenting ciphertext as content.
- Preserve the existing non-fatal, worker-thread save behavior so a diagnostic refusal never crashes a user turn.

## Target Files or Areas
- `scripts/agent/diagnostic_store.py`
- `scripts/agent/config_dataclasses.py`
- `scripts/agent/config_builders.py`
- `scripts/agent/config_section_builders.py`
- `scripts/agent/services/config_validators.py` (or the diagnostics-specific validator module; `Unknown`)
- `scripts/db/schema_sql.py` (`session_diagnostics` DDL)
- Diagnostic producers that call `save()` (Orchestrator wiring, LLM transport-error and partial-text paths)
- Tests for DiagnosticStore under `tests/` (actual path `Unknown`; locate by search)

## Required Changes
- Inject the validated `DiagnosticsConfig` snapshot into `DiagnosticStore`; remove per-operation `_load_diagnostics_config()` use.
- Add strict `DiagnosticsConfig` validation: a valid Fernet key when configured, a positive retention, non-empty string field names, correct section and list types. Invalid configuration fails startup or reload.
- Remove the public `encrypt` argument. Encrypt every record when a key is configured.
- When no key is configured, always run filtering and secret detection before persistence.
- On filter failure, reject persistence or replace all content with a fixed marker. Never write the original.
- Add an explicit storage format or encrypted flag to `session_diagnostics` and make `fetch()` report encrypted, redacted-plaintext, and decrypt-failed records distinctly.
- Bound or sanitize LLM transport-error details before persistence.
- Ensure all producers share exactly one store instance (Orchestrator and test injection).

## Constraints
- Preserve non-fatal, `asyncio.to_thread()`-offloaded diagnostic saves.
- Follow `rules/coding.md` Type-coercion policy (`get_typed`-style validation, no bare `int()` coercion).
- Schema change follows `rules/persisted-schema-change.md` and the repository's current-schema-only policy (no compatibility shim).
- Follow `skills/DESIGN.md` No secrets in output for any test fixture or log text.

## Acceptance Criteria
- No filter failure can cause original content to be persisted.
- With a key configured, every diagnostic row is encrypted without caller participation.
- Invalid diagnostics configuration fails startup or reload with a typed error.
- Retrieval distinguishes encrypted, redacted-plaintext, and decrypt-failed records and never returns ciphertext as ordinary content.
- A diagnostic save failure never crashes the user turn.
- `DiagnosticStore` performs no configuration file reads per operation.

## Testing Expectations
- Unit tests: JSON and non-JSON secrets, filter exceptions, invalid key, retention bounds, automatic encryption, decryption failure, no-key redaction path.
- Regression tests replacing any existing plaintext or fail-open expectations in the DiagnosticStore tests.
- Config validation tests for malformed `diagnostics` sections.
- Run `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run ruff check scripts/`, `uv run python tools/check_db_separation.py`, and the targeted pytest files.

## Documentation Impact
Update the diagnostics and security documents under `docs/` that describe storage and encryption behavior: intent, failure behavior (fail closed), the stored-format states, and Needs Confirmation items for the production policy decision. Do not copy concrete configuration values (see `skills/DESIGN.md` No concrete configuration values).

## Out of Scope
- Changing the non-fatal save contract or moving diagnostics to another database.
- RAG audit and MCP authentication work in `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md`.
- Any retention policy change beyond validation.

## Dependencies
Duplicate and overlap check (2026-11-11): no open issue duplicates this one. Overlapping archived items:
- `issues/done/20261025-115935_sess006_diagnostic-store-config-reload.md` (overlap: partial, archived): resolve the diagnostics config once per DiagnosticStore operation instead of re-reading `agent.toml` up to three times per `save()`. This issue goes further (inject a validated snapshot, no per-operation read); re-verify what sess006 already changed.
- `plans/done/20261101-120804_diagstore001_diagnostic-save-crashes-turn.md` (overlap: partial, archived): contain `DiagnosticStore.save()` RuntimeError so a sensitive-pattern refusal degrades to a warning instead of crashing the turn. This issue must preserve that non-fatal contract.

Ordering and other dependencies:
- `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md`: no shared target files found in this check; no ordering required.
- Re-verify against `issues/done/20261025-115935_sess006_diagnostic-store-config-reload.md` and `plans/done/20261101-120804_diagstore001_diagnostic-save-crashes-turn.md` outcomes before planning.
- Related sibling in this batch: the Issue for RuntimeToolRegistry authority does not share files; no ordering.

## Unresolved Questions
Decisions required from the maintainer before implementation:
- Decision 1 (production encryption policy): require an encryption key in production (a missing key is a startup error), or allow validated redacted plaintext when no key is configured. It determines the startup validation rule and the stored-format states.
- Decision 2 (decrypt-failed behavior): what a consumer of `fetch()` sees for a decrypt-failed record (explicit state with no content, an error, or skip). Consumers are not yet enumerated.

Open facts (不明):
- the actual path of the DiagnosticStore tests and the diagnostics validator module.
- Assumption: the schema may change under the current-schema-only policy without a migration path.

## AI Implementation Instruction
- Change only the diagnostics configuration, store, schema, and their tests; do not rewrite unrelated files.
- Do not weaken the non-fatal save behavior.
- Stop and report if the production encryption decision above is unresolved when the storage format is designed.
- Do not implement out-of-scope items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261111-163701
- **Related target files**: `scripts/agent/diagnostic_store.py`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_builders.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/services/config_validators.py`, `scripts/db/schema_sql.py`
