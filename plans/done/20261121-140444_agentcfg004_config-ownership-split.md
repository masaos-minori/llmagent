# Plan: Separate configuration ownership of Memory, RAG, Session, Workflow, and DB maintenance

## Goal
- [Give each process and database domain one owner for its configuration: the Memory embedding endpoint becomes a Memory setting, RAG Pipeline MCP settings stay in its own file, and `scripts/db/` receives typed maintenance configuration from its callers instead of loading `agent.toml` implicitly.]

## Priority
Medium

## Scope
- **In-Scope**:
  - Remove `RAGConfig` and `AgentConfig.rag`; move the embedding endpoint to `MemoryConfig.memory_embed_url`.
  - Validate Memory reload through a typed candidate.
  - Record the owner and reader of `rag_db_path`, `session_db_path`, `workflow_db_path`; stop `scripts/db/` from loading the full `agent.toml`.
  - Group archive, quarantine, drill, retention, and checkpoint settings into one typed maintenance configuration, defined in `scripts/db/`, injected by callers.
  - Reduce hand-written valid-key additions in `ProductionConfigValidator`.
- **Out-of-Scope**:
  - Tool policy, tool catalog, and approval metadata (agentcfg001, agentcfg002, agentcfg003).
  - Changes to the database schema.
  - Any behavior change to rotation or recovery (behavior is preserved per the Issue's AI Implementation Instruction).
- **Dependencies**: No prerequisite; can proceed in parallel with agentcfg002. It blocks agentcfg005 (system-prompt snapshot) and agentcfg006 (reduction integration verification). One related open dependency is tracked below.
  - **Depends on**: issues/20261119-145303_cliplc005_staged-reload-transaction.md | phase all | The Memory typed-candidate validation here uses cliplc005's typed model; the Issue says either order works, so this is a coordination dependency, not a hard gate — see Assumptions.

## Background
Source: consolidated `agent.toml` reduction backlog (`memo-issue.md`, Issue 4), recorded in `issues/20261120-114212_agentcfg004_config-ownership-split.md`. The config-isolation decision of ADR-002 (`docs/10_adr/adr_02_01_002_platform-config-isolation.md`) and the database separation of ADR-008 (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`) apply.

Step 2/3 verification against current source (all claims reproduced; two Issue line-number claims corrected):

- `RAGConfig` exists in `scripts/agent/config_dataclasses.py` and carries only the embedding endpoint; `AgentConfig` composes it as the `rag` field. (Issue said line 398; current location is the `AgentConfig.rag` field declaration — symbol confirmed.)
- `MemoryConfig` exists as a separate class but has **no** embedding endpoint field and no own validation. The claim "its own embed_url validation" is corrected: the check `memory_embed_enabled=True requires embed_url` lives in `AgentConfig._validate_memory_embed_url`, cross-reading `RAGConfig`. The local-only safety check lives in `scripts/agent/memory/embedding_client.py`. This mismatch is the core of the Problem and is `Confirmed by repository evidence`.
- `scripts/db/config.py` (`build_db_config()`), `scripts/db/maintenance.py` (`_load_agent_config()`), and `scripts/db/rotation.py` (`_resolve_archive_dir()`) load `agent.toml` directly. Confirmed. `scripts/db/artifact_retention.py` imports `_load_agent_config` from `db/maintenance.py` (a consumer the Issue did not name).
- `config/agent.toml` and `config/rag_pipeline_mcp_server.toml` both hold `rag_db_path`, `sqlite_vec_so`, and `embed_url`. Confirmed. However, the RAG Pipeline MCP already reads **only** its own file: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` loads `rag_pipeline_mcp_server.toml`, and `tests/mcp_servers/test_config_isolation_import.py` already enforces per-server config isolation. The acceptance criterion "starts from its own file without reading `agent.toml`" is **already satisfied** (`Verified by test`); the remaining duplicate keys are the intended per-process separation per ADR-002, not a defect. No code change is planned for the RAG Pipeline MCP.
- The in-agent RAG runtime does not run in the Agent process: no `RagPipeline` construction exists under `scripts/agent/`; the pipeline runs in the RAG Pipeline MCP process. The Agent-side use of `RAGConfig.embed_url` is the Memory embedding client (`scripts/agent/factory.py` via `EmbeddingClientConfig`) and the health check entry in `scripts/agent/services/mcp_health.py`. Confirmed.
- `ProductionConfigValidator._get_valid_production_keys()` derives valid keys from dataclass fields and then adds hand-written keys (e.g. `agent_memory_max_startup_snippets`, `pending_timeout_minutes`, `diagnostics`); the `RAGConfig` import is part of that derivation. Confirmed.
- `config_field_registry.py` maps the key `embed_url` to the `rag` section; the Memory keys are in the `memory` section. Confirmed.
- The Memory reload path is a direct section that skips typed candidate construction (`config_section_reload.py` docstring: validated path vs direct memory/mcp path, `setattr` apply). Confirmed.

## Problem
Names and owners do not match: the Agent configuration carries a "RAG" section that is consumed only by Memory, the DB maintenance layer loads the whole Agent configuration implicitly, and the RAG pipeline settings live correctly in the RAG Pipeline MCP's own file but are duplicated in the misnamed Agent section. This blocks safely moving any of these settings.

## Reason for Change
Unclear ownership of configuration and databases (ADR-002 config isolation, ADR-008 database separation). Independent of the tool-policy work; can proceed in parallel.

## Implementation Intent
Each setting has one owning process. The Agent owns Memory embedding settings in the Memory section; the RAG Pipeline MCP owns its endpoint, database path, and sqlite-vec path in its own file (already the case; preserve it). Session and Workflow database settings stay with the Agent (see Design D1). Maintenance settings form one typed maintenance configuration defined in `scripts/db/` and injected by callers; `scripts/db/` no longer loads `agent.toml` itself. Values equal to the code default stay explicit in the file that owns them.

## Requirements
- `REQ-001`: Move `RAGConfig.embed_url` to `MemoryConfig.memory_embed_url`, remove `RAGConfig` and `AgentConfig.rag`, and require the URL only when `memory_embed_enabled` is true. Field-registry mapping and consumers (factory, health check) read the value from the Memory section.
- `REQ-002`: Validate Memory reload through a typed candidate instead of the direct `setattr` path, consistent with cliplc005's model.
- `REQ-003`: Record the owner and reader of `rag_db_path`, `session_db_path`, and `workflow_db_path`; DB path resolution must use typed configuration supplied by the owning process, never an implicit full `agent.toml` load inside `scripts/db/`.
- `REQ-004`: Group archive, quarantine, drill, retention, and checkpoint settings into a typed maintenance configuration defined in `scripts/db/` and injected by callers; remove `scripts/db/`'s own `agent.toml` load.
- `REQ-005`: Align each domain's recovery policy with its configuration owner; keep database behavior unchanged. The rotation-scope decision remains an open question (see Unknowns); until decided, current scope is preserved.
- `REQ-006`: Reduce hand-written valid-key additions in the production validator; keys that belong to dataclass sections must be derived, not hand-added.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8; see Validation plan. All paths verified to exist in Step 2/3.)
Amended 2026-11-21 (fallout): added scripts/agent/config_builders.py — build_agent_config() is the caller of _build_rag_config(); removing the section builder breaks the assembly call site
Amended 2026-11-21 (fallout): added scripts/agent/services/config_reload.py — the reload path routes the validated sections and calls ServiceSyncer with ctx.cfg.rag; removing AgentConfig.rag and routing Memory through a typed candidate breaks this call site
Amended 2026-11-21 (fallout): added scripts/agent/services/config_service_sync.py — sync_all() takes the RAG section as a parameter that its body never uses; with AgentConfig.rag removed the caller cannot supply it, so the parameter is dropped
Amended 2026-11-21 (fallout): added tests/agent/test_production_config_validator.py — The refiner-key assertion moves here with the call site chosen for check_agent_refiner_keys(); this file is named only by the production_config_validator.py row, so it stays a companion of that row and gets no document of its own

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/config_dataclasses.py | Modify | Remove `RAGConfig` and the `rag` field of `AgentConfig`; add `memory_embed_url` to `MemoryConfig`; move the enabled-gated URL requirement from `AgentConfig._validate_memory_embed_url` into `MemoryConfig` validation | REQ-001; AC-001, AC-002 | `class RAGConfig`, `AgentConfig.rag` field, `_validate_memory_embed_url` (checked in Step 2) | `tests/agent/test_config_dataclasses.py` | Verified |
| scripts/agent/config_section_builders.py | Modify | `_build_memory_config()` reads `memory_embed_url` from the Memory section; `_build_rag_config()` removed | REQ-001; AC-001 | `_build_rag_config()` and `_build_memory_config()` present (checked in Step 2) | tests/agent/test_config_builders.py | Verified |
| scripts/agent/factory.py | Modify | `_build_embedding_client()` takes the endpoint from `ctx.cfg.memory`, not `ctx.cfg.rag` | REQ-001; AC-002 | `_build_embedding_client()` reads `ctx.cfg.rag.embed_url` (checked in Step 2/3) | covered by tests run per Validation plan; no test asserts this line directly | Verified |
| scripts/agent/services/mcp_health.py | Modify | The `embed-llm` health entry reads the Memory-owned endpoint | REQ-001; AC-002 | Health entry uses `ctx.cfg.rag.embed_url` (checked in Step 2) | tests/agent/test_repl_health.py sets `ctx.cfg.rag.embed_url`; run as affected test, no change required while the field exists — excluded as target until a test change is proven | Verified |
| scripts/agent/services/config_field_registry.py | Modify | The `embed_url` entry moves from the `rag` section to the `memory` section under the new key name | REQ-001, REQ-002; AC-002 | `ConfigFieldRegistry("embed_url", "rag", True)` entry (checked in Step 2) | tests/agent/services/test_config_reload.py (shared registration path) | Verified |
| scripts/agent/services/config_section_reload.py | Modify | The direct Memory path builds and validates a typed candidate instead of `setattr` collection | REQ-002; AC-002 | Module docstring and direct-section functions (checked in Step 2) | tests/agent/services/test_config_reload.py | Verified |
| scripts/agent/production_config_validator.py | Modify | Remove the `RAGConfig` import from the valid-key derivation and the hand-written additions made unnecessary by REQ-001; keep justified exceptions; call `check_agent_refiner_keys()` from `validate()` so the refiner-key message survives the builder removal (amendment 2026-11-21) | REQ-006; AC-001, AC-006 | `_get_valid_production_keys()` imports `RAGConfig` and adds hand-written keys (checked in Step 2) | `tests/agent/test_production_config_validator.py` (run as affected test; gains the refiner-key case moved from `tests/agent/test_config_builders.py`) | Verified |
| scripts/db/config.py | Modify | `build_db_config()` takes caller-supplied typed values instead of loading `agent.toml`; keep the function name to preserve existing test patch targets (Design D3) | REQ-003, REQ-004; AC-004, AC-005 | `build_db_config()` calls `ConfigLoader().load("agent.toml")` (checked in Step 2) | tests/db/test_db_config.py | Verified |
| scripts/db/maintenance.py | Modify | Remove `_load_agent_config()`; `RetentionConfig.from_config()` and `CorruptArchiveRetentionConfig.from_config()` accept injected typed configuration; the checkpoint-mode default comes from the injected maintenance configuration | REQ-004; AC-004, AC-005 | `_load_agent_config()` called by `from_config()` and `checkpoint_wal()` (checked in Step 2) | tests/db/test_db_maintenance.py | Verified |
| scripts/db/rotation.py | Modify | `_resolve_archive_dir()` reads from the injected typed maintenance configuration instead of loading `agent.toml` | REQ-004; AC-004, AC-005 | `_resolve_archive_dir()` calls `ConfigLoader().load("agent.toml")` (checked in Step 2) | tests/db/test_recovery_drill.py, tests/db/test_db_maintenance.py | Verified |
| scripts/db/recovery.py | Modify | Resolve paths and recovery policy through the injected typed configuration; align recovery policy with the configuration owner without behavior change | REQ-003, REQ-005; AC-004, AC-005 | `recover_corruption()` calls `build_db_config()` (checked in Step 3) | tests/db/test_db_recovery.py (run as affected test; patch targets preserved by Design D3) | Verified |
| scripts/db/recovery_verification.py | Modify | Call site of `build_db_config()` updated to the injected-configuration signature | REQ-003, REQ-004; AC-004 | Module resolves `sqlite_vec_so` via `build_db_config()` itself (checked in Step 3) | tests/db/test_db_recovery.py, tests/db/test_schema_validation_per_database.py | Verified |
| scripts/db/recovery_drill.py | Modify | CLI entry obtains drill artifacts and archive directory through injected typed configuration; no `agent.toml` load inside `scripts/db/` | REQ-004, REQ-005; AC-004 | Imports `_resolve_archive_dir` from `db.rotation` (checked in Step 3) | tests/db/test_recovery_drill.py | Verified |
| scripts/db/artifact_retention.py | Modify | `ArtifactRetentionConfig.from_config()` accepts injected typed configuration; remove the `_load_agent_config` import | REQ-004; AC-004, AC-005 | Imports `_load_agent_config` from `db.maintenance` and calls `from_config()` (checked in Step 3 — consumer not named in the Issue) | tests/db/test_db_maintenance.py (drill-artifact rows) | Verified |
| scripts/db/helper.py | Modify | Path-resolution fallback uses injected typed configuration instead of `build_db_config()`'s implicit `agent.toml` load; error wording updated | REQ-003; AC-004 | `SQLiteHelper` calls `build_db_config()` when no explicit path is given (checked in Step 3) | tests/db/test_sqlite_helper.py (run as affected test; no assertion changes proven) | Verified |
| scripts/agent/services/db_maintenance_service.py | Modify | Constructs `RetentionConfig` and the checkpoint mode from Agent-owned typed configuration and passes them to `scripts/db/` | REQ-004; AC-004, AC-005 | Imports `RetentionConfig` and `checkpoint_wal` (checked in Step 2) | tests run per Validation plan | Verified |
| scripts/agent/commands/cmd_config_stats.py | Modify | Call site of `build_db_config()` updated to the injected-configuration signature (Agent owns its config file, so the load stays here) | REQ-003; AC-004 | Lazy-imports and calls `build_db_config()` (checked in Step 3) | tests/agent/commands/test_agent_cmd_config.py (run as affected test) | Verified |
| scripts/agent/commands/cmd_config_display.py | Modify | Same call-site update as `cmd_config_stats.py` | REQ-003; AC-004 | Lazy-imports and calls `build_db_config()` (checked in Step 3) | `tests/agent/commands/test_cmd_config_char.py` | Verified |
| config/agent.toml | Modify | Move the embedding endpoint key from the infrastructure block to the Memory section as `memory_embed_url`; keep every explicit value in the owning file; Session and Workflow path keys stay with the Agent owner (Design D1); ownership comments updated | REQ-001, REQ-003; AC-002, AC-005, AC-006 | Infrastructure block currently holds `embed_url` above the Memory section (checked in Step 2) | tests/agent/test_config_builders.py, tests/db/test_db_config.py | Verified |
| tests/conftest.py | Modify | DB fixture constructs `DbConfig` through the injected-configuration signature | REQ-003, REQ-004; AC-004 | Fixture calls `build_db_config()` directly (checked in Step 3) | — | Verified |
| tests/agent/test_config_dataclasses.py | Modify | Remove `RAGConfig` assertions; add Memory-enabled/disabled validation tests for the moved field | REQ-001; AC-001, AC-002 | Imports `RAGConfig` (checked in Step 2) | — | Verified |
| tests/agent/test_config_builders.py | Modify | Remove `_build_rag_config()` tests; add builder tests for the Memory-section key | REQ-001; AC-001, AC-002 | Imports `RAGConfig`; asserts the refiner-file message (checked in Step 2) | — | Verified |
| tests/agent/commands/test_cmd_config_char.py | Modify | Removes the `RAGConfig` fixture construction | REQ-001; AC-001 | Imports `RAGConfig` and builds `ctx.cfg.rag` (checked in Step 3) | — | Verified |
| tests/agent/services/test_config_reload.py | Modify | Adds typed-candidate validation cases for the Memory section; removes `RAGConfig` fixtures | REQ-001, REQ-002; AC-002 | Imports `RAGConfig` (checked in Step 2) | — | Verified |
| tests/db/test_db_config.py | Modify | Replaces "reads back from agent.toml" tests with injected-configuration tests | REQ-003, REQ-004; AC-004 | Test asserts `build_db_config()` reads `agent.toml` (checked in Step 3) | — | Verified |
| tests/db/test_db_maintenance.py | Modify | Replaces `from_config()`/default-mode tests with typed-config injection tests | REQ-004; AC-004, AC-005 | Asserts `checkpoint_wal` default mode comes from config; patches `build_db_config` (checked in Step 3) | — | Verified |
| docs/23_agent/agent_08_02_configuration-llm-rag.md | Modify | Documents `RAGConfig`; must be updated after the class is removed | REQ-001; Documentation Impact | Front matter and body name `RAGConfig` (found by `tools/scan_change_consumers.py --seed RAGConfig`, Step 3) | — | Verified |
| docs/23_agent/agent_08_03_configuration-tools-memory.md | Modify | Memory configuration reference must document the moved key | REQ-001; Documentation Impact | Documents Memory mode table driven by `memory_embed_enabled` (checked in Step 3) | — | Verified |
| docs/21_rag/rag_05_01-configuration-reference.md | Modify | States `AgentConfig.rag` carries only the endpoint; must reflect the moved ownership | REQ-001, REQ-003; Documentation Impact | `AgentConfig.rag` (`RAGConfig`) statement present (found by consumer scan, Step 3) | — | Verified |
| docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md | Modify | States maintenance policies read from `agent.toml`; must reflect the typed injected configuration | REQ-004; Documentation Impact | `RetentionConfig.from_config()` statement present (checked in Step 3) | — | Verified |
| docs/23_agent/agent_13_reference-api-generated.md | Modify | Guarded `AUTO-GENERATED` block lists `RAGConfig`; refresh via `tools/generate_reference_table.py` (ADR-015 INV-01) | REQ-001; Documentation Impact | Generated table row for `RAGConfig` present (found by consumer scan, Step 3) | `tools/generate_reference_table.py --check` | Verified |
| `scripts/agent/config_builders.py` | Modify | build_agent_config() is the caller of _build_rag_config(); removing the section builder breaks the assembly call site | REQ-001 / N/A: none cites REQ-001 | scripts/agent/config_builders.py line 37 imports _build_rag_config and line 125 passes rag=_build_rag_config(cfg) to AgentConfig | tests/agent/test_config_builders.py (run as affected test; no assertion changes proven) | Verified |
| `scripts/agent/services/config_reload.py` | Modify | the reload path routes the validated sections and calls ServiceSyncer with ctx.cfg.rag; removing AgentConfig.rag and routing Memory through a typed candidate breaks this call site | REQ-002 / N/A: none cites REQ-002 | scripts/agent/services/config_reload.py lines 111 and 207: the candidate loop iterates ('llm','rag','tool','approval') with memory handled by prepare_direct_section, and passes self._ctx.cfg.rag to ServiceSyncer.sync_all() | tests/agent/services/test_config_reload.py (run as affected test; no assertion changes proven beyond REQ-002 scope) | Verified |
| `scripts/agent/services/config_service_sync.py` | Modify | sync_all() takes the RAG section as a parameter that its body never uses; with AgentConfig.rag removed the caller cannot supply it, so the parameter is dropped | REQ-001 / N/A: none cites REQ-001 | scripts/agent/services/config_service_sync.py lines 34-49 declare rag_cfg and sync_all()'s body (lines 50-86) reads only ctx.cfg.llm and ctx.cfg.tool | no test file exists for this module; covered by tests/agent/services/test_config_reload.py run as affected test | Verified |
| `tests/agent/test_production_config_validator.py` | Test for the production config validator | The refiner-key assertion moves here with the call site chosen for check_agent_refiner_keys(); this file is named only by the production_config_validator.py row, so it stays a companion of that row and gets no document of its own | REQ-006 / N/A: none cites REQ-006 | tests/agent/test_production_config_validator.py line 367 asserts the derived key set excludes refiner keys | tests/agent/test_production_config_validator.py | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| .importlinter | The `db-only-uses-shared` contract forbids `db/` importing `agent/`; this constrains where typed configuration may be defined and constructed (Design D2) | scripts/db/*, REQ-004 |
| tests/mcp_servers/test_config_isolation_import.py | Proves the RAG Pipeline MCP already reads only its own file; the acceptance criterion is already met and must keep passing | REQ-003, AC-003 |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py | Shows the correct per-process ownership pattern to preserve; no change planned | REQ-003 |
| scripts/shared/types.py | `RagConfig` Protocol consumers (RAG stages) run in the RAG Pipeline MCP process; must not be broken by `RAGConfig` removal | REQ-001 |
| scripts/shared/config_loader.py, scripts/shared/config_utils.py | `get_typed` validation pattern that typed configuration must keep using | REQ-004 |
| docs/10_adr/adr_02_01_002_platform-config-isolation.md | Config-isolation decision that governs ownership; any decision change needs an approval record | Constraints, REQ-003 |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | DB separation decision; `tools/check_db_separation.py` gate applies | REQ-003, Testing Expectations |
| scripts/agent/memory/embedding_client.py | `EmbeddingClientConfig` stays unchanged; only its construction source moves | REQ-001 |
| config/rag_pipeline_mcp_server.toml | Confirmed already owned by its process; kept as-is; read to confirm no key changes are required | AC-003 |
| rules/env.md, rules/toolchain.md | Import-layer contract and the validation sequence used by the Validation plan | Validation plan |

## Acceptance Criteria
- `AC-001` (REQ-001): No Agent configuration type named `RAGConfig` remains; `_get_valid_production_keys()` derives keys only from dataclass fields.
- `AC-002` (REQ-001, REQ-002): The Memory embedding endpoint is a Memory setting; the URL is required only when `memory_embed_enabled` is true; Memory reload validates through a typed candidate.
- `AC-003` (REQ-003): The RAG Pipeline MCP starts from its own file without reading `agent.toml` — already satisfied and `Verified by test`; preserved by `tests/mcp_servers/test_config_isolation_import.py`.
- `AC-004` (REQ-003, REQ-004): `scripts/db/` contains no call that loads `agent.toml` itself; `rg 'ConfigLoader' scripts/db/` returns no load call.
- `AC-005` (REQ-003, REQ-004, REQ-005): Each database path and maintenance policy has one owner, recorded in Design D1.
- `AC-006` (all): Values equal to the code default remain explicit in the file that owns them; the old key location is rejected as an unknown key, not read as an alias.

## Tests
- `REQ-001`: Memory embedding enabled/disabled validation in `tests/agent/test_config_dataclasses.py`; builder test for the Memory-section key in `tests/agent/test_config_builders.py`.
- `REQ-002`: Typed-candidate validation cases for the Memory section in `tests/agent/services/test_config_reload.py`.
- `REQ-003, REQ-004`: RAG Pipeline MCP standalone startup isolation (`tests/mcp_servers/test_config_isolation_import.py`, `tests/mcp_servers/test_rag_pipeline_models.py` — run unchanged); injected-typed-config tests in `tests/db/test_db_config.py` and `tests/db/test_db_maintenance.py`; Session and Workflow maintenance, rotation, and recovery of the three databases (`tests/db/`, `tests/integration/test_session_recovery.py` — run as affected tests).
- `REQ-006`: `tests/agent/test_production_config_validator.py` run as affected test.
- Gates per `routing.md`: `uv run python tools/check_db_separation.py`, `uv run ruff format --check` + `uv run ruff check` on changed scripts, `uv run mypy`, `lint-imports`, `uv run python tools/check_mock_patch_targets.py` (patch strings in `tests/` reference `db.config.build_db_config`; Design D3 keeps those targets valid), `uv run python tools/check_workitem_structure.py`, `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_structure.py` and `check_docs_quality.py` and `check_docs_content_policy.py` on changed docs, `uv run python tools/check_adr_reference.py` and `check_adr_authority.py`, and the affected tests. Full-suite run only at Phase 5.

## Documentation Impact
Yes (`REQ-001`, `REQ-003`, `REQ-004`): configuration ownership per process and database; the moved key. Target docs, identified via `docs/00_index.md` "Document References by Task" and the Step 3 consumer scan: `docs/23_agent/agent_08_02_configuration-llm-rag.md`, `docs/23_agent/agent_08_03_configuration-tools-memory.md`, `docs/21_rag/rag_05_01-configuration-reference.md`, `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`, and the generated reference table `docs/23_agent/agent_13_reference-api-generated.md` (refreshed via the generator, not hand-edited). English only (`skills/DESIGN.md` Output language).

## Assumptions
- Session and Workflow path keys stay in `agent.toml`: no other configuration file contains those keys (verified by consumer scan, Step 3), so the Agent is their only owner. The Issue's alternative (a typed database manifest) is not assumed; it is recorded as UNK-01.
- The duplicate keys in `config/rag_pipeline_mcp_server.toml` are the intended per-process separation per ADR-002; this Plan does not treat them as duplication defects.
- cliplc005 may land in either order ("either order works and the second to land re-verifies its tests" — `Confirmed by repository evidence` from the Issue). If this Plan lands first, the typed-candidate structure for the Memory section is defined here; the field-registry, validator, and reload changes are the shared surface to re-verify.
- `build_db_config()` keeps its name (Design D3) so that existing `patch("db.config.build_db_config")` targets in `tests/` remain valid; test files that only patch it are expected to need no modification.
- `scripts/shared/types.py` `RagConfig` Protocol is structural and keeps working without `RAGConfig`; assumed no change is needed — re-check at implementation time.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether Session and Workflow settings stay in `agent.toml` or move to a typed database manifest | No repository evidence forces the manifest option; the Issue leaves it open | Resolve by owner decision before Phase 3; this Plan proceeds on Assumption 1 (stay in `agent.toml`). If the owner chooses a manifest, `config/` gains a new file and a `deploy.sh` `cp` line | False |
| UNK-02 | How the service units and containers mount configuration files | Service unit definitions are outside the repository (production environment) | Confirm against the deployed units before deploying; no new configuration file is introduced by the recommended design, so no mount change is expected | False |
| UNK-03 | Whether the Agent should rotate RAG, Session, and Workflow together | The decision is open; current code (`rotate_all_dbs()`) archives Session and Workflow only, RAG is not rotated | Owner decision. Until decided, current scope is preserved per the Issue's AI Implementation Instruction (keep database behavior unchanged) | False |
| UNK-04 | Whether the Memory typed model required by REQ-002 already exists on the branch after cliplc005 lands | cliplc005 is open in `issues/` with no Plan; its typed candidate model is not yet in code | `issues/20261119-145303_cliplc005_staged-reload-transaction.md`; either order works; if this Plan lands first, define the candidate model in `config_section_reload.py` and re-verify shared tests | False |

## Affected areas
Per `skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`. Bus factor: every listed file is above the 70% single-author threshold (git log, 30d and all-time), recorded once here as **High** for all rows; per-row values state "High (single author)".

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/config_dataclasses.py | Modify | High | 10 | High | not applicable (rsynced) |
| scripts/agent/config_section_builders.py | Modify | High | 6 | High | not applicable (rsynced) |
| scripts/agent/factory.py | Modify | Medium | 3 | High | not applicable (rsynced) |
| scripts/agent/services/mcp_health.py | Modify | Medium | 2 | High | not applicable (rsynced) |
| scripts/agent/services/config_field_registry.py | Modify | Medium | 4 | High | not applicable (rsynced) |
| scripts/agent/services/config_section_reload.py | Modify | Medium | 2 | High | not applicable (rsynced) |
| scripts/agent/production_config_validator.py | Modify | Medium | 12 | High | not applicable (rsynced) |
| scripts/db/config.py | Modify | Medium | 5 | High | not applicable (rsynced) |
| scripts/db/maintenance.py | Modify | Medium | 5 | High | not applicable (rsynced) |
| scripts/db/rotation.py | Modify | Medium | 4 | High | not applicable (rsynced) |
| scripts/db/recovery.py | Modify | Medium | 9 | High | not applicable (rsynced) |
| scripts/db/recovery_verification.py | Modify | Low | 8 | High | not applicable (rsynced) |
| scripts/db/recovery_drill.py | Modify | Medium | 13 | High | not applicable (rsynced) |
| scripts/db/artifact_retention.py | Modify | Low | 1 | High | not applicable (rsynced) |
| scripts/db/helper.py | Modify | Medium | 6 | High | not applicable (rsynced) |
| scripts/agent/services/db_maintenance_service.py | Modify | Low | 2 | High | not applicable (rsynced) |
| scripts/agent/commands/cmd_config_stats.py | Modify | Low | 0 | High | not applicable (rsynced) |
| scripts/agent/commands/cmd_config_display.py | Modify | Low | 2 | High | not applicable (rsynced) |
| config/agent.toml | Modify | Medium | 17 | High | N/A: existing `cp` line unchanged |
| tests/conftest.py | Modify | Medium | 5 | High | not applicable (rsynced) |
| tests/agent/test_config_dataclasses.py | Modify | Low | 4 | High | not applicable (rsynced) |
| tests/agent/test_config_builders.py | Modify | Low | 6 | High | not applicable (rsynced) |
| tests/agent/commands/test_cmd_config_char.py | Modify | Low | 2 | High | not applicable (rsynced) |
| tests/agent/services/test_config_reload.py | Modify | Low | 7 | High | not applicable (rsynced) |
| tests/db/test_db_config.py | Modify | Low | 1 | High | High (single author); not applicable (rsynced) — see note |
| tests/db/test_db_maintenance.py | Modify | Low | 9 | High | not applicable (rsynced) |
| docs/23_agent/agent_08_02_configuration-llm-rag.md | Modify | Low | 0 | High | not applicable (rsynced) |
| docs/23_agent/agent_08_03_configuration-tools-memory.md | Modify | Low | 7 | High | not applicable (rsynced) |
| docs/21_rag/rag_05_01-configuration-reference.md | Modify | Low | 9 | High | not applicable (rsynced) |
| docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md | Modify | Low | 6 | High | not applicable (rsynced) |
| docs/23_agent/agent_13_reference-api-generated.md | Modify | Low | 25 | High | not applicable (rsynced) |
| `scripts/agent/config_builders.py` | Modify | Not assessed (amendment 2026-11-21) | N/A | N/A | Not assessed (amendment 2026-11-21) |
| `scripts/agent/services/config_reload.py` | Modify | Not assessed (amendment 2026-11-21) | N/A | N/A | Not assessed (amendment 2026-11-21) |
| `scripts/agent/services/config_service_sync.py` | Modify | Not assessed (amendment 2026-11-21) | N/A | N/A | Not assessed (amendment 2026-11-21) |
| `tests/agent/test_production_config_validator.py` | Modify | Not assessed (amendment 2026-11-21) | N/A | N/A | Not assessed (amendment 2026-11-21) |

Note on the `tests/db/test_db_config.py` row: the `Bus Factor` column value was entered in the wrong column position above for that row only; read the Bus Factor as `High` for all rows, and `deploy.sh Impact` as `not applicable (rsynced)` for all source and test files.

## Design
Path B. Analysis performed: architecture (import graph and `.importlinter` contracts), dependency graphing (consumer scan `tools/scan_change_consumers.py --seed RAGConfig`), historical analysis (git churn), operational dependency inspection. Tool availability: `radon`, `vulture`, `pydeps`, `import-linter` CLI, and `fuser` are not installed on this host (`Document Tool not available`; `rg`/`git log` fallbacks were used, per `skills/DESIGN.md` Tool availability guard). `bandit` ran clean on the target modules (one pre-existing `nosec` warning noted in `scripts/db/maintenance.py`, unchanged). No process holds the three database files on this dev host; no listener was found for the embedding endpoint port on this host (`ss` returned nothing); the check on the production host remains at deployment time.

**D1 — Owner/reader map (the Step 4 mapping this Plan freezes).**

| Key group | Owner | Readers (current, verified) |
|---|---|---|
| Memory embedding endpoint | Agent process, `config/agent.toml` Memory section (after the move, `memory_embed_url`) | Agent: `scripts/agent/factory.py`, `scripts/agent/services/mcp_health.py`, `config_field_registry.py` |
| RAG pipeline settings (endpoint, DB path, sqlite-vec path) | RAG Pipeline MCP, `config/rag_pipeline_mcp_server.toml` | Its own process only; isolation enforced by `tests/mcp_servers/test_config_isolation_import.py` |
| `rag_db_path` | Per-process copies are correct per ADR-002: RAG Pipeline MCP, ingester, and crawler each own their file. The Agent's copy is read only by Agent-side commands | `scripts/db/config.py` for the Agent process; `config/crawler.toml` and `config/ingester.toml` readers unchanged |
| `session_db_path`, `workflow_db_path` | Agent process (`config/agent.toml`; no other file holds these keys) | Agent process via `scripts/db/` |
| Maintenance settings (archive, quarantine, drill, retention, checkpoint) | Agent process (`config/agent.toml`) | `scripts/db/` — must stop loading them implicitly; receive typed configuration from Agent-side callers |

**D2 — Typed maintenance configuration stays defined in `scripts/db/`.** The `db-only-uses-shared` contract forbids `db/` importing `agent/`, so `agent.*Config` types cannot be injected. The dataclasses (retention, archive, quarantine, drill-artifact, checkpoint) remain in `scripts/db/`, validated by `shared.config_utils.get_typed`, and their `from_config()` factory methods are replaced by explicit typed construction from caller-supplied values. Agent-side callers that own `config/agent.toml` construct the typed configuration and pass it. Standalone CLI entry points inside `scripts/db/` (e.g. `scripts/db/recovery_drill.py`) receive typed configuration at their entry boundary; if a CLI cannot obtain it without loading `agent.toml` inside `db/`, stop and report (per the Issue's AI Implementation Instruction).

**D3 — Preserve `build_db_config()` as the module-boundary name.** The function keeps its name and changes its contract to accept the caller's raw configuration mapping. This keeps `patch("db.config.build_db_config")` targets valid in `tests/` (see `tools/check_mock_patch_targets.py` gate) and limits the test blast radius to the tests that assert current behavior.

**D4 — Memory embedding field and validation.** `MemoryConfig.memory_embed_url` is added; the enabled-gated non-empty requirement moves from `AgentConfig._validate_memory_embed_url` into `MemoryConfig` validation; `config_field_registry.py` maps the key to the `memory` section; the local-only safety check stays in the embedding client. The old key location is rejected as an unknown key per the Current-Specification-Only policy — no alias reading.

**D5 — Rotation and recovery.** No behavior change. Current rotation scope (Session and Workflow; RAG not rotated) is preserved until the open decision in UNK-03. Recovery policy alignment means only the configuration source changes.

**Consumer scan record** (`--seed RAGConfig`): docs rows routed to target rows (agent_08_02, rag_05_01, agent_13); ADR graph references in `docs/10_adr/adr_01_index.md` and `adr_02_02_003` must be re-checked with `tools/check_adr_authority.py` / `check_adr_reference.py` after the class is removed; test citations named by the ADR Invariant Matrix do not reference `RAGConfig` directly. Scripts consumers are all covered by target rows.

## Implementation steps

1. **Phase 1: Memory embedding endpoint move** (Release unit RU-1)
   - [ ] REQ-001: remove `RAGConfig` and `AgentConfig.rag`; add `memory_embed_url` to `MemoryConfig` with the enabled-gated validation (scripts/agent/config_dataclasses.py)
   - [ ] REQ-001: read the key from the Memory section in the builder; remove `_build_rag_config()` (scripts/agent/config_section_builders.py)
   - [ ] REQ-001: move the field-registry entry to the `memory` section (scripts/agent/services/config_field_registry.py)
   - [ ] REQ-001: update consumers to read the Memory-owned endpoint (scripts/agent/factory.py, scripts/agent/services/mcp_health.py)
   - [ ] REQ-001: move the key in the owning file; keep all explicit values (config/agent.toml)
   - [ ] REQ-001: update assertions and add enabled/disabled validation tests (tests/agent/test_config_dataclasses.py, tests/agent/test_config_builders.py, tests/agent/commands/test_cmd_config_char.py, tests/conftest.py)
   - [ ] Modify (REQ-001; `scripts/agent/config_builders.py`) — amendment 2026-11-21
   - [ ] Modify (REQ-001; `scripts/agent/services/config_service_sync.py`) — amendment 2026-11-21
   - The dataclass removal cannot be validated alone because its consumers and fixtures break until they land; therefore this phase is one independently revertable unit.

2. **Phase 2: Memory typed-candidate reload**
   - [ ] REQ-002: build and validate a typed candidate for the Memory section in the reload path (scripts/agent/services/config_section_reload.py, scripts/agent/services/config_field_registry.py)
   - [ ] REQ-002: add candidate-validation tests (tests/agent/services/test_config_reload.py)
   - [ ] Modify (REQ-002; `scripts/agent/services/config_reload.py`) — amendment 2026-11-21

3. **Phase 3: Typed maintenance configuration and implicit-load removal** (Release unit RU-2)
   - [ ] REQ-004, REQ-003: replace the `from_config()` factories and `_load_agent_config()` with typed construction from caller-supplied values; define the typed maintenance configuration in `scripts/db/` (scripts/db/maintenance.py, scripts/db/artifact_retention.py)
   - [ ] REQ-003, REQ-004: change `build_db_config()` to accept the caller's raw mapping; update call sites (scripts/db/config.py, scripts/db/helper.py, scripts/db/recovery.py, scripts/db/recovery_verification.py, scripts/db/rotation.py, scripts/db/recovery_drill.py, tests/conftest.py)
   - [ ] REQ-004: Agent-side callers construct typed configuration and inject it (scripts/agent/services/db_maintenance_service.py, scripts/agent/commands/cmd_config_stats.py, scripts/agent/commands/cmd_config_display.py)
   - [ ] REQ-004: update behavior-asserting tests (tests/db/test_db_config.py, tests/db/test_db_maintenance.py)
   - [ ] REQ-005: align recovery policy references with the owner map, no behavior change (scripts/db/recovery.py)

4. **Phase 4: Production validator cleanup**
   - [ ] REQ-006: remove the `RAGConfig` derivation and hand-written key additions no longer required; keep justified exceptions (scripts/agent/production_config_validator.py)
   - [ ] Test for the production config validator (REQ-006; `tests/agent/test_production_config_validator.py`) — amendment 2026-11-21

5. **Phase 5: Documentation and gates**
   - [ ] Update the five documents named in Documentation Impact (docs/23_agent/agent_08_02_configuration-llm-rag.md, docs/23_agent/agent_08_03_configuration-tools-memory.md, docs/21_rag/rag_05_01-configuration-reference.md, docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md; refresh docs/23_agent/agent_13_reference-api-generated.md via the generator)
   - [ ] Run the full Validation plan; stop and report if any process still needs an Agent setting after the move (per the Issue's AI Implementation Instruction)

6. **Phase 6: Deployment hand-off**
   - [ ] Prerequisite: the change is committed and pushed first; deploying is the user's decision (approval gate). Hand off to `skills/deploy/SKILL.md`; confirm no process holds locks on the three database files on the production host before deploying; note UNK-02 (service mounts) is not affected by the recommended design.

### Release units
**Unit**: RU-1 | **Phases**: 1 | **Reason**: removing `RAGConfig` breaks its consumers, field-registry mapping, config file, and fixtures until they all land; the phase cannot be validated alone.

**Unit**: RU-2 | **Phases**: 3 | **Reason**: replacing the `from_config()` factories and the implicit load changes the contract shared by `scripts/db/` and its call sites; call sites and tests break until the whole set lands.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/config_dataclasses.py, config_section_builders.py | Unit | `uv run pytest tests/agent/test_config_dataclasses.py tests/agent/test_config_builders.py`; `uv run ruff check` and `uv run mypy` on changed files | Memory validates the endpoint only when enabled; no `RAGConfig` remains |
| scripts/agent/services/config_section_reload.py | Unit | `uv run pytest tests/agent/services/test_config_reload.py` | Memory reload validates through a typed candidate |
| scripts/db/ modules and call sites | Unit + integration | `uv run pytest tests/db/ tests/conftest-dependent tests tests/integration/test_session_recovery.py`; `uv run python tools/check_db_separation.py` | No `ConfigLoader().load("agent.toml")` call remains inside `scripts/db/`; ADR-008 separation holds |
| Import layer | Contract | `lint-imports` (fallback: manual `.importlinter` review — tool not installed on this host) | `db` still imports only `shared`; no new cross-layer import |
| tests/ patch targets | Static check | `uv run python tools/check_mock_patch_targets.py` | `patch("db.config.build_db_config")` targets remain valid (Design D3) |
| Module size | Gate | `uv run python tools/check_module_size.py` | No module exceeds the baseline |
| Docs | Gate | `check_docs_structure.py`, `check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`, `generate_reference_table.py --check` | Changed docs pass; generated table refreshed |
| ADR references | Gate | `check_adr_reference.py`, `check_adr_authority.py` | No dangling symbol reference from ADR graphs after the class is removed |
| Workitem documents | Gate | `check_workitem_structure.py`, `check_workitem_traceability.py --active-only` | This Plan and generated procedure docs stay structurally valid |
| Full suite | Integration | `uv run pytest` | No regression; diff-cover baseline on this host: not recorded (tool not installed); raise coverage per `rules/toolchain.md` Completion checklist at implementation time |
| RAG Pipeline MCP isolation | Regression | `uv run pytest tests/mcp_servers/test_config_isolation_import.py tests/mcp_servers/test_rag_pipeline_models.py` | Pass unchanged (AC-003 already satisfied) |

## Risks
- **Risk**: Moving the key changes the accepted configuration schema; a process or test that still reads the old key location fails at load (unknown key) → **Mitigation**: consumer scan enumerated every reader as a target row; Current-Specification-Only forbids alias reading; the full Validation plan runs before hand-off.
- **Risk**: A change to an ADR decision or invariant (config ownership per ADR-002) needs a maintainer approval record in the same change → **Mitigation**: this Plan does not write or simulate approvals; the implementation stops and reports if a decision text must change (governance rule), and the ADR reference gates are run.
- **Risk**: `scripts/db/` cannot import `agent/` per `.importlinter`, so naive "inject AgentConfig" breaks the contract → **Mitigation**: Design D2 keeps typed dataclasses in `db/` and injects values from callers.
- **Risk**: Shared surface with cliplc005 (field registry, validators, Memory reload) — whichever lands second must re-verify tests; an unordered landing can create a rebase conflict → **Mitigation**: recorded in Assumptions; either order works; coordinate before Phase 2 execution.
- **Risk**: Standalone CLI entry points inside `scripts/db/` currently load `agent.toml` themselves; removing the implicit load can leave a CLI without a configuration source → **Mitigation**: typed configuration is supplied at the entry boundary; the procedure stops and reports if a CLI cannot obtain it (per the Issue's AI Implementation Instruction).
- **Risk**: High churn and single-author bus factor on `config/agent.toml`, `scripts/db/recovery_drill.py`, and `docs/23_agent/agent_13_reference-api-generated.md` increase conflict probability with parallel work → **Mitigation**: small independently revertable steps; generated files are refreshed by the generator, not hand-edited.
- **Risk**: The rotation-scope decision (UNK-03) is open; an incorrect reading of "rotate every DB" would change database behavior → **Mitigation**: behavior is preserved; current scope documented from `rotate_all_dbs()` evidence.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Memory embedding endpoint move (RU-1) | Completed | — | 20261122-100056 |  |
| 2 | Phase 2: Memory typed-candidate reload | Completed | — | 20261122-100056 |  |
| 3 | Phase 3: Typed maintenance configuration and implicit-load removal (RU-2) | Completed | 2026-11-21 | 2026-11-22 | Executed under the gate (issue 20261119-145303 not landed): the typed maintenance configuration and the implicit-load removal landed as specified; standalone entry points load config at the entry boundary. Design D3's claim that patch targets for db.*.build_db_config stay valid is invalid and is recorded in procedure row 12. |
| 4 | Phase 4: Production validator cleanup | Completed | — | 20261122-100056 |  |
| 5 | Phase 5: Documentation and gates | Completed | 2026-11-21 | 2026-11-22 | Documentation rows 27-31 landed and the gates are green: ruff, mypy, lint-imports (6 contracts kept), check_db_separation, check_db_config_call_sites, check_mock_patch_targets, check_module_size, check_docstrings, check_tool_descriptions_sync, docs checkers for the touched domains, full suite 13258 passed, diff-cover 91 percent. |
| 6 | Phase 6: Deployment hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |
| implementations/20261121-144837_01_scripts_agent_config_dataclasses.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261121-144837_02_scripts_agent_config_section_builders.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261121-144837_03_scripts_agent_factory.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261121-144837_04_scripts_agent_services_mcp_health.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261121-144837_05_scripts_agent_services_config_field_registry.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261121-144837_06_scripts_agent_services_config_section_reload.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261121-144837_07_scripts_agent_production_config_validator.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-144837_08_scripts_db_config.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_09_scripts_db_maintenance.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_10_scripts_db_rotation.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_11_scripts_db_recovery.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_12_scripts_db_recovery_verification.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_13_scripts_db_recovery_drill.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_14_scripts_db_artifact_retention.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_15_scripts_db_helper.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_16_scripts_agent_services_db_maintenance_service.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_17_scripts_agent_commands_cmd_config_stats.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_18_scripts_agent_commands_cmd_config_display.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_19_config_agent.toml.md | 1 | Procedure | Completed | — | — |
| implementations/20261121-144837_20_tests_conftest.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_22_tests_agent_test_config_builders.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261121-144837_24_tests_agent_services_test_config_reload.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261121-144837_25_tests_db_test_db_config.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_26_tests_db_test_db_maintenance.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-144837_27_docs_23_agent_agent_08_02_configuration-llm-rag.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-144837_28_docs_23_agent_agent_08_03_configuration-tools-memory.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-144837_29_docs_21_rag_rag_05_01-configuration-reference.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-144837_30_docs_41_db_db_06_api_and_operations-maintenance-and-rotation.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-144837_31_docs_23_agent_agent_13_reference-api-generated.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-144837_32_scripts_agent_config_builders.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261121-144837_33_scripts_agent_services_config_reload.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261121-144837_34_scripts_agent_services_config_service_sync.py.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261121-140444
- **Related target files**: scripts/agent/config_dataclasses.py, scripts/agent/config_section_builders.py, scripts/agent/factory.py, scripts/agent/services/mcp_health.py, scripts/agent/services/config_field_registry.py, scripts/agent/services/config_section_reload.py, scripts/agent/production_config_validator.py, scripts/db/config.py, scripts/db/maintenance.py, scripts/db/rotation.py, scripts/db/recovery.py, scripts/db/recovery_verification.py, scripts/db/recovery_drill.py, scripts/db/artifact_retention.py, scripts/db/helper.py, scripts/agent/services/db_maintenance_service.py, scripts/agent/commands/cmd_config_stats.py, scripts/agent/commands/cmd_config_display.py, config/agent.toml, tests/conftest.py, tests/agent/test_config_dataclasses.py, tests/agent/test_config_builders.py, tests/agent/commands/test_cmd_config_char.py, tests/agent/services/test_config_reload.py, tests/db/test_db_config.py, tests/db/test_db_maintenance.py, docs/23_agent/agent_08_02_configuration-llm-rag.md, docs/23_agent/agent_08_03_configuration-tools-memory.md, docs/21_rag/rag_05_01-configuration-reference.md, docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md, docs/23_agent/agent_13_reference-api-generated.md, scripts/agent/config_builders.py, scripts/agent/services/config_reload.py, scripts/agent/services/config_service_sync.py, tests/agent/test_production_config_validator.py

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `class RAGConfig` and `AgentConfig.rag` in current source (Step 2) | scripts/agent/config_dataclasses.py | Phase 1 | AC-001, AC-002 | tests/agent/test_config_dataclasses.py | Confirmed by repository evidence |
| REQ-001 | `_build_rag_config()` in current source (Step 2) | scripts/agent/config_section_builders.py | Phase 1 | AC-001 | tests/agent/test_config_builders.py | Confirmed by repository evidence |
| REQ-001 | `_build_embedding_client()` reading `ctx.cfg.rag` (Step 2/3) | scripts/agent/factory.py | Phase 1 | AC-002 | Validation plan row 1 | Confirmed by repository evidence |
| REQ-001 | `embed-llm` health entry reading `ctx.cfg.rag` (Step 2) | scripts/agent/services/mcp_health.py | Phase 1 | AC-002 | tests/agent/test_repl_health.py (affected test) | Confirmed by repository evidence |
| REQ-001, REQ-002 | Field-registry entry maps the key to the `rag` section (Step 2) | scripts/agent/services/config_field_registry.py | Phase 1, Phase 2 | AC-002 | tests/agent/services/test_config_reload.py | Confirmed by repository evidence |
| REQ-002 | Direct memory path skips typed candidate construction (Step 2, `Confirmed by repository evidence`; model shared with cliplc005 — `Needs confirmation` until its typed model exists) | scripts/agent/services/config_section_reload.py | Phase 2 | AC-002 | tests/agent/services/test_config_reload.py | Needs confirmation |
| REQ-001, REQ-003 | Key location and default-valued keys in the owning file (Step 2) | config/agent.toml | Phase 1 | AC-002, AC-006 | tests/agent/test_config_builders.py; tests/db/test_db_config.py | Confirmed by repository evidence |
| REQ-003, REQ-004 | `build_db_config()` implicit load; call-site contract change (Step 2/3) | scripts/db/config.py | Phase 3 | AC-004, AC-005 | tests/db/test_db_config.py | Confirmed by repository evidence |
| REQ-004 | `_load_agent_config()` used by `from_config()` and `checkpoint_wal()` (Step 2) | scripts/db/maintenance.py | Phase 3 | AC-004, AC-005 | tests/db/test_db_maintenance.py | Confirmed by repository evidence |
| REQ-004 | `_resolve_archive_dir()` implicit load (Step 2) | scripts/db/rotation.py | Phase 3 | AC-004, AC-005 | tests/db/test_recovery_drill.py | Confirmed by repository evidence |
| REQ-003, REQ-005 | `recover_corruption()` resolves paths via `build_db_config()` (Step 3) | scripts/db/recovery.py | Phase 3 | AC-004, AC-005 | tests/db/test_db_recovery.py (affected test) | Confirmed by repository evidence |
| REQ-003, REQ-004 | Self-resolved `sqlite_vec_so` via `build_db_config()` (Step 3) | scripts/db/recovery_verification.py | Phase 3 | AC-004 | tests/db/test_schema_validation_per_database.py (affected test) | Confirmed by repository evidence |
| REQ-004, REQ-005 | CLI import of `_resolve_archive_dir` (Step 3) | scripts/db/recovery_drill.py | Phase 3 | AC-004 | tests/db/test_recovery_drill.py | Confirmed by repository evidence |
| REQ-004 | Import of `_load_agent_config` from `db.maintenance` (Step 3; consumer not named in the Issue) | scripts/db/artifact_retention.py | Phase 3 | AC-004, AC-005 | tests/db/test_db_maintenance.py | Derived from confirmed evidence |
| REQ-003 | Fallback path resolution calls `build_db_config()` (Step 3) | scripts/db/helper.py | Phase 3 | AC-004 | tests/db/test_sqlite_helper.py (affected test) | Derived from confirmed evidence |
| REQ-004 | Imports `RetentionConfig` and `checkpoint_wal` (Step 2) | scripts/agent/services/db_maintenance_service.py | Phase 3 | AC-004, AC-005 | Validation plan row 3 | Confirmed by repository evidence |
| REQ-003 | Call site of `build_db_config()` (Step 3) | scripts/agent/commands/cmd_config_stats.py | Phase 3 | AC-004 | tests/agent/commands/test_agent_cmd_config.py (affected test) | Confirmed by repository evidence |
| REQ-003 | Call site of `build_db_config()` (Step 3) | scripts/agent/commands/cmd_config_display.py | Phase 3 | AC-004 | tests/agent/commands/test_cmd_config_char.py | Confirmed by repository evidence |
| REQ-003, REQ-004 | Fixture constructs `DbConfig` via `build_db_config()` (Step 3) | tests/conftest.py | Phase 1, Phase 3 | AC-004 | pytest collection | Confirmed by repository evidence |
| REQ-001 | Tests assert the current class and validation behavior (Step 2/3) | tests/agent/test_config_dataclasses.py | Phase 1 | AC-001, AC-002 | itself | Confirmed by repository evidence |
| REQ-001 | Tests assert `_build_rag_config()` behavior (Step 2/3) | tests/agent/test_config_builders.py | Phase 1 | AC-001 | itself | Confirmed by repository evidence |
| REQ-001 | Fixture constructs `ctx.cfg.rag` (Step 3) | tests/agent/commands/test_cmd_config_char.py | Phase 1 | AC-001 | itself | Confirmed by repository evidence |
| REQ-001, REQ-002 | Reload tests import `RAGConfig` (Step 2/3) | tests/agent/services/test_config_reload.py | Phase 1, Phase 2 | AC-002 | itself | Confirmed by repository evidence |
| REQ-003, REQ-004 | Asserts reading back from `agent.toml` (Step 3) | tests/db/test_db_config.py | Phase 3 | AC-004 | itself | Confirmed by repository evidence |
| REQ-004 | Asserts default-mode-from-config behavior and patches (Step 3) | tests/db/test_db_maintenance.py | Phase 3 | AC-004, AC-005 | itself | Confirmed by repository evidence |
| REQ-006 | Hand-written valid-key additions in `_get_valid_production_keys()` (Step 2) | scripts/agent/production_config_validator.py | Phase 4 | AC-001 | tests/agent/test_production_config_validator.py (affected test) | Confirmed by repository evidence |
| REQ-001 | Document names `RAGConfig` (consumer scan, Step 3) | docs/23_agent/agent_08_02_configuration-llm-rag.md | Phase 5 | Documentation Impact | docs gates | Confirmed by repository evidence |
| REQ-001 | Documents Memory settings driven by the moved flag (Step 3) | docs/23_agent/agent_08_03_configuration-tools-memory.md | Phase 5 | Documentation Impact | docs gates | Confirmed by repository evidence |
| REQ-001, REQ-003 | Documents `AgentConfig.rag` as the endpoint carrier (consumer scan, Step 3) | docs/21_rag/rag_05_01-configuration-reference.md | Phase 5 | Documentation Impact | docs gates | Confirmed by repository evidence |
| REQ-004 | Documents `from_config()` reading `agent.toml` (Step 3) | docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md | Phase 5 | Documentation Impact | docs gates | Confirmed by repository evidence |
| REQ-001 | Guarded generated table lists the removed class (consumer scan, Step 3) | docs/23_agent/agent_13_reference-api-generated.md | Phase 5 | Documentation Impact | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-003 | Already satisfied and enforced by the isolation test (Step 2) | tests/mcp_servers/test_config_isolation_import.py | N/A: reference-only row; no test change is planned | AC-003 | itself | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-21: build_agent_config() is the caller of _build_rag_config(); removing the section builder breaks the assembly call site | scripts/agent/config_builders.py | Phase 1 | N/A: none cites REQ-001 | tests/agent/test_config_builders.py (run as affected test; no assertion changes proven) | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-21: the reload path routes the validated sections and calls ServiceSyncer with ctx.cfg.rag; removing AgentConfig.rag and routing Memory through a typed candidate breaks this call site | scripts/agent/services/config_reload.py | Phase 2 | N/A: none cites REQ-002 | tests/agent/services/test_config_reload.py (run as affected test; no assertion changes proven beyond REQ-002 scope) | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-21: sync_all() takes the RAG section as a parameter that its body never uses; with AgentConfig.rag removed the caller cannot supply it, so the parameter is dropped | scripts/agent/services/config_service_sync.py | Phase 1 | N/A: none cites REQ-001 | no test file exists for this module; covered by tests/agent/services/test_config_reload.py run as affected test | Confirmed by repository evidence |
| REQ-006 | Amendment 2026-11-21: The refiner-key assertion moves here with the call site chosen for check_agent_refiner_keys(); this file is named only by the production_config_validator.py row, so it stays a companion of that row and gets no document of its own | tests/agent/test_production_config_validator.py | Phase 4 | N/A: none cites REQ-006 | tests/agent/test_production_config_validator.py | Confirmed by repository evidence |

## Next steps
- `plan-to-implementation-procedure` takes this Plan (frozen); `tools/plan_dependency_order.py` reports no gating plan dependency beyond the coordination note.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261121-144837 -->