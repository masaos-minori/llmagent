# Plan: Make DiagnosticStore configuration and persistence fail closed

## Goal
Make `DiagnosticStore` consume a validated, injected `DiagnosticsConfig` snapshot and make its persistence path fail closed: no original content is written when filtering fails, encryption is applied by policy instead of by caller choice, and retrieval reports the stored form (encrypted, redacted-plaintext, decrypt-failed) distinctly instead of presenting ciphertext as content.

## Priority
High

## Scope
- **In-Scope**:
  - Inject the validated `DiagnosticsConfig` snapshot into `DiagnosticStore` at construction; remove per-operation `_load_diagnostics_config()` reads.
  - Add strict `DiagnosticsConfig` validation (valid Fernet key when configured, positive-int retention type, string field names); invalid configuration fails startup or reload with a typed error.
  - Remove the public `encrypt` argument. Encrypt every record when a key is configured; otherwise always filter and secret-check before persistence.
  - On filter failure, reject persistence or replace all content with a fixed marker. Never write the original.
  - Add an explicit storage-format column to `session_diagnostics` and make `fetch()` report encrypted, redacted-plaintext, and decrypt-failed records distinctly.
  - Bound or sanitize LLM transport-error details before persistence.
  - Consolidate producers onto a single shared store instance (Orchestrator-owned and test-injected).
  - Preserve the non-fatal, worker-thread (`asyncio.to_thread`) save behavior.
  - Update the diagnostics/security documents that describe storage and encryption behavior.
- **Out-of-Scope**:
  - Changing the non-fatal save contract or moving diagnostics to another database.
  - Retention policy changes beyond type validation (the `<= 0 disables purge` runtime semantic is intentionally preserved; see `UNK-03`).
  - RAG audit and MCP authentication work in `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md`.
  - Introducing a new `config/*.toml` file (no new config file; the `[diagnostics]` table already exists in `agent.toml`).
- **Dependencies**:
  - `N/A: none` — no open Plan or Issue shares a target file with this one.
  - Ordering notes (sequencing-only, not hard dependencies):
    - `plans/done/20261101-120804_diagstore001_diagnostic-save-crashes-turn.md` (archived): establishes the non-fatal save contract this Plan must preserve. Depends on its outcome being understood; no file overlap.
    - `issues/done/20261025-115935_sess006_diagnostic-store-config-reload.md` (archived): already fixed the per-operation config reload cost (single `ConfigLoader.load` per op). This Plan goes further by injecting a validated snapshot and removing `_load_diagnostics_config()` entirely. No file overlap; understand sess006 before touching the config-read path.

## Background
Source: `memo-issue.md` (Revised Implementation Issues A-H, Issue G), re-verified against current source on 2026-11-11 and again 2026-11-14.

- `Explicit in code`: `DiagnosticStore.save()` calls `_filter_sensitive_fields()` inside a try block; on exception it logs "proceeding without filtering" and continues with the original content (`scripts/agent/diagnostic_store.py`, `save()`).
- `Explicit in code`: secret detection (`detects_secrets`) runs only when no encryption key is configured and the filter did not fail. After a filter failure it is skipped.
- `Explicit in code`: encryption happens only when the caller passes `encrypt=True` and a key is configured. The default is `encrypt=False`. No production caller passes `encrypt=True`.
- `Explicit in code`: `_load_diagnostics_config()` is called per `save()` and per `fetch()` and re-reads `agent.toml` via `ConfigLoader().load("agent.toml")`.
- `Explicit in code`: `fetch()` treats content starting with the Fernet prefix as ciphertext when a key is configured and, on decrypt failure, leaves the ciphertext in place and logs a warning.
- `Documentation only` (accepted decision, 2026-10-25): the owner formally accepted Option B — plaintext-with-redaction — for `session_diagnostics` in production. Shipped configs set `encryption_key = ""` and no production call site passes `encrypt=True`. The residual risk (the filter-failure path persists unencrypted content) is documented.
- `Needs confirmation` (resolved by this Plan): non-dict section becoming `{}`, non-list `sensitive_fields` becoming an empty set, bare `int()` coercion of `retention_days`, missing `__post_init__` validation in `DiagnosticsConfig`, redaction limited to list-valued fields, fetch returning ciphertext on decrypt failure, and the LLM partial-text / transport-error save path.

## Problem
A failure in the redaction step results in unredacted diagnostic content (LLM partial text, transport-error details) being persisted to `session_diagnostics`. When an encryption key is configured, plaintext is still stored unless every caller opts in. Configuration is re-read on every operation and is not validated at the type level, so a malformed diagnostics section silently weakens protection (for example, a non-positive retention disables purge, and a wrong-typed `retention_days` is silently coerced by bare `int()`, violating the type-coercion policy).

