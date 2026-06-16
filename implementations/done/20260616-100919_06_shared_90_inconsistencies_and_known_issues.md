# Implementation: docs/06_shared_90_inconsistencies_and_known_issues.md

## Goal

Create a structured catalog of all known inconsistencies, spec conflicts, open questions,
and undocumented behaviors identified during the shared/DB documentation restructuring.

## Scope

- Content from: `06_spec_shared.md` §13 (未解決事項・既知問題, 8 items)
- Content from: `07_spec_db.md` §13 (未解決事項・既知問題, 2 items)
- Content from: `07_ref-sqlite.md` constructor section (workflow target gap)
- Content from: `06_shared.md` LLMMessage field discrepancy analysis
- Output: `docs/06_shared_90_inconsistencies_and_known_issues.md`
- Must contain 18+ issues as enumerated in requirements

## Assumptions

- Issue types: BUG / SPEC_CONFLICT / OPEN_QUESTION / DOC_INCONSISTENCY
- "workflow" target in SQLiteHelper is documented only in ref file, not spec — this is a gap
- LLMMessage importance/pinned fields appear in spec §9.1 but not in 06_shared.md table

## Implementation

### Target file

`docs/06_shared_90_inconsistencies_and_known_issues.md`

### Procedure

Write the following issues in order:

**Shared Layer — Open Questions / Undocumented:**
1. OPEN: McpServerConfig.transport type is str (not Literal["http","stdio"]) — needs strengthening
2. OPEN: token_counter._warned_unavailable is module global — needs instance variable refactor
3. DOC: ToolRouteResolver warn_on_fallback: spec says unimplemented; ref says implemented
   (route_resolver.py:62,74-79) — actual code wins; spec needs update
4. OPEN: plugin_registry.load_plugins() returns count but no structured failure report
5. OPEN: git_helper.get_repo_info() swallows all exceptions with bare except Exception → None
6. DOC: LLMClient (shared/llm_client.py) ~600 lines undocumented (RobustSSEParser, retry logic)
7. DOC: ToolExecutor (shared/tool_executor.py) detail undocumented (ToolCallResult, TTL+LRU,
   McpServerHealthRegistry gating, Semaphore concurrency)
8. DOC: ArtifactEvent event bus unimplemented — events.py is data-only, no pub/sub

**Shared Layer — Spec Conflicts:**
9. SPEC_CONFLICT: LLMMessage fields discrepancy — 06_shared.md shows 5 fields (role/content/
   tool_calls/tool_call_id/name); 06_spec_shared.md §9.1 shows 7 fields (adds importance/pinned)
   — spec §9.1 is canonical; 06_shared.md needs update
10. SPEC_CONFLICT: ServerLifecycleManager deleted — spec §8.3 references it; actual routing is
    factory.py _ServerLifecycleRouter — spec needs update

**DB Layer — Known Issues:**
11. BUG: common.toml not in load_all() — build_db_config() cannot get rag_db_path from load_all();
    db/helper.py and rag/pipeline.py each call ConfigLoader().load("common.toml") as workaround
12. DOC: Trigger definitions undocumented — chunks_ai, chunks_ad, chunks_au, chunks_vec_ad exist
    in create_schema.py:65-85 but not in any spec section
13. DOC: workflow target in SQLiteHelper only in 07_ref-sqlite.md constructor table;
    07_spec_db.md §2 scope and §6.1 connection management do not mention workflow target
14. OPEN: prune_old_memories has no try/except — exceptions propagate uncaught (maintenance.py:122-130)
15. OPEN: recover_corruption target parameter: spec §10.3 says "rag" default, ref confirms
    both "rag" and "session" supported — verify implementation covers session target
16. OPEN: migrate_schema() behavior: spec says ALTER TABLE ADD COLUMN suppresses duplicate
    column error; verify idempotency on re-run
17. DOC: MemoryStore is in agent/memory/store.py but documented in 07_ref-sqlite.md —
    layer boundary: agent/ depends on db/ but doc is in db ref
18. OPEN: memories_vec uses float BLOB format (not float[N] vec0 syntax) in session.sqlite —
    contrast with chunks_vec which uses vec0 virtual table with embedding float[DIMS]

### Method

Issue format:
```
### [TYPE-N] Short title
- **Type:** BUG | SPEC_CONFLICT | OPEN_QUESTION | DOC_INCONSISTENCY
- **Impact scope:** (affected files)
- **Description:** (problem statement)
- **Current safe interpretation:** (what to assume)
- **Recommended action:** (fix or investigation)
- **Source reference:** (where found)
```

## Validation plan

- File exists at `docs/06_shared_90_inconsistencies_and_known_issues.md`
- 18 or more distinct issues
- LLMMessage field discrepancy documented (issue 9)
- workflow target gap documented (issue 13)
- common.toml non-integration documented (issue 11)
- Each issue has all 6 fields in standard format
