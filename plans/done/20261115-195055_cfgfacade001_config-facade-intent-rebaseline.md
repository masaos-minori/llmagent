# Re-baseline the memo2 config-facade intent against the current architecture; classify each item

## Goal
Produce an evidence-cited classification of every `memo2.md` config-facade item against the
current filesystem — already-implemented, gap-confirmed, or rejected — and conclude which (if
any) require implementation. No facade, settings module, or config-loading code is created.

## Priority
Medium

## Scope
- **In-Scope**:
  - Classify each of the six `memo2.md` items (P1-1 providers normalization, P1-2 MCP timeout
    keys, P1-3 result-token cap, P1-4 providers facade delegation, P2-1 unified validation,
    P2-2 config consistency) against the existing architecture with file/line citations.
  - Record each verdict in this Plan's classification table.
  - File a separate follow-up issue only for a gap that repository evidence confirms.
  - Capture the superseded pointer for `memo2.md` in this Plan's traceability so the memo is not
    re-executed.
- **Out-of-Scope**:
  - Implementing any facade, settings module, or providers normalization.
  - Creating or reviving `agent/settings.py`, `agent/providers.py`, `mcp/config.py`,
    `mcp/toll_gate.py`, or `mcp_settings.py`.
  - Adding config-loading code while an existing mechanism covers the same responsibility.
  - Changing any `config/agent.toml` key.
  - Modifying `memo2.md` itself during this phase (see Documentation Impact).

- **Dependencies**: `N/A: none`

## Background
Re-baseline performed against the current tree, `master` clean, in sync with `origin/master`
(0/0), verified 2026-11-15.

**What `memo2.md` actually is.** `memo2.md` (repository root) currently holds only a Japanese
instruction header for the plan → implementation-procedure phase. It contains no P1-1..P2-2
improvement list, no `agent/settings.py` reference, and no completed-refactor claim. Its last
tracked version (parent of `5a9fd2920 chore: stop tracking memo2.md`) was identical. The file is
an intentionally-untracked local memo (commit message: "not meant to be shared"; the
`memo*.md` `.gitignore` pattern applies). The P1-1..P2-2 strings appear nowhere in the working
tree or any branch except inside this issue's own text.

**Phantom premises (verified absent).** None of these exist:
`agent/settings.py`, `agent/providers.py`, `mcp/config.py`, `mcp/toll_gate.py`,
`mcp_settings.py`, `tests/agent/test_settings.py`, `tests/agent/test_providers.py`,
`tests/mcp/test_config.py`, `scripts/mcp/` (MCP code lives in `scripts/mcp_servers/` and
`scripts/mcp_launcher.py`). Config keys `mcp_timeout`, `mcp_max_call_time`, `mcp_max_result_tokens`
and a `providers = "openai, gemini"` string have zero occurrences in `config/agent.toml` or the
repository. The claimed commit `refactor(config): unify config loading and MCP settings into
agent.settings facade` and the archived procedure do not exist in any branch or in
`implementations/done/`.

**Real config architecture (verified present).**
- `scripts/shared/config_loader.py` — shared `ConfigLoader` (TOML/JSON), `_merge_one_level`
  (`:172`) for `[mcp_servers.<key>]` sections, and per-process file isolation via
  `restrict_to()` (`:41`).
- `scripts/agent/config_builders.py`, `config_section_builders.py`, `config_dataclasses.py` —
  typed `AgentConfig` assembly from loaded data.
- `scripts/shared/mcp_config.py` — `McpServerConfig` with `call_timeout_sec`, `health_timeout`,
  `startup_timeout_sec` and `_validate_timeouts` (`:156`); `get_effective_health_timeout`.
- `scripts/agent/production_config_validator.py` — `ProductionConfigValidator.validate()` and
  `validate_against_registry()`, deriving valid keys from dataclass introspection plus tool
  safety-tier and registry checks.
- Per-domain loaders instantiate `ConfigLoader` with their own allowed files: `scripts/db/config.py`,
  `scripts/eventbus/config.py`, `scripts/rag/config_resolution.py`,
  `scripts/mcp_servers/<server>/*_models.py`.

## Problem
Acting on `memo2.md` as described would build parallel config machinery alongside the existing
shared loader/builders/validator and contradict the per-process config isolation design
(`ConfigLoader.restrict_to`, adrrev008). The memo's premise (a phantom tree with a completed
facade refactor) does not match the filesystem, so the next session risks repeating the same
phantom-premise work.

## Reason for Change
A re-baselined, evidence-cited classification prevents re-executing phantom claims and lets the
pipeline judge whether any genuine residual gap remains. Only a gap-confirmed item may proceed to
a plan.

