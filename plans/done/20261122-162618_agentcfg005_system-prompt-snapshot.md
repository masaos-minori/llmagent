## Goal
- Keep one default system prompt stored in one read-only source, remove every config-layer copy of prompt content, keep the reload registry and the production valid-key set free of the removed fields, report a removed key as an unknown key, and pin the standard `config/agent.toml` with an effective-configuration snapshot test.

## Priority
Medium

## Scope
- **In-Scope**:
  - Create the single read-only prompt source (`registry/manifests/prompt_source.toml`) and one typed model for it (Requirement REQ-001).
  - Remove `ToolConfig.system_prompt_tool` and `ToolConfig.system_prompts` — field, builder construction, default fallback (REQ-002).
  - Remove the two `config_field_registry` prompt entries and regenerate `registry/manifests/config_ownership.yaml` from the registry source (REQ-003).
  - Reject `system_prompt_tool` and `system_prompts` as unknown keys at startup and at `/reload`, with the same result; no alias, no compatibility reader (REQ-004).
  - Delete the duplicate key block from `config/agent.toml`; keep every other explicit value that equals its code default (REQ-005).
  - Make the startup prompt path and the reload path read prompt content through the same typed single-source model (REQ-006, REQ-007).
  - Add an effective-configuration snapshot of the real `config/agent.toml` and a test that an explicit TOML value takes precedence over the code default (REQ-008).
  - Correct the two documentation statements that present the removed key as a config field (REQ-009).
- **Out-of-Scope**:
  - History-style comment cleanup (id `adrchk022`).
  - Typed staged reload and rollback (id `cliplc005`); its prepare/commit two-phase model is already in `scripts/agent/services/config_reload.py` and is reused unchanged, so it is not a blocker.
  - Alias, fallback reader, or compatibility shim for a removed key (`Current-Specification-Only` policy).
  - Deleting any TOML value only because it equals its code default.
  - Prompt-name selection semantics (`ctx.conv.system_prompt_name`) beyond keeping the existing name lookup against the single source.