## Reason for Change
This is a data-protection defect on a persistence path that stores model output and error details, and it fails open on the exact condition (a redaction error) that the protection exists for. Severity is High because of the security-sensitive behavior. No time-sensitive deadline is stated.

## Implementation Intent
- Resolve and validate the diagnostics configuration once, at startup or reload, in the canonical config-building and validation layer, and inject the validated snapshot into `DiagnosticStore` at construction.
- Make the persistence policy a store responsibility, not a caller option: with a key, every record is encrypted; without a key, every record is filtered and secret-checked before storage.
- On filter failure, reject persistence or replace all content with a fixed marker. The original content is never written.
- Make the stored form explicit (a storage-format column) so retrieval can report a decrypt-failed state instead of presenting ciphertext as content.
- Preserve the existing non-fatal, worker-thread save behavior so a diagnostic refusal never crashes a user turn.

## Requirements
- `REQ-001`: Inject the validated `DiagnosticsConfig` snapshot into `DiagnosticStore` at construction; remove per-operation `_load_diagnostics_config()` use.
- `REQ-002`: Validate `DiagnosticsConfig` strictly — a valid Fernet key when configured, a positive-int `retention_days`, and string `sensitive_fields` entries — via `config_validators`, wired through `config_section_builders` and `config_dataclasses.__post_init__`; invalid configuration fails startup or reload with a typed error.
- `REQ-003`: Remove the public `encrypt` argument. Encrypt every record when a key is configured, by policy, without caller participation.
- `REQ-004`: When no key is configured, always run filtering and secret detection before persistence.
- `REQ-005`: On filter failure, reject persistence or replace all content with a fixed marker. Never write the original.
- `REQ-006`: Add an explicit storage-format column to `session_diagnostics` and make `fetch()` report encrypted, redacted-plaintext, and decrypt-failed records distinctly, never returning ciphertext as ordinary content.
- `REQ-007`: Bound or sanitize LLM transport-error details before persistence.
- `REQ-008`: Ensure all producers share exactly one store instance (Orchestrator-owned, test-injected).
- `REQ-009`: Preserve the non-fatal, `asyncio.to_thread()`-offloaded diagnostic save behavior.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified`; `issue-to-plan` Step 8's Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/diagnostic_store.py` | Modify | Inject `DiagnosticsConfig` into `__init__`; delete `_load_diagnostics_config()`; make persistence fail closed on filter failure; remove `encrypt` argument; populate and read the storage-format column in `save()`/`fetch()`. | REQ-001, REQ-003, REQ-004, REQ-005, REQ-006, REQ-009 | `save()` lines 132-179, `fetch()` lines 181-212, `_load_diagnostics_config()` lines 37-61, `_encrypt_content()` lines 94-104 | `tests/agent/test_diagnostic_store_security.py`, `tests/agent/test_diagnostic_store.py` | Verified |
| `scripts/agent/config_dataclasses.py` | Modify | Add `__post_init__` to `DiagnosticsConfig` calling the new validators (valid key, positive-int retention, string field names). | REQ-002 | `DiagnosticsConfig` lines 329-342 currently has no `__post_init__` | `tests/agent/test_config_dataclasses.py` | Verified |
| `scripts/agent/services/config_validators.py` | Modify | Add `validate_diagnostics_encryption_key`, `validate_diagnostics_retention_days`, `validate_diagnostics_sensitive_fields` following the existing `validate_<field>(cfg) -> None` pattern. | REQ-002 | `validate_memory_retention_days(cfg)` at line 170 is the established signature template | new tests for diagnostics validation | Verified |
| `scripts/agent/config_section_builders.py` | Modify | Route `DiagnosticsConfig` construction through the new validators so a rejected value surfaces as `ConfigReloadValidationError`. | REQ-002 | `_build_diagnostics_config()` lines 322-335 uses `_build_model` but no key/retention validation | config-build tests | Verified |
| `scripts/db/schema_sql.py` | Modify | Add a `storage_format` column to the `session_diagnostics` DDL in `_SESSION_SCHEMA_TEMPLATE`. | REQ-006 | `_SESSION_SCHEMA_TEMPLATE` `session_diagnostics` block, lines 134-142 | session-schema fingerprint tests (review) | Verified |
| `scripts/agent/orchestrator.py` | Modify | Construct the single shared `DiagnosticStore` with `ctx.cfg.diagnostics` injected. | REQ-001, REQ-008 | `self._diagnostic_store = DiagnosticStore()` at line 89; `ctx.diagnostics = self._diagnostic_store` at line 90 | orchestrator wiring tests | Verified |
| `scripts/agent/repl.py` | Modify | Construct its `DiagnosticStore` with `self._ctx.cfg.diagnostics` injected. | REQ-001 | `self._diagnostic_store = DiagnosticStore()` at line 80; `self._ctx` available | repl tests | Verified |
| `scripts/agent/session.py` | Modify | Supply a validated `DiagnosticsConfig` to the store it constructs (wiring resolved — see `Design`). | REQ-001, REQ-008 | `self._diagnostic_store = DiagnosticStore(self.session_id)` at line 62; `AgentContext.__init__` builds `self.cfg` (context.py:389) before constructing `AgentSession()` at line 395, so `cfg.diagnostics` is reachable at the construction site | session tests | Verified |
| `tests/agent/test_diagnostic_store_security.py` | Modify | Regress the fail-open carve-out and every `encrypt=` expectation to the fail-closed contract. | REQ-003, REQ-005 | `test_filter_failed_carve_out_preserved` lines 451-493 asserts fail-open; `TestEncryptionStatus`/`TestSharedDetectorGuard` pass `encrypt=` | this file | Verified |
| `tests/agent/test_diagnostic_store.py` | Modify | Regress `encrypt=True` / `_load_diagnostics_config()` round-trip tests to injection + fail-closed behavior. | REQ-001, REQ-003 | `TestEncryption` lines ~354-440, `test_save_rejects_sensitive_data_without_encryption` ~552, `TestFetchEncryptedRoundTrip` ~746 | this file | Verified |
| `tests/agent/test_config_dataclasses.py` | Modify | Update `DiagnosticsConfig` assertions for the new validated fields / `__post_init__`. | REQ-002 | assertions at lines 242, 278-283 | this file | Verified |
| `tests/agent/test_llm_turn_runner.py` | Modify | Update references to the sensitive-data refusal message if the message text changes. | REQ-004 | message string referenced at lines 393, 396, 421 | this file | Verified |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | Modify | Document the fail-closed persistence policy, the stored-format states, and the resolved production-encryption decision. | REQ-005, REQ-006 | "Accepted storage posture" lines 70-76, decryption-failure handling line 61 | N/A | Verified |