## Implementation Intent
Classify each item against the existing architecture first, citing file/line evidence. Where an
existing mechanism already covers an item, mark it already-implemented. Where a residual gap is
plausible, confirm or reject it with evidence; confirmed gaps become follow-up issues. Any future
unification must respect `ConfigLoader.restrict_to` (per-domain loaders keep their own allowed
files); a single process-wide agent-side facade must not be introduced.

## Requirements
- `REQ-001`: P1-1 (providers normalization) is classified with evidence. Verdict: **rejected** —
  no comma-separated `providers` config or normalization exists in `scripts/` or `config/`;
  there is nothing to normalize.
- `REQ-002`: P1-2 (MCP timeout keys) is classified with evidence. Verdict: **already-implemented**
  — `scripts/shared/mcp_config.py` `McpServerConfig` carries `call_timeout_sec`, `health_timeout`,
  `startup_timeout_sec` and validates them in `_validate_timeouts` (`:156-168`).
- `REQ-003`: P1-3 (result-token cap) is classified with evidence. Verdict: **rejected** as stated —
  no `mcp_max_result_tokens` or result-token cap exists; only unrelated server-side result-count
  caps (`ins_limit`, `default_ins`) are present.
- `REQ-004`: P1-4 (providers facade delegation) is classified with evidence. Verdict: **rejected**
  — per-domain loaders already assemble config with their own allowed files; a single
  `agent/settings.py` facade would weaken `ConfigLoader.restrict_to` per-process isolation.
- `REQ-005`: P2-1 (unified validation) is classified with evidence. Verdict: **already-implemented**
  — `scripts/agent/production_config_validator.py` `ProductionConfigValidator` performs production
  key, tool safety-tier, and registry validation.
- `REQ-006`: P2-2 (config consistency) is classified with evidence. Verdict: **already-implemented**
  — cross-domain consistency is the shared `ConfigLoader` base (`scripts/shared/config_loader.py`);
  per-domain separation is by design, not a gap.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `plans/20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md` | Create | Author the evidence-cited classification of the six `memo2.md` items and record the conclusion that no implementation code is required. | REQ-001..REQ-006 | `issues/20261115-165529_cfgfacade001...` Required Changes enumerates the six items; classification recorded in this Plan's Design section (checked in Step 2/5) | — | Verified |

Rules:
- One row per file. A directory, glob pattern, component/module name, file group, or vague
  phrase MUST NOT appear as a row.
- Test, configuration, schema, migration, deployment, and documentation files are their own
  rows when they require modification.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `memo2.md` | The source document being re-baselined; confirm its current content (instruction header only) before classifying. | `plans/...cfgfacade001...` / REQ-001..REQ-006 |
| `scripts/shared/config_loader.py` | Confirm the shared loader and `restrict_to` per-process isolation that any unification must respect. | REQ-004, REQ-006 |
| `scripts/shared/mcp_config.py` | Confirm `McpServerConfig` timeout fields and `_validate_timeouts` cover P1-2. | REQ-002 |
| `scripts/agent/production_config_validator.py` | Confirm `ProductionConfigValidator` covers P2-1. | REQ-005 |
| `scripts/agent/config_builders.py`, `config_section_builders.py`, `config_dataclasses.py` | Confirm typed `AgentConfig` assembly already exists (no builder gap). | REQ-004, REQ-006 |
| `scripts/db/config.py`, `scripts/eventbus/config.py`, `scripts/rag/config_resolution.py`, `scripts/mcp_servers/<server>/*_models.py` | Confirm per-domain loaders with their own allowed files (P1-4, P2-2). | REQ-004, REQ-006 |
| `config/agent.toml` | Confirm the claimed keys and `providers` string are absent. | REQ-001, REQ-003 |

## Acceptance Criteria
- Each of the six `memo2.md` items has a recorded verdict (already-implemented / gap-confirmed /
  rejected) with file/line citations. (REQ-001..REQ-006)
- No gap-confirmed item requires implementation; if one were confirmed, it would be filed as a
  separate follow-up issue. (REQ-001..REQ-006)
- No new config-loading code, facade, or settings module is created; no `config/agent.toml` key
  changes. (Out-of-Scope)
- The superseded pointer for `memo2.md` is captured so the memo is not re-executed. (In-Scope)

## Tests
No code changes in this issue; no new tests. Verification is evidence review (grep/file
citations) recorded in the classification table. Follow-up issues from confirmed gaps carry
their own test expectations.

