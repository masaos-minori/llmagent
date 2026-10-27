# Plan: Make config reload apply all-or-nothing to the live context

## Goal
- `/config reload` applies the fully assembled new config to the live `ctx.cfg` /
  `ctx.conv` only after every section validates; on any validation failure the live
  config is byte-for-byte unchanged and services are not re-synced.

## Priority
Medium — ambiguous live configuration after a failed reload is a debugging hazard, but
the failure window is narrow and restart is a known workaround today. Path A task
(2 production files, 1 test file, 1 doc).

## Scope
- **In-Scope**:
  - Two-phase (prepare/validate → commit) reordering inside
    `scripts/agent/services/config_reload.py`.
  - Prepare/apply split of the section-reload primitives in
    `scripts/agent/services/config_section_reload.py`.
  - Regression tests for partial-apply scenarios in
    `tests/agent/services/test_config_reload.py`.
  - Docs: state the all-or-nothing guarantee of `/reload`.
- **Out-of-Scope**:
  - Hot-reload of fields that are intentionally startup-only.
  - Config file format changes.
  - New validators or registry-semantics changes (issue AI instruction).
  - Transactional service sync / rollback of `_sync_services` side effects (see Risks).
- **Dependencies**: N/A: none

## Background
From the python-code-review pass over the REPL command path (finding F-005). Verified
against current code:
- `scripts/agent/services/config_reload.py` `apply_config_dict` (L89-122) runs
  `_apply_validated_sections` (llm→rag→tool, L210-221), then `_apply_direct_reloads`
  (approval→memory→mcp, L223-234), then `_apply_direct_fields` (system_prompt_tool →
  `ctx.conv.system_prompt_content`, `allowed_tools`/`masked_fields` → `ctx.cfg.tool`,
  L236-243), then `_handle_mcp_changes` (lifecycle cleanup for removed servers,
  L245-264), then `_sync_services` (L144-161).
- `scripts/agent/services/config_section_reload.py` `reload_validated_section`
  (L15-57) already validates against a `dataclasses.replace` candidate before
  `setattr` — atomic per section, but `_apply_validated_sections` applies each section
  as it succeeds, so a failure in `tool` leaves `llm`/`rag` already applied.
  `reload_direct_fields` (L60-94) mutates the live section with `setattr` and runs no
  validation at all.

## Problem
A config file with one invalid section leaves a mix of new and old live config (early
sections applied, later ones not) with services never re-synced, until restart.

## Reason for Change
Issue claims corrected against current code (adversarial verification):
- The issue's evidence order is stale: direct fields are applied **after** the validated
  sections today, not before, and no cross-section validators exist (all registry
  `validator_fn` take one section dataclass candidate; grep over
  `scripts/agent/services/config_field_registry.py` / `config_validators.py`). The
  partial-apply defect is real but arises from the sequential per-section apply loop.
- "`cmd_config.py` calls service re-sync only when the whole reload succeeds" is
  imprecise: re-sync happens inside `apply_config_dict`; `cmd_config.py` `_cmd_reload`
  (L43-107) only catches `OSError`/`ValueError` and prints the failure. It needs no
  change (Reference File, not a target).
- The issue names a public `reload_config` signature; the actual stable public entries
  are `ConfigReloadService.apply_config` / `apply_config_dict`. Those stay stable.

## Implementation Intent
Keep the field registry and validator rules unchanged; change only ordering:
1. Candidate phase — build candidate section objects (`dataclasses.replace`, already the
   pattern in `reload_validated_section`) and run the same validators, for **all**
   sections, before any live mutation. Collect direct-field changes (`allowed_tools`,
   `masked_fields` folded into the `tool` candidate; `system_prompt_tool` held aside for
   commit) and MCP change classification (read-only) without cleanup.
2. Commit phase — only after the whole candidate set is valid: `setattr` the candidate
   sections onto `ctx.cfg`, set `ctx.conv.system_prompt_content`, run removed-server
   lifecycle cleanup, then `_sync_services`. Nothing in the commit phase can raise a
   validation error, so failure = untouched live config.

