# Implementation procedure: confirm requirements 04-09 have landed (plan step 1)

Source plan: `plans/20260717-130629_plan.md` (requirement `requires/done/20260717_10_require.md`),
Implementation step 1.

## Goal

Determine whether requirements 04-09 of today's RuntimeToolRegistry migration batch have "landed"
before this requirement's compatibility-only labeling work (docstrings/comments in
`tool_registry.py`, `tool_constants.py`, `config_dataclasses.py`, `tool_executor_helpers.py`,
`tool_policy.py`) is actually applied to real source — per this plan's own Implementation step 1
("stop and flag rather than proceeding against unmigrated code") and its Risks section (first risk:
executing this plan before 04-09 land would document a state the code doesn't yet match).

## Scope

**In scope**
- Audit `implementations/` (top-level, not `done/`, since nothing from this batch has been moved to
  `done/` yet) for same-day (`20260717`) implementation procedure docs whose target files match each
  of requirements 02-09's `## Target files` lists, as given in `requires/done/20260717_0{2..9}_require.md`.
- Record a landed / partially-landed / not-landed verdict per requirement, with file evidence.

**Out of scope**
- Performing any of requirements 04-09's actual migration work (not this requirement's job).
- Verifying against the real runtime source tree whether the migrations are coded — per this task's
  background, `RuntimeTool`/`RuntimeToolRegistry` do not exist in real source at all yet; the entire
  batch is still in the design/procedure-authoring phase. "Landed" here is judged by presence of a
  same-day implementation procedure document, not by presence of the change in `scripts/`.

## Assumptions

1. `requires/done/20260717_{02..10}_require.md` give the canonical `## Target files` list for each
   requirement (confirmed by direct read of each file's header/Target files section).
2. Because this whole batch is a documentation-generation exercise preceding actual coding, "landed"
   is a proxy: presence of a dated implementation procedure document under `implementations/`
   covering a requirement's target files, not literal code in `scripts/`.

## Implementation

### Target file

N/A — this item is an audit/investigation, not a source-file edit. Its output (the landed/not-landed
table below) gates and informs the docstring wording chosen in the `tool_registry.py`,
`tool_constants.py`, and `tool_executor_helpers.py`/`tool_policy.py` procedure docs produced alongside
this one.

### Procedure

1. List each of `requires/done/20260717_{02..09}_require.md`'s `## Target files` entries.
2. `ls implementations/*.md` and grep for filenames matching those target files, restricted to
   today's `20260717-2*` timestamp prefix (the batch's working window).
3. For each requirement, read the matching doc's `## Goal` (or title) to confirm genuine overlap
   (not a stale/unrelated filename collision — same check discipline this whole workflow uses per
   item).
4. Record landed / partially-landed / not-landed.

### Method

Manual `ls`/`grep` over `implementations/*.md`, cross-referenced against each requirement's Target
files list; no source-code inspection needed for this item since the verdict is about documents, not
`scripts/`.

### Details

Findings (from direct investigation performed for this batch run):

| Requirement | Target files (per require.md) | Matching implementations/ docs (20260717) | Verdict |
|---|---|---|---|
| 02 — Introduce RuntimeTool/RuntimeToolRegistry | `shared/runtime_tool.py`, `shared/runtime_tool_registry.py` + tests | `20260717-203121_runtime_tool.py.md`, `20260717-203200_runtime_tool_registry.py.md`, `20260717-203244_test_runtime_tool.py.md`, `20260717-203310_test_runtime_tool_registry.py.md`, `20260717-203339_deploy.sh.md` | **Landed** |
| 03 — MCP tool discovery / startup validation | `agent/services/mcp_tool_discovery.py` + test | `20260717-203830_mcp_tool_discovery.py.md`, `20260717-203931_test_mcp_tool_discovery.py.md` | **Landed** |
| 04 — RuntimeToolRegistry for routing/MCP execution | `shared/route_resolver.py`, `shared/tool_executor.py`, `shared/tool_transport_invoker.py`, `shared/http_transport.py`, `shared/transport_dto.py` + tests | none found dated `20260717` (only unrelated docs from `20260608`-`20260715`) | **Not landed** |
| 05 — RuntimeToolRegistry for LLM tool schema/help | `agent/llm_turn_runner.py`, `shared/llm_client.py`, `agent/commands/registry.py` + tests | none found dated `20260717` | **Not landed** |
| 06 — RuntimeToolRegistry for scheduler metadata/side-effect detection | (implied: `tool_executor_helpers.py`, `agent/tool_enums.py`) | `20260717-220404_tool_enums.py.md` (adds `OperationType.UNKNOWN` only) | **Partially landed** — enum scaffolding only; `is_side_effect()` migration itself has no doc |
| 07 — RuntimeToolRegistry for policy/approval classification | (implied: `agent/tool_policy.py`) | `20260717-220433_test_tool_policy.py.md`, `20260717-220527_test_tool_approval_risk.py.md` (test-side only) | **Partially landed** — test scaffolding only; no `tool_policy.py` production-code migration doc |
| 08 — Reapply policy to RuntimeToolRegistry after `/reload` | `agent/services/config_reload.py` + test | `20260717-223600_config_reload.py.md`, `20260717-223720_test_config_reload.py.md` | **Landed** |
| 09 — Consolidate startup validation into discovery service | `agent/services/mcp_tool_discovery.py` (ext.), `agent/startup.py`, `agent/repl_health.py` + test | `20260717-224511_mcp_tool_discovery.py.md`, `20260717-224630_startup.py.md`, `20260717-224725_repl_health.py.md`, `20260717-224812_test_mcp_tool_discovery.py.md` | **Landed** |

**Conclusion**: requirements 04 and 05 have no implementation procedure document yet in this batch;
06 and 07 only have partial (enum/test) scaffolding, not the production-code migration of
`is_side_effect()`/`classify_operation_type()`/`classify_risk()` to consult `RuntimeToolRegistry`.
Per this plan's own Risk-section mitigation, the docstring/comment text drafted in the companion
procedure docs for `tool_registry.py`, `tool_constants.py`, and
`tool_executor_helpers.py`/`tool_policy.py` must be treated as **forward-looking end-state text**,
not a description of current source behavior — real source today (confirmed by direct read) still
has zero `RuntimeToolRegistry` references in `is_side_effect()` (`scripts/shared/tool_executor_helpers.py:47-50`)
or `classify_operation_type()` (`scripts/agent/tool_policy.py:52-60`), and `tool_registry.py`'s
docstring (`scripts/shared/tool_registry.py:4,18-19`) still accurately describes today's code as-is.
`config_dataclasses.py`'s `ToolConfig.tool_definitions` comment (item 4) and the documentation sweep
(item 7) are the two items in this requirement that do **not** depend on 04-07 landing first, since
they describe intent/compatibility framing independent of which functions currently do the lookup.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Re-run this audit before applying items 2/3/5's edits for real | manual `ls implementations/*.md` + grep for req04-07 target files | all of req04-07 show a "Landed" (production-code, not just test/enum) doc before those docstring/comment edits are committed as fact |
| No premature edits | manual diff review at execution time | `tool_registry.py`, `tool_constants.py`, `tool_executor_helpers.py`, `tool_policy.py` edits are not merged while their gating requirement is "Not landed" per this table |