Rules:
- One row per file. No directory, glob, component, file group, or vague phrase appears as a row.
- Test, schema, and documentation files are their own rows, not folded into the source file they accompany.
- `Validation Status` is `Verified` for every row before freeze. `session.py`'s injection wiring was confirmed feasible in Step 8b: `AgentContext.__init__` builds `self.cfg` (context.py:389) before constructing `AgentSession()` (line 395), so a validated `DiagnosticsConfig` is reachable; the row is now `Verified`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/config_builders.py` | Assembly entry point; calls `_build_diagnostics_config(cfg)` and owns the reload/startup pipeline the validation must hook into. | REQ-002 |
| `scripts/db/create_schema.py` | Recreate-only DDL executor; `_refuse_existing_drift` + `assert_matches` enforce that the schema change forces archive-and-recreate. | REQ-006 |
| `scripts/db/session_consistency.py` | `_check_schema_fingerprint` asserts live schema == canonical DDL; the storage-format column makes existing DBs fail this gate. | REQ-006 |
| `scripts/agent/session_persister.py` | Non-fatal save path (`asyncio.to_thread`, catches `RuntimeError`/`sqlite3.Error`); must keep degrading to a warning. | REQ-009 |
| `scripts/agent/context.py` | Holds `ctx.diagnostics` (the shared store) and `ctx.cfg`; the wiring reference for injection. | REQ-001, REQ-008 |
| `scripts/agent/services/config_reload.py` | Documents diagnostics fields as "always live" (read per op); the injection removes this per-op read. | REQ-001 |
| `scripts/agent/services/config_outcome_classification.py` | `detect_diagnostics_live_fields` lists diagnostics fields for `/reload` outcome classification; must reflect the removed per-op reads. | REQ-001 |
| `scripts/agent/error_injection_service.py` | A `save()` producer site; confirm it shares the single store instance. | REQ-008 |
| `scripts/agent/tool_loop_guard.py` | A `save()` producer site (guard hints); confirm it shares the single store instance. | REQ-008 |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Defines `detects_secrets()` (the shared detector backing the fail-closed guard). | REQ-004 |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Documents `retention_days` ("0 or less disables purge"); the preserved runtime semantic. | REQ-002 |