## Requirements
- `REQ-001`: `ConfigReloadService.apply_config_dict` validates a fully assembled
  candidate config (llm/rag/tool validated sections + approval/memory/mcp direct
  sections + direct fields + MCP classification) before mutating `ctx.cfg` or
  `ctx.conv`.
- `REQ-002`: `config_section_reload.py` exposes prepare variants (build candidate +
  run the same validators, no live mutation) and apply variants (`setattr` only) for
  both the validated and direct paths; existing `reload_validated_section` /
  `reload_direct_fields` remain as prepare+apply compositions so existing callers/tests
  keep working.
- `REQ-003`: On any `ConfigReloadValidationError`, `ctx.cfg` (all sections, including
  `tool.allowed_tools` / `tool.masked_fields`) and `ctx.conv.system_prompt_content` are
  unchanged; the raised type and message specificity (field names from the failing
  validator, per-section `ValueError→ConfigReloadValidationError` wrapping,
  `config_section_reload.py` L42-54) are preserved.
- `REQ-004`: Removed-server lifecycle cleanup (`lifecycle.cleanup_server_resources`,
  `config_reload.py` L245-264) runs only in the commit phase — a failed validation
  leaves server resources untouched.
- `REQ-005`: Service re-sync (`_sync_services`) runs only in the commit phase, i.e. only
  after whole-config validation succeeded.
- `REQ-006`: No new validators, no registry semantics change, no weakening of existing
  cross-field checks; direct sections do not gain validators they don't have today.
- `REQ-007`: A fully valid reload still updates all sections, direct fields,
  `system_prompt_tool`, MCP classification outcome categories, and services — outcome
  report shape unchanged.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/services/config_reload.py | Reorder `apply_config_dict` into candidate phase (prepare/validate all sections + direct fields + MCP classification, no mutation) then commit phase (apply sections, conv field, MCP cleanup, `_sync_services`) | Sequential per-section apply (L106-108) mutates `ctx.cfg` before later sections validate | REQ-001, REQ-004, REQ-005, REQ-007 | Read: `apply_config_dict` L89-122; `_apply_validated_sections` L210-221; `_handle_mcp_changes` L245-264 | tests/agent/services/test_config_reload.py | Verified |
| scripts/agent/services/config_section_reload.py | Split into `prepare_validated_section`/`apply_validated_section` and `prepare_direct_section`/`apply_direct_section`; keep `reload_validated_section`/`reload_direct_fields` as compositions | Validated-section candidate pattern exists but apply is fused (L56); direct path mutates live cfg unvalidated (L91-92) | REQ-002, REQ-003, REQ-006 | Read: `reload_validated_section` L15-57, `reload_direct_fields` L60-94 | tests/agent/services/test_config_reload.py | Verified |
| tests/agent/services/test_config_reload.py | Add regression: invalid `tool` field + valid `llm`/`rag`/direct changes → live cfg and conv unchanged, error names the failing field; MCP removed-server cleanup not run on failure; valid reload applies everything (all-or-nothing happy path) | Existing tests cover per-section apply, not cross-section failure atomicity | REQ-001, REQ-003, REQ-004, REQ-007 | Read: file exists, exercises `ConfigReloadService`; 4 commits/30d, 2 authors | — | Verified |
| docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md | State the all-or-nothing guarantee of `/reload` and the failure behavior (live config unchanged, no service re-sync, actionable error) | Issue Documentation Impact: reload semantics change is user-visible | REQ-001, REQ-003 | `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` L56 maps reload category semantics to `agent_07_06`; file exists | N/A: documentation only | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/commands/cmd_config.py | `_cmd_reload` error surface (`OSError`/`ValueError` branches L102-107) — confirm it already reports `ConfigReloadValidationError` without change | REQ-003 |
| scripts/agent/services/config_field_registry.py | Registry entries and `validator_fn` wiring — must not change semantics | REQ-006 |
| scripts/agent/services/config_validators.py | Validator signatures all take one section candidate; confirms no live-cfg cross-section coupling to untangle | REQ-006 |
| scripts/agent/config_dataclasses.py | All six sections (`LLMConfig` L109, `RAGConfig` L147, `ToolConfig` L154, `MemoryConfig` L221, `MCPConfig` L263, `ApprovalConfig` L278) are dataclasses — `dataclasses.replace` candidate construction is safe for the direct sections too | REQ-002 |
| scripts/agent/services/config_service_sync.py | `ServiceSyncer.sync_all` consumes already-updated `ctx.cfg` sections (called at `config_reload.py` L152-157) — commit-phase placement only | REQ-005 |
| scripts/agent/services/exceptions.py | `ConfigReloadValidationError(ValueError)` L17-18 — error type preserved | REQ-003 |
| tests/agent/commands/test_agent_cmd_config.py | Existing command-level reload expectations — regression gate, expected unchanged | REQ-007 |

