# Implementation Design: Add "Current behavior" and "Known discrepancy / Needs confirmation" sections to agent docs

## Goal

Add clearly separated "Current behavior" and "Known discrepancy / Needs confirmation" sections to the five target agent docs so readers can distinguish implemented behavior from intended design without ambiguity.

## Scope

- **In-Scope**:
  - `docs/05_agent_04_state-and-persistence.md` — compressed history persistence, diagnostics.jsonl location
  - `docs/05_agent_09_data-layer.md` — memory table storage ambiguity, diagnostics role in messages table vs DiagnosticStore
  - `docs/05_agent_08_configuration.md` — memory_jsonl_dir canonical key, workflow_mode startup-blocking behavior
  - `docs/05_agent_10_operations-and-observability.md` — diagnostics.jsonl path, session_diagnostics table, deprecation status
  - `docs/05_agent_12_memory.md` — branch field in retrieval, memory_jsonl_path vs memory_jsonl_dir confusion
  - `docs/05_agent_90_inconsistencies_and_known_issues.md` — add DISC-01 through DISC-05 entries

## Implementation Steps

### Phase 1: Add "Current behavior" sections to each doc

**05_agent_04_state-and-persistence.md**
- Under "Message save rules": add `> **Current behavior:**` block confirming DiagnosticStore writes to session_diagnostics table; diagnostics.jsonl written to Path(session_db_path).parent (/opt/llm/db/diagnostics.jsonl)
- Add `> **Known discrepancy:**` callout clarifying diagnostic role in messages table is historical/secondary path
- Mark "may be deprecated in future" as `> **Needs confirmation:** deprecation timeline not decided.`

**05_agent_09_data-layer.md**
- Under "sessions table": explicitly note diagnostic role rows written by save_diagnostic() if path still exists, or mark as stale if DiagnosticStore is exclusive path
- Under "Memory Tables (optional)": clarify memories table lives in session.sqlite (same DB)
- Add `> **Current behavior:**` block for diagnostics data ownership

**05_agent_08_configuration.md**
- Under MemoryConfig: add `> **Current behavior:**` confirming memory_jsonl_dir is canonical key (not memory_jsonl_path)
- Under workflow_mode: add `> **Current behavior:**` clarifying RuntimeError raised at Orchestrator.__init__() when WorkflowLoader fails

**05_agent_10_operations-and-observability.md**
- Under "Runtime Diagnostics": add `> **Current behavior:**` confirming diagnostics.jsonl path is `{session_db_path_parent}/diagnostics.jsonl` (not configurable)
- Clarify dual persistence: diagnostics.jsonl AND session_diagnostics table; add `> **Known discrepancy:**` note if stores diverge
- Add `> **Needs confirmation:**` on whether diagnostics.jsonl will be removed

**05_agent_12_memory.md**
- Fix memory_jsonl_path → memory_jsonl_dir wherever it appears incorrectly
- Under "Data Model / MemoryEntry": add `> **Current behavior:**` noting branch field IS actively used in FtsRetriever._context_boost()
- Clarify branch, project, repo passed to HybridRetriever.search() affect result ranking

**05_agent_90_inconsistencies_and_known_issues.md**
- Add DISC-01: diagnostics.jsonl vs session_diagnostics table dual persistence
- Add DISC-02: memory_jsonl_path vs memory_jsonl_dir
- Add DISC-03: branch field in memory retrieval
- Add DISC-04: workflow_mode=required startup blocking scope
- Add DISC-05: memory SQLite DB location

## Acceptance Criteria

- [x] All five agent docs have "Current behavior" sections for documented behaviors
- [x] Known discrepancies clearly separated from current behavior
- [x] Needs confirmation items marked where timeline/decision is undecided
- [x] DISC-01 through DISC-05 entries added to inconsistencies file
- [x] No runtime code changes (docs-only)