## Acceptance Criteria
- `AC-1`: No filter failure can cause original content to be persisted. (`REQ-005`)
- `AC-2`: With a key configured, every diagnostic row is encrypted without caller participation. (`REQ-003`)
- `AC-3`: Invalid diagnostics configuration fails startup or reload with a typed error. (`REQ-002`)
- `AC-4`: Retrieval distinguishes encrypted, redacted-plaintext, and decrypt-failed records and never returns ciphertext as ordinary content. (`REQ-006`)
- `AC-5`: A diagnostic save failure never crashes the user turn. (`REQ-009`)
- `AC-6`: `DiagnosticStore` performs no configuration file reads per operation. (`REQ-001`)

## Tests
- Unit tests (`REQ-005`): JSON secrets, non-JSON secrets, filter exceptions (fail closed — reject or fixed marker), invalid key, invalid retention type, automatic encryption with a key, decryption failure reported distinctly, no-key redaction path.
- Regression tests (`REQ-003`, `REQ-001`): replace `test_filter_failed_carve_out_preserved` and every `encrypt=` / `_load_diagnostics_config()` expectation in `tests/agent/test_diagnostic_store_security.py` and `tests/agent/test_diagnostic_store.py`.
- Config validation tests (`REQ-002`): malformed `[diagnostics]` sections — non-Fernet key when set, non-int/float `retention_days`, non-list `sensitive_fields`, non-dict section.
- Storage-format tests (`REQ-006`): fresh canonical schema includes `storage_format`; `fetch()` marks decrypt-failed rows distinctly and never returns ciphertext as `content`.
- Producer-wiring tests (`REQ-008`): Orchestrator and test injection share one `DiagnosticStore` instance.
- Run `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run ruff check scripts/`, `uv run python tools/check_db_separation.py`, and the targeted pytest files.

## Documentation Impact
`docs/23_agent/agent_09_01_data-layer-session-db.md` MUST be updated for `REQ-005` and `REQ-006`: document the fail-closed persistence intent, the stored-format states (`encrypted` / `redacted_plaintext` / `decrypt_failed`), and the resolved production-encryption decision. Do not copy concrete configuration values (see `skills/DESIGN.md` No concrete configuration values). The `retention_days` doc in `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` should note the validated positive-int type while preserving the "0 or less disables purge" runtime semantic.

## Assumptions
- The storage-format column is added as `storage_format TEXT NOT NULL DEFAULT 'plaintext'`; the write path always sets it explicitly (`encrypted` when a key encrypts, otherwise `plaintext`). Because `session.sqlite` is recreate-only, no backfill is needed.
- Encryption is applied by policy when a key is configured and redacted plaintext is preserved when no key is configured. This preserves the documented 2026-10-25 Option B decision while removing the caller-choice aspect (`REQ-003`). Switching to "require a key in production (startup error)" requires explicit maintainer sign-off and is out of scope unless directed (`UNK-01`).
- `retention_days <= 0` retains its documented "disable purge" runtime semantic. Validation enforces a positive-int *type* (fixing the bare `int()` coercion violation); it does not reject `<= 0` at load time. Changing that runtime policy is out of scope (`UNK-03`).
- The single-store-instance goal (`REQ-008`) is achieved by the Orchestrator owning the instance and sharing it via `ctx.diagnostics`; `session.py`'s independently-created store is consolidated onto the shared instance or wired to receive the injected config.
- Cross-plan overlaps (`tools/check_plan_target_overlaps.py`, Step 8b): `orchestrator.py`, `session.py`, and `schema_sql.py` are also targeted by the Frozen Plan `plans/20261112-122030_rmcompat007_history-comment-sweep.md`, which is a comment/docstring-only sweep (its Goal and AC-6 forbid any code/logic change). The overlaps are **compatible**, not conflicting: rmcompat007 edits history/plan-identifier comments (`orchestrator.py` 187-188, `session.py` 139/240, `schema_sql.py` 223 SQL comment inside a string literal) while this Plan edits code and DDL. No contradiction. Implementation sequencing: run this Plan's code/DDL edits before rmcompat007's comment sweep on the same files (rmcompat007 re-reads each file and closes rows whose matches are gone), so the comment sweep does not re-touch lines this Plan already changed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | Production encryption policy: require an encryption key in production (missing key = startup error), or allow validated redacted plaintext when no key is configured? | Maintainer policy decision. The documented 2026-10-25 decision (Option B) points to redacted-plaintext baseline; no current instruction overturns it. | Recommended: encryption by policy when a key is configured; redacted plaintext when no key (preserves Option B). Require maintainer sign-off to switch to "require key." | False |
| `UNK-02` | What a consumer of `fetch()` sees for a decrypt-failed record (explicit state with no content, an error, or skip)? | Consumers are not fully enumerated. | Add `storage_format` so consumers distinguish states; mark decrypt-failed rows distinctly and never return ciphertext as `content` (`AC-4`). Consumers read `storage_format`. | False |
| `UNK-03` | Should `retention_days <= 0` be rejected at config load, or retain the documented "disable purge" semantic? | Policy question. Out-of-Scope says "validation only"; the doc treats disable-purge as intentional. | Scope to type validation (positive-int type); preserve disable-purge semantics unless maintainer directs otherwise. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/diagnostic_store.py` | modify | callers constructing `DiagnosticStore` (Orchestrator, repl, session, tests); public `encrypt` arg removed | 3 | shared (multiple producers) | not applicable (rsynced) |
| `scripts/agent/config_dataclasses.py` | modify | all config consumers via `AgentConfig.diagnostics`; adds `__post_init__` validation | 10 | shared (config layer) | not applicable (rsynced) |
| `scripts/agent/services/config_validators.py` | modify | config-build pipeline; new validators imported by `config_dataclasses` | N/A | shared (config layer) | not applicable (rsynced) |
| `scripts/agent/config_section_builders.py` | modify | config-build pipeline | 4 | shared (config layer) | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | modify | session.sqlite recreation on next schema apply; fingerprint gate | 17 | shared (DB layer, SSOT DDL) | not applicable (rsynced) |
| `scripts/agent/orchestrator.py` | modify | single store construction | N/A | owner-dominant | not applicable (rsynced) |
| `scripts/agent/repl.py` | modify | REPL store construction | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/session.py` | modify | store construction (wiring TBD) | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_diagnostic_store_security.py` | modify | security test suite | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_diagnostic_store.py` | modify | store test suite | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_config_dataclasses.py` | modify | config dataclass tests | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_llm_turn_runner.py` | modify | LLM turn runner tests | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | modify | diagnostics documentation | N/A | N/A | N/A |

