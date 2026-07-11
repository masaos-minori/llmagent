# Implementation: Fix `workflow_require_approval` Mechanism Attribution in Docs

## Goal

Correct two documentation files that mischaracterize the workflow-level approval gate's controlling mechanism as an `AgentConfig`/`agent.toml` field (`workflow_require_approval`). The actual, current mechanism is `WorkflowDef.require_approval`, a per-workflow-JSON-file field (`config/workflows/*.json`), defaulting to `False`. `config/workflows/default.json` does not set it, so the gate does not currently fire by default. Per explicit user direction, this documents the current conditional/inactive-by-default state as correct, not the requirement's original "always-on" premise.

## Scope

**In scope:**
- `docs/01_overview-arch-02-pipelines.md` (line ~72): replace the `workflow_require_approval=True`/`AgentConfig`/`agent/config_dataclasses.py` framing.
- `docs/05_agent_06_04_tool-execution-and-approval-canonical.md` (lines ~47-50): replace the `AgentConfig.workflow_require_approval` mechanism-attribution paragraph immediately following the boundary table.

**Out of scope:**
- `docs/05_agent_06_04_tool-execution-and-approval-canonical.md`'s boundary table itself (line ~45: `"Currently active | 常に有効 | 無効 (require_approval=False)"`) — already correct, do not touch.
- `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` and `-part2.md` — already correctly state `workflow_require_approval` is a removed/forbidden `AgentConfig` key (`_FORBIDDEN_KEYS`); unrelated and correct, no fix needed.
- Making the gate unconditionally always-on in code — out of scope per explicit user direction (see plan's Out-of-Scope/Assumption 5); this doc fix documents current reality only.
- The `/approve`/`/reject` syntax fixes in other doc files (separate implementation doc).

## Assumptions

- `docs/01_overview-arch-02-pipelines.md:72` currently reads (confirmed by direct read):
  `workflow_require_approval=True` で execute → verify 間に人間承認ゲートを挿入できる。承認待ち状態は `workflow.sqlite` に永続化されるため、再起動後も pending approvals が復元される。(根拠: `agent/config_dataclasses.py`, `agent/orchestrator.py`, `agent/startup.py`)
- `docs/05_agent_06_04_tool-execution-and-approval-canonical.md:47-50` currently attributes the mechanism to `AgentConfig.workflow_require_approval`, citing a config-file setting (confirmed by direct read).
- `WorkflowDef.require_approval` is confirmed (by direct read per the plan) to live in `agent/workflow/models.py` and be loaded via `agent/workflow/workflow_loader.py`; `WorkflowEngine.run()` in `agent/workflow/workflow_engine.py` gates on `self._wdef.require_approval` (lines ~85-93, ~111-130 per the plan's Design section).
- `config/workflows/default.json` does not set `require_approval` (confirmed by direct read), so it defaults to `False`.

## Implementation

### Target file

`docs/01_overview-arch-02-pipelines.md` and `docs/05_agent_06_04_tool-execution-and-approval-canonical.md`

### Procedure

1. In `docs/01_overview-arch-02-pipelines.md:72`, replace the `workflow_require_approval=True`/`AgentConfig`-attributed sentence with text stating: the workflow-level approval gate is controlled by `require_approval` (default `false`) in the workflow definition JSON file itself (`config/workflows/*.json`, `WorkflowDef.require_approval`), not by an `AgentConfig`/`agent.toml` setting; `config/workflows/default.json` does not set it today, so the gate does not currently fire by default. Update the persistence sentence (`workflow.sqlite` / pending approvals restored on restart) to remain, since it is unaffected by this correction.
2. Update the trailing citation `(根拠: ...)` from `agent/config_dataclasses.py` to `agent/workflow/models.py`, `agent/workflow/workflow_loader.py` (keep `agent/orchestrator.py`, `agent/startup.py` as still-relevant citations for the persistence/recovery behavior).
3. In `docs/05_agent_06_04_tool-execution-and-approval-canonical.md:47-50`, replace the `AgentConfig.workflow_require_approval` / `agent.toml`-setting framing with the same corrected mechanism description as step 1, referencing `WorkflowDef.require_approval` and `config/workflows/*.json`.
4. Leave the boundary table (line ~45) untouched — it already correctly states current inactive-by-default status.

### Method

Prose replacement in both Markdown files; no code, no table restructuring. Keep surrounding paragraph structure and heading levels intact — this is a narrow, localized correction, not a section rewrite (per Assumption 6 of the plan).

### Details

- Write corrected prose in Japanese, matching the existing document language (these two docs are in Japanese; note this is a documentation content matter, distinct from the `rules/coding.md` "English only" rule which governs code comments/log output, not doc prose).
- Do not alter any other paragraph, table, or diagram in either file.
- Cross-check after editing that no other paragraph in either file still references `AgentConfig.workflow_require_approval` as the controlling mechanism.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to these two doc files:

| Check | Tool | Target |
|---|---|---|
| Manual grep | `grep -rn "workflow_require_approval" docs/01_overview-arch-02-pipelines.md docs/05_agent_06_04_tool-execution-and-approval-canonical.md` | No remaining attribution to `AgentConfig`/`agent.toml`; any remaining mention must be in the corrected, `WorkflowDef.require_approval`-attributed context |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
