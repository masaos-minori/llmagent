# Implementation: Fix `/approve [reason]`/`/reject [reason]` Syntax in Docs (4 files)

## Goal

Correct 4 documentation files that show `/approve [reason]`/`/reject [reason]` as the command syntax, omitting the required `approval_id` argument. Additionally, correct one file's stale claim that a missing `ctx.turn.pending_approval_id` falls back to a DB search — no such fallback exists; a missing/unparseable `approval_id` argument is an immediate validation error.

## Scope

**In scope:**
- `docs/05_agent_01_system-overview.md` (line ~115): fix `/approve [reason]`, `/reject [reason]` table entry.
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` (line ~66): fix the startup-warning-format line.
- `docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md` (lines ~35-36, ~49, ~54, ~56): fix `/approve [reason]`/`/reject [reason]` occurrences; additionally fix the "DB検索にフォールバック" claim at lines ~35-36.
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md` (lines ~95, ~97): fix `/approve [reason]`/`/reject [reason]` occurrences.

**Out of scope:**
- The runtime message fixes themselves in `startup.py`/`orchestrator.py` (separate implementation docs) — this doc only documents the corrected syntax, matching what those runtime fixes will produce.
- The `workflow_require_approval` mechanism-attribution fix (separate implementation doc).
- Any other content in these 4 files not related to `/approve`/`/reject` syntax or the DB-fallback claim.

## Assumptions

- All occurrences below are confirmed present by direct read/grep:
  - `docs/05_agent_01_system-overview.md:115`: `| ワークフロー | \`/approve [reason]\`, \`/reject [reason]\` |`
  - `docs/05_agent_10_01_operations-and-observability-startup-and-health.md:66`: `... Use /approve [reason] or /reject [reason].\``
  - `docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md:35-36`: table rows for `/approve [reason]` / `/reject [reason]` each citing `ctx.turn.pending_approval_id`(Noneの場合はDB検索にフォールバック); line ~49 repeats the startup warning text; lines ~54/56 reference `/approve`/`/reject` prose.
  - `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md:95,97`: `[workflow] Approval required. Use /approve [reason] or /reject [reason].` and a prose sentence `/approve [reason]`または`/reject [reason]`を実行すると...
- `cmd_workflow.py::_cmd_approve`/`_cmd_reject` (confirmed by direct read) treat a missing/unparseable `approval_id` argument as an immediate validation error (`"Approval ID required. Use: /approve <approval_id> [reason]"`), with no DB-search fallback of any kind — this is the ground truth the workflow-debug doc must be corrected to match.

## Implementation

### Target file

`docs/05_agent_01_system-overview.md`, `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`, `docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`, `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`

### Procedure

1. In `docs/05_agent_01_system-overview.md:115`, replace `\`/approve [reason]\`, \`/reject [reason]\`` with `` `/approve <approval_id> [reason]`, `/reject <approval_id> [reason]` ``.
2. In `docs/05_agent_10_01_operations-and-observability-startup-and-health.md:66`, replace `Use /approve [reason] or /reject [reason].` with `Use /approve <approval_id> [reason] or /reject <approval_id> [reason].` (matching the corrected runtime message format from the `startup.py` fix).
3. In `docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`:
   - Lines ~35-36: replace `/approve [reason]` / `/reject [reason]` with `/approve <approval_id> [reason]` / `/reject <approval_id> [reason]` in the table's left column.
   - Same lines, right column: replace `` `ctx.turn.pending_approval_id`(Noneの場合はDB検索にフォールバック) `` with `` `approval_id` は必須引数 — 省略時は検証エラー（DB検索フォールバックは存在しない） ``.
   - Line ~49 (startup warning example text): apply the same `<approval_id>` fix as step 2.
   - Lines ~54/56 (prose referencing `/approve`/`/reject`): update to show `<approval_id>` as a required argument wherever the bare command is shown without it.
4. In `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`:
   - Line ~95: replace `Use /approve [reason] or /reject [reason].` with `Use /approve <approval_id> [reason] or /reject <approval_id> [reason].`.
   - Line ~97: replace `\`/approve [reason]\`または\`/reject [reason]\`` with `` `/approve <approval_id> [reason]`または`/reject <approval_id> [reason]` ``.

### Method

Prose/table-cell text replacement across 4 Markdown files; no structural changes (headings, table columns, diagrams) beyond the cell/sentence content itself.

### Details

- Preserve Japanese prose language and existing formatting/markup (backticks, table pipes) exactly, only substituting the corrected command syntax and the corrected DB-fallback sentence.
- After editing, grep each file to confirm no remaining bare `/approve [reason]` or `/reject [reason]` (without `<approval_id>`) remains, and no remaining "DB検索にフォールバック" claim remains in the workflow-debug doc.
- Do not touch `docs/05_agent_08_01_configuration-loading-agent-config-part1.md`/`-part2.md` — confirmed already correct per the plan's Out-of-Scope section.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to these 4 doc files:

| Check | Tool | Target |
|---|---|---|
| Manual grep | `grep -rn "/approve \[reason\]\|/reject \[reason\]" docs/05_agent_01_system-overview.md docs/05_agent_10_01_operations-and-observability-startup-and-health.md docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md` | No matches remain |
| Manual grep (DB-fallback claim) | `grep -n "DB検索にフォールバック" docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md` | No matches remain |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
