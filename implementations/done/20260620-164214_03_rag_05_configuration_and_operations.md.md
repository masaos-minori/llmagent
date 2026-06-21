# Implementation: Update use_rrf config entry in docs/03_rag_05_configuration_and_operations.md

## Goal
Expand the `use_rrf` row in the configuration table at line 63 of
`docs/03_rag_05_configuration_and_operations.md` to include quality impact description.

## Scope
- File: `docs/03_rag_05_configuration_and_operations.md`
- Line 63: `use_rrf` configuration row — expand description only
- Do NOT touch `rrf_k` row (line 53)

## Assumptions
- Current line 63: `| \`use_rrf\` | Enable RRF merge (True) or simple dedup fallback (False) |`
  — lacks quality impact information
- Note: the plan originally targets `docs/05_agent_08_configuration.md`, but `use_rrf` is
  actually in `docs/03_rag_05_configuration_and_operations.md` (confirmed by grep). Update
  the correct file.
- Default value column may exist; preserve existing structure

## Implementation

### Target file
`docs/03_rag_05_configuration_and_operations.md`

### Procedure
1. Read line 63 to confirm exact current text
2. Replace description cell with expanded version

### Method
Single string replacement.

### Details

**Current line 63 (approximate):**
```
| `use_rrf` | Enable RRF merge (True) or simple dedup fallback (False) |
```

**Updated line:**
```
| `use_rrf` | `True` | Enable RRF merge (`True`, default) for rank-weighted fusion, or dedup-only (`False`). **Quality tradeoff:** `False` disables rank scoring — all hits get `rrf_score=0.0`; MQE provides no additional ranking benefit. Recommended: keep `True` unless minimizing overhead. |
```

If the table has a different column structure (e.g. 3 columns: key, default, description),
adjust to match — add description text to the description column only.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Quality note present | `grep "rrf_score\|Quality tradeoff\|dedup-only" docs/03_rag_05_configuration_and_operations.md` | 1+ matches |
| use_rrf row preserved | `grep "use_rrf" docs/03_rag_05_configuration_and_operations.md` | 1 match |