`deploy.sh Impact`: `deploy/deploy.sh` rsyncs `scripts/` wholesale, so Python file changes need no `deploy.sh` update; no new `config/*.toml` is introduced.

## Design
Architecture and dependency analysis (Path B).

- **Config-validation layer (`REQ-002`)**: `DiagnosticsConfig` gains a `__post_init__` that calls new validators in `config_validators.py`, mirroring the existing `validate_<field>(cfg) -> None` contract (e.g. `validate_memory_retention_days`). Each validator raises `ValueError` on a bad value; `_build_model` in `config_section_builders.py` wraps `ValueError` as `ConfigReloadValidationError`, so a malformed `[diagnostics]` table fails startup/reload. This also fixes the coding-policy violation: `retention_days` currently uses bare `int()` in `diagnostic_store.py::_load_diagnostics_config`, which silently coerces wrong types. The new validators use `get_typed`-style checks.
- **Injection (`REQ-001`, `REQ-008`)**: `DiagnosticStore.__init__` takes a `diagnostics_cfg: DiagnosticsConfig` and stores it; `_load_diagnostics_config()` is deleted. `save()`/`fetch()` use the injected snapshot instead of reading `agent.toml`. Producers construct the store from `ctx.cfg.diagnostics`. The Orchestrator owns the single instance and shares it via `ctx.diagnostics` (already wired at `orchestrator.py` line 90); `repl.py` passes `self._ctx.cfg.diagnostics`. `session.py` constructs a store without holding `ctx`; the wiring is confirmed feasible because `AgentContext.__init__` builds `self.cfg` (context.py:389) before constructing `AgentSession()` (line 395), so a validated `DiagnosticsConfig` is reachable at the construction site. Two feasible paths remain as an implementation-phase decision: (a) thread `cfg.diagnostics` into `AgentSession.__init__`, or (b) consolidate `session.py` onto the Orchestrator-owned shared instance (aligns with `REQ-008`). Path choice affects how many `AgentSession` test fixtures (`test_agent_session.py` and related) must be updated — recorded as a Risk.
- **Fail-closed persistence (`REQ-003`, `REQ-004`, `REQ-005`)**: With a key, `save()` encrypts unconditionally (the `encrypt` argument is removed). Without a key, `save()` always runs `_filter_sensitive_fields()` then `detects_secrets()`. On filter failure it no longer persists the original; it either raises (rejected persistence) or writes a fixed marker. The non-fatal contract (`session_persister.py` catches `RuntimeError`) is preserved, so a rejection degrades to a warning rather than crashing the turn.
- **Storage format (`REQ-006`, critical)**: A `storage_format` column is added to `session_diagnostics`. `fetch()` reads it to classify each row as `encrypted` / `redacted_plaintext` / `decrypt_failed` and never returns ciphertext as `content`. **Operational impact**: `session.sqlite` is recreate-only with no migration registry or version stamp (unlike `workflow.sqlite` and `eventbus.sqlite`). Adding a column changes the canonical DDL, and `assert_matches` (in `create_schema.py::_refuse_existing_drift` and `session_consistency.py::_check_schema_fingerprint`) compares the live schema against canonical DDL, so any existing `session.sqlite` fails the fingerprint gate on startup and must be archived and recreated. Pre-existing rows are discarded; they are operator-facing auxiliary data with low retention value. This is the highest-impact change in the Plan and must be communicated as a production `session.sqlite` recreation.
- **Release units**: The `storage_format` column and its write/read path (`save()` populates it, `fetch()` classifies it) MUST land together. Under recreate-only there is no partial-production state, but within development a fresh DB created after the DDL change has the column, so every `INSERT` into `session_diagnostics` must populate it before the schema change is tested in isolation.
- **Blast radius**: `DiagnosticsConfig` and `DiagnosticStore.save()` are broadly referenced. `rg` over `tests/` shows the `encrypt`/`_load_diagnostics_config` surface spans `test_diagnostic_store_security.py`, `test_diagnostic_store.py`, `test_config_dataclasses.py`, and `test_llm_turn_runner.py` — recorded here per `rules/toolchain.md` rather than discovered at test time. Complexity baseline (radon) is all A/B for the touched modules; no complexity regression expected.

