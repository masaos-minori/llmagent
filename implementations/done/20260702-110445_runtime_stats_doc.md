## Goal

Add 5 missing `RuntimeStats` fields to the `RuntimeStats` table in `docs/05_agent_04_state-and-persistence.md` to bring the documentation in sync with `scripts/agent/context.py:RuntimeStats`.

## Scope

**In**: `docs/05_agent_04_state-and-persistence.md` — RuntimeStats table only (approximately lines 64–76). Add 5 rows.

**Out**:
- No Python source files are modified.
- No other sections of the same doc file are touched.
- No other doc files.

## Assumptions

1. The current RuntimeStats table uses the three-column format `| Field | Type | Description |`. The 5 new rows follow the same format.
2. The "Initial value" information is included in the Description column (no dedicated column), consistent with existing rows.
3. `stat_memory_circuit_open` and `stat_memory_fts_fallback_count` are **declared** in `RuntimeStats` (`context.py:104–105`) but their values shown by `/stats` are read live from `MemoryServices` at display time via `cmd_config_stats.py` helpers — they are NOT written to `ctx.stats` during operation. The doc must note this behavior explicitly.
4. `stat_memory_fts_fallback_count` mirrors `MemoryServices.retriever.fts_fallback_count` (confirmed via `cmd_config_stats.py:40–45`).

## Implementation

### Target file
`docs/05_agent_04_state-and-persistence.md`

### Procedure
1. Read lines 61–78 to confirm current table structure and last row position.
2. Insert 5 new rows after the last existing data row (`stat_output_tokens`), before the closing separator.
3. Verify row count reaches 12.

### Method
Direct file edit — insert rows at the identified location.

### Details

**Current state** (lines 64–76, 7 rows):
Table ends at `| stat_output_tokens | int | ... |`.

**Insert after the last existing row**, add:

```markdown
| `stat_serialization_events` | `list[dict]` | Per-round serialization events recorded by the DAG tool scheduler (`_execute_with_dag`) and standard runner (`_execute_standard`). Accumulated across all turns. Initial: `[]`. Surfaced by the `/mcp` command. |
| `stat_serialization_total_overhead_ms` | `float` | Total serialization overhead in milliseconds, accumulated across all turns. Initial: `0.0`. |
| `stat_memory_consistency_failures` | `int` | Count of `/memory check-consistency` failures this session. Incremented by `cmd_memory.py`. Initial: `0`. |
| `stat_memory_circuit_open` | `bool` | `True` when the memory embedding circuit breaker is open. Read at display time from `MemoryServices` via `cmd_config_stats._get_mem_circuit_open()` — **not written to `ctx.stats`** during normal operation. Initial: `False`. |
| `stat_memory_fts_fallback_count` | `int` | Count of FTS fallbacks this session (triggered when embedding is unavailable). Mirrors `MemoryServices.retriever.fts_fallback_count` — read at display time via `cmd_config_stats._get_mem_fts_fallback()`, not independently tracked in `ctx.stats`. Initial: `0`. |
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All 5 field names present in docs | `grep -c "stat_serialization_events\|stat_serialization_total_overhead_ms\|stat_memory_consistency_failures\|stat_memory_circuit_open\|stat_memory_fts_fallback_count" docs/05_agent_04_state-and-persistence.md` | 5 |
| RuntimeStats table row count | `grep -c "^\| \`stat_" docs/05_agent_04_state-and-persistence.md` | 12 |
| No other sections modified | `git diff docs/05_agent_04_state-and-persistence.md` | Only RuntimeStats table rows added |
| Field types match context.py | Manual cross-check against `scripts/agent/context.py:88–105` | `list[dict]`, `float`, `int`, `bool`, `int` |
| "not written to ctx.stats" note present | `grep -n "not written to" docs/05_agent_04_state-and-persistence.md` | ≥ 1 match |
