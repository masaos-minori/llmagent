# Implementation: Doc discrepancy sections — Current behavior vs Known discrepancy

## Goal

Add clearly separated "Current behavior" and "Known discrepancy / Needs confirmation" sections to five target agent docs so readers can distinguish implemented behavior from intended design without ambiguity.

## Scope

- **In-Scope**:
  - `docs/05_agent_04_state-and-persistence.md` — compressed history persistence, diagnostics.jsonl location
  - `docs/05_agent_09_data-layer.md` — memory table storage ambiguity (session.sqlite vs separate), diagnostics role in messages table vs DiagnosticStore
  - `docs/05_agent_08_configuration.md` — memory_jsonl_dir (canonical key), workflow_mode startup-blocking behavior
  - `docs/05_agent_10_operations-and-observability.md` — diagnostics.jsonl path, session_diagnostics table, deprecation status
  - `docs/05_agent_12_memory.md` — branch field in retrieval (active vs unused), memory_jsonl_path vs memory_jsonl_dir confusion
  - `docs/05_agent_90_inconsistencies_and_known_issues.md` — add new entries for the above discrepancy items

- **Out-of-Scope**:
  - Runtime behavior changes
  - Repository-wide documentation renumbering
  - Changes to `04_mcp_90`, `03_rag_90`, or `90_shared_90` inconsistency files

## Assumptions

- The six specific confusion points in the requirement are all doc-layer issues; no code changes are needed.
- `memory_jsonl_dir` is the canonical config key (verified: `config_dataclasses.py:297`, `config_builders.py:203`). `memory_jsonl_path` does not exist in code.
- `diagnostics.jsonl` is located at `Path(session_db_path).parent / "diagnostics.jsonl"` (verified: `repl.py:286`), which is `/opt/llm/db/diagnostics.jsonl`.
- `branch` field in memory retrieval IS actively used in `FtsRetriever._context_boost()` for relevance rescoring.
- `workflow_mode = "required"` causes `RuntimeError` at `Orchestrator.__init__()` (not at REPL startup).
- `AgentSession.save_diagnostic()` now writes to `DiagnosticStore.save()` → `session_diagnostics` table, NOT to the messages table with `role="diagnostic"`.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether `messages` table still accepts `diagnostic` role rows via `save_diagnostic()` | Resolved: `session.py:52-56` confirms `save_diagnostic()` writes to `DiagnosticStore.save()`, not to messages table. The `diagnostic` role in the messages table column list is a stale reference. |
| UNK-02 | Exact planned timeline for deprecating `diagnostics.jsonl` vs keeping it | No deprecation timeline found; "may be deprecated in future" remains unconfirmed. Mark as Needs confirmation. |
| UNK-03 | Whether `workflow_mode = "required"` fails at Orchestrator construction or at first turn | Resolved: `orchestrator.py:132-136` confirms RuntimeError is raised during `Orchestrator.__init__()`, not at first turn. |

## Implementation Steps

### Target file: `docs/05_agent_04_state-and-persistence.md`

#### Procedure
Add "Current behavior" and discrepancy sections under Message save rules.

#### Method
Direct file edit — add subsections after existing content.

#### Details

**Add under "Message save rules":**

```markdown
### Current behavior

- `DiagnosticStore.save()` writes diagnostic data to the `session_diagnostics` table (SQLite), not to a separate file.
- `diagnostics.jsonl` is written to `Path(session_db_path).parent / "diagnostics.jsonl"` (i.e., `/opt/llm/db/diagnostics.jsonl` for default config).

### Known discrepancy: diagnostics.jsonl deprecation status

> **Needs confirmation:** The doc states "may be deprecated in future" but no deprecation timeline has been decided. Both `diagnostics.jsonl` (file) and `session_diagnostics` table (SQLite) currently coexist as dual persistence paths.

### Known discrepancy: diagnostic role in messages table

> **Known discrepancy:** The `messages` table column list mentions a `diagnostic` role, but this is stale — `AgentSession.save_diagnostic()` now writes exclusively to the `session_diagnostics` table via `DiagnosticStore.save()`. No `role="diagnostic"` rows are written to the messages table.
```

### Target file: `docs/05_agent_09_data-layer.md`

#### Procedure
Fix the `messages` table role column and clarify memory table storage.

#### Method
Direct file edit — replace ambiguous text with explicit clarifications.

#### Details

**Under "Messages Table" role column:**
- Replace `diagnostic` role entry with: `diagnostic (stale — no longer written; see 05_agent_04)` with a note that `save_diagnostic()` now routes to `session_diagnostics`.

**Under "Memory Tables (optional)":**
- Replace "session.sqlite or separate" with: "session.sqlite (same DB as sessions/messages)" and verify by checking `factory.py` line 286 for the SQLiteHelper connection.

### Target file: `docs/05_agent_08_configuration.md`

#### Procedure
Under MemoryConfig and workflow_mode sections, add Current behavior blocks.

#### Method
Direct file edit — insert Current behavior callouts.

#### Details

**Under MemoryConfig section:**
```markdown
> **Current behavior:** `memory_jsonl_dir` is the canonical config key (not `memory_jsonl_path`). The full JSONL path is `{memory_jsonl_dir}/memories.jsonl`.
```

**Under workflow_mode section:**
```markdown
> **Current behavior:** When `workflow_mode = "required"` and `WorkflowLoader` fails during `Orchestrator.__init__()`, a `RuntimeError` is raised immediately — this blocks at Orchestrator construction time, not at the first turn. If `StartupOrchestrator.run()` does not catch this exception, startup aborts before the REPL loop starts.
```

### Target file: `docs/05_agent_10_operations-and-observability.md`

