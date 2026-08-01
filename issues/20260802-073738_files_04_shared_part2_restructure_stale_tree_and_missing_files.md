# Restructure docs/01_overview-files-04-shared-part2.md: remove stale file tree, resolve missing files, summarize tool-cache/health-gate design, clarify drift-verification failure behavior

## Priority
High

## Summary
`docs/01_overview-files-04-shared-part2.md` (~lines 26-71) has a manually-maintained file tree that is already missing 3 files that exist in current source (`config_utils.py`, `runtime_tool.py`, `runtime_tool_registry.py`) — confirmed drift. Separately, its description of `tool_cache.py` (LRU+TTL), `mcp_health.py`, and `tool_transport_invoker.py` is a bare filename listing without design rationale, and it is unclear whether drift verification (`tool_registry.py`/`tool_routing_validation.py`) blocks startup or only logs a warning on failure.

## Reason for Change
The missing-file gap is a confirmed, already-manifested drift risk in a file explicitly cited by this review as maintenance-cost-not-justified. `runtime_tool_registry.py` in particular may be routing-relevant, which could connect to the separately-tracked critical tool-routing-priority documentation error in `arch-03` — leaving it undocumented risks compounding that confusion. The cache/health-gate design rationale (TTL cache trading staleness risk for reduced duplicate calls; health-gating tool calls by server health) is valuable and currently missing. The drift-verification failure behavior (block vs. warn) materially affects how an operator interprets a startup or runtime failure.

## Implementation Intent
Remove the manual file tree in favor of an implementation-tree pointer. Determine whether the 3 missing files were an intentional exclusion or an oversight, and either add them with a one-line responsibility description or note the exclusion rationale explicitly. Summarize the cache/health-gate design intent in 1-2 sentences. Confirm and document the drift-verification failure behavior.

## Target Files or Areas
`docs/01_overview-files-04-shared-part2.md`

## Required Changes
- Remove the file tree enumeration (~lines 26-71); replace with a pointer to `scripts/shared/` for the current file list.
- Investigate `config_utils.py`, `runtime_tool.py`, `runtime_tool_registry.py` — determine their responsibilities and whether their absence from this document was intentional; add them (with role description) or note the exclusion reason explicitly. Pay particular attention to whether `runtime_tool_registry.py` relates to the tool-routing-authority question tracked in the separate arch-03 critical fix issue.
- Replace the bare filename listing for `tool_cache.py`/`mcp_health.py`/`tool_transport_invoker.py` with a 1-2 sentence design-intent summary (health-gating + TTL-cache tradeoff).
- Determine, via source inspection, whether drift verification failure blocks startup or only logs a warning; document the confirmed behavior explicitly (or register as a Needs Confirmation item if not determinable from a reasonable investigation).

## Acceptance Criteria
The file tree is replaced with an implementation-tree pointer; the 3 previously-missing files are either documented or their exclusion is explicitly justified; the cache/health-gate rationale is summarized in prose; drift-verification failure behavior is stated as confirmed fact or tracked as Needs Confirmation.

## Testing Expectations
Not required (documentation-only). The underlying investigation (missing files' role, drift-verification behavior) requires source reading, not test execution.

## Documentation Impact
`docs/01_overview-files-04-shared-part2.md` substantially restructured.

## Out of Scope
Do not resolve the arch-03 tool-routing-priority error in this issue (tracked separately) — only flag the potential connection if `runtime_tool_registry.py`'s role turns out to be routing-relevant.

## AI Implementation Instruction
Investigate each of the 3 missing files' actual responsibility via source reading before deciding to add or justify-exclude them. Do not guess at drift-verification failure behavior — read `tool_registry.py`/`tool_routing_validation.py` or register as Needs Confirmation if genuinely unclear.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §2 削除候補 item 5 (context), §3 要約候補 item 5, §6A (config_utils.py等欠落), §6B (ドリフト検証失敗時の挙動)
- Generated at: 2026-08-02
