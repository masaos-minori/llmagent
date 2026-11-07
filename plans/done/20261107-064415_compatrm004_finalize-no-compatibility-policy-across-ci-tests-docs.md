# Plan: Finalize the no-compatibility policy across CI, tests, documentation, and runbooks

## Goal
- After compatrm001/002/003 land, consolidate the compatibility checker and its exception manifest around the final deleted-symbol set, make CI and pre-commit enforce one blocking policy, rewrite all remaining active documentation and runbooks to the current-only policy, and align regression tests around rejection instead of migration.

## Priority
Medium

## Scope
- **In-Scope**: `tools/check_compat_shims.py` removed-name pattern consolidation (the complete compatrm001/002/003 deleted set plus migration-claim doc patterns) and production-exception-zero enforcement; `tools/compat_exceptions.toml` manifest cleanup (delete the three `migration` entries, reclassify `check-compat-shims-source`, keep narrowly scoped `fixture` entries, retain the separate `symbol_stage_allowance` table); checker self-tests; pre-commit and CI hook alignment verification; active-documentation rewrite of the files compatrm001/002/003 do not own (ADRs, MCP policy docs, agent operations runbook, db_03_07) plus a residual sweep of the docs they do own; a repository-wide no-compatibility gate test.
- **Out-of-Scope**: Any change to production modules deleted or modified by compatrm001/002/003 (those Plans own them), replacing Git history with an active archive document, adding deprecation periods, and adding compatibility exceptions without a separate approved policy change.
- **Dependencies**: Must start after `issues/20261106-125142_compatrm001_...`, `issues/20261106-125143_compatrm002_...`, `issues/20261106-125144_compatrm003_...` have established the final deleted-symbol and deleted-module set (their Plans are frozen; this Plan's implementation lands last).
  - **Depends on**: N/A: this is the final issue of the initiative; the three implementation plans are prerequisites for execution order, not for freezing this Plan.

## Background
- Initiative issue M-2 of `memo-issue.md`, fourth and final. Verified 2026-11-07 against current source:
  - `tools/check_compat_shims.py` exposes `--check-removed-names`, `--check-doc-symbols`, `--allowlist`; `COMPAT_PATTERNS` (line 39) holds the always-on literal/import regexes, including the `db.workflow_schema` entries (lines 81-84) although `scripts/db/workflow_schema.py` no longer exists; the `_update_null_fill` and other confirmed-removed-name entries live in `_REMOVED_NAME_PATTERNS` (lines 334-389, applied to `*.md` only, gated by `--check-removed-names` with the `_is_historical_context()` exemption); the approval-stage entries already live in `COMPAT_PATTERNS` itself (lines 62-74); the syntax-tree rules are the functions `check_mcp_health_reexport_import()` (line 430) and `check_gateless_discovery_construction()` (line 451). `load_exceptions()` (line 157) and `validate_exceptions()` (line 181) enforce required fields and a known `category` per manifest entry but do not cap production categories.
  - `tools/compat_exceptions.toml` holds 21 `[[compatibility_exceptions]]` entries (structured count; the 22nd grep match is a header comment): 3 `migration` (`mcp-00-document-guide`, `mcp-07-tool-schema-export-policy`, `db-03-migration-and-scaling`), 1 `compatibility` (`check-compat-shims-source`, line 204, the checker's self-reference), and 17 `fixture` (negative-test files, test reset hooks). `symbol_stage_allowance` (line 219) is already a dedicated table for names defined outside `scripts/` (stdlib/third-party/conceptual), not a backward-compatibility exception.
  - CI `.github/workflows/backward-compat-check.yml` (line 39) and pre-commit `.pre-commit-config.yaml` (line 38) already invoke the identical blocking option pair `--check-removed-names --check-doc-symbols`. No task-runner configuration exists (verified: no `Makefile`, `makefile`, or `justfile` at repository root) — the Issue's second Unresolved Question is resolved: none.
  - Active-document terminology inventory (grep, excluding `done/`): removed-symbol/migration-claim text remains in `docs/10_adr/adr_01_index.md` (line 63 dbmig001 amendment summary), `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (lines 60, 73-75 Amendment, 137, 363), `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` (line 54 `SELECT * FROM workflow_schema_version` runbook command; line 93 "Re-run the deployment scripts to apply migrations" response), `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (lines 46-47, 74-78 migration-ledger references), `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (sections 8a/8b/9/10/11 migration contract, CLI contract, and the "Removal condition: Never" policy table), `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (lines 147, 177 `policy: migrate`, 184 `ledger` drill fields), `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, and `docs/24_eventbus/eventbus_08_reference_api.md` (lines 130-131 list `scripts/eventbus/migrate.py main` and `scripts/eventbus/migrations.py verify_backup` as live API rows — stale once compatrm001 deletes both scripts, and no prerequisite plan owns this document; row added during adversarial verification).
  - Ownership split from the three prerequisite Plans: compatrm001 owns `docs/41_db/db_01`, `db_02`, `db_03` (core rewrite), `db_07` (§11), `eventbus_06`; compatrm002 owns `adr_02_04_013`; compatrm003 owns `db_04`, `db_05`, `eventbus_05`, `scripts/eventbus/README.md`. This Plan owns everything the three do not, plus a residual-terminology sweep of the shared files after they land (see Assumptions for the compatibility judgments).
  - Test fixtures that intentionally mention removed names are covered by the 17 `fixture` manifest entries (e.g. `check-compat-shims-test-data` → `tests/tools/test_check_compat_shims.py`, `cmd-registry-note-removal-test`, `removed-commands-test`); these are negative-test data and stay, scoped as the Issue requires.
  - `symbol_stage_allowance` necessity (Issue Unresolved Question 1): resolved as **still needed** — its names (`copy2`, `isinstance`, `to_thread`, etc.) are stdlib/third-party references unrelated to the removed machinery; it is already a dedicated table separate from `[[compatibility_exceptions]]`, satisfying "dedicated configuration".
  - The checker self-tests `tests/tools/test_check_compat_shims.py` iterate `COMPAT_PATTERNS` generically and pin the approval-stage subset; adding the consolidated compatrm patterns requires new true-positive and historical-text false-positive self-tests (Issue's Align automation).

## Problem
- If code is removed without updating these controls, deleted behavior can be reintroduced or documentation can keep promising unsupported upgrade paths; deleting every fixture reference would weaken the tests that intentionally detect removed names.

## Reason for Change
- One enforceable policy needs the exceptions, the checks, the documentation, and the tests to agree.

## Implementation Intent
- Create one enforceable policy: production code has no backward-compatibility or migration exceptions; active documentation describes only the current supported schema and APIs; history stays in version control, not in active specifications; negative tests may mention deleted names only in narrowly scoped test data; CI and pre-commit reject reintroduction of deleted symbols, modules, import paths, or migration claims.

## Requirements
- `REQ-001`: Consolidate `tools/check_compat_shims.py` `COMPAT_PATTERNS` into one final set targeting the complete deleted set of compatrm001/002/003: `_TOKEN_PRINCIPAL_MAP`, `_populate_token_maps`, `principal_map` (word-boundary), `verify_backup_by_path`, `shared.db_migrations`, `db.migrations_workflow`, `eventbus.migrations`, `eventbus.migrate`, `migrate_db.py`, `schema_migrations`, `workflow_schema_version`, `WORKFLOW_SCHEMA_VERSION`, `from db.store import` / `import db.store`, `from eventbus.db import` / `import eventbus.db`, plus the two-argument `nack_event(` call form — superseding the per-issue incremental additions of the 002/003 Plans with the final consolidated configuration.
- `REQ-002`: Add documentation-claim patterns to the checker: active docs that assert automatic migration, registered migration paths/ledgers, migration CLIs, dry-run/apply migration contracts, or legacy-database upgrade support must fail `--check-removed-names` (these phrase patterns land in `_REMOVED_NAME_PATTERNS`, the `--check-removed-names` path; the REQ-001 symbol/import patterns land in `COMPAT_PATTERNS`).
- `REQ-003`: Clean the manifest: delete the three `migration` entries once their docs are rewritten; move `check-compat-shims-source` out of the production `compatibility` category into a dedicated checker-self-reference allowance outside the production exception model; keep only narrowly scoped `fixture` entries; enforce zero production-category (`compatibility` / `migration` / `fallback`) entries in `validate_exceptions()`.
- `REQ-004`: Keep CI (`.github/workflows/backward-compat-check.yml`) and pre-commit (`.pre-commit-config.yaml`) invoking the identical blocking checker option pair; no task-runner configuration exists to align (verified).
- `REQ-005`: Rewrite the active documents the three prerequisite Plans do not own: `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (amendment superseded by the no-migration policy), `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` (runbook commands and failure-response wording), `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/22_mcp/mcp_00_document-guide.md`, `docs/22_mcp/mcp_07_tool_schema_export_policy.md` (remove the `_MCP_TOOLS` → `TOOL_LIST` migration framing), and the residual sections of `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (sections 8c-11 policy table) and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (lines 147/177/184 drill-policy fields) that compatrm001's rewrite does not claim, and `docs/24_eventbus/eventbus_08_reference_api.md` (lines 130-131 live API rows for the `scripts/eventbus/migrate.py` / `scripts/eventbus/migrations.py` modules deleted by compatrm001).
- `REQ-006`: Add the current policy text wherever the rewrite applies: only the current schema is supported; no automatic migration or version stamping; schema mismatch is fail closed; operators may archive an incompatible database and must recreate it manually; no data-transfer facility; removed APIs and import aliases are unsupported; an archive is not a migration source.
- `REQ-007`: Regression-test alignment: verify (not re-implement) that migration-success tests are gone and rejection tests exist with the no-mutation check (compatrm001 delivers them), and add a repository-wide gate test asserting: zero production-category manifest entries, the consolidated removed names have no live references, `AuthzGeneration`-only auth state, mandatory `consumer_id` for NACK, removed import paths rejected by the checker, and rotation/archive/recovery regression tests pass.
- `REQ-008`: Add checker self-tests for true positives and historical-text false positives of the consolidated patterns to `tests/tools/test_check_compat_shims.py`.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed 2026-11-07: every row `Verified` against current
source; overlaps with Frozen prerequisite plans judged compatible (see Assumptions);
`tools/check_workitem_structure.py` clean.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tools/check_compat_shims.py | MODIFY | Consolidated `COMPAT_PATTERNS` for the final deleted set (REQ-001), doc-claim patterns (REQ-002), production-exception-zero enforcement in `validate_exceptions()` (REQ-003) | REQ-001, REQ-002, REQ-003 / AC-001, AC-002, AC-006 | Line 39 (`COMPAT_PATTERNS`), lines 81-84 (`db.workflow_schema` import regexes), lines 157/181 (`load_exceptions()` / `validate_exceptions()`), line 334 (`_REMOVED_NAME_PATTERNS`), lines 430/451 (syntax-tree rule functions) verified by grep | tests/tools/test_check_compat_shims.py (MODIFY) | Verified |
| tools/compat_exceptions.toml | MODIFY | Delete 3 `migration` entries; reclassify `check-compat-shims-source` (line 204) out of the production model; keep the 17 `fixture` entries; `symbol_stage_allowance` table (line 219) retained as dedicated config | REQ-003 / AC-001 | 21 entries enumerated 2026-11-07 (adversarial recount) | tests/tools/test_check_compat_shims.py (MODIFY) | Verified |
| tests/tools/test_check_compat_shims.py | MODIFY | Add true-positive and historical-text false-positive self-tests for the consolidated patterns | REQ-008 / AC-002 | Fixture manifest entry `check-compat-shims-test-data` | — | Verified |
| tests/tools/test_no_compatibility_policy_gate.py | CREATE | Repository-wide initiative gate test: zero production-category manifest entries, zero live references to consolidated removed names, mandatory-consumer NACK signature, `AuthzGeneration`-only state, checker blocking on reintroduction | REQ-007 / AC-002, AC-004, AC-005, AC-007 | Replaces ad-hoc grep verification with a CI test | — | Verified |
| .pre-commit-config.yaml | VERIFY (no edit unless divergence found) | Hook already invokes `--check-removed-names --check-doc-symbols` (line 38); confirm identity with CI after checker consolidation | REQ-004 / AC-003 | Line 38 grep-verified | — | Verified |
| .github/workflows/backward-compat-check.yml | VERIFY (no edit unless divergence found) | CI already invokes the same option pair (line 39) | REQ-004 / AC-003 | Line 39 grep-verified | — | Verified |
| pyproject.toml | VERIFY (no edit expected) | Issue lists it under automation alignment; verified no checker invocation exists in it — no change unless a task-runner addition is requested | REQ-004 / AC-003 | grep: no `check_compat_shims` reference | — | Verified |
| docs/10_adr/adr_01_index.md | MODIFY | Line 63 dbmig001 amendment summary and ADR-008 row status must state the superseded no-migration policy | REQ-005, REQ-006 / AC-004 | Lines 52, 63 grep-verified | tools/check_adr_invariant_matrix.py (existing CI) | Verified |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | MODIFY | Lines 60 migration contract, 73-75 dbmig001 Amendment (supersession note), 137 schema-repair vocabulary, 363 re-evaluation trigger must describe current-only policy | REQ-005, REQ-006 / AC-004 | grep-verified | governance-docs-consistency CI (existing) | Verified |
| docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md | MODIFY | Runbook command `SELECT * FROM workflow_schema_version` (line 54) and "Re-run the deployment scripts to apply migrations" (line 93) replaced with the archive-and-recreate procedure | REQ-005, REQ-006 / AC-004, AC-005 | Lines 54, 93 grep-verified | — | Verified |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | MODIFY | Lines 46-47, 74-78 cite the workflow migration ledger and `migrations_workflow.py` as the tables' provenance | REQ-005 / AC-004 | grep-verified | docs consistency CI (existing) | Verified |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | MODIFY (residual sweep, after compatrm001's rewrite) | Sections 8c-11: migration contract text, CLI contract, "Removal condition: Never" policy table, minimum-supported-schema policy — residual content compatrm001's core rewrite does not claim | REQ-002, REQ-005, REQ-006 / AC-004 | Lines 29-94 verified by read; overlap judgment in Assumptions | tools/check_compat_shims.py (doc-claim patterns) | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | MODIFY (residual sweep, after compatrm001) | Lines 147 (user_version fail-start sentence), 177 (`policy: migrate` field), 184 (`ledger` drill fields) describe removed machinery in the drill/reference sections | REQ-005 / AC-004, AC-005 | Lines 147/177/184 grep-verified; §11 itself owned by compatrm001 | — | Verified |
| docs/22_mcp/mcp_00_document-guide.md | MODIFY | Remove the migration-framing row (line 94) and content covered by the deleted `mcp-00-document-guide` manifest exception | REQ-003, REQ-005 / AC-001, AC-004 | Manifest entry line 24 + doc line 94 | tools/check_compat_shims.py | Verified |
| docs/22_mcp/mcp_07_tool_schema_export_policy.md | MODIFY | Remove the `_MCP_TOOLS` → `TOOL_LIST` migration policy framing (line 27 legacy-mention context) covered by the deleted manifest exception | REQ-003, REQ-005 / AC-001, AC-004 | Manifest entry line 33 + doc lines 27-33 | tools/check_compat_shims.py | Verified |
| docs/24_eventbus/eventbus_08_reference_api.md | MODIFY | Remove the `scripts/eventbus/migrate.py main` and `scripts/eventbus/migrations.py verify_backup` API rows (lines 130-131) and the scripts-directory description referencing `migrate.py`/`migrations.py` as live modules | REQ-001, REQ-005 / AC-004 | Lines 130-131 grep-verified; no prerequisite plan owns this document | tools/check_compat_shims.py (doc-symbol sweep) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md | Frozen prerequisite: deleted-symbol/module set, rejection test suite, and its docs rows (db_01, db_02, db_03 core, db_07 §11, eventbus_06) this Plan must not re-claim | REQ-001, REQ-005 / whole Plan |
| plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md | Frozen prerequisite: removed auth names and their patterns; consolidated set supersedes its incremental checker row | REQ-001 |
| plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md | Frozen prerequisite: facade import paths and NACK call-form patterns; docs rows (db_04, db_05, eventbus_05) owned there | REQ-001, REQ-005 |
| docs/41_db/db_01_architecture_and_schema-overview-and-config.md, docs/41_db/db_02_architecture_and_schema-schema-reference.md, docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md, docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md, docs/41_db/db_05_api_and_operations-protocol-and-backend.md, docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md, docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md, scripts/eventbus/README.md | Owned by compatrm001/002/003; this Plan only sweeps them for residual removed-terminology via the grep gate (AC-004) — no target rows, to keep frozen scopes disjoint | REQ-005 / AC-004 |
| tests/db/test_create_schema.py | Issue target area; verified it is owned and rewritten by compatrm001 (marker-absence and rejection expectations) — this Plan adds no edit, only the gate test asserts its post-state | REQ-007 |
| rules/env.md, rules/toolchain.md | Validation sequence and DB paths for the gate test and isolated recreate rehearsal | REQ-007 / Validation plan |
| docs/00_index.md | Task-scope mapping used to name the documentation rows (MCP row, DB row) | REQ-005 |

## Acceptance Criteria
- AC-001: Production compatibility and migration exceptions are zero (`validate_exceptions()` fails any `compatibility` / `migration` / `fallback` entry); fixture allowances and the documentation symbol-stage allowance are configured separately from the production policy (REQ-003).
- AC-002: Deleted names, modules, and imports from the consolidated set fail CI when reintroduced; checker self-tests prove true positives and historical-text false positives (REQ-001, REQ-002, REQ-008).
- AC-003: CI and pre-commit use the same blocking checker options (REQ-004).
- AC-004: Active documentation contains no supported backward-compatibility or migration behavior; the repository-wide grep gate for the removed terminology and symbols returns nothing outside `done/` archives, negative-test fixtures (manifest-covered), and the checker's own pattern literals (REQ-002, REQ-005, REQ-006).
- AC-005: Tests no longer expect legacy data to be upgraded or preserved; rejection tests verify incompatible database files remain unchanged (delivered by compatrm001, gate-asserted here) (REQ-007).
- AC-006: Current-schema creation and startup tests pass; rotation, archive, and recovery regression tests pass (gate-asserted) (REQ-007).
- AC-007: Code, tests, documentation, CI, and runbooks describe one consistent current-only policy; the initiative gate test passes and the complete test suite passes (REQ-007).

## Tests
- `uv run python -m tools.check_compat_shims --check-removed-names --check-doc-symbols` clean on the final tree; failing on a seeded reintroduction of each consolidated name (self-test pattern data only) (AC-002).
- Checker self-tests: for every consolidated pattern, a true-positive fixture and a historical-text false-positive case (ADR amendment supersession wording must not trip the doc-claim patterns) (AC-002).
- `tests/tools/test_no_compatibility_policy_gate.py`: manifest-category zero-production assertion (unit), removed-name live-reference scan (unit), NACK signature inspection via `inspect.signature` (unit), checker blocking behavior (integration) (AC-002, AC-004, AC-005, AC-007).
- Rejection-test confirmation (delivered by compatrm001): legacy workflow/eventbus rejection, unversioned rejection, malformed current-version rejection, each with database-file-hash-unchanged verification (AC-005).
- Documentation grep gate executed by the gate test and by `--check-removed-names`/`--check-doc-symbols`; run the documentation checkers `routing.md` names for the edited `docs/` files (ADR invariant matrix, governance/MCP/DB consistency workflows) (AC-004).
- Isolated runbook rehearsal: follow `docs/41_db/db_07` section 11 recreate procedure against a scratch-database copy under `/tmp/opencode` (never `/opt/llm/`), per `rules/persisted-schema-change.md` (AC-006).
- Full suite `uv run pytest tests/` plus pre-commit run locally and the complete CI workflow (AC-003, AC-007).

## Documentation Impact
Yes: this Plan is the documentation rewrite itself. Per `docs/00_index.md` "Document References by Task": the ADR rows (ADR index, ADR-008), the MCP rows (`mcp_00`, `mcp_07`), the DB rows (`db_03`, `db_07` residual), the eventbus reference API row (`eventbus_08`), and the agent operations row (`agent_10_04`). Documents are written in English (`skills/DESIGN.md` Output language); no configuration values or implementation counts are copied into them.

## Assumptions
- Overlap judgments (Step 8b, all against Frozen prerequisite Plans; this Plan lands after all three per the Issue's Dependencies):
  - `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (also in compatrm001): compatible — compatrm001 performs the core rewrite (sections 8a/8b lifecycle + runbook); this Plan sweeps sections 8c-11 (policy table, CLI contract, contract text) which compatrm001's row does not claim. Sequencing: 001 first, then this Plan re-reads the file and edits only residual text.
  - `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (also in compatrm001): compatible — compatrm001 owns §11 policy text; this Plan owns lines 147/177/184 drill/reference fields. Same file, disjoint sections, 001 first.
  - `tools/check_compat_shims.py` (also in compatrm002 and compatrm003): compatible — 002/003 add their issue-scoped patterns; this Plan consolidates the same `COMPAT_PATTERNS` dict into the final set after both land (REQ-001 supersedes their incremental rows; 002/003 already record that consolidation stays here).
  - `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`: excluded from this Plan's table (owned by compatrm002); this Plan only grep-sweeps it.
- Docs owned entirely by compatrm001/003 (`db_01`, `db_02`, `eventbus_06`, `db_04`, `db_05`, `eventbus_05`, `scripts/eventbus/README.md`) are kept out of this Plan's frozen table; residual terminology in them is caught by the AC-004 grep gate and corrected inside the owning Plan's scope if found (implementation-time note, not a new target row). Exception: `docs/24_eventbus/eventbus_08_reference_api.md` is owned by no prerequisite plan and is therefore a target row of this Plan (row 16, added during adversarial verification).
- `symbol_stage_allowance` is retained (Issue Unresolved Question 1 resolved: needed for stdlib/third-party doc symbol references; already separate dedicated-table configuration, satisfying the Issue's "move ... if it remains necessary").
- No task-runner configuration exists (Issue Unresolved Question 2 resolved: no `Makefile`/`makefile`/`justfile`; `pyproject.toml` holds no checker invocation) — kept as a verify-only target row.
- "Production exceptions zero" is enforced by treating `compatibility` / `migration` / `fallback` categories as production-policy categories in `validate_exceptions()`; `fixture` and the separate allowance table remain permitted. This is a checker behavior change, so it follows `routing.md` "Adding a new tool" guidance for `tools/check_compat_shims.py` modifications (constraint honored: the checker row cites the existing test file and TOOL_DESCRIPTIONS update in Phase 4).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the checker's existing history/resolved-context exclusion covers the ADR-008 supersession wording once rewritten, or whether the doc-claim patterns need line-level exemption semantics | Checker's exclusion logic for ADR text not fully enumerated (only the `ToolRouteResolver`+`server_configs` denial-line precedent verified) | Implement the ADR rewrite first, run the checker, and choose between supersession phrasing that passes and a narrowly scoped pattern refinement | False |
| UNK-02 | Exact live-reference count of `schema_migrations` / `workflow_schema_version` remaining in docs after compatrm001 lands (prerequisites not yet implemented at plan time) | 001/002/003 are planned, not landed | The gate test (REQ-007) is authored against the post-001/002/003 tree; run it in Phase 4 after all three implementations complete | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tools/check_compat_shims.py | MODIFY | CI + pre-commit blocking behavior | 10 | 1 | No (tools/ is not deployed) |
| tools/compat_exceptions.toml | MODIFY | checker exception model | 6 | 1 | No |
| tests/tools/test_check_compat_shims.py | MODIFY | checker self-tests | 5 | 1 | No |
| tests/tools/test_no_compatibility_policy_gate.py | CREATE | new CI gate | — | — | No |
| .pre-commit-config.yaml | VERIFY | local hook parity | 3 | 1 | No |
| .github/workflows/backward-compat-check.yml | VERIFY | CI gate parity | 2 | 1 | No |
| pyproject.toml | VERIFY | none expected | 8 | 1 | No |
| docs/10_adr/adr_01_index.md | MODIFY | ADR index status | 7 | 1 | Yes — docs sync |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | MODIFY | DB architecture ADR | 6 | 1 | Yes — docs sync |
| docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md | MODIFY | agent ops runbook | 4 | 1 | Yes — docs sync |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | MODIFY | table provenance doc | 3 | 1 | Yes — docs sync |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | MODIFY (residual) | DB policy doc | 9 | 1 | Yes — docs sync |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | MODIFY (residual) | DB runbook | 8 | 1 | Yes — docs sync |
| docs/22_mcp/mcp_00_document-guide.md | MODIFY | MCP doc index framing | 5 | 1 | Yes — docs sync |
| docs/22_mcp/mcp_07_tool_schema_export_policy.md | MODIFY | MCP export policy | 4 | 1 | Yes — docs sync |
| docs/24_eventbus/eventbus_08_reference_api.md | MODIFY | eventbus reference API row | 23 | 1 | Yes — docs sync |

## Design
- **One checker, one final pattern set.** `COMPAT_PATTERNS` becomes the single authoritative list of the initiative's deleted surface (REQ-001 enumeration). Patterns follow the existing two shapes: literal word-boundary regexes for symbols, import-syntax regexes for module paths (precedent: `db.workflow_schema` import regexes at `COMPAT_PATTERNS` lines 81-84; the separate syntax-tree rules are `check_mcp_health_reexport_import()` and `check_gateless_discovery_construction()`), and a call-shape regex for `nack_event(` forms missing a consumer argument. Migration-claim doc patterns are phrase regexes in `_REMOVED_NAME_PATTERNS` scoped to active `docs/` (excluding `docs/**/done/` and ADR "Superseded" sections) — e.g. "registered forward-only migration", "schema_migrations ledger", "migrates through", "apply migrations" — tuned so supersession history text passes (historical-text false-positive self-tests pin this, AC-002).
- **Exception model split.** `validate_exceptions()` gains a rule: any entry whose category is `compatibility` / `migration` / `fallback` fails as a production compatibility exception (exit 1). The manifest then contains only `fixture` entries plus the allowance table. `check-compat-shims-source` moves to a dedicated `[checker_self_reference]`-style allowance table (same shape as `symbol_stage_allowance`), keeping the checker's own pattern literals tolerated without living in the production exception model.
- **Parity is verification, not rewrite.** Pre-commit and CI already share the option pair; the Plan's row is a confirm-and-pin step: the gate test asserts both invocation strings carry the same options (prevents silent drift), satisfying AC-003 without changing the hooks unless divergence is found.
- **Docs supersession pattern.** ADR-008 keeps its Amendment subsection as dated history but adds a "Superseded (2026-11, compatrm001/002/003/004)" statement naming the current-only policy; the ADR index row status is amended to match. `agent_10_04` runbook commands switch from version-table queries and "apply migrations" responses to the `db_07` §11 archive-and-recreate procedure. `mcp_00`/`mcp_07` lose the migration-policy framing; their manifest exceptions are deleted in the same phase they pass the checker.
- **Gate test, not grep folklore.** `tests/tools/test_no_compatibility_policy_gate.py` encodes the initiative's acceptance as executable assertions (manifest categories, live references, NACK signature, checker behavior), so the policy is enforced by the suite itself, not by convention.
- **Prerequisite ordering is enforced by construction**: this Plan implements only after 001/002/003 land (Release units), so the consolidated pattern set matches the final code state rather than a moving target.

## Implementation steps
1. **Phase 1: Checker and manifest consolidation** (starts only after compatrm001/002/003 implementations have landed)
   - [ ] Consolidate `COMPAT_PATTERNS` in `tools/check_compat_shims.py` to the REQ-001 final set plus the REQ-002 migration-claim doc patterns; add the production-category-zero rule to `validate_exceptions()` (REQ-001, REQ-002, REQ-003).
   - [ ] Clean `tools/compat_exceptions.toml`: delete the 3 `migration` entries, move the checker self-reference to a dedicated allowance table, keep the 17 `fixture` entries (REQ-003).
   - [ ] Add true-positive and historical-text false-positive self-tests to `tests/tools/test_check_compat_shims.py` (REQ-008); update `tools/TOOL_DESCRIPTIONS.md` for the changed checker behavior per `routing.md` "When to run which tool".
2. **Phase 2: Documentation rewrite**
   - [ ] Rewrite `docs/10_adr/adr_01_index.md` and `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` with the supersession statement and current-only policy (REQ-005, REQ-006).
   - [ ] Rewrite `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` runbook commands and failure responses (REQ-005).
   - [ ] Sweep `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` residual sections 8c-11 and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` lines 147/177/184 (post-compatrm001 state) (REQ-005).
   - [ ] Update `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/22_mcp/mcp_00_document-guide.md`, `docs/22_mcp/mcp_07_tool_schema_export_policy.md`, and `docs/24_eventbus/eventbus_08_reference_api.md` lines 130-131 (REQ-005).
   - [ ] Run the documentation checkers `routing.md` names for the edited docs (ADR invariant matrix, governance/MCP/DB consistency workflows).
3. **Phase 3: Regression-test alignment and gate**
   - [ ] Confirm compatrm001's rejection suite exists with file-hash no-mutation assertions; confirm migration-success tests are gone; confirm `AuthzGeneration`-only auth state and mandatory-consumer NACK tests (REQ-007).
   - [ ] Create `tests/tools/test_no_compatibility_policy_gate.py` (REQ-007).
4. **Phase 4: Automation parity and full validation**
   - [ ] Verify `.pre-commit-config.yaml` and `.github/workflows/backward-compat-check.yml` option parity; pin it in the gate test (REQ-004); confirm no `pyproject.toml`/task-runner divergence (resolved: none).
   - [ ] Run `uv run python -m tools.check_compat_shims --check-removed-names --check-doc-symbols`, `uv run pytest tests/`, pre-commit locally, the full CI workflow, and `rules/toolchain.md` §1-§8 gates (AC-001-AC-007).
   - [ ] Rehearse the `db_07` §11 recreate procedure on a scratch copy under `/tmp/opencode` (never `/opt/llm/`) to validate the runbook text (AC-006). Resolve UNK-01 during checker tuning.

### Release units
**Unit**: policy-finalization | **Phases**: 1, 2, 3, 4 | **Reason**: the checker's consolidated patterns must match the post-001/002/003 tree and the docs sweep must match post-001 doc state; validating any phase against the pre-cutover tree would report findings the prerequisite Plans already own, so all four phases land as one unit after the three implementation Plans complete.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_compat_shims.py | Unit self-tests + live corpus run | `uv run pytest tests/tools/test_check_compat_shims.py`; `uv run python -m tools.check_compat_shims --check-removed-names --check-doc-symbols` | Self-tests pass; live corpus zero findings |
| tools/compat_exceptions.toml | Unit (manifest validation) | via checker run | Zero production-category entries; fixture entries valid |
| tests/tools/test_no_compatibility_policy_gate.py | Integration gate | `uv run pytest tests/tools/test_no_compatibility_policy_gate.py` | All initiative assertions pass |
| docs/ (9 target files) | Documentation checkers + grep gate | `routing.md`-named doc checkers; gate-test scan | No removed terminology or migration claims outside history/fixture exemptions |
| .pre-commit-config.yaml + CI workflow | Parity check | `pre-commit run --all-files`; GitHub Actions run | Identical blocking options; green |
| Whole repository | Suite + full gates | `uv run pytest tests/`; `uv run ruff check .`; `uv run mypy scripts/`; `uv run bandit -q -r scripts/ -c pyproject.toml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`; pre-commit | Baselines preserved; AC-007 initiative gate green |

## Risks
- **Risk**: Overly broad migration-claim doc patterns flag legitimate supersession history → **Mitigation**: patterns are scoped to active policy sentences; the historical-text false-positive self-tests (REQ-008) pin the boundary before merge (UNK-01 resolution path).
- **Risk**: Consolidating patterns after three Plans land could strand a per-issue pattern (e.g. a 002/003 entry removed too early) → **Mitigation**: the consolidated set is written as a superset from the frozen prerequisite tables (all symbol names copied verbatim from those Plans); the gate test asserts each name individually.
- **Risk**: The production-category-zero rule breaks an existing manifest entry whose finding is still live (a prerequisite doc rewrite slips) → **Mitigation**: the rule lands in the same phase as the doc rewrites (Release unit), and the checker run in Phase 4 fails locally before any commit if an entry's finding persists.
- **Risk**: Gate test asserting prerequisite test structure could rot when those tests evolve → **Mitigation**: gate assertions target behavior (signature inspection, checker exit codes, manifest categories), not test file names, minimizing coupling to the prerequisite Plans' internal test organization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Checker and manifest consolidation | In Progress | — | — | Procedure documents generated 2026-11-07 |
| 2 | Phase 2: Documentation rewrite | In Progress | — | — | Procedure documents generated 2026-11-07 |
| 3 | Phase 3: Regression-test alignment and gate | In Progress | — | — | Procedure documents generated 2026-11-07 |
| 4 | Phase 4: Automation parity and full validation | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | Artifacts referenced in session-early searches (`TestGateguardCoverage`, `tests/test_precommit_gate_failure_recovery.py`, `tests/tools/test_gateguard_rotation.py`, `docs/40_testing/test_document.md`) do not exist in the current tree or git history at procedure-generation time; cause unknown (noted UNK-03 in procedure doc 04). Mitigation: the gate-test procedure (doc 04) is self-contained (parses config files directly, implements its own rotation sandbox) and does not depend on those artifacts. Flagged for user confirmation. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261107-103000_01_tools_check_compat_shims.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261107-103000_02_tools_compat_exceptions.toml.md | 1 | Procedure | Pending | — | — |
| implementations/20261107-103000_03_tests_tools_test_check_compat_shims.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261107-103000_04_tests_tools_test_no_compatibility_policy_gate.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261107-103000_05_.pre-commit-config.yaml.md | 4 | Procedure | Pending | — | — |
| implementations/20261107-103000_06_.github_workflows_backward-compat-check.yml.md | 4 | Procedure | Pending | — | — |
| implementations/20261107-103000_07_pyproject.toml.md | 4 | Procedure | Pending | — | — |
| implementations/20261107-103000_08_docs_10_adr_adr_01_index.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-103000_09_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-103000_10_docs_23_agent_agent_10_04_operations-and-observability-validation-and-troubleshooting.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-103000_11_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-103000_12_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-103000_13_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-103000_14_docs_22_mcp_mcp_00_document-guide.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-103000_15_docs_22_mcp_mcp_07_tool_schema_export_policy.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-103000_16_docs_24_eventbus_eventbus_08_reference_api.md.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-064415
- **Related target files**: tools/check_compat_shims.py, tools/compat_exceptions.toml, tests/tools/test_check_compat_shims.py, tests/tools/test_no_compatibility_policy_gate.py, .pre-commit-config.yaml, .github/workflows/backward-compat-check.yml, pyproject.toml, docs/10_adr/adr_01_index.md, docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md, docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md, docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md, docs/41_db/db_07_api_and_operations-recovery-and-reference.md, docs/22_mcp/mcp_00_document-guide.md, docs/22_mcp/mcp_07_tool_schema_export_policy.md, docs/24_eventbus/eventbus_08_reference_api.md

### Requirement Traceability
| Requirement ID | Source | Acceptance Criteria | Implementation Target Files | Procedure | Status |
|---|---|---|---|---|---|
| REQ-001 | issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md Required Changes (blocking checks) | AC-002 | tools/check_compat_shims.py | — | Planned |
| REQ-002 | same, Required Changes (documentation claims) | AC-002, AC-004 | tools/check_compat_shims.py | — | Planned |
| REQ-003 | same, Required Changes (manifest cleanup) | AC-001 | tools/compat_exceptions.toml, tools/check_compat_shims.py | — | Planned |
| REQ-004 | same, Required Changes (align automation) | AC-003 | .pre-commit-config.yaml, .github/workflows/backward-compat-check.yml, pyproject.toml | — | Planned |
| REQ-005 | same, Required Changes (rewrite documentation) | AC-004 | docs rows in Implementation Target Files | — | Planned |
| REQ-006 | same, Required Changes (current policy text) | AC-004 | docs rows in Implementation Target Files | — | Planned |
| REQ-007 | same, Required Changes (restructure tests) | AC-005, AC-006, AC-007 | tests/tools/test_no_compatibility_policy_gate.py | — | Planned |
| REQ-008 | same, Required Changes (checker self-tests) | AC-002 | tests/tools/test_check_compat_shims.py | — | Planned |

## Freeze Decision Log

| Timestamp | Freeze status | Validation evidence |
|---|---|---|
| 2026-11-07 06:48 | Frozen | All `Implementation Target Files` rows `Verified` against HEAD `1b2dded66`: manifest contents enumerated (22 entries: 3 `migration` at lines 24/33/42, `check-compat-shims-source` `compatibility` at line 204, 18 `fixture`, `[symbol_stage_allowance]` at line 219); checker surfaces verified (`--check-removed-names`/`--check-doc-symbols`/`--allowlist`, `COMPAT_PATTERNS` ~line 335, `db.workflow_schema` syntax rules lines 81-84, `validate_exceptions()` lines 184-204); pre-commit line 38 and CI line 39 invoke the identical option pair; no `Makefile`/`makefile`/`justfile` at repository root and no checker invocation in `pyproject.toml` (both Issue Unresolved Questions resolved); doc terminology lines (`adr_01_index:52/63`, `adr_02_05_008:60/73-75/137/363`, `agent_10_04:54/93`, `db_03_07:46-47/74-78`, `db_03:29-94`, `db_07:147/177/184`, `mcp_00:94`, `mcp_07:27-33`) spot-checked by grep/read this cycle. `tools/check_workitem_structure.py` clean. Post-freeze `tools/check_plan_target_overlaps.py` findings involving this Plan — `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` with compatrm001, `tools/check_compat_shims.py` with compatrm002/compatrm003 — all judged **compatible** (disjoint sections / additive same-dict pattern entries, sequencing after prerequisites) and recorded in `Assumptions`. No blocking Unknown: UNK-01, UNK-02 `Blocking? = False`. |
| 2026-11-07 (adversarial verification, procedure-generation pass) | Frozen (inventory corrected) | Re-verified against HEAD `1a13653e8`; `tools/check_compat_shims.py` and `tools/compat_exceptions.toml` unchanged since freeze base `1b2dded66`. Corrections: structured manifest count is 21 `[[compatibility_exceptions]]` entries (3 `migration` at id lines 24/33/42, `check-compat-shims-source` `compatibility` at line 204, 17 `fixture`) — the freeze entry's 22/18 figures were a grep overcount (header comment line 4); checker attribution corrected (`COMPAT_PATTERNS` line 39, dict spans 39-115, with the approval-stage entries at 62-74 and `db.workflow_schema` import regexes at 81-84; `_update_null_fill` and the other confirmed-removed-name entries in `_REMOVED_NAME_PATTERNS` lines 334-389, `*.md`-only and `--check-removed-names`-gated; `load_exceptions()` 157, `validate_exceptions()` 181; syntax-tree rules are the functions at lines 430/451). New gap: `docs/24_eventbus/eventbus_08_reference_api.md` lines 130-131 list compatrm001-deleted scripts as live API with no owning plan — added as target row 16 (REQ-001/REQ-005) with Background, Assumptions, Affected areas, Design, steps, Validation plan, and Traceability updated. No new blocking Unknown. |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261107-103000 -->