# Implementation procedure: `docs/04_mcp_90_inconsistencies_and_known_issues.md` (verify/update stale fallback wording)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 3 (item 5).

Five prior docs target this same filename (`implementations/done/20260616-094501_...`,
`20260618-150339_...`, `20260709-103731_...`, `20260718-101707_...`, `20260719-111204_...`) — the most
recent (`20260719-111204`) was read in full: it deletes a stale MDQ hybrid-search known-issue entry,
unrelated to routing-authority fallback wording. None of the five addresses this plan's specific
concern. This is a new document.

## Goal

Verify the plan's specific claim ("line 42 wording... フォールバックとして使用される language...
if present after full read") against current source, and update only if actual stale fallback
wording is found — the plan itself flags this as conditional ("if present"), not a certain edit.

## Scope

**In scope**: `docs/04_mcp_90_inconsistencies_and_known_issues.md`, the known-issue entry titled
"ツール実行時可用性メタデータ（config_dependent/enabled/disabled_reason/RuntimeToolRegistry）は
一部実装済み" (current lines ~38-45) and any other entry mentioning `ToolRegistry`/
`RuntimeToolRegistry`/routing fallback.

**Out of scope**: All other known-issue entries in this file unrelated to routing (MDQ, unrelated
config gaps, etc.).

## Assumptions

1. Direct grep of the current file for `フォールバックとして使用される` (the exact phrase the plan
   cites) returns **zero matches in this file** — confirmed by a repo-wide grep for that exact
   string, which only matches `docs/04_mcp_03_01_dispatch-and-routing.md` (line 70) and
   `docs/04_mcp_03_02_tool-registry.md` (line 140), not this file. The plan's specific line-42 claim
   for this file does not hold as literally stated — this is a stale/speculative citation in the
   plan, not a confirmed edit target.
2. This file's actual routing-adjacent content (lines 33, 38, 41-45) describes the
   `config_dependent`/`enabled`/`disabled_reason` metadata rollout status and states "RuntimeToolRegistry
   は McpToolDiscoveryService によりライブ検出され、`ToolExecutor.set_runtime_registry()` で接続
   された" (line 42) — this is a factual wiring-completion statement, not a fallback-priority claim.
   It requires no change under this plan; the entry's subject (partial `config_dependent`/`enabled`/
   `disabled_reason` rollout) is orthogonal to routing-authority sole-vs-fallback status.

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure

1. Re-confirm via `grep -n "フォールバック" docs/04_mcp_90_inconsistencies_and_known_issues.md` that
   no fallback-specific wording exists in this file (expected: no output, or output unrelated to
   `ToolRegistry`/`RuntimeToolRegistry` routing).
2. If confirmed empty (expected outcome per Assumption 1): **no edit** — record that the plan's
   line-42 citation for this file was speculative and did not materialize on a full read; do not
   invent a fallback-wording edit where none exists.
3. If a grep miss above turns out wrong (e.g., a different revision of the file than assumed here
   contains the phrase): apply the same fix pattern as the companion `04_mcp_03_01`/`04_mcp_03_02`
   docs — replace two-tier/fallback framing with sole-authority framing, in the same style.
4. Separately, verify the known-issue entry's own framing ("は一部実装済み" / partially implemented)
   does not become stale for an unrelated reason once `RuntimeToolRegistry` becomes sole authority —
   it does not: the entry is about `config_dependent`/`enabled`/`disabled_reason` field rollout, a
   different axis from routing-authority tier count. No change needed here either.

### Method

Verification pass; conditional edit only if the exact phrase is found (expected: not found, per
direct grep already run for this doc).

### Details

- This doc exists primarily to record that the plan's specific line-42 citation for this file did
  not hold up under a full read — an important finding for the implementer, who should not spend
  time hunting for wording that a direct grep already shows is absent here (it lives in the two
  routing-spec docs instead, both separately covered).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Confirm no fallback wording present | `grep -n "フォールバック" docs/04_mcp_90_inconsistencies_and_known_issues.md` | No output (confirms no edit needed) |
| Docs consistency | `uv run check-mcp-docs` | Passes |
