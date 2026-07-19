# `summarize_issues()` repair guidance points to the removed `/db rag rebuild-fts` command

Discovered while authoring `plans/20260719-091140_plan.md` (for
`requires/20260719_01_require.md`, itself filed from
`issues/20260717-133541_stale_db_rag_consistency_hint.md`). Same defect class
as the `/stats` hint bug — a different code path, not yet covered by that fix.

## Problem

`scripts/db/rag_consistency.py`'s `summarize_issues()` embeds repair guidance
that recommends a removed slash command, in two of its four issue messages:

```python
# line 103 (fts_gap > 0, severity WARNING):
f" Run '/db rag rebuild-fts' to repair."

# line 120 (fts_orphan_count > 0, severity CRITICAL — data loss risk):
f" Run '/db rag rebuild-fts' immediately; orphan FTS entries indicate data loss risk."
```

Per `docs/05_agent_07_07_cli-and-commands-migration-notes.md`, `/db rebuild-fts`
has "後継コマンドなし" (no successor command) — same status as `/db consistency`.
`/db` itself is fully removed and rejected as an unrecognized command.

Unlike the `/stats` hint (a cosmetic nudge), this text is emitted as CRITICAL
repair guidance for data-loss-risk scenarios (orphan FTS entries), surfaced:

- automatically at every agent startup when the check finds issues
  (`agent/startup.py:271-282`, `pipeline.add_warning("rag_consistency", f"[RAG] Consistency issue: {issue}")`)
- and will also be surfaced by any on-demand consistency command built per
  `requires/20260719_01_require.md` / `plans/20260719-091140_plan.md`, since
  those print `RagConsistencyResult.issues` (which is exactly
  `summarize_issues()`'s output) verbatim.

So an operator hitting a CRITICAL data-integrity warning is told to run a
command that does not exist, at the exact moment the guidance matters most.

The underlying capability is not gone: `RagMaintenanceService.rebuild_fts()`
(`scripts/agent/services/rag_maintenance_service.py`) still exists and works
— it is simply not exposed via any slash command today (confirmed: `grep -rn
"rebuild_fts" scripts/agent/commands/` finds no callers).

## Reproduction

- Force `report.fts_gap > 0` or `report.fts_orphan_count > 0` (e.g. via a
  fixture DB matching `tests/test_rag_consistency.py`'s patterns).
- Call `check_rag_consistency()` / `summarize_issues()`.
- Observe an issue string telling the operator to run `/db rag rebuild-fts`.
- Attempting that command in the REPL is rejected as unrecognized.

## Why this wasn't fixed inline

Same reasoning as the original hint issue: fixing the string requires
deciding where `rebuild_fts()` should be exposed on-demand (if at all), which
is the same product decision already in flight for `consistency()` via
`requires/20260719_01_require.md`. Folding this into that same
plan/requirement risks silently expanding its scope without an explicit
decision; filing separately keeps the two decisions (consistency check
exposure vs. rebuild-fts exposure) independently reviewable, even though they
likely land together.

## Recommended action

Decide, most likely alongside `requires/20260719_01_require.md`'s resolution:

- (a) Expose `RagMaintenanceService.rebuild_fts()` via a new on-demand command
  (e.g. `/session rag-rebuild-fts`, following the same naming precedent as
  the `/session rag-consistency` proposal), and point `summarize_issues()`'s
  guidance at it, or
- (b) If no on-demand exposure is wanted, rewrite the guidance text to
  describe the actual repair mechanism available today (there is none via
  slash command — repair would require direct script/service invocation) so
  it does not name a nonexistent command.

Update `tests/test_rag_consistency.py` (or add a new test) to pin whichever
guidance text is chosen, so this cannot silently drift again.
