# Correct stale statements and minor defects in reference documents and code comments

## Priority
Low

## Summary
Fix small stale or wrong statements in reference documents and one code docstring (and make an empty `sqlite_vec_so` a startup error, as decided by the maintainer) that were found during the ADR review (database inventories, DLQ artifact format, delivery semantics wording, duplicated table rows, broken headings, wrong cross-references, an ambiguous function name), so that the documents match the code and the ADRs.

## Background
- Source: `memo-issue.md` items L-04 and L-06, re-checked against current source on 2026-11-09. None of these changes behavior except where marked; each can mislead a reader.
- `Explicit in documentation`, confirmed by search on 2026-11-09:
  - `docs/24_eventbus/eventbus_01_system-overview.md` says DLQ events are written as JSONL files; the memo says DLQ artifacts are per-event `{event_id}.json` (`Needs confirmation` against `scripts/eventbus/dlq.py`).
  - `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` cites "18. Area Dependency Graph Validation", while `governance_04` numbers that check `### 19`.
  - `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` mentions `requested_target` twice (the memo reports a duplicate table row).
  - `docs/23_agent/agent_09_01_data-layer-session-db.md` mentions `agent.db` (the memo says `/opt/llm/agent.db` should read session.sqlite; `Needs confirmation` of the exact sentence).