## Acceptance Criteria
- `AC-001` (REQ-001, REQ-003): A config payload with one invalid section leaves every
  section of `ctx.cfg`, `tool.allowed_tools`/`tool.masked_fields`, and
  `ctx.conv.system_prompt_content` unchanged (byte-for-byte equal to pre-reload state),
  and services are not re-synced.
- `AC-002` (REQ-007): A fully valid reload still updates all sections, direct fields,
  `system_prompt_tool`, and services; outcome categories (`applied` / `needs_restart` /
  `skipped` / `startup_only` / `always_live`) unchanged.
- `AC-003` (REQ-003): The failure message names the failing field/section at least as
  specifically as today (`ConfigReloadValidationError` from the registry validators).
- `AC-004` (REQ-004): On validation failure, `lifecycle.cleanup_server_resources` is
  not called for removed MCP servers.
- `AC-005` (REQ-006): No validator/registry entry is added, removed, or weakened;
  existing config reload tests pass or are updated with explicit justification.

## Tests
- `T-001` (REQ-001, REQ-003, regression, the issue's core scenario): payload with valid
  `llm` + `rag` changes and an invalid `tool` value → `ConfigReloadValidationError`,
  all live sections unchanged, `_sync_services` not reached.
- `T-002` (REQ-003, direct-field + section interaction): payload with `allowed_tools`,
  `masked_fields`, `system_prompt_tool` plus a later-failing section → direct fields and
  `ctx.conv.system_prompt_content` unchanged.
- `T-003` (REQ-004, MCP): payload removing an MCP server plus an invalid section →
  cleanup not invoked, `needs_restart` not reported.
- `T-004` (REQ-007): fully valid payload still applies everything (extend existing
  happy-path cases rather than replace them).
- Regression gate: `uv run pytest tests/agent/services/test_config_reload.py
  tests/agent/services/test_config_reload_classification.py
  tests/agent/commands/test_agent_cmd_config.py`.

## Documentation Impact
Docs update required, driven by REQ-001/REQ-003: the hot-reload command doc (mapped via
`docs/00_index.md` / `agent_08_01` L56 → `agent_07_06_cli-and-commands-hot-reload.md`)
must state the all-or-nothing guarantee and the no-partial-application failure behavior.

## Assumptions
- `dataclasses.replace` is safe for all six section dataclasses (all six classes in
  `scripts/agent/config_dataclasses.py` confirmed dataclasses; llm/rag/tool already use
  `replace` at `config_section_reload.py` L43).
- Registry validators never read the live `ctx.cfg` (all take the candidate section only)
  — confirmed by signature review of `scripts/agent/services/config_validators.py`;
  therefore candidate-phase validation needs no live-cfg extraction.
- `scripts/agent/services/config_service_sync.py` `ServiceSyncer.sync_all` does not
  perform validation that can fail on a config the sections already accepted; commit-
  phase ordering is sufficient (any sync-time failure remains out of scope — see Risks).
- `cmd_config.py` needs no change; its `except ValueError` branch already surfaces
  `ConfigReloadValidationError`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether existing tests assert that partial application occurs (i.e., encode today's non-atomic behavior) | `test_config_reload.py` case-by-case review not yet done | Run the existing suite after the reorder; update only cases that assert partial-apply, with explicit justification per AC-005 | False |

Note: `Blocking?` column values are `False` for all rows above.

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/services/config_reload.py | Two-phase reorder of `apply_config_dict` | `/config reload` command path only; 2 importers (`cmd_config`, `cmd_mcp`-related flows confirmed by grep) | 0 | 1 | None (no schema/deploy change) |
| scripts/agent/services/config_section_reload.py | prepare/apply split | `config_reload` + its tests only (grep: sole production importer is `config_reload.py`) | 1 | 1 | None |
| tests/agent/services/test_config_reload.py | Regression extensions | test suite | 4 | 2 | None |
| docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md | reload semantics section | docs | — | — | None |

## Design
- Candidate object: for each touched section, `candidate = dataclasses.replace(current,
  **changed_fields)` (already the validated-section pattern). Validation runs against
  the candidate exactly as today for llm/rag/tool; direct sections build candidates the
  same way but run no validators (rule set unchanged, REQ-006) — the change is that
  `setattr` moves to the commit phase.
- Direct fields: `allowed_tools`/`masked_fields` are fields of the `tool` section, so
  they join the `tool` candidate's `changed_fields` and become atomic with it;
  `system_prompt_tool` targets `ctx.conv`, not `ctx.cfg`, so it is held in a small
  pending-apply list executed only in the commit phase.
- MCP: `classify_mcp_server_changes` is read-only classification → candidate phase;
  removed-server `cleanup_server_resources` side effect → commit phase (REQ-004).
- Failure model: the candidate phase is the only place validation can raise; once in the
  commit phase, no validation error path exists, making whole-config atomicity a
  structural property rather than a compensation routine. No rollback/compensation code
  is introduced (unlike the turn001 Plan's DB compensation — different mechanism, same
  Plan-level goal).
- Public API stability: `apply_config` / `apply_config_dict` / `ConfigReloadOutcome`
  signatures unchanged; `reload_validated_section` / `reload_direct_fields` kept as
  prepare+apply compositions for existing callers/tests (REQ-002).

## Implementation steps
1. **Phase 1: Prepare/apply split in `scripts/agent/services/config_section_reload.py`**
   - [ ] Add `prepare_validated_section` (candidate + validators, returns candidate and
     changed-field report, no setattr) and `apply_validated_section` (setattr only);
     re-implement `reload_validated_section` as the composition (REQ-002;
     scripts/agent/services/config_section_reload.py)
   - [ ] Add `prepare_direct_section` (candidate via `dataclasses.replace`, no
     validators) and `apply_direct_section`; re-implement `reload_direct_fields` as the
     composition (REQ-002, REQ-006; scripts/agent/services/config_section_reload.py)
2. **Phase 2: Two-phase orchestration in `scripts/agent/services/config_reload.py`**
   - [ ] Restructure `apply_config_dict`: candidate phase over llm/rag/tool (folding
     `allowed_tools`/`masked_fields` into the tool candidate), approval/memory/mcp,
     `system_prompt_tool` pending list, and MCP classification; commit phase applies
     candidates, conv field, MCP cleanup, then `_sync_services` (REQ-001, REQ-004,
     REQ-005, REQ-007; scripts/agent/services/config_reload.py)
   - [ ] Confirm `cmd_config.py` error rendering unchanged (REQ-003; reference only)
3. **Phase 3: Regression tests and docs**
   - [ ] Add T-001..T-004 to `tests/agent/services/test_config_reload.py` (REQ-001,
     REQ-003, REQ-004, REQ-007; tests/agent/services/test_config_reload.py)
   - [ ] Update the hot-reload doc section (docs/23_agent/agent_07_06_cli-and-commands-
     hot-reload.md) with the all-or-nothing guarantee (REQ-001, REQ-003)
   - [ ] Run the full validation plan below; check `deploy.sh` impact: none (config
     service change only, no schema or deployment file touched)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/services/config_section_reload.py | Unit: prepare returns candidate without mutating live cfg; apply is setattr-only | `uv run pytest tests/agent/services/test_config_reload.py` | New atomicity cases pass |
| scripts/agent/services/config_reload.py | Unit (service-level payload injection): T-001..T-004 | `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_classification.py` | Failed reload leaves cfg/conv untouched; valid reload applies all |
| scripts/agent/commands/cmd_config.py | Regression gate (unchanged behavior) | `uv run pytest tests/agent/commands/test_agent_cmd_config.py` | Existing cases pass without edits |
| whole config subsystem | Regression gate | `uv run pytest tests/agent/services/ tests/agent/commands/ -q` | All pass or failures justified per AC-005 |
| lint/type | Static checks | `uv run ruff check . && uv run mypy scripts/agent/services/config_reload.py scripts/agent/services/config_section_reload.py` | Clean |

## Risks
- **Risk**: Existing tests may encode today's partial-apply behavior (UNK-01) →
  **Mitigation**: run the suite before/after each phase; update only asserting cases
  with explicit justification (AC-005 allows it).
- **Risk**: `system_prompt_tool` write to `ctx.conv` is outside `cfg`, easy to forget in
  the commit phase → **Mitigation**: T-002 covers it explicitly.
- **Risk**: Service sync failures after commit could still leave services partially
  updated → **Mitigation**: out of scope by issue (validation-failure atomicity only);
  `ServiceSyncer` already reports per-service `skipped`, recorded here for follow-up if
  observed.
- **Risk**: `_handle_mcp_changes` duplicate logic exists in both `config_reload.py` and
  `config_outcome_classification.py` → **Mitigation**: move only ordering, do not touch
  classification semantics (REQ-006); note as existing duplication, not this Plan's
  scope.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: prepare/apply split in config_section_reload.py | Pending | — | — | |
| 2 | Phase 2: two-phase orchestration in config_reload.py | Pending | — | — | |
| 3 | Phase 3: regression tests and docs | Pending | — | — | |

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
- **Source issue**: issues/20261026-224903_config001_make-config-reload-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-10-27 07:36:38
- **Related target files**: `scripts/agent/services/config_reload.py`,
  `scripts/agent/services/config_section_reload.py`,
  `tests/agent/services/test_config_reload.py`,
  `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Section | Source Content | Target File | Implementation Phase | Acceptance Criteria | Test Case | Basis |
|---|---|---|---|---|---|---|---|
| REQ-001 | Problem; Required Changes 1 | Partial apply across sequential section loop | scripts/agent/services/config_reload.py | Phase 2 | AC-001 | T-001 | Confirmed by repository evidence (L89-122, L210-221) |
| REQ-002 | Implementation Intent | Ordering change, rules unchanged | scripts/agent/services/config_section_reload.py | Phase 1 | AC-005 | T-001 | Confirmed (L15-57, L60-94) |
| REQ-003 | Required Changes 2; Constraints 1 | Failure leaves cfg untouched, error specificity kept | scripts/agent/services/config_section_reload.py | Phase 1 | AC-003 | T-002 | Confirmed (L42-54 wrapping; cmd_config L105-107) |
| REQ-004 | Problem (ambiguity) + AI instruction (side effects) | MCP cleanup must not run on failed reload | scripts/agent/services/config_reload.py | Phase 2 | AC-004 | T-003 | Confirmed (L245-264) |
| REQ-005 | Required Changes 3 | Re-sync tied to whole-config success | scripts/agent/services/config_reload.py | Phase 2 | AC-001 | T-001 | Confirmed (L111-117) |
| REQ-006 | Constraints 2; AI Instruction | No new validators / registry change | scripts/agent/services/config_section_reload.py | Phase 1 | AC-005 | — | Confirmed (registry/validator signature review) |
| REQ-007 | Acceptance Criteria 2 | Valid reload still applies everything | scripts/agent/services/config_reload.py | Phase 2 | AC-002 | T-004 | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-113958 -->