#### Procedure
Under Runtime Diagnostics section, add Current behavior blocks for dual persistence and deprecation status.

#### Method
Direct file edit — insert callout blocks.

#### Details

**Under "Runtime Diagnostics":**
```markdown
### Current behavior

- `diagnostics.jsonl` path: `{session_db_path_parent}/diagnostics.jsonl` (not configurable; for default config this is `/opt/llm/db/diagnostics.jsonl`).
- Dual persistence: `diagnostics.jsonl` (file) AND `session_diagnostics` table (via `DiagnosticStore.save(kind="session_summary")`) both receive diagnostic data. They may diverge in schema or content.

### Needs confirmation: diagnostics.jsonl deprecation

> **Needs confirmation:** Whether `diagnostics.jsonl` will be removed in a future release. No deprecation timeline has been decided.
```

### Target file: `docs/05_agent_12_memory.md`

#### Procedure
Fix `memory_jsonl_path` and document branch field usage.

#### Method
Direct file edit — replace stale key name and add Current behavior blocks.

#### Details

**Under JSONL Format section:**
- Replace "File path controlled by `memory_jsonl_path` config" with "File path is `{memory_jsonl_dir}/memories.jsonl`; `memory_jsonl_dir` is set in `config/memory.toml` (default: `/opt/llm/memory`)"

**Under "Data Model / MemoryEntry":**
```markdown
> **Current behavior:** The `branch` field IS actively used in `FtsRetriever._context_boost()` for relevance rescoring. It is not merely stored metadata — entries matching the current branch receive a scoring bonus.

> **Current behavior:** `branch`, `project`, and `repo` are passed to `HybridRetriever.search()` and affect result ranking (not filtering). Records without matching branch are still returned but ranked lower.
```

### Target file: `docs/05_agent_90_inconsistencies_and_known_issues.md`

#### Procedure
Add new discrepancy entries for the above items.

#### Method
Direct file edit — append new entries to existing list.

#### Details

**Append after existing entries:**

```markdown
### DISC-01: diagnostics.jsonl vs session_diagnostics table dual persistence

- **Type:** Document inconsistency
- **Description:** `diagnostics.jsonl` (file) and `session_diagnostics` table (SQLite via `DiagnosticStore.save()`) both receive diagnostic data. The doc does not clarify which is authoritative for post-mortem analysis.
- **Needs confirmation:** Which store should operators query for diagnostics? Both coexist; no deprecation decision has been made.

### DISC-02: memory_jsonl_path vs memory_jsonl_dir

- **Type:** Document inconsistency
- **Description:** `memory_jsonl_path` appears in docs but does not exist in code. The canonical key is `memory_jsonl_dir`.
- **Resolution:** Replace all occurrences of `memory_jsonl_path` with `memory_jsonl_dir` in docs.

### DISC-03: branch field in memory retrieval

- **Type:** Undocumented behavior
- **Description:** The `branch` field in `MemoryEntry` is actively used as a rescoring signal in `FtsRetriever._context_boost()`, but docs describe it as mere metadata.
- **Resolution:** Update docs to clarify that branch affects result ranking, not just storage.

### DISC-04: workflow_mode=required startup blocking scope

- **Type:** Needs confirmation
- **Description:** The doc does not specify whether `workflow_mode = "required"` failure blocks at Orchestrator construction (during startup) or at the first turn. Code confirms it raises `RuntimeError` during `Orchestrator.__init__()`.
- **Resolution:** Add clarification that failure occurs at Orchestrator construction, before REPL loop starts.

### DISC-05: memory SQLite DB location

- **Type:** Needs confirmation
- **Description:** The doc says "session.sqlite or separate" for memory table storage — ambiguous whether memories use the same DB as sessions or a separate one.
- **Resolution:** Verify in `factory.py` and clarify: memories use the same `session.sqlite` DB.
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| All 6 doc files | Markdown lint (no broken links, valid structure) | `grep -n "## " docs/05_agent_*.md` | Section headers present and consistent |
| `memory_jsonl_dir` canonical key | Grep code to confirm no `memory_jsonl_path` in source | `rg "memory_jsonl_path" scripts/` | Zero matches |
| `branch` active in retrieval | Verify `_context_boost` usage | `rg "branch" scripts/agent/memory/retriever.py` | References to `entry.branch` in scoring |
| `diagnostics.jsonl` path | Verify hardcoded path formula | `grep "diagnostics.jsonl" scripts/agent/repl.py` | `session_db_path parent / diagnostics.jsonl` |
| `workflow_mode=required` scope | Verify RuntimeError in Orchestrator.__init__ | `grep -n "required" scripts/agent/orchestrator.py` | RuntimeError raised on WorkflowLoader failure |
| No code changes | Confirm diff is docs-only | `git diff --name-only` | Only `docs/` paths |

## Risks & Mitigations

- **Risk:** Incorrectly marking a behavior as "Current" when it was already changed in code → **Mitigation:** All current-behavior claims in this plan are backed by line-level code references verified above.
- **Risk:** `memory_jsonl_path` appears somewhere in docs as a cross-reference from another file → **Mitigation:** Run `rg "memory_jsonl_path" docs/` before and after edits to catch all occurrences.
- **Risk:** Over-marking items as `Needs confirmation` where the code already resolves them → **Mitigation:** Phase 1 code reads specifically target the three UNKs; if resolved, use `Current behavior` not `Needs confirmation`.
- **Risk:** Dual-persistence description (diagnostics.jsonl + session_diagnostics) confuses readers further if written ambiguously → **Mitigation:** Use a clear two-row table showing path, format, and query method for each store.