- `Explicit in code`: `scripts/mcp_servers/server.py` has a docstring saying "Tool dispatch helpers live in mcp/dispatch.py" and "Audit log helpers live in mcp/audit.py" while the modules are `scripts/mcp_servers/dispatch.py` and `scripts/mcp_servers/audit.py`. Two functions named `attach_auth_middleware` exist: `scripts/mcp_servers/server.py` and `scripts/eventbus/auth.py`.
- `Explicit in code`: `scripts/db/config.py` documents `sqlite_vec_so` as optional ("empty string means vec extension is not required") while the memo says an empty value should fail at startup instead of at the first vec-table access (design decision; see Unresolved Questions).
- `Needs confirmation` (not found by this review's search, so they may already be fixed): the "Four DB files exist" inventory in `db_01` (the remaining "Four Databases" hits are the ADR-008 title and the index), "never received twice" in `eventbus_03` (a search for the phrase found nothing), and the other memo items (`db_03` recreation-impact table lacking rag.sqlite and session.sqlite; `db_07` section 11a listing four EventBus tables including `dlq_outbox`; the integrity procedure note about JSONL line count versus DB rows; `eventbus_03` broken headings; `mcp_03_03` merged heading and the DEGRADED state in the state diagram; the `Z` versus `+00:00` timestamp suffix policy; the meaning of EventBus `liveness` versus MCP liveness; the Document Guide and Index consistency on unresolved deviations; the plaintext-diagnostics decision in `agent_09_01`; the "Canonical Source" wording for code in `agent_09_01` (GV-012)).

- Verification result (2026-11-11, adversarial check against current source):
  - `Confirmed by repository evidence` (still wrong): `eventbus_01` line 37 says DLQ events are written as JSONL files, while DLQ artifacts are per-event `{event_id}.json` files (`eventbus_03` Reconciliation, `dlq.py`); `governance_05` lines 102-103 cite "18. Area Dependency Graph Validation" while `governance_04` numbers it `### 19.`; `mcp_02_03` lines 38 and 42 are two `requested_target` rows; `server.py` docstring lines 7-8 name `mcp/dispatch.py` and `mcp/audit.py`; `agent_09_01` line 80 names code as "Canonical Source" (GV-012); `db_07` section 11a queries "its three tables" of `eventbus.sqlite`, but `schema.sql` defines four (`events`, `consumer_delivery`, `consumer_offsets`, `dlq_outbox`); the `mcp_03_03` state diagram omits `DEGRADED` (defined in `McpServerHealthState` and in its own table); `adr_01_index.md` line 39 cites ADR-006 as an example that holds open deviations, but every ADR's Known Deviations is "Not applicable".
  - Refuted or already correct: "agent.db" in `agent_09_01` (no match); "never received twice" (no match anywhere in `docs/`); `eventbus_03` broken headings and the `mcp_03_03` merged heading (the heading lists are clean); `db_03` recreation table (it lists `rag.sqlite` and `session.sqlite`); `governance_00_document-guide.md` (it has no deviation text to reconcile). The "Four DB files exist" sentence in `db_01` is accurate for the four platform databases but omits the derived `mdq.sqlite` that `db_03` names (`Needs confirmation`: whether to say "four platform databases").
  - `Confirmed by repository evidence` (decisions and gaps): the EventBus writes `Z` timestamps (`now_iso()` in `json_utils.py`, `dlq.py`) and no document states the format; `eventbus_10` defines `liveness` as "the DLQ sweep task is running" while `mcp_02_02` defines it as an overridable process-state flag, so the two meanings differ and neither document points at the other; the two `attach_auth_middleware` functions differ in behavior: the MCP one authenticates with a Bearer token (`server.py`), while the EventBus one only injects `X-Request-Id` and leaves authentication to endpoint dependencies (`auth.py`); `agent_09_01` lines 70-76 hold the plaintext-diagnostics storage decision (owner decision 2026-10-25), which needs an ADR and a maintainer approval to move; `eventbus_05` Cleanup Procedure does not say that `events.jsonl` keeps more lines than the DB after a manual deletion (the issue's "integrity procedure note").
  - Empty `sqlite_vec_so`: `DbConfig.sqlite_vec_so` defaults to `""`, `SQLiteHelper` is built per use (`SQLiteHelper("session")` at every call site), and its target-based constructor reads `db_cfg.sqlite_vec_so` and fails only at the first vec load (`_load_vec_extension`). The processes that read the DB config are the Agent (agent.toml), the ingester and crawler (`build_db_config()` users), and rag-pipeline-mcp, whose posture check already reports an empty `sqlite_vec_so` as FAILED and refuses to bind. The Agent has an existing startup config validator for agent.toml (`ProductionConfigValidator.validate()`, which already rejects an empty `allowed_root`, and lists `sqlite_vec_so` as a known key), so that is the natural place for the startup error; `build_db_config()` is the shared place for the other processes. Components that run without the extension use an explicit `db_path` helper (the explicit path derives load behavior from its own `sqlite_vec_so` argument) and are unaffected. `tests/conftest.py` deliberately tolerates a missing sqlite-vec library on CI (the vec tables are skipped), so the check must test for an empty value, not for the file's existence.
  - Open: which of the memo items must still be fixed beyond the above cannot be decided without the maintainer for the plaintext-diagnostics ADR move and the `Z` timestamp assumption.

## Problem
- Stale inventories and wrong file names send operators to files that do not exist during an incident.
- Wrong delivery-semantics wording ("never received twice") contradicts the at-least-once design and can lead consumers to skip idempotency.
- An ambiguous function name and a wrong docstring path add small, avoidable confusion.

## Reason for Change
- Low severity; none blocks other work. Bundle them so one documentation pass fixes them together. Timing: after the history wording issue in this batch to avoid editing the same documents twice.

## Implementation Intent
- The reference documents match the code and the ADRs, down to file names, counts (where the policy allows), and wording. Each item is confirmed against current source before it is edited; items already fixed are skipped.

## Target Files or Areas
- `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
- `docs/23_agent/agent_09_01_data-layer-session-db.md`
- `docs/24_eventbus/eventbus_01_system-overview.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`
- `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `docs/22_mcp/mcp_03_03_transport-and-health.md`
- `docs/00_governance/governance_04_documentation-checks.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, `docs/00_governance/governance_00_document-guide.md`, `docs/10_adr/adr_01_index.md`
- `scripts/mcp_servers/server.py` (docstring and, if renamed, the function), `scripts/eventbus/auth.py`, `scripts/db/config.py`, `scripts/db/helper.py`, `tests/db/` (empty `sqlite_vec_so` startup error)

## Required Changes
- For each memo item listed in Background, confirm it against current source and fix it only if it is still wrong: inventories (`db_01`, `db_03`, `db_07` 11a, `agent_09_01`), DLQ artifact format (`eventbus_01`), at-least-once wording and headings (`eventbus_03`), the duplicate `requested_target` row (`mcp_02_03`), the merged heading and DEGRADED state (`mcp_03_03`), the governance cross-reference (`governance_05`), and the Document Guide / Index consistency.
- Document the integrity-procedure note (manual deletion leaves more JSONL lines than DB rows) if the procedure still applies.
- Document the timestamp suffix policy as `Z` (assumption above), and add the startup failure for an empty `sqlite_vec_so` (maintainer decision of 2026-11-09), scoped to processes that open rag.sqlite or session.sqlite, with tests.
- Fix the `server.py` docstring module paths.
- Rename one of the two `attach_auth_middleware` functions to remove the ambiguity (update imports and tests), or document the distinction.
- Clarify the meaning of EventBus `liveness` against MCP liveness.
- Move the plaintext-diagnostics decision in `agent_09_01` into an ADR, and stop calling code the "Canonical Source" (GV-012), if still present.

## Constraints
- Docs content policy and English-only rule apply; do not copy config values or implementation locations into documents.
- A function rename needs the impact-radius check from `rules/toolchain.md` and must keep import-layer contracts (`lint-imports`).
- Moving a decision into an ADR needs the ADR process and a maintainer approval (see the governance-ledger issue); otherwise record it as a Needs Confirmation item.
- Do not change EventBus or MCP runtime behavior. The empty `sqlite_vec_so` error must not break components that legitimately run without the extension (see Unresolved Questions).

## Acceptance Criteria
- Every listed statement that is still wrong matches the code and the ADRs after the change; items already correct are recorded as such in the PR.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py` for each touched domain, and `check_needs_confirmation_inventory.py` pass.
- A process that opens rag.sqlite or session.sqlite fails at startup with an explicit error when `sqlite_vec_so` is empty, instead of at the first vec-table access; a test proves it.
- If a function is renamed: `rg -n "attach_auth_middleware"` shows distinct names for the two functions, and tests plus `lint-imports` pass.

## Testing Expectations
- Add a startup test for the empty `sqlite_vec_so` error in `tests/db/` (and the affected startup tests). Documentation checkers above; for a function rename, `uv run pytest tests/mcp_servers tests/eventbus -v` and the standard validation sequence from `rules/toolchain.md`.

## Documentation Impact
- The documents listed under Target Files change. State current behavior, intent, and failure behavior only.

## Out of Scope
- History wording removal (separate issue in this batch).
- Any behavior change to EventBus or MCP; the only startup behavior change is the empty `sqlite_vec_so` error.
- Checker changes.

## Dependencies
- Depends on: none (schedule after `issues/20261109-113318_adrrev017_docs-history-wording.md` to avoid editing the same documents twice).
- Related: `issues/20261109-112538_adrrev002_agent-eventbus-coupling.md` and `issues/20261109-112715_adrrev005_schema-fingerprint-unify.md` (they also change `db_01` and `db_07`).

## Unresolved Questions
- Decided by the maintainer on 2026-11-09: an empty `sqlite_vec_so` is a startup error (not an optional setting). `Explicit in code`: `scripts/db/config.py` currently defaults it to an empty string ("vec extension not required"), `scripts/db/helper.py` raises `ValueError` only at the first vec load, and `config/agent.toml` and `config/ingester.toml` both set a value. `Needs confirmation`: which components may legitimately run without the extension (for example the workflow-only or eventbus paths) so that the startup check is scoped to the processes that open rag.sqlite or session.sqlite.
- `Explicit in code`: the EventBus writes timestamps with `Z`; the only `+00:00` producer found is the Agent-side client that the Agent-side EventBus coupling issue removes. Assumption: document `Z` as the EventBus timestamp format; confirm with the maintainer.
- Resolved by verification: which memo items are already fixed (see the verification result above).
- `Needs confirmation` (maintainer): move the plaintext-diagnostics decision into an ADR (needs approval; until then it is recorded as a pending item); say "four platform databases" in `db_01`; keep the two `attach_auth_middleware` names with a documented distinction rather than a rename (the plan's default).

## AI Implementation Instruction
- Confirm each item against current source before editing; skip items already fixed and say so.
- Make minimal, targeted edits; do not rewrite surrounding text.
- Do not decide the open questions; list them in the report.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-113421
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/23_agent/agent_09_01_data-layer-session-db.md`, `docs/24_eventbus/eventbus_01_system-overview.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `docs/22_mcp/mcp_03_03_transport-and-health.md`, `docs/00_governance/governance_04_documentation-checks.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, `docs/00_governance/governance_00_document-guide.md`, `docs/10_adr/adr_01_index.md`, `scripts/mcp_servers/server.py`, `scripts/eventbus/auth.py`, `scripts/db/config.py`
