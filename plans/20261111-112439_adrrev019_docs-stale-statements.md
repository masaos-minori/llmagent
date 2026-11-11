## Goal
Correct the stale statements and small defects in reference documents and one code docstring that still hold after verification (DLQ artifact format, a wrong cross-reference, a duplicated table row, a stale table count, a missing health state, an unstated timestamp format, an ambiguous `liveness` term, a code-as-canonical-source label, a wrong docstring path, an ambiguous function name), and make an empty `sqlite_vec_so` an explicit startup error for the processes that open `rag.sqlite` or `session.sqlite`, as the maintainer decided on 2026-11-09, without changing EventBus or MCP runtime behavior.

## Priority
Low

## Scope
- **In-Scope**: The confirmed items listed in the Requirements; one startup validation (an empty `sqlite_vec_so` in `agent.toml` is rejected by `ProductionConfigValidator` and by `build_db_config()`), with tests; docstring corrections in `scripts/mcp_servers/server.py` and `scripts/eventbus/auth.py`; documentation of the two `attach_auth_middleware` functions' distinction.
- **Out-of-Scope**: Items verified as already correct or absent (`agent.db`, "never received twice", `eventbus_03` and `mcp_03_03` headings, the `db_03` recreation table, `governance_00`); renaming either `attach_auth_middleware` (the plan documents the distinction instead; a rename is a maintainer option, UNK-03); moving the plaintext-diagnostics decision into an ADR (needs an ADR and a maintainer approval, UNK-01); history wording removal (the history-wording Plan); any EventBus or MCP runtime behavior change; checker changes; a file-existence check for `sqlite_vec_so` (CI tolerates a missing library by design).
- **Dependencies**: This Plan follows the history-wording Plan, which edits several of the same documents, so each passage is edited once.
  - **Depends on**: plans/20261111-110144_adrrev017_docs-history-wording.md | phase all | edits the same documents (`db_01`, `eventbus_06`, `mcp_03_03`, the ADR index); land first so these edits apply to cleaned text.

## Background
Verification (2026-11-11) confirmed these items against current source: `eventbus_01` line 37 says DLQ events are written as JSONL files while the artifacts are per-event `{event_id}.json` files; `governance_05` cites "18. Area Dependency Graph Validation" while `governance_04` numbers it 19; `mcp_02_03` carries two `requested_target` rows; the `server.py` docstring names `mcp/dispatch.py` and `mcp/audit.py`; `agent_09_01` labels code as "Canonical Source" (GV-012); `db_07` 11a lists three of the four EventBus tables (`dlq_outbox` is missing); the `mcp_03_03` state diagram omits `DEGRADED`; the ADR index cites ADR-006 as an owner of open deviations although every ADR says "Not applicable"; the EventBus writes `Z` timestamps and no document says so; `eventbus_10` and `mcp_02_02` define `liveness` differently without cross-reference; and the two `attach_auth_middleware` functions differ in behavior (the MCP one authenticates a Bearer token, the EventBus one only injects `X-Request-Id`). Refuted: `agent.db`, "never received twice", broken headings, the `db_03` table, and `governance_00`. For `sqlite_vec_so`, `DbConfig` defaults to an empty string, the helper is built per use and fails only at the first vec load, rag-pipeline-mcp's posture check already refuses to bind on an empty value, and the Agent's startup config validator already rejects other empty keys.

## Problem
- Stale inventories, wrong format statements, and a wrong cross-reference send operators and implementers to files and sections that do not match the code.
- An ambiguous function name and a wrong docstring path add avoidable confusion.
- An empty `sqlite_vec_so` is reported only at the first vec-table access, long after startup.

## Reason for Change
Each item is a small, confirmed discrepancy; bundling them in one documentation pass avoids repeated edits, and the startup error follows the maintainer decision of 2026-11-09.

## Implementation Intent
Reference documents match the code and the ADRs; each statement is confirmed against current source before it is edited, and an already-correct item is skipped and reported. The only behavior change is the empty `sqlite_vec_so` startup error, scoped to processes that read the DB configuration for `rag.sqlite` or `session.sqlite`.