- **Dependencies**: No ordering dependency remains: the fields the earlier issues removed (`agentcfg001` tool-policy fields, `agentcfg002` `tool_definitions`/`tool_names`) are already absent from the field registry — verified by the Step 3 registry-vs-dataclass check (`stale entries: []`). The earlier issues' `Execution Status` rows do not all show `Completed` (`agentcfg001` In Progress, `agentcfg002` all Pending, `agentcfg004` Phase 6 Pending), so they are recorded as stale status, not as blockers. This plan blocks `agentcfg006`.
  - **Depends on**: N/A: none (verified against current source; nothing in this plan waits on another plan's unlanded field).

## Background
- Source: consolidated `agent.toml` reduction backlog, Issue 5 (`memo-issue.md`), filed as Issue `agentcfg005`.
- Step 2 verification against current source:
  - `config/agent.toml` line 215 carries `system_prompt_tool`; lines 229-232 carry the `[system_prompts]` table with `default`, `strict`, `creative`. `default` is byte-for-byte identical to `system_prompt_tool`. The Issue's line 243 citation is stale; the current position is line 215.
  - `scripts/agent/services/config_field_registry.py` lines 78-79 still carry both prompt entries, so the Issue's "the registries hold no trace of the field" is not true today for these fields.
  - `scripts/agent/production_config_validator.py` line 172 adds `system_prompt_tool` to the valid-key set as an explicit exception on top of the dataclass-derived keys, so both keys are accepted at startup with no rejection and no migration message.
  - `scripts/agent/config_section_builders.py` lines 183-186 build `ToolConfig.system_prompts` with the fallback `{"default": system_prompt_tool}`; `scripts/agent/config_builders.py` lines 119, 126, 160, 162 pass the prompt value through the builders.
  - `scripts/agent/services/config_reload.py` lines 138-142 apply the raw `system_prompt_tool` value directly to `ctx.conv.system_prompt_content`; the dataclass field is not read by the reload path, so it is a stored copy with no live consumer.
  - The claimed single source `registry/manifests/prompt_source.toml` does not exist and is not referenced by any file (checked: `ls registry/manifests/`, `rg -F prompt_source` over the repository). The only single place today is the runtime state `ctx.conv.system_prompt_content` (`scripts/agent/context.py` lines 106, 109), which is filled at startup by `scripts/agent/startup_prompt_setup.py` lines 67-70 from `ctx.cfg.tool.system_prompts`.
  - The duplication is therefore config-to-config (`system_prompt_tool` vs `[system_prompts].default`) plus a config-to-runtime derived copy, not a config-vs-runtime ownership violation.
  - `registry/manifests/config_ownership.yaml` is a generated artifact derived from `scripts/agent/services/config_field_registry.py` (`tools/generate_reference_table.py` line 499); the current drift check reports `No drift found`. It is not hand-edited.
- Owner decision (2026-11-22, this pass): the single source is a new read-only manifest created by this work, and the added live consumers and created files are recorded in the plan as scope additions.

## Problem
- Two config keys carry one prompt, and one of them has no consumer other than the fallback that recreates the other. Any change to one is invisible to the other.
- Eight test files depend on the config-layer prompt fields as fixtures (`tests/agent/test_config_builders.py`, `tests/agent/services/test_config_reload.py`, `tests/agent/services/test_config_reload_classification.py`, `tests/agent/test_production_config_validator.py`, `tests/agent/test_startup_prompt_setup.py`, `tests/agent/test_startup.py`, `tests/agent/commands/test_agent_cmd_context.py`, `tests/agent/services/test_conversation_service.py`), so the removal cannot be validated without migrating them; the Issue's Unresolved Question about additional referencing tests is answered by these files.
- `tests/agent/services/test_config_reload.py` lines 1149-1168 asserts the exact tool-section field set, which includes both prompt names, so the registry removal is observable there.
- The standard file has no snapshot that pins its effective values: measured with the current builders, 18 explicit values equal their code defaults and 14 differ, and 2 registered fields are absent from the file. Nothing fails if an explicit value is dropped and a code default takes over.
- Re-measured for this pass (2026-11-22): the 14 differing values include the two prompt fields, so the inventory the snapshot must record after this plan lands is 18 equal / 12 differing / 2 absent, and the field registry goes from 34 entries to 32. The snapshot test asserts the post-change inventory; the pre-change numbers are the baseline only, not the contract. The 2 absent registered fields are `tool.disabled_tools` and `approval.gitops_push_blocked` (recorded here; adding them is out of scope, see UNK-05).

## Reason for Change
- The field removals of the earlier issues have landed, so the remaining prompt entries are now live in the registry, the valid-key set, and the tests; keeping them means a removed key is silently accepted, and the prompt has two stored copies.
- The snapshot is the deployment contract for the standard file, so it must be pinned before further reduction work (`agentcfg006`) reads the same file.

## Implementation Intent
- One read-only prompt source, read through one typed model, is the only stored prompt content. The config layer keeps no prompt copy; the runtime state (`ctx.conv`) keeps the live value.
- Startup resolves the initial prompt from the single source through that typed model; `/reload` keeps the existing two-phase invariant: the candidate is built in the prepare phase and the conversation-state change is applied only in the commit phase.
- Removed keys are rejected by the same path that rejects any other unknown key; no special-case handling remains.
- The standard `config/agent.toml` keeps every explicit value it has today except the duplicate prompt block, and a snapshot test pins the effective configuration it produces.

## Requirements
- `REQ-001`: Create `registry/manifests/prompt_source.toml` as the single stored prompt source and one typed read-only model for it (prompt name to content, frozen, no mutable copy). A missing source file or a missing `default` entry is an error at the read boundary, not a silent default.
- `REQ-002`: Remove `ToolConfig.system_prompt_tool` and `ToolConfig.system_prompts` (field, section-builder construction, and the `{"default": system_prompt_tool}` fallback) from the config layer.
- `REQ-003`: Remove both prompt entries from `scripts/agent/services/config_field_registry.py`; `registry/manifests/config_ownership.yaml` must contain no prompt entries after regeneration. Confirm no other field removed by the earlier issues remains in the registry, the startup-only classification, or service sync.
- `REQ-004`: `system_prompt_tool` and `system_prompts` are reported as unknown keys by the production validator at startup and at `/reload`, with the same result. No alias, no compatibility reader.
- `REQ-005`: Delete the duplicate `system_prompt_tool` key from `config/agent.toml`; every other explicit value, including values equal to a code default, stays.
- `REQ-006`: `scripts/agent/startup_prompt_setup.py` builds the initial prompt from the single source through the typed model, keeping the existing name lookup (`ctx.conv.system_prompt_name`, default `default`) and the memory-injection behaviour.
- `REQ-007`: `/reload` applies a prompt-content change to the conversation state only in the commit phase, using the same typed model as startup; the outcome report shape is unchanged.
- `REQ-008`: Add a test that pins the effective configuration of the real `config/agent.toml` and a test that an explicit TOML value takes precedence over the code default.
- `REQ-009`: Correct the documentation statements that present the removed key as a config field and that present the config layer as the prompt source.

## Implementation Target Files
**Freeze status**: Frozen (Step 8's Implementation Target Files Validation passed on 2026-11-22: every row `Verified`, `tools/check_workitem_structure.py` no findings, `tools/audit_plan_target_paths.py` no findings, `tools/check_plan_target_overlaps.py` no findings).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `config/agent.toml` | config | Delete the `system_prompt_tool` key block; the prompt table content moves to the single source. | REQ-005, AC-3 | Step 2: `config/agent.toml` lines 215, 229-232; values identical | `tests/agent/test_config_effective_snapshot.py` | Verified |
| `registry/manifests/prompt_source.toml` | create (new file) | New file: single stored prompt source (name to content). Directory exists; file absent today. | REQ-001, AC-1 | Step 2: `ls registry/manifests/` — no prompt source file; `rg -F prompt_source` — no reference | `tests/agent/test_prompt_source.py` | Verified |
| `scripts/agent/prompt_source.py` | create (new module) | New file: typed prompt-source model used by both the startup and the reload path. | REQ-001, REQ-006, REQ-007, AC-4 | Step 3: reader pattern precedent `scripts/shared/component_mandatoriness.py` lines 31-41 with `shared.runtime_paths.resolve_registry_dir` (`scripts/shared/runtime_paths.py` lines 80-89) | `tests/agent/test_prompt_source.py` | Verified |
| `scripts/agent/config_dataclasses.py` | config dataclass | Remove `ToolConfig.system_prompt_tool` and `ToolConfig.system_prompts`. | REQ-002, AC-1 | Step 2: `scripts/agent/config_dataclasses.py` lines 194-195 | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/config_section_builders.py` | section builder | Remove the prompt dict construction and the `{"default": system_prompt_tool}` fallback. | REQ-002, AC-1 | Step 2: `scripts/agent/config_section_builders.py` lines 183-186 | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/config_builders.py` | builder plumbing | Remove the `system_prompt_tool` parameter and its pass-through. | REQ-002, AC-1 | Step 2: `scripts/agent/config_builders.py` lines 119, 126, 160, 162 | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/services/config_field_registry.py` | reload registry | Remove both prompt entries; no other stale entry exists. | REQ-003, AC-2 | Step 2: `scripts/agent/services/config_field_registry.py` lines 78-79; Step 3: registry-vs-dataclass check reported `stale entries: []` | `tests/agent/services/test_config_reload.py` | Verified |
| `registry/manifests/config_ownership.yaml` | regenerate (generated manifest) | Regenerate from the registry source so the two prompt rows disappear; not hand-edited. | REQ-003, AC-2 | Step 3: rows 118-123; `tools/generate_reference_table.py` line 499 maps `config_ownership` to `scripts/agent/services/config_field_registry.py` | `tests/tools/test_generate_reference_table.py` (no prompt row asserted) | Verified |
| `scripts/agent/production_config_validator.py` | valid-key set | Remove the explicit `system_prompt_tool` exception so the removed keys are rejected as unknown. | REQ-004, AC-2 | Step 2: `scripts/agent/production_config_validator.py` line 172 | `tests/agent/test_production_config_validator.py` | Verified |
| `scripts/agent/services/config_reload.py` | reload path | Replace the raw-key branch with the typed single-source read; keep the commit-phase-only application. | REQ-007, AC-4 | Step 2: `scripts/agent/services/config_reload.py` lines 138-142, 144-152 | `tests/agent/services/test_config_reload.py` | Verified |
| `scripts/agent/startup_prompt_setup.py` | startup path | Read the initial prompt from the single source through the typed model. | REQ-006, AC-4 | Step 2: `scripts/agent/startup_prompt_setup.py` lines 67-70, 122 | `tests/agent/test_startup_prompt_setup.py`, `tests/agent/test_startup.py` | Verified |
| `tests/agent/test_prompt_source.py` | create (new test file) | New file: typed model and reader contract tests (name lookup, missing file, missing entry). | REQ-001, AC-1, AC-5 | Step 3: no existing test covers the prompt source (`rg -F prompt_source` — no match) | itself | Verified |
| `tests/agent/test_config_effective_snapshot.py` | create (new test file) | New file: effective-configuration snapshot of the real `config/agent.toml` plus explicit-over-default precedence. | REQ-008, AC-5 | Step 3: no existing snapshot test for the effective configuration; measured 18 explicit-equal-default and 14 differing values | itself | Verified |
| `tests/agent/test_config_builders.py` | test | Remove prompt-field assertions and the prompt argument from the section-builder tests. | REQ-002, AC-1 | Step 3: lines 144-152, 168, 171, 174, 429-437 | itself | Verified |
| `tests/agent/services/test_config_reload.py` | test | Replace the prompt-key reload cases with single-source cases; update the tool-section expected field set. | REQ-003, REQ-007, AC-2, AC-4 | Step 3: lines 51, 101, 275, 320, 931, 1081, 1149-1168 | itself | Verified |
| `tests/agent/services/test_config_reload_classification.py` | test | Remove the `ctx.cfg.tool.system_prompts` fixture. | REQ-003, AC-2 | Step 3: line 22 | itself | Verified |
| `tests/agent/test_production_config_validator.py` | test | Change the accepted-key cases to assert the removed keys are rejected as unknown. | REQ-004, AC-2 | Step 3: lines 196-202, 296 | itself | Verified |
| `tests/agent/test_startup_prompt_setup.py` | test | Replace the `system_prompt_tool` fixture with the single-source fixture. | REQ-006, AC-4 | Step 3: lines 27, 37 | itself | Verified |
| `tests/agent/test_startup.py` | test | Remove the `ctx.cfg.tool.system_prompts` fixtures (5 sites). | REQ-006, AC-4 | Step 3: lines 50, 72, 90, 106, 127 | itself | Verified |
| `tests/agent/commands/test_agent_cmd_context.py` | test | Remove the `ctx.cfg.tool.system_prompts` fixture. | REQ-006, AC-4 | Step 3: line 51 | itself | Verified |
| `tests/agent/services/test_conversation_service.py` | test | Remove the `system_prompts` fixture parameter and its default. | REQ-006, AC-4 | Step 3: lines 16, 26 | itself | Verified |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | docs | Replace the `system_prompt_tool` config-field mapping with the single-source contract. | REQ-009, AC-6 | Step 3: `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` line 51 | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | docs | Remove the removed key from the Agent config-key example list. | REQ-009, AC-6 | Step 3: `docs/10_adr/adr_02_01_002_platform-config-isolation.md` line 85 | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |

## Reference Files
Files that must be read but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/services/config_section_reload.py` | Builds the tool-section candidate through `registry_for(section_path)`; contains no prompt-specific code, so the registry removal needs no change here. | REQ-003 |
| `scripts/agent/services/config_outcome_classification.py` | Startup-only classification is driven by the registry `hot_reloadable` flags; no prompt or removed-field entry exists (`rg` — no match), so it is confirmed not affected. | REQ-003 |
| `scripts/agent/services/config_service_sync.py` | Confirmed by search that no prompt or removed-field reference exists; the Issue lists it as a prune target, and the finding is that it needs no change. | REQ-003 |
| `scripts/agent/context.py` | Runtime state fields `system_prompt_name` and `system_prompt_content` (lines 106, 109) remain the runtime copy. | REQ-001, REQ-006 |
| `scripts/agent/conversation_state_manager.py` | Syncs `history[0]` from `ctx.conv.system_prompt_content` (lines 81-90); unaffected by the config-layer removal. | REQ-007 |
| `scripts/agent/services/session_restore.py` | Reads `ctx.conv.system_prompt_content` (lines 182-188); unaffected. | REQ-007 |
| `scripts/agent/commands/cmd_config.py` | Reports hot-reloadable fields from the registry (lines 68-91); the prompt fields disappear from the report with the registry entries. | REQ-003 |
| `scripts/agent/commands/cmd_context.py` | Displays `ctx.conv.system_prompt_name` (line 75) only; not affected. | REQ-006 |
| `scripts/shared/runtime_paths.py` | `resolve_registry_dir` (lines 80-89) is the path contract the new reader must use. | REQ-001 |
| `scripts/shared/component_mandatoriness.py` | Precedent for a leaf-safe registry reader (lines 31-41); the new reader stays under `agent` because only agent consumers use it (`shared-is-leaf` contract). | REQ-001 |
| `tools/generate_reference_table.py` | `config_ownership` manifest source mapping (line 499) and the `--check` gate; regeneration is part of the validation plan. | REQ-003 |
| `tests/agent/test_config_dataclasses.py` | Confirmed by search that it has no prompt-field reference, so it is not affected by REQ-002. | REQ-002 |
| `tests/agent/test_session_restore.py`, `tests/agent/test_resource_shutdown_coordinator.py`, `tests/integration/test_orchestrator_integration.py` | Use `ctx.conv.system_prompt_content` only; recorded as not affected. | REQ-007 |
| `tests/tools/test_generate_reference_table.py` | Confirmed by search that no prompt row is asserted; recorded as not affected. | REQ-003 |
| `deploy/deploy.sh` | `registry/` is rsynced as a whole (lines 79-82) and `config/agent.toml` already has a `cp` line (line 152); no deploy change is required. | REQ-001, REQ-005 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): Prompt content is stored in exactly one place: the single source. No config dataclass field, builder, or fallback holds prompt content. Verified by `tests/agent/test_prompt_source.py` and `tests/agent/test_config_builders.py`.
- `AC-2` (REQ-003, REQ-004): `system_prompt_tool` and `system_prompts` are reported as unknown keys by the production validator at startup and at `/reload` with the same result, and are never silently ignored. No field-registry entry, no generated `config_ownership` row.
- `AC-3` (REQ-005): `config/agent.toml` keeps every explicit value that equals its code default; only the duplicate prompt block is removed. Verified by the snapshot test's explicit-value inventory.
- `AC-4` (REQ-006, REQ-007): Startup and `/reload` use the same typed single-source model; `/reload` mutates the conversation state only in the commit phase, and a prepare-phase failure leaves `ctx.cfg` and `ctx.conv` untouched.
- `AC-5` (REQ-008): The snapshot test passes against the real `config/agent.toml`, and an explicit TOML value is shown to take precedence over the code default.
- `AC-6` (REQ-009): No documentation presents the removed key as a config field or the config layer as the prompt source; the docs checkers for the `agent` domain pass.

## Tests
- `REQ-001` (`tests/agent/test_prompt_source.py`): reader returns the frozen typed model; name lookup resolves `default`; missing source file and missing `default` entry raise an error at the read boundary; no mutable copy escapes the model.
- `REQ-002` (`tests/agent/test_config_builders.py`): section builder has no prompt fields; the override-reflection test no longer includes prompt keys; the builder pass-through test is removed.
- `REQ-003` (`tests/agent/services/test_config_reload.py`): the tool-section expected field set excludes both prompt names; `tests/agent/services/test_config_reload_classification.py` fixture removal; the generated `config_ownership` manifest contains no prompt rows (`uv run python tools/generate_reference_table.py --check`).
- `REQ-004` (`tests/agent/test_production_config_validator.py`): the removed keys produce an unknown-key error; the existing real-config integration test passes after the TOML deletion.
- `REQ-005`, `REQ-008` (`tests/agent/test_config_effective_snapshot.py`): effective configuration of the real file is pinned; the post-change inventory (18 equal-default, 12 differing, 2 absent) is asserted as the recorded contract, not the pre-change measurement; one case proves explicit-over-default precedence. Marked `integration` per the existing real-config test pattern (`tests/agent/test_production_config_validator.py` line 348). Caveat: the marker is defined as "tests that start real subprocesses" and the full-suite and diff-coverage runs deselect `integration`, so this test runs in CI only; coverage of the changed lines must come from the reader and startup unit tests, not from this test.
- `REQ-006` (`tests/agent/test_startup_prompt_setup.py`, `tests/agent/test_startup.py`, `tests/agent/commands/test_agent_cmd_context.py`, `tests/agent/services/test_conversation_service.py`): startup resolves the prompt through the typed model; memory injection behaviour unchanged.
- `REQ-007` (`tests/agent/services/test_config_reload.py`): prompt change is applied at commit; prepare-phase failure path leaves live state untouched; outcome report shape unchanged.
- Gate order: `rules/toolchain.md` full sequence via `uv run python tools/run_validation_gates.py`; full suite `-n logical`; `diff-cover` ≥ 90% on changed lines against the recorded baseline (95.49% at 2026-11-22).

## Documentation Impact
- Yes, driven by REQ-009. Per `docs/00_index.md` "Document References by Task" → Agent spec, the two documents that carry the claim are the configuration-loading document (line 51 mapping) and the platform-config-isolation ADR (line 85 example key list). `uv run python tools/check_docs_consistency.py --domain agent` is the checker that confirms no config-key claim remains stale; `check_docs_quality.py` and `check_docs_structure.py` apply to both rows.
- No decision-log document is created: the repository has no decision-log convention (`docs/90_meta/` does not exist; `docs/00_governance/` has no decision-record document class). The single-source decision is recorded in the ADR row above.

## Assumptions
- The owner decision for the single source is the new read-only manifest (option B), confirmed in this pass on 2026-11-22; the plan's created-file rows depend on it.
- `registry/manifests/prompt_source.toml` is a hand-authored source-of-truth data file, not a generator-derived manifest; it is not added to `tools/generate_reference_table.py`'s `_MANIFEST_SOURCES`. Caveat recorded during this pass: every committed file in `registry/manifests/` is `.yaml`, and the generator's `--check` only reads registered manifest names, so a `.toml` file there is outside the drift check and breaks the directory's format convention. The `.toml` name is kept per the recorded owner decision; if the format is to match the directory convention, that is a Plan revision, not a procedure change.
- Cross-plan overlap judgement (`tools/check_plan_target_overlaps.py`, 2026-11-22): the six shared rows with `plans/20261121-172154_mcpdl003_dedup-config-isolation.md` are compatible, not a conflict. That plan adds an `approval_grant_ttl_seconds` field and key, this plan removes the prompt field and key; no row's change contradicts the other's. Two consequences are recorded: the snapshot inventory counts change if that plan's key lands in `config/agent.toml` first, so the snapshot must be written against the state at its own execution time; and `tools/plan_dependency_order.py` recommends that plan first, which is a recommendation only (`Ready`, no gating edge).
- Named prompts (`default`, `strict`, `creative`) move to the single source as data; no prompt content is dropped from the current values.
- The Issue's Constraint "Change only the Target Files" is resolved as a reported scope amendment: the added live consumers (`scripts/agent/startup_prompt_setup.py`, `tests/agent/test_startup_prompt_setup.py`) and the additional test files listed as rows were found by the Step 3 consumer scan.
- Prompt content is not part of `ConfigReloadRequest`'s config dict after removal; the reload path reads the single source directly.
- `docs/*.md` files and `registry/manifests/*` are not renamed or moved by this plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `/reload` keeps prompt content hot-reloadable (current observable behaviour) or the prompt becomes startup-only. | No owner decision; the current behaviour is hot-reloadable (`registry/manifests/config_ownership.yaml` `hot_reloadable: true`, `tests/agent/services/test_config_reload.py` lines 275, 320). | Owner decision. Default taken here: preserve the observable behaviour and apply the change in the commit phase only (REQ-007). | False |
| UNK-02 | Whether `registry/manifests/prompt_source.toml` should be registered as a generator manifest type. | `tools/generate_reference_table.py` has no `prompt_source` entry; existing manifest entries are derived from source, while this file would be its own source. | Owner decision; if registered, `tools/generate_reference_table.py` and `tests/tools/test_generate_reference_table.py` become additional target files. | False |
| UNK-03 | Error behaviour when the single source is missing or has no `default` entry. | No existing convention for a missing registry data file except the startup-abort pattern for `config/agent.toml` (ADR 002). | Owner decision; the plan takes "error at the read boundary, no silent default" as the design (REQ-001). | False |
| UNK-04 | Whether prompt-name selection (`default`/`strict`/`creative`) remains a supported feature. | `ctx.conv.system_prompt_name` has no setter in `scripts/` (only `scripts/agent/context.py` line 106 default and `scripts/agent/commands/cmd_context.py` line 75 display); no command selects a name. | Owner decision; the plan keeps the existing lookup and does not add a selection feature. | False |
| UNK-05 | Whether `config/agent.toml`'s two registered-but-absent fields should be added to the standard file. | Measured: 2 registry fields are absent from the file; the Issue's constraint only forbids deleting values. | Out of this plan's scope; report to `agentcfg006`. | False |

## Affected areas
Per `skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`. `Churn (30d)` = commits touching the file in the last 30 days; `Bus Factor` = distinct git author names. New files have no history.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `config/agent.toml` | delete key block | 1 test reads the real file (`tests/agent/test_production_config_validator.py` line 349) | 18 | 3 | not applicable (existing `cp` line) |
| `registry/manifests/prompt_source.toml` | create | 1 new reader | 0 (new) | N/A: new file | not applicable (rsynced) |
| `scripts/agent/prompt_source.py` | create | 2 consumers (`startup_prompt_setup.py`, `services/config_reload.py`) | 0 (new) | N/A: new file | not applicable (rsynced) |
| `scripts/agent/config_dataclasses.py` | delete fields | 6 test files reference `ToolConfig`; 4 files reference the prompt fields | 12 | 4 | not applicable (rsynced) |
| `scripts/agent/config_section_builders.py` | delete construction | 1 test file | 8 | 2 | not applicable (rsynced) |
| `scripts/agent/config_builders.py` | delete parameter | 1 test file | 3 | 4 | not applicable (rsynced) |
| `scripts/agent/services/config_field_registry.py` | delete entries | generated manifest + 1 test asserting the field set + `cmd_config.py` report | 6 | 2 | not applicable (rsynced) |
| `scripts/agent/production_config_validator.py` | delete exception | 1 test file; 2 test cases change meaning | 14 | 2 | not applicable (rsynced) |
| `scripts/agent/services/config_reload.py` | replace branch | 1 test file (7 sites) | 4 | 4 | not applicable (rsynced) |
| `scripts/agent/startup_prompt_setup.py` | change read path | 2 test files | 2 | 2 | not applicable (rsynced) |
| `tests/agent/test_prompt_source.py` | create | new | 0 (new) | N/A: new file | not applicable (rsynced) |
| `tests/agent/test_config_effective_snapshot.py` | create | new | 0 (new) | N/A: new file | not applicable (rsynced) |
| `tests/agent/test_config_builders.py` | delete assertions | 8 sites | 8 | 2 | not applicable (rsynced) |
| `tests/agent/services/test_config_reload.py` | change cases and expected set | 7 sites | 9 | 2 | not applicable (rsynced) |
| `tests/agent/services/test_config_reload_classification.py` | remove fixture | 1 site | 0 | 2 | not applicable (rsynced) |
| `tests/agent/test_production_config_validator.py` | change key-acceptance cases | 2 sites | 11 | 2 | not applicable (rsynced) |
| `tests/agent/test_startup_prompt_setup.py` | change fixture | 2 sites | 1 | 2 | not applicable (rsynced) |
| `tests/agent/test_startup.py` | remove fixtures | 5 sites | 12 | 2 | not applicable (rsynced) |
| `tests/agent/commands/test_agent_cmd_context.py` | remove fixture | 1 site | 1 | 2 | not applicable (rsynced) |
| `tests/agent/services/test_conversation_service.py` | remove fixture | 2 sites | 0 | 2 | not applicable (rsynced) |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | correct claim | 1 line | 1 | 2 | not applicable (docs not deployed by deploy.sh) |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | correct claim | 1 line | 8 | 2 | not applicable (docs not deployed by deploy.sh) |

Below the `rules/toolchain.md` blast-radius rule of thumb (>10 test files or >20 references): 4 test files carry the config-key references, 8 test files carry the field references. The change is small enough to validate with targeted tests, and the full-suite run confirms it.

## Design
- Path B classification: 22 target rows (>3), a new module, and a runtime-facing read boundary change. Path B analysis performed (see `skills/issue-to-plan/workflow-path-b.md`).
- Architecture: `config/` holds ownership, `conv/` holds runtime state (ADR 002). Prompt content is data owned by the single source, not by the config layer; `ctx.conv.system_prompt_content` stays the runtime copy. The config layer's two prompt fields and their fallback are removed, so no second stored copy exists.
- Typed model: one frozen model plus one reader, used by both startup and `/reload`. This is what satisfies the Issue's "same typed schema for the removed fields" after the fields are gone. The reader resolves the path through `shared.runtime_paths.resolve_registry_dir` so a compiled binary reads the deployed registry; it stays under `agent` because only agent code consumes it, keeping `shared` a leaf module.
- No code default for prompt content: the single source is the only source, so a missing file or missing `default` entry is an error at the read boundary instead of a silent default (the Issue's Problem names silent defaults as the failure mode).
- Reload: the two-phase prepare/commit invariant already implemented in `scripts/agent/services/config_reload.py` is reused. The prompt candidate is built in the prepare phase; the conversation-state update remains the only prompt mutation and runs in the commit phase. `config_section_reload.py`, `config_outcome_classification.py`, and `config_service_sync.py` need no change: they are generic or hold no prompt reference.
- Consumer scan (`tools/scan_change_consumers.py --seed system_prompt_tool`, candidates only): 13 candidates in `scripts/`, 2 in `docs/`, plus the 8 test files recorded above; every candidate is recorded as a target row, a reference row, or a stated not-affected reason.
- Predictable fallout check: module size gate — no baseline entry for any target file, and all changes shrink files; pinned counts — no test or doc pins the registry entry count (`rg` — no match); tool inventory — unchanged; generated blocks — the `config_ownership` manifest is regenerated and drift-checked, no guarded docs block contains prompt rows.
- Tool availability: `radon`, `vulture`, `diff-cover`, `grimp`, `networkx` run through `uv run`; `pydeps`, `lint-imports`, `pyan3`, `ctags`, `git-fame` are not installed, so the documented fallbacks were used (import-linter contract reading, `git log` for churn, `rg` for consumer scan).
- Validation quality baseline: full-suite coverage 95.49% at 2026-11-22; `diff-cover` reports no changed lines yet (no code change in this pass); the ≥90% gate applies to the implementation diff. Testmon data is 4.3 days old, so the first implementation run does a full targeted run rather than a testmon-selected subset.
- Static baseline at analysis time: cyclomatic complexity of every target module is grade A (max 4, `config_dataclasses.MemoryConfig`); `vulture --min-confidence 80` reports no unused `system_prompt` declaration; `bandit` findings (Low 47, Medium 6, High 41) are pre-existing and unrelated to this change.

## Implementation steps

1. **Phase 1: Single source and typed model**
   - [ ] Create the single prompt source with the current prompt values as data (REQ-001; `registry/manifests/prompt_source.toml`).
   - [ ] Create the frozen typed model and the single reader (REQ-001; `scripts/agent/prompt_source.py`).
   - [ ] Add the reader contract tests, including missing-file and missing-entry error cases (REQ-001, AC-1, AC-5; `tests/agent/test_prompt_source.py`).
2. **Phase 2: Startup path**
   - [ ] Read the initial prompt from the single source through the typed model, keeping the existing name lookup and memory injection (REQ-006; `scripts/agent/startup_prompt_setup.py`).
   - [ ] Migrate the startup fixtures from the config-layer fields to the typed source (REQ-006, AC-4; `tests/agent/test_startup_prompt_setup.py`, `tests/agent/test_startup.py`, `tests/agent/commands/test_agent_cmd_context.py`, `tests/agent/services/test_conversation_service.py`).
3. **Phase 3: Reload path**
   - [ ] Replace the raw-key branch with the typed single-source read and keep the mutation in the commit phase only (REQ-007; `scripts/agent/services/config_reload.py`).
   - [ ] Update the prompt reload cases and the prepare/commit failure paths (REQ-007, AC-4; `tests/agent/services/test_config_reload.py`).
4. **Phase 4: Config-layer removal** (release unit RU-1 with Phase 5)
   - [ ] Remove the two `ToolConfig` fields (REQ-002; `scripts/agent/config_dataclasses.py`).
   - [ ] Remove the section-builder construction and the default fallback (REQ-002; `scripts/agent/config_section_builders.py`).
   - [ ] Remove the builder parameter and pass-through (REQ-002; `scripts/agent/config_builders.py`).
   - [ ] Remove the two field-registry entries and confirm no other stale entry exists (REQ-003; `scripts/agent/services/config_field_registry.py`).
   - [ ] Remove the valid-key exception (REQ-004; `scripts/agent/production_config_validator.py`).
5. **Phase 5: Standard file and test migration** (release unit RU-1 with Phase 4)
   - [ ] Delete the duplicate key block from the standard file and keep every other explicit value (REQ-005; `config/agent.toml`).
   - [ ] Migrate the builder, reload-classification, and valid-key tests (REQ-002, REQ-003, REQ-004; `tests/agent/test_config_builders.py`, `tests/agent/services/test_config_reload_classification.py`, `tests/agent/test_production_config_validator.py`).
   - [ ] Add the effective-configuration snapshot and the explicit-over-default precedence test (REQ-008; `tests/agent/test_config_effective_snapshot.py`).
6. **Phase 6: Deployment & Verification**
   - [ ] Regenerate the ownership manifest from the registry source and run the drift check (REQ-003; `registry/manifests/config_ownership.yaml`, `tools/generate_reference_table.py --check`).
   - [ ] Correct the two documentation claims and run the docs checkers (REQ-009, AC-6; `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`).
   - [ ] Deployment check: `registry/` is rsynced and `config/agent.toml` already has its `cp` line, so no `deploy.sh` change; confirm the deployed registry path resolves through `LLMAGENT_REGISTRY_DIR` (REQ-001; `deploy/deploy.sh` read-only, `scripts/shared/runtime_paths.py` read-only).
   - [ ] Run `uv run python tools/run_validation_gates.py` including the full suite and `diff-cover` (REQ-008, AC-5).

### Release units
**Unit**: RU-1 | **Phases**: 4, 5 | **Reason**: removing the dataclass fields breaks the builder, reload-classification, valid-key, and snapshot tests until the test migration and the standard-file deletion land in the same commit; Phase 4 alone cannot pass validation.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `registry/manifests/prompt_source.toml`, `scripts/agent/prompt_source.py` | Unit (reader contract, error boundary) | `uv run pytest tests/agent/test_prompt_source.py` | Name lookup resolves `default`; missing file or missing entry raises at the read boundary; model is immutable. |
| `scripts/agent/startup_prompt_setup.py` | Unit | `uv run pytest tests/agent/test_startup_prompt_setup.py tests/agent/test_startup.py` | Initial prompt comes from the typed source; memory injection unchanged. |
| `scripts/agent/services/config_reload.py` | Unit (prepare/commit phases) | `uv run pytest tests/agent/services/test_config_reload.py` | Prompt change applied only in commit; prepare failure leaves `ctx.cfg` and `ctx.conv` untouched; outcome shape unchanged. |
| `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/config_builders.py` | Unit | `uv run pytest tests/agent/test_config_builders.py` | No prompt field or fallback; remaining fields unaffected. |
| `scripts/agent/services/config_field_registry.py` | Static + generated-artifact check | `uv run python tools/generate_reference_table.py --manifests` then `--check` | No prompt entry; regenerated manifest has no prompt rows; no drift. |
| `scripts/agent/production_config_validator.py` | Unit | `uv run pytest tests/agent/test_production_config_validator.py` | Both removed keys are reported as unknown keys. |
| `config/agent.toml` + effective snapshot | Integration | `uv run pytest tests/agent/test_config_effective_snapshot.py tests/agent/test_production_config_validator.py -m integration` | Real file passes both validators with zero errors; snapshot matches the recorded inventory. |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Docs gates | `uv run python tools/check_docs_consistency.py --domain agent`, `check_docs_quality.py`, `check_docs_structure.py` | No config-key claim references a removed field; structure checks pass. |
| All changed Python files | Static gates | `uv run ruff check .`, `uv run mypy scripts/`, `uv run lint-imports` | Pass; `shared-is-leaf` contract intact. |
| Full suite | Regression | `uv run pytest tests/ -n logical --cov=scripts` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | No regression; diff coverage ≥ 90%. |

## Risks
- **Risk**: the Issue's premise that a single source already exists is false, so Phase 1 creates a new source of truth rather than pruning a copy. → **Mitigation**: the decision is recorded above (option B, 2026-11-22); Phase 1 is self-contained and passes validation alone.
- **Risk**: moving prompt content out of `config/agent.toml` changes the operational contract for operators, who treat `config/agent.toml` as the deployment configuration. → **Mitigation**: state the move explicitly in the documentation rows and keep every other explicit value in the standard file (REQ-005); the deploy path already syncs `registry/`.
- **Risk**: the new manifest is outside the generator's two-way drift check, so a hand-edited manifest can drift silently. → **Mitigation**: recorded as UNK-02; if the owner registers it as a manifest type, the generator and its test become target files before implementation.
- **Risk**: prompt hot-reload behaviour changes if the owner decides the prompt is startup-only. → **Mitigation**: UNK-01 records the decision point; the default taken here preserves observable behaviour, and the reload test asserts the commit-phase-only contract either way.
- **Risk**: 8 test files depend on the config-layer fields as fixtures; a partial migration leaves a failing suite. → **Mitigation**: all test files are target rows and are grouped in release unit RU-1 with the code removal.
- **Risk**: the stale `Execution Status` rows of `agentcfg001` and `agentcfg002` make a dependency look open when the code has landed. → **Mitigation**: the dependency is verified against current source (registry check `stale entries: []`), not against status rows; recorded in Scope.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: single source and typed model | In Progress | — | — | RU-1 not involved; passes validation alone |
| 2 | Phase 2: startup path | In Progress | — | — | — |
| 3 | Phase 3: reload path | In Progress | — | — | — |
| 4 | Phase 4: config-layer removal (RU-1) | In Progress | — | — | cannot be validated alone |
| 5 | Phase 5: standard file and test migration (RU-1) | In Progress | — | — | releases RU-1 |
| 6 | Phase 6: deployment, generated manifest, docs, gates | In Progress | — | — | `registry/` rsynced, no `deploy.sh` change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261122-165517_01_config_agent.toml.md | 5 | Procedure | Pending | — | — |
| implementations/20261122-165517_02_registry_manifests_prompt_source.toml.md | 1 | Procedure | Pending | — | — |
| implementations/20261122-165517_03_scripts_agent_prompt_source.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261122-165517_04_scripts_agent_config_dataclasses.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-165517_05_scripts_agent_config_section_builders.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-165517_06_scripts_agent_config_builders.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-165517_07_scripts_agent_services_config_field_registry.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-165517_08_registry_manifests_config_ownership.yaml.md | 6 | Procedure | Pending | — | — |
| implementations/20261122-165517_09_scripts_agent_production_config_validator.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-165517_10_scripts_agent_services_config_reload.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261122-165517_11_scripts_agent_startup_prompt_setup.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261122-165517_12_tests_agent_test_prompt_source.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261122-165517_13_tests_agent_test_config_effective_snapshot.py.md | 5 | Procedure | Pending | — | — |
| implementations/20261122-165517_14_tests_agent_test_config_builders.py.md | 5 | Procedure | Pending | — | — |
| implementations/20261122-165517_15_tests_agent_services_test_config_reload.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261122-165517_16_tests_agent_services_test_config_reload_classification.py.md | 5 | Procedure | Pending | — | — |
| implementations/20261122-165517_17_tests_agent_test_production_config_validator.py.md | 5 | Procedure | Pending | — | — |
| implementations/20261122-165517_18_tests_agent_test_startup_prompt_setup.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261122-165517_19_tests_agent_test_startup.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261122-165517_20_tests_agent_commands_test_agent_cmd_context.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261122-165517_21_tests_agent_services_test_conversation_service.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261122-165517_22_docs_23_agent_agent_08_01_configuration-loading-agent-config.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261122-165517_23_docs_10_adr_adr_02_01_002_platform-config-isolation.md.md | 6 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261122-162618
- **Related target files**: see `Implementation Target Files` above (frozen rows)

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; Target Files; verified absent today (`ls registry/manifests/`) | `registry/manifests/prompt_source.toml` | Phase 1 | AC-1 | `tests/agent/test_prompt_source.py` | Planned |
| REQ-001 | Reader pattern precedent `scripts/shared/component_mandatoriness.py` lines 31-41 | `scripts/agent/prompt_source.py` | Phase 1 | AC-1, AC-4 | `tests/agent/test_prompt_source.py` | Planned |
| REQ-001 | Design: no silent default | `tests/agent/test_prompt_source.py` | Phase 1 | AC-5 | error-boundary cases | Planned |
| REQ-002 | Required Changes; `config_dataclasses.py` lines 194-195 | `scripts/agent/config_dataclasses.py` | Phase 4 | AC-1 | `tests/agent/test_config_builders.py` | Planned |
| REQ-002 | `config_section_builders.py` lines 183-186 | `scripts/agent/config_section_builders.py` | Phase 4 | AC-1 | `tests/agent/test_config_builders.py` | Planned |
| REQ-002 | `config_builders.py` lines 119, 126, 160, 162 | `scripts/agent/config_builders.py` | Phase 4 | AC-1 | `tests/agent/test_config_builders.py` | Planned |
| REQ-002 | `test_config_builders.py` lines 144-152, 168, 171, 174, 429-437 | `tests/agent/test_config_builders.py` | Phase 5 | AC-1 | same file | Planned |
| REQ-003 | `config_field_registry.py` lines 78-79; stale-entry check `stale entries: []` | `scripts/agent/services/config_field_registry.py` | Phase 4 | AC-2 | `tests/agent/services/test_config_reload.py` lines 1149-1168 | Planned |
| REQ-003 | generated manifest rows 118-123 | `registry/manifests/config_ownership.yaml` | Phase 6 | AC-2 | `tools/generate_reference_table.py --check` | Planned |
| REQ-003 | `test_config_reload_classification.py` line 22 | `tests/agent/services/test_config_reload_classification.py` | Phase 5 | AC-2 | same file | Planned |
| REQ-004 | `production_config_validator.py` line 172; `test_production_config_validator.py` lines 196-202, 296 | `scripts/agent/production_config_validator.py` | Phase 4 | AC-2 | unknown-key rejection cases | Planned |
| REQ-004 | `test_production_config_validator.py` lines 196-202, 296 | `tests/agent/test_production_config_validator.py` | Phase 5 | AC-2 | unknown-key rejection cases | Planned |
| REQ-005 | `config/agent.toml` lines 215, 229-232 (values identical) | `config/agent.toml` | Phase 5 | AC-3 | snapshot inventory | Planned |
| REQ-006 | `startup_prompt_setup.py` lines 67-70, 122 | `scripts/agent/startup_prompt_setup.py` | Phase 2 | AC-4 | `tests/agent/test_startup_prompt_setup.py` | Planned |
| REQ-006 | `test_startup_prompt_setup.py` lines 27, 37 | `tests/agent/test_startup_prompt_setup.py` | Phase 2 | AC-4 | same file | Planned |
| REQ-006 | `test_startup.py` lines 50, 72, 90, 106, 127 | `tests/agent/test_startup.py` | Phase 2 | AC-4 | same file | Planned |
| REQ-006 | `test_agent_cmd_context.py` line 51 | `tests/agent/commands/test_agent_cmd_context.py` | Phase 2 | AC-4 | same file | Planned |
| REQ-006 | `test_conversation_service.py` lines 16, 26 | `tests/agent/services/test_conversation_service.py` | Phase 2 | AC-4 | same file | Planned |
| REQ-007 | `config_reload.py` lines 138-142, 144-152 | `scripts/agent/services/config_reload.py` | Phase 3 | AC-4 | `tests/agent/services/test_config_reload.py` lines 275, 320 | Planned |
| REQ-007 | `test_config_reload.py` lines 51, 101, 275, 320, 931, 1081, 1149-1168 | `tests/agent/services/test_config_reload.py` | Phase 3 | AC-4 | prepare/commit failure paths | Planned |
| REQ-008 | Testing Expectations; measured inventory 18 equal / 14 differing / 2 absent | `tests/agent/test_config_effective_snapshot.py` | Phase 5 | AC-5 | snapshot and precedence tests | Planned |
| REQ-009 | `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` line 51 | `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Phase 6 | AC-6 | `check_docs_consistency.py --domain agent` | Planned |
| REQ-009 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` line 85 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 6 | AC-6 | `check_docs_consistency.py --domain agent` | Planned |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261122-165517 -->