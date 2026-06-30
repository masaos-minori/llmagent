# Implementation: Fix JSONL "source of truth" descriptions in memory documentation

## Goal

Correct all remaining "JSONL source of truth" descriptions to "JSONL archive" in documentation, and verify that cmd_memory.py and tests already satisfy the remaining acceptance criteria.

## Scope

- **In-Scope**:
  - `docs/05_agent_12_memory.md`: replace "JSONL source of truth" with "JSONL archive" (3 occurrences: L55, L124, L413)
  - `docs/05_agent_12_memory.md`: fix method name `rebuild_from_jsonl` → `import_from_jsonl` (L336) and clarify it does not replay deletes/pin state
  - `docs/05_agent_12_memory.md`: clarify that SQLite is the authoritative state, JSONL is the append-only archive
- **Out-of-Scope**:
  - DB schema changes
  - New commands beyond the existing `import-jsonl` alias (already implemented)
  - Other documentation files (no "source of truth" mentions related to JSONL memory)

## Assumptions

- `import-jsonl` alias is already implemented in `cmd_memory.py` (L98) — confirmed
- `_MEMORY_HELP` already uses "archive" (L56) — confirmed
- `_memory_rebuild` messages already use "JSONL archive records" and "NOT replayed" — confirmed
- All 8 tests in `test_cmd_memory.py` already pass — confirmed
- The only remaining work is updating `docs/05_agent_12_memory.md` to remove "source of truth" references to JSONL

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|---|---|---|---|---|
| UNK-01 | Docs at L336 reference `rebuild_from_jsonl` but actual store.py method is `import_from_jsonl` | None — confirmed by grep | Update doc to use correct method name | No |

## Verification Results

### 1. "JSONL source of truth" occurrences confirmed
- **File**: `docs/05_agent_12_memory.md`
- Line 55: `| jsonl_store.py | Append-only JSONL source of truth |`
- Line 124: `| jsonl_store.py  |  Append-only source of truth`
- Line 413: `### 11. jsonl_store.py — JSONL source of truth`

### 2. Method name mismatch confirmed
- **File**: `docs/05_agent_12_memory.md:336`
- Doc references: `rebuild_from_jsonl(jsonl_store, *, dry_run=False)`
- Actual method: `import_from_jsonl` at `scripts/agent/memory/store.py:354`

### 3. cmd_memory.py already uses "archive" terminology
- **File**: `scripts/agent/commands/cmd_memory.py`
- `_MEMORY_HELP` (L56): uses "archive" — no changes needed
- `_memory_rebuild` messages: use "JSONL archive records" and "NOT replayed" — no changes needed

### 4. Other docs checked for "source of truth" references
- `docs/04_mcp_01_system_overview.md:L102`: "Single source of truth for tool definitions" — not JSONL-related, out of scope
- `docs/06_eventbus_00_document-guide.md:L30`: "The canonical source of truth for behavior is the source code" — not JSONL-related, out of scope
- `docs/04_mcp_03_routing_lifecycle_and_execution.md:L96`: "Single source of truth for MCP tool definitions" — not JSONL-related, out of scope

## Implementation

### Target file: `docs/05_agent_12_memory.md`

#### Procedure

Apply all documentation changes from Phase 1 of the plan.

#### Method

Direct file edit — targeted replacements for each occurrence.

#### Details

**Change 1: Fix line 55 — table description**
```markdown
# Before:
| `jsonl_store.py` | Append-only JSONL source of truth |

# After:
| `jsonl_store.py` | Append-only JSONL archive |
```

**Change 2: Fix line 124 — architecture diagram label**
```markdown
# Before:
| jsonl_store.py  |  Append-only source of truth

# After:
| jsonl_store.py  |  Append-only archive
```

**Change 3: Fix line 336 — method name and description**
```markdown
# Before:
| `rebuild_from_jsonl(jsonl_store, *, dry_run=False)` | `tuple[int, int]` | Rebuild memories/FTS/vec from JSONL; returns (jsonl_count, inserted_count) |

# After:
| `import_from_jsonl(jsonl_store, *, dry_run=False)` | `tuple[int, int]` | Import entries from JSONL archive into SQLite; returns (jsonl_count, inserted_count). Does NOT replay deletes or pin/unpin state changes. |
```

**Change 4: Fix line 413 — section heading**
```markdown
# Before:
### 11. `jsonl_store.py` — JSONL source of truth

# After:
### 11. `jsonl_store.py` — Append-only JSONL archive
```

**Change 5: Add SQLite authoritative state note (after line 423, after jsonl_store section)**
```markdown
**Note:** SQLite (`memories` table) is the authoritative state for memory data. The JSONL archive is an append-only backup used for import/export and disaster recovery only. Deletions and pin/unpin state changes are not replayed from the JSONL archive — they must be applied directly to SQLite.
```

### Target file: `docs/05_agent_12_memory.md`

#### Procedure (optional)

Verify no remaining "JSONL source of truth" string after changes.

#### Method

Run grep to confirm zero matches.

#### Details

```bash
grep -n "JSONL source of truth" docs/05_agent_12_memory.md
# Expected: no output
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/test_cmd_memory.py` | Re-run existing 8 tests | `uv run --no-sync pytest tests/test_cmd_memory.py -q` | 8 passed, 0 failed |
| `docs/05_agent_12_memory.md` | String search for forbidden phrase | `grep -n "JSONL source of truth" docs/05_agent_12_memory.md` | No output (0 matches) |
| `docs/05_agent_12_memory.md` | String search for correct method name | `grep -n "import_from_jsonl" docs/05_agent_12_memory.md` | At least 1 match on API table row |

## Risks & Mitigations

- **Risk**: Other documentation files may reference the old method name `rebuild_from_jsonl` → **Mitigation**: run `grep -rn "rebuild_from_jsonl" docs/` before closing; confirmed 0 additional hits
- **Risk**: Changing "source of truth" label may cause confusion if readers expect JSONL to be authoritative → **Mitigation**: add explicit note that SQLite `memories` table is the authoritative state; JSONL is an append-only archive for backup/import purposes only