## Requirements
- `REQ-001`: Correct the DLQ artifact statement in `eventbus_01` (per-event JSON files, not JSONL), the `governance_05` cross-reference (section 19), the duplicated `requested_target` row in `mcp_02_03` (keep one row with the complete description), and the `db_07` 11a EventBus inventory (add `dlq_outbox` and state four tables).
- `REQ-002`: Correct `mcp_03_03` so the state diagram includes `DEGRADED` (and the table's `UNKNOWN`, if the code uses it), correct the `adr_01_index.md` Known Deviations sentence so it names no ADR as holding an open deviation, and replace "Canonical Source" for code in `agent_09_01` with the wording the policy allows.
- `REQ-003`: Document the EventBus timestamp format as `Z`-suffixed UTC (`eventbus_06`), the meaning of EventBus `liveness` against the MCP `liveness` flag with a cross-reference (`eventbus_10`), and that manual event deletion leaves `events.jsonl` with more lines than the database (`eventbus_05` Cleanup Procedure).
- `REQ-004`: Fix the `server.py` docstring module paths (`mcp_servers/dispatch.py`, `mcp_servers/audit.py`) and document the distinction between the two `attach_auth_middleware` functions in their docstrings (Bearer authentication versus request-ID injection only), keeping both names and every import unchanged.
- `REQ-005`: An empty or absent `sqlite_vec_so` in `agent.toml` is a startup error with an explicit message: `ProductionConfigValidator.validate()` reports it (Agent startup) and `build_db_config()` raises `ValueError` naming the key (ingester, crawler, and any helper built from the DB configuration); explicit-`db_path` helpers and the EventBus are unaffected; tests prove both paths and that a non-empty missing file is still accepted.
- `REQ-006`: `db_01` states that `sqlite_vec_so` is required for the processes that open `rag.sqlite` or `session.sqlite` and says "four platform databases" with the derived `mdq.sqlite` named separately (maintainer confirms the wording, UNK-02); `scripts/db/config.py` documentation no longer calls the key optional.
- `REQ-007`: The final report lists each memo item as fixed, already correct, or refuted with its evidence, and lists the open decisions (plaintext-diagnostics ADR, `Z` assumption, rename option) without deciding them.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/24_eventbus/eventbus_01_system-overview.md` | Modify | Line 37: "DLQ events are written as JSONL files" becomes the per-event JSON artifact statement | REQ-001 / AC-1 | Line 37; `eventbus_03` Reconciliation names `{event_id}.json` files and `dlq.py` writes per-event artifacts (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Modify | Lines 102-103: "18. Area Dependency Graph Validation" becomes section 19 | REQ-001 / AC-1 | `governance_04` line 232 is `### 19. Area Dependency Graph Validation` (checked in Step 2) | `tools/check_docs_consistency.py --domain overview` | Verified |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | Merge the two `requested_target` rows (lines 38 and 42) into one | REQ-001 / AC-1 | Two rows with different descriptions (checked in Step 2) | `tools/check_docs_quality.py`, `tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Section 11a (lines 123-135): add the `dlq_outbox` query and say four tables | REQ-001 / AC-1 | Block queries `events`, `consumer_delivery`, `consumer_offsets` ("its three tables"); `scripts/eventbus/schema.sql` defines four tables (checked in Step 2) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Modify | Add `DEGRADED` to the state-transition diagram (lines 68-96) | REQ-002 / AC-2 | Diagram goes `HEALTHY -> UNAVAILABLE` only while the table and `McpServerHealthState` define `DEGRADED` (checked in Step 2) | `tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/10_adr/adr_01_index.md` | Modify | Line 39: remove the "(for example ADR-006)" claim that an ADR holds open deviations | REQ-002 / AC-2 | Line 39; all 15 ADR Known Deviations sections read "Not applicable" (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_known_deviation_sync.py` | Verified |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | Modify | Line 80: replace "Canonical Source" for code (`agent/diagnostic_store.py`, `db/maintenance.py`) | REQ-002 / AC-2 | Line 80 `**Canonical Source**: ...` code paths (GV-012); the plaintext-diagnostics decision at lines 70-76 stays pending (checked in Step 2) | `tools/check_docs_quality.py`, `tools/check_docs_content_policy.py --strict` | Verified |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Modify | State that EventBus timestamps are UTC with a `Z` suffix | REQ-003 / AC-3 | `now_iso()` in `scripts/eventbus/json_utils.py` formats `%Y-%m-%dT%H:%M:%SZ`; `dlq.py` line 377 uses the same format; no document states it (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Modify | Clarify `liveness` (line 69) against the MCP `liveness` flag with a cross-reference | REQ-003 / AC-3 | Line 69 "The DLQ sweep task is running"; `mcp_02_02` line 30 defines `liveness` as an overridable process-state flag (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify | Add the `events.jsonl` line-count note to the Cleanup Procedure | REQ-003 / AC-3 | Cleanup Procedure (lines 177-193) is silent on `events.jsonl`; lines 195-199 say the file grows until the operator rotates it (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `scripts/mcp_servers/server.py` | Modify | Docstring lines 7-8 module paths; document the distinction from the EventBus function in `attach_auth_middleware`'s docstring | REQ-004 / AC-4 | Lines 7-8 "mcp/dispatch.py", "mcp/audit.py"; the function authenticates a Bearer token (lines 95-131) (checked in Step 3) | `uv run pytest tests/mcp_servers -v` | Verified |
| `scripts/eventbus/auth.py` | Modify | Document that `attach_auth_middleware` only injects `X-Request-Id` and where authentication happens | REQ-004 / AC-4 | `def attach_auth_middleware(app)` at line 454: "This middleware only injects X-Request-Id" (checked in Step 3) | `uv run pytest tests/eventbus -v` | Verified |
| `scripts/db/config.py` | Modify | `build_db_config()` rejects an empty `sqlite_vec_so`; update the module and field documentation | REQ-005, REQ-006 / AC-5, AC-6 | Line 9 "sqlite_vec_so is optional"; line 28 default `""`; `build_db_config()` passes `cfg.get("sqlite_vec_so", "")` through (checked in Step 3) | `tests/db/test_sqlite_helper.py` | Verified |
| `scripts/agent/production_config_validator.py` | Modify | Report an empty or absent `sqlite_vec_so` in `validate()` like the existing `allowed_root` check (lines 265-270) | REQ-005 / AC-5 | `sqlite_vec_so` is a known key (line 191); `allowed_root` shows the pattern (checked in Step 3); 14129 bytes | `tests/agent/test_production_config_validator.py` | Verified |
| `tests/db/test_sqlite_helper.py` | Modify | Add tests that `build_db_config()` raises for an empty `sqlite_vec_so` and a target-based helper reports it explicitly | REQ-005 / AC-5 | Existing vec tests at lines 300-340 (explicit `db_path` helper, empty value skips the load) (checked in Step 3) | itself | Verified |
| `tests/agent/test_production_config_validator.py` | Modify | Add tests that `validate()` rejects an empty or absent `sqlite_vec_so` and accepts a non-empty value whose file does not exist | REQ-005 / AC-5 | File tests `ProductionConfigValidator` (checked in Step 3) | itself | Verified |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Modify | State that `sqlite_vec_so` is required for processes opening `rag.sqlite` or `session.sqlite`; "Four DB files exist" becomes "four platform databases" with `mdq.sqlite` named as derived | REQ-006 / AC-6 | Lines 34 and 50-60; `db_03` names `mdq.sqlite` as a fifth database file (checked in Step 2) | `tools/check_docs_consistency.py --domain db` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/helper.py` | Target-based constructor reads `db_cfg.sqlite_vec_so`; the first vec load raises `ValueError`; explicit-path helpers derive load behavior from their own argument | REQ-005 |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py` | rag-pipeline-mcp's posture check already fails an empty `sqlite_vec_so` | REQ-005 |
| `tests/conftest.py` | Isolation fixture tolerates a missing sqlite-vec library on CI; the check must reject only an empty value | REQ-005 |
| `config/agent.toml` | Sets `sqlite_vec_so` (line 9) | REQ-005 |
| `scripts/eventbus/dlq.py` | Per-event artifact generation and the `Z` timestamp format | REQ-001, REQ-003 |
| `scripts/eventbus/json_utils.py` | `now_iso()` format | REQ-003 |
| `scripts/eventbus/schema.sql` | The four EventBus tables | REQ-001 |
| `scripts/shared/mcp_health.py` | `McpServerHealthState` members | REQ-002 |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | MCP `liveness` definition for the cross-reference | REQ-003 |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Names `mdq.sqlite` and lists `rag.sqlite` and `session.sqlite` in the baseline table (so that item is already correct) | REQ-006 |
| `docs/00_governance/governance_04_documentation-checks.md` | Section 19 numbering | REQ-001 |
| `docs/00_governance/governance_01_documentation-policy.md` | GV-012 canonical-source wording rule | REQ-002 |
| `scripts/eventbus/app.py` | Caller of the EventBus `attach_auth_middleware`; unchanged | REQ-004 |

## Acceptance Criteria
- AC-1: `eventbus_01`, `governance_05`, `mcp_02_03`, and `db_07` match the code (per-event JSON artifacts, section 19, one `requested_target` row, four EventBus tables) (`REQ-001`).
- AC-2: The `mcp_03_03` diagram shows `DEGRADED`, the ADR index names no ADR as holding an open deviation, and `agent_09_01` no longer calls code a canonical source (`REQ-002`).
- AC-3: The timestamp format, the `liveness` distinction, and the `events.jsonl` note are documented (`REQ-003`).
- AC-4: `rg -n "mcp/dispatch|mcp/audit" scripts/mcp_servers/server.py` finds nothing, both `attach_auth_middleware` docstrings state the distinction, and no import changed (`REQ-004`).
- AC-5: An empty or absent `sqlite_vec_so` fails Agent startup validation and `build_db_config()` with an explicit message, a non-empty missing path is still accepted, and tests prove each (`REQ-005`).
- AC-6: `db_01` and `scripts/db/config.py` state that the key is required for `rag.sqlite` and `session.sqlite` processes (`REQ-006`).
- AC-7: The report lists every memo item as fixed, already correct, or refuted, plus the open decisions (`REQ-007`).
- AC-8: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py` for each touched domain, `check_needs_confirmation_inventory.py`, and the standard validation sequence for the changed Python files pass.

## Tests
- `REQ-005` (new): in `tests/agent/test_production_config_validator.py`, `validate()` reports an error for `sqlite_vec_so = ""` and for an absent key, and none for a non-empty value naming a missing file; in `tests/db/test_sqlite_helper.py`, `build_db_config()` raises `ValueError` mentioning `sqlite_vec_so` for an empty value, and `SQLiteHelper("session")` surfaces it as its existing `RuntimeError("DbConfig load failed ...")`. Each is written first and shown to fail.
- Regression: the existing explicit-`db_path` vec tests (empty value skips the load) and `tests/rag`, `tests/agent`, `tests/db`, `tests/mcp_servers`, `tests/eventbus` suites run unchanged; any fixture that builds the Agent configuration without the key is updated minimally.
- Documentation items are verified by the checkers in the Validation plan.

## Documentation Impact
`docs/24_eventbus/` (`eventbus_01`, `_05`, `_06`, `_10`), `docs/22_mcp/` (`mcp_02_03`, `mcp_03_03`), `docs/41_db/` (`db_01`, `db_07`), `docs/23_agent/agent_09_01_data-layer-session-db.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, and the ADR index; locate them through `docs/00_index.md` "Document References by Task". State current behavior, intent, and failure behavior only. Write in English.

## Assumptions
- The default for the two `attach_auth_middleware` functions is to document the distinction and keep both names: a rename changes the generated EventBus reference and its manifest, and the issue accepts documentation as an alternative; a rename stays a maintainer option (UNK-03).
- The empty-value check lives in `ProductionConfigValidator.validate()` (Agent startup) and `build_db_config()` (other processes) because the helper is built per use and cannot give a startup error; explicit-`db_path` helpers and the EventBus are not changed, so components that run without the extension keep working.
- Documenting `Z` as the EventBus timestamp format follows the code and the issue's assumption; the maintainer confirms it (UNK-04).
- Overlap judgment (`tools/check_plan_target_overlaps.py`): `eventbus_05`, `eventbus_06`, and `eventbus_10` are also edited by the EventBus specification Plan (adrrev014: cleanup procedure, health fields) and the history-wording Plan; `mcp_02_03` by the MCP audit Plan (adrrev011: audit-writing server list); `db_07` and `db_01` by the recovery, RAG consistency, and history-wording Plans; `governance_05` by the authority-format Plan (adrrev016: the Agent-to-RAG statement); the ADR index by several ADR Plans; compatible, because this Plan edits other passages, and the shared `eventbus_05` Cleanup Procedure paragraph is edited after the EventBus specification Plan lands.
- The `agent_09_01` plaintext-diagnostics decision stays as is and is reported as a pending item (UNK-01), because moving it needs an ADR and a maintainer approval.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to move the plaintext-diagnostics decision in `agent_09_01` into an ADR | Needs an ADR and a maintainer approval | Report as a pending Needs Confirmation item; no edit in this Plan | False |
| UNK-02 | Wording for the `db_01` database count ("four platform databases" plus the derived `mdq.sqlite`) | Maintainer confirmation | Default to that wording; trivial to revise | False |
| UNK-03 | Whether to rename one `attach_auth_middleware` instead of documenting the distinction | Maintainer preference; a rename affects `app.py`, tests, the generated EventBus reference and its manifest | Default to documentation; a rename becomes a separate issue | False |
| UNK-04 | Confirmation that `Z` is the intended documented EventBus timestamp format | The only `+00:00` producer found is the Agent-side client that another issue removes | Maintainer confirms; the text follows the code either way | False |
| UNK-05 | Whether tests or fixtures build the Agent or DB configuration with no `sqlite_vec_so` and would fail after REQ-005 | The affected suites were not run with the change | Run `tests/db`, `tests/agent`, `tests/rag`, `tests/mcp_servers`, `tests/eventbus` in Phase 4; update only the failing fixtures through a plan amendment (fallout class) | False |
| UNK-06 | Whether the ingester and crawler load `sqlite_vec_so` through `build_db_config()` or a separate `ingester.toml` path that also needs the check | Their configuration path was not traced in full | Phase 4 traces it; `config/ingester.toml` already sets the key, and the check is added only where the empty value would otherwise reach a vec load | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/24_eventbus/eventbus_01_system-overview.md` | Modify | Low | 3 | N/A | not applicable (docs) |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Modify | Medium | 8 | N/A | not applicable (docs) |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | Low | 7 | N/A | not applicable (docs) |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Low | 19 | N/A | not applicable (docs) |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Modify | Low | 9 | N/A | not applicable (docs) |
| `docs/10_adr/adr_01_index.md` | Modify | Medium | 29 | N/A | not applicable (docs) |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | Modify | Low | 10 | N/A | not applicable (docs) |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Modify | Low | 12 | N/A | not applicable (docs) |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Modify | Low | 5 | N/A | not applicable (docs) |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify | Low | 13 | N/A | not applicable (docs) |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Modify | Low | 8 | N/A | not applicable (docs) |
| `scripts/mcp_servers/server.py` | Modify | Low (docstring only) | 10 | N/A | Requires deploy of `scripts/` (docstring change; no behavior change) |
| `scripts/eventbus/auth.py` | Modify | Low (docstring only) | 8 | N/A | Requires deploy of `scripts/` (docstring change; no behavior change) |
| `scripts/db/config.py` | Modify | Medium (shared by the Agent, ingester, crawler, and DB tools) | 1 | N/A | Requires deploy of `scripts/` |
| `scripts/agent/production_config_validator.py` | Modify | Medium (Agent startup gate) | 5 | N/A | Requires deploy of `scripts/` |
| `tests/db/test_sqlite_helper.py` | Modify | Low | 3 | N/A | not applicable (tests are not deployed) |
| `tests/agent/test_production_config_validator.py` | Modify | Low | 6 | N/A | not applicable (tests are not deployed) |

## Design
Path B (more than 3 files; startup behavior of a shared configuration builder). Findings from the inspection:
- Architecture: `scripts/db/config.py` is a db-layer module imported by `agent`, `rag`, and the DB tools; the new check raises `ValueError` already handled by `SQLiteHelper.__init__` (it wraps a `build_db_config()` `ValueError` as `RuntimeError`), so no new import appears. `production_config_validator.py` stays in the Agent layer.
- Dependency graph: `build_db_config()` users are `db.helper`, `db.maintenance`, `db.rotation`, `db.recovery*`, `agent.commands`, `rag.ingestion.crawler`, and `rag.ingestion.ingester`; each already receives `ValueError` for other config defects. Explicit-`db_path` helpers bypass it.
- Historical: churn from `git log --since=30.days`; bus factor `N/A` (git-fame not installed).
- Operational: the Agent is the process that restarts on deploy; `config/agent.toml` and `config/ingester.toml` already set `sqlite_vec_so`, so a correctly configured deployment starts unchanged. Persisted schema: not applicable. Consumer scan: the changed constant behavior is the empty-string default of `DbConfig.sqlite_vec_so`; candidate consumers are the `build_db_config()` users listed above and tests that build the DB configuration; `not affected`: explicit-`db_path` helpers and the EventBus.
- Design decisions: (1) validate emptiness, not file existence (CI intentionally lacks the library, `tests/conftest.py`); (2) put the Agent startup check in the existing config validator, not in a new startup stage; (3) keep both `attach_auth_middleware` names and document the distinction; (4) edit each document passage once, after the history-wording Plan.
- Failure behavior: an empty value stops Agent startup with a message that names the key and the file to edit, without printing any value.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Confirmation and baseline** (all target files)
   - [ ] Re-read each passage before editing; record items already correct or changed since verification; run `rg -n "attach_auth_middleware"` for a baseline.
   - [ ] Run `uv run pytest tests/db tests/agent/test_production_config_validator.py -q` for a baseline.
2. **Phase 2: Documentation fixes** (REQ-001, REQ-002, REQ-003, REQ-006; `docs/24_eventbus/eventbus_01_system-overview.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/22_mcp/mcp_03_03_transport-and-health.md`, `docs/10_adr/adr_01_index.md`, `docs/23_agent/agent_09_01_data-layer-session-db.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`)
   - [ ] Apply each confirmed correction with a minimal edit; skip and record any item found already fixed.
3. **Phase 3: Docstrings** (REQ-004; `scripts/mcp_servers/server.py`, `scripts/eventbus/auth.py`)
   - [ ] Correct the module paths and document the distinction between the two `attach_auth_middleware` functions; run `uv run pytest tests/mcp_servers tests/eventbus -q` and `uv run python tools/generate_reference_table.py --check` (a first-line-only docstring change keeps the generated reference stable).
4. **Phase 4: Empty `sqlite_vec_so` startup error** (REQ-005, REQ-006; `scripts/db/config.py`, `scripts/agent/production_config_validator.py`, `tests/db/test_sqlite_helper.py`, `tests/agent/test_production_config_validator.py`)
   - [ ] Write the failing tests first; add the validator check and the builder check; update the key's documentation in `scripts/db/config.py`.
   - [ ] Trace the ingester and crawler paths (UNK-06) and run `tests/db`, `tests/agent`, `tests/rag`, `tests/mcp_servers`, and `tests/eventbus`; update only fixtures that fail for the missing key (UNK-05).
5. **Phase 5: Deployment & Verification** (all target files)
   - [ ] Run the Validation plan commands and the `rules/toolchain.md` sequence for the changed Python files.
   - [ ] Hand off to `skills/deploy/SKILL.md`: the change is committed and pushed first, and deploying is the user's decision (approval gate); the Agent restarts on deploy and `config/agent.toml` already sets `sqlite_vec_so`.
   - [ ] Report each memo item (fixed, already correct, refuted) and the open decisions UNK-01 to UNK-04.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/db/config.py`, `scripts/agent/production_config_validator.py` | Unit | `uv run pytest tests/db tests/agent/test_production_config_validator.py -v` | Pass |
| Wider regression | Unit and integration | `uv run pytest tests/rag tests/agent tests/mcp_servers tests/eventbus -q` | Pass |
| Changed Python files | Format, lint, type, security | `uv run ruff format <files>`, `uv run ruff check <files>`, `uv run mypy <files>`, `uv run bandit -r scripts/db scripts/agent/production_config_validator.py -c pyproject.toml` | Clean |
| Architecture | Import contracts | `uv run lint-imports` | Pass |
| Module size | Size gate | `uv run python tools/check_module_size.py` | Pass |
| Generated reference | Guarded block drift | `uv run python tools/generate_reference_table.py --check` | No drift |
| Coverage | Changed lines | `rules/toolchain.md` section 7 diff-cover sequence | At or above the Completion checklist threshold |
| Touched documents | Structure and policy | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` | Pass |
| Touched domains | Claims against code | `uv run python tools/check_docs_consistency.py --domain eventbus`, `--domain mcp`, `--domain db`, `--domain overview` | Pass |
| Inventories | Needs Confirmation and deviations | `uv run python tools/check_needs_confirmation_inventory.py`, `check_known_deviation_sync.py` | Pass |

Validation quality baseline: `radon` and `vulture` are not installed on this host (Tool availability guard; ruff covers the lightweight checks). The Python targets are small edits to `scripts/db/config.py` (2756 bytes) and `scripts/agent/production_config_validator.py` (14129 bytes), far below the module-size gate; no `bandit` run was made for this Plan's targets (it runs in Phase 5).

## Risks
- **Risk**: Rejecting an empty `sqlite_vec_so` breaks a legitimate component or a test fixture that builds the configuration without the key. → **Mitigation**: Explicit-`db_path` helpers and the EventBus are untouched; Phase 4 runs the five affected suites and updates only failing fixtures (UNK-05, UNK-06).
- **Risk**: The check is extended to the library file's existence and breaks CI, which intentionally lacks the library. → **Mitigation**: The tests include a non-empty missing path that must be accepted.
- **Risk**: Documenting the `attach_auth_middleware` distinction changes the generated EventBus reference. → **Mitigation**: Keep the docstring's first line unchanged and run `generate_reference_table.py --check`.
- **Risk**: A passage was already fixed by another Plan before this Plan runs. → **Mitigation**: Phase 1 re-reads each passage first and skips and records any already-correct item (the issue's instruction).
- **Risk**: Overlapping edits to shared passages (`eventbus_05` Cleanup Procedure, ADR index) conflict with sibling Plans. → **Mitigation**: Land after the history-wording and EventBus specification Plans and edit only the listed sentences; rerun `tools/check_plan_target_overlaps.py`.
- **Risk**: Stating "four platform databases" or `Z` as policy is read as a decision. → **Mitigation**: Both follow the code and are flagged for the maintainer (UNK-02, UNK-04); no ADR changes.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirmation and baseline | Pending | — | — | |
| 2 | Documentation fixes (REQ-001, REQ-002, REQ-003, REQ-006) | Pending | — | — | |
| 3 | Docstrings (REQ-004) | Pending | — | — | |
| 4 | Empty `sqlite_vec_so` startup error (REQ-005, REQ-006) | Pending | — | — | |
| 5 | Deployment & Verification (REQ-007) | Pending | — | — | |

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
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-112439
- **Related target files**: `docs/24_eventbus/eventbus_01_system-overview.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/22_mcp/mcp_03_03_transport-and-health.md`, `docs/10_adr/adr_01_index.md`, `docs/23_agent/agent_09_01_data-layer-session-db.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `scripts/mcp_servers/server.py`, `scripts/eventbus/auth.py`, `scripts/db/config.py`, `scripts/agent/production_config_validator.py`, `tests/db/test_sqlite_helper.py`, `tests/agent/test_production_config_validator.py`, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Background: `eventbus_01` DLQ artifacts are JSONL (confirmed stale) | `docs/24_eventbus/eventbus_01_system-overview.md` | Step 2 | AC-1 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-001 | Background: `governance_05` cites section 18 | `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Step 2 | AC-1 | `check_docs_consistency.py --domain overview` | Confirmed by repository evidence |
| REQ-001 | Background: `mcp_02_03` mentions `requested_target` twice | `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Step 2 | AC-1 | `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes: `db_07` 11a EventBus inventory (stale in the other direction: three tables, `dlq_outbox` missing) | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Step 2 | AC-1 | `check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-002 | Required Changes: `mcp_03_03` DEGRADED state in the state diagram | `docs/22_mcp/mcp_03_03_transport-and-health.md` | Step 2 | AC-2 | `check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-002 | Required Changes: Document Guide and Index consistency on unresolved deviations | `docs/10_adr/adr_01_index.md` | Step 2 | AC-2 | `check_adr_structure.py`, `check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes: stop calling code the "Canonical Source" (GV-012) | `docs/23_agent/agent_09_01_data-layer-session-db.md` | Step 2 | AC-2 | `check_docs_quality.py`, `check_docs_content_policy.py --strict` | Confirmed by repository evidence |
| REQ-003 | Required Changes: document the timestamp suffix policy as `Z` | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Step 2 | AC-3 | `check_docs_consistency.py --domain eventbus` | Derived from confirmed evidence |
| REQ-003 | Required Changes: clarify EventBus `liveness` against MCP liveness | `docs/24_eventbus/eventbus_10_health_endpoint.md` | Step 2 | AC-3 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes: document the integrity-procedure note (manual deletion leaves more JSONL lines) | `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Step 2 | AC-3 | `check_docs_consistency.py --domain eventbus` | Derived from confirmed evidence |
| REQ-004 | Required Changes: fix the `server.py` docstring module paths | `scripts/mcp_servers/server.py` | Step 3 | AC-4 | `uv run pytest tests/mcp_servers -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes: remove the ambiguity of two `attach_auth_middleware` functions (document the distinction) | `scripts/eventbus/auth.py` | Step 3 | AC-4 | `uv run pytest tests/eventbus -v` | Confirmed by repository evidence |
| REQ-005 | Required Changes: empty `sqlite_vec_so` startup error (maintainer decision of 2026-11-09) | `scripts/db/config.py` | Step 4 | AC-5 | `tests/db/test_sqlite_helper.py` | Confirmed by repository evidence |
| REQ-005 | Same; Agent startup validation | `scripts/agent/production_config_validator.py` | Step 4 | AC-5 | `tests/agent/test_production_config_validator.py` | Derived from confirmed evidence |
| REQ-005 | Testing Expectations: add a startup test for the empty `sqlite_vec_so` error in `tests/db/` | `tests/db/test_sqlite_helper.py` | Step 4 | AC-5 | itself | Explicit in issue |
| REQ-005 | Same; Agent-side startup test | `tests/agent/test_production_config_validator.py` | Step 4 | AC-5 | itself | Derived from confirmed evidence |
| REQ-006 | Required Changes: inventories (`db_01`) and the `sqlite_vec_so` requirement | `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Step 2 | AC-6 | `check_docs_consistency.py --domain db` | Needs confirmation |
| REQ-006 | Same; the module documentation calls the key optional | `scripts/db/config.py` | Step 4 | AC-6 | `tests/db/test_sqlite_helper.py` | Confirmed by repository evidence |
| REQ-007 | AI Implementation Instruction: confirm each item, skip items already fixed, list open questions in the report | `docs/23_agent/agent_09_01_data-layer-session-db.md` | Step 5 | AC-7 | final report content | Explicit in issue |