## Documentation Impact
The authoritative classification lives in this Plan. `memo2.md` is an intentionally-untracked
local memo (commit `5a9fd2920`), so a superseded marker is recorded here in Traceability rather
than committed to the memo during this phase (editing files outside `plans/`, `issues/`, and the
moved Issue is out of this phase's allowed operations). If a later confirmed-gap follow-up
changes behavior, `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` or agent config docs
would be updated by that follow-up, not here. Driven by REQ-001..REQ-006.

## Assumptions
- The six items to classify are those enumerated in the issue's Required Changes; the issue's
  claim that `memo2.md` itself enumerates them is treated as the issue's framing, not as
  `memo2.md` content (the current `memo2.md` holds no such list).
- The real config architecture described in Background fully covers the six items; any item not
  clearly covered is carried as a `Needs confirmation` Unknown rather than assumed implemented.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the transport-level `call_timeout_sec` (`McpServerConfig`) vs server-internal timeout relationship (e.g. `search_timeout_sec` in `config/web_search_mcp_server.toml`) is an operational problem in practice. | Observed timeout-budget mismatches at runtime. | Record as a non-blocking observation; confirm operationally only if a follow-up is opened. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `plans/20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md` | Create | Low | N/A | N/A | None |

## Design
Classification: Path A. The deliverable is a document-only classification; no source, test,
config, schema, or deployment file is modified (only this plan is authored). No persisted-schema,
public-API, or shared-constant change is involved.

**Classification result (evidence-cited).**

| Item | Verdict | Evidence |
|---|---|---|
| P1-1 providers normalization | Rejected | No `providers` handling anywhere in `scripts/`; no comma-separated providers config to normalize. |
| P1-2 MCP timeout keys | Already-implemented | `scripts/shared/mcp_config.py` `McpServerConfig` (`call_timeout_sec`, `health_timeout`, `startup_timeout_sec`) + `_validate_timeouts` (`:156-168`). |
| P1-3 result-token cap | Rejected | No `mcp_max_result_tokens` or result-token cap; only unrelated server result-count caps (`ins_limit`, `default_ins`). |
| P1-4 providers facade delegation | Rejected | Per-domain loaders keep their own allowed files; a single facade weakens `ConfigLoader.restrict_to` isolation. |
| P2-1 unified validation | Already-implemented | `scripts/agent/production_config_validator.py` `ProductionConfigValidator`. |
| P2-2 config consistency | Already-implemented | Shared `ConfigLoader` base; per-domain separation is by design. |

**Conclusion.** All six items are already-implemented or rejected; no confirmed implementation
gap. The single residual question (UNK-01, transport vs server-internal timeout budget) is an
operational "needs confirmation" item, not a confirmed gap, so it does not open an implementation
plan.

## Implementation steps
Each step cites the exact file path(s) via `Implementation Target Files` rows. Steps are small
enough to be independently revertable.

1. **Phase 1: Record the classification** (`plans/20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md`)
    - [ ] Write the evidence-cited classification of the six items (table above) with file/line
      citations into this Plan. (REQ-001..REQ-006)
    - [ ] Record the superseded pointer for `memo2.md` in this Plan's Traceability. (In-Scope)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| This Plan | Structure check | `uv run python tools/check_workitem_structure.py --file plans/20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md` | All required `## ` sections present |
| Classification | Evidence review | grep/file citations against `scripts/`, `config/` | Every verdict backed by a citation |

## Risks
- **Risk**: A later session re-executes `memo2.md` believing it still describes a config-facade
  refactor. → **Mitigation**: Record the superseded pointer in this Plan's Traceability and mark
  each item already-implemented/rejected so no phantom work is implied.
- **Risk**: The re-baseline misses a genuine residual gap (e.g. the UNK-01 timeout budget
  question). → **Mitigation**: Record UNK-01 explicitly; open a follow-up only if operational
  evidence confirms a defect.
- **Risk**: Introducing a facade anyway to "complete" the memo's intent. → **Mitigation**: Keep
  the Out-of-Scope list and the `ConfigLoader.restrict_to` constraint; no new config machinery
  while an existing mechanism covers the responsibility.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the classification (`plans/...cfgfacade001...`) | In Progress | — | — | REQ-001..REQ-006 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| implementations/20261116-092800_01_plans_20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261115-165529_cfgfacade001_config-facade-intent-rebaseline.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-195055
- **Related target files**: `plans/20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md`

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (P1-1) | plan | 1 | AC 1 | evidence review | Confirmed by repository evidence |
| REQ-002 | Required Changes (P1-2) | plan | 1 | AC 1 | `mcp_config.py` citation | Confirmed by repository evidence |
| REQ-003 | Required Changes (P1-3) | plan | 1 | AC 1 | evidence review | Confirmed by repository evidence |
| REQ-004 | Required Changes (P1-4) | plan | 1 | AC 1 | `config_loader.py` citation | Confirmed by repository evidence |
| REQ-005 | Required Changes (P2-1) | plan | 1 | AC 1 | `production_config_validator.py` citation | Confirmed by repository evidence |
| REQ-006 | Required Changes (P2-2) | plan | 1 | AC 1 | `config_loader.py` citation | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261116-092800 -->