## Implementation steps
Each step cites the exact file paths from `Implementation Target Files`.

1. **Phase 1: Config validation layer** (`REQ-002`)
   - [ ] Add `validate_diagnostics_encryption_key`, `validate_diagnostics_retention_days`, `validate_diagnostics_sensitive_fields` to `scripts/agent/services/config_validators.py` (`get_typed`-style; raise `ValueError`). [`scripts/agent/services/config_validators.py`]
   - [ ] Add `DiagnosticsConfig.__post_init__` calling the new validators. [`scripts/agent/config_dataclasses.py`]
   - [ ] Route `_build_diagnostics_config` through the validators so rejections surface as `ConfigReloadValidationError`. [`scripts/agent/config_section_builders.py`]
   - [ ] Config-validation tests for malformed `[diagnostics]` sections. [`tests/agent/test_config_dataclasses.py`]
2. **Phase 2: Store injection + fail-closed persistence** (`REQ-001`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-009`)
   - [ ] Inject `DiagnosticsConfig` into `DiagnosticStore.__init__`; delete `_load_diagnostics_config()`. [`scripts/agent/diagnostic_store.py`]
   - [ ] Remove the `encrypt` argument; encrypt by policy when a key is configured; always filter + secret-check without a key; reject or marker on filter failure. [`scripts/agent/diagnostic_store.py`]
   - [ ] Wire the single shared instance: pass `ctx.cfg.diagnostics` in `orchestrator.py` and `self._ctx.cfg.diagnostics` in `repl.py`; resolve `session.py` wiring. [`scripts/agent/orchestrator.py`, `scripts/agent/repl.py`, `scripts/agent/session.py`]
   - [ ] Regress `test_diagnostic_store_security.py` (fail-open carve-out, `encrypt=` expectations) and `test_diagnostic_store.py` (`encrypt`/`_load_diagnostics_config` round-trips). [`tests/agent/test_diagnostic_store_security.py`, `tests/agent/test_diagnostic_store.py`]
3. **Phase 3: Storage format + retrieval** (`REQ-006`) — release unit with Phase 2's write path
   - [ ] Add `storage_format` column to the `session_diagnostics` DDL. [`scripts/db/schema_sql.py`]
   - [ ] Populate `storage_format` in `save()`; classify rows and never return ciphertext in `fetch()`. [`scripts/agent/diagnostic_store.py`]
   - [ ] Update any test pinning the session schema fingerprint; verify fresh canonical schema includes the column. [`scripts/db/schema_sql.py` related]
4. **Phase 4: Transport-error sanitization + docs** (`REQ-007`, documentation)
   - [ ] Bound/sanitize LLM transport-error details before persistence. [`scripts/agent/diagnostic_store.py`]
   - [ ] Update `docs/23_agent/agent_09_01_data-layer-session-db.md` for the fail-closed policy, stored-format states, and resolved encryption decision. [`docs/23_agent/agent_09_01_data-layer-session-db.md`]
5. **Phase 5: Validation suite**
   - [ ] Run the full validation sequence (`rules/toolchain.md`): ruff, mypy, import-linter, ast-grep, bandit, targeted pytest, `check_db_separation.py`, diff-cover, pre-commit.

### Release units
**Unit**: `storage_format` column + save()/fetch() write-and-read path | **Phases**: 2, 3 | **Reason**: a fresh DB created after the DDL change has the column, so every `INSERT` must populate it before the schema change can be validated in isolation; the schema and its write path ship as one unit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_validators.py` | Unit: each new validator rejects a bad value, accepts a good one | `uv run pytest tests/agent/test_config_dataclasses.py` | Pass |
| `scripts/db/schema_sql.py` | Integration: fresh canonical schema includes `storage_format`; fingerprint matches | `uv run python tools/check_db_separation.py`; schema fingerprint test | Pass |
| `scripts/agent/diagnostic_store.py` | Unit: fail-closed on filter failure, encrypted-by-policy, decrypt-failed distinct, no per-op read | `uv run pytest tests/agent/test_diagnostic_store_security.py tests/agent/test_diagnostic_store.py` | Pass |
| `scripts/agent/{orchestrator,repl,session}.py` | Integration: single shared store instance | targeted wiring test | Pass |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | Doc consistency | `uv run python tools/check_docs_consistency.py --domain agent` | Pass |

## Risks
- **Risk**: Adding `storage_format` forces recreation of the production `session.sqlite` (fingerprint gate rejects the existing file; no migration path under current-schema-only). → **Mitigation**: documented as an explicit operational impact; `session_diagnostics` holds low-value auxiliary data; recreate is the repository's established archive-and-recreate path. Communicate the recreation to the owner before landing.
- **Risk**: Removing the public `encrypt` argument breaks callers/tests that pass it. → **Mitigation**: blast radius measured (`rg` over `tests/`); all such sites listed as targets; regression tests updated in Phase 2.
- **Risk**: `session.py` constructs its store without `ctx`, so injection wiring was initially uncertain. → **Mitigation**: wiring confirmed feasible in Step 8b (`AgentContext.__init__` builds `self.cfg` before `AgentSession()`); two feasible paths (thread config into `Session`, or consolidate onto the Orchestrator-owned instance) resolved in Phase 2.
- **Risk**: A decrypt-failed consumer silently receives ciphertext if `fetch()` is not updated. → **Mitigation**: `storage_format` classification in `fetch()` is a dedicated release unit (Phase 3) with an explicit acceptance criterion (`AC-4`).
- **Risk**: Changing `retention_days` semantics unexpectedly. → **Mitigation**: scope limited to type validation; the `<= 0 disables purge` runtime semantic is preserved (`UNK-03`).
- **Risk**: Injecting config into `AgentSession` changes its constructor, breaking the 40+ test sites that call `AgentSession()`. → **Mitigation**: resolve the injection path (thread `cfg.diagnostics` vs. consolidate onto the Orchestrator-owned shared instance) in Phase 2; any `AgentSession` test fixtures that must update are added to `Implementation Target Files` before freeze if the chosen path requires it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1–2 | Identify target issue; assess current issue against source | Completed | — | 2026-11-14 | All claims confirmed; Path B; baseline recorded |
| 3 | Inspect related files — task-size classification | Completed | — | 2026-11-14 | Full Path B inspection; consumer scan done |
| 4–7 | Map issue to plan; create plan; analyze unknowns/risks; add traceability | Completed | — | 2026-11-14 | Plan written; 3 non-blocking Unknowns; risks mitigated |
| 8a | Verify information completeness and traceability | Completed | — | 2026-11-14 | Structure checker: No findings; all info present & traceable |
| 8b | Validate and freeze Implementation Target Files | Completed | — | 2026-11-14 | All rows Verified; section Frozen; 3 overlaps compatible with rmcompat007 |
| 8c | Report outcome | Completed | — | 2026-11-14 | Pass |
| 9 | Final validation | Pending | — | — | After maintainer Unknown resolution |
| 10 | Move the issue | Pending | — | — | After Step 9 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261111-163701_diagstore002_diagnostic-store-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261114-161816
- **Related target files**: `scripts/agent/diagnostic_store.py`, `scripts/agent/config_dataclasses.py`, `scripts/agent/services/config_validators.py`, `scripts/agent/config_section_builders.py`, `scripts/db/schema_sql.py`, `scripts/agent/orchestrator.py`, `scripts/agent/repl.py`, `scripts/agent/session.py`, `tests/agent/test_diagnostic_store_security.py`, `tests/agent/test_diagnostic_store.py`, `tests/agent/test_config_dataclasses.py`, `tests/agent/test_llm_turn_runner.py`, `docs/23_agent/agent_09_01_data-layer-session-db.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Required Changes (inject validated config, drop per-op read) — Confirmed by repository evidence (`_load_diagnostics_config` at `diagnostic_store.py` 37-61) | `scripts/agent/diagnostic_store.py` | Phase 2 | AC-6 | `test_diagnostic_store.py`, `test_diagnostic_store_security.py` | Confirmed by repository evidence |
| REQ-001 | Problem; Required Changes | `scripts/agent/orchestrator.py` | Phase 2 | AC-6 | orchestrator wiring test | Confirmed by repository evidence |
| REQ-001 | Problem; Required Changes | `scripts/agent/repl.py` | Phase 2 | AC-6 | repl tests | Confirmed by repository evidence |
| REQ-001 | Problem; Required Changes (wiring feasible — `AgentContext.__init__` builds `self.cfg` before `AgentSession()`, context.py:389-395) | `scripts/agent/session.py` | Phase 2 | AC-6 | session tests | Confirmed by repository evidence |
| REQ-002 | Problem; Required Changes (bare `int()` coercion of `retention_days`; missing `__post_init__`) — Confirmed by repository evidence | `scripts/agent/config_dataclasses.py` | Phase 1 | AC-3 | `test_config_dataclasses.py` | Confirmed by repository evidence |
| REQ-002 | Problem; Required Changes | `scripts/agent/services/config_validators.py` | Phase 1 | AC-3 | new diagnostics validation tests | Confirmed by repository evidence |
| REQ-002 | Problem; Required Changes | `scripts/agent/config_section_builders.py` | Phase 1 | AC-3 | config-build tests | Confirmed by repository evidence |
| REQ-003 | Explicit in code (`encrypt=False` default); Problem | `scripts/agent/diagnostic_store.py` | Phase 2 | AC-2 | `test_diagnostic_store_security.py`, `test_diagnostic_store.py` | Confirmed by repository evidence |
| REQ-004 | Explicit in code (secret-check gated on no key + no filter failure); Problem | `scripts/agent/diagnostic_store.py` | Phase 2 | N/A: no dedicated AC (covered by AC-1 fail-closed) | `test_diagnostic_store_security.py` | Confirmed by repository evidence |
| REQ-005 | Explicit in code (filter failure proceeds with original); Problem | `scripts/agent/diagnostic_store.py` | Phase 2 | AC-1 | `test_diagnostic_store_security.py` (regress `test_filter_failed_carve_out_preserved`) | Confirmed by repository evidence |
| REQ-005 | Documentation Impact (accepted storage posture) | `docs/23_agent/agent_09_01_data-layer-session-db.md` | Phase 4 | AC-1 | docs consistency check | Confirmed by repository evidence |
| REQ-006 | Explicit in code (fetch leaves ciphertext on decrypt failure); Problem | `scripts/agent/diagnostic_store.py` | Phase 3 | AC-4 | `test_diagnostic_store.py` | Confirmed by repository evidence |
| REQ-006 | Persisted schema change (recreate-only; fingerprint gate rejects existing DB) | `scripts/db/schema_sql.py` | Phase 3 | AC-4 | `check_db_separation.py`, schema fingerprint test | Confirmed by repository evidence |
| REQ-006 | Documentation Impact | `docs/23_agent/agent_09_01_data-layer-session-db.md` | Phase 4 | AC-4 | docs consistency check | Confirmed by repository evidence |
| REQ-007 | Problem (transport-error details persisted); Required Changes | `scripts/agent/diagnostic_store.py` | Phase 4 | N/A: no dedicated AC (part of fail-closed, AC-1) | unit test: transport-error sanitization | Confirmed by repository evidence |
| REQ-008 | Required Changes (single shared store) | `scripts/agent/orchestrator.py` | Phase 2 | N/A: no dedicated AC | producer-wiring test | Confirmed by repository evidence |
| REQ-008 | Required Changes (single shared store) | `scripts/agent/session.py` | Phase 2 | N/A: no dedicated AC | producer-wiring test | Confirmed by repository evidence |
| REQ-009 | Explicit in code (`session_persister.py` catches `RuntimeError`/`sqlite3.Error`); Dependencies | `scripts/agent/diagnostic_store.py` | Phase 2 | AC-5 | `session_persister.py` non-fatal behavior | Confirmed by repository evidence |
