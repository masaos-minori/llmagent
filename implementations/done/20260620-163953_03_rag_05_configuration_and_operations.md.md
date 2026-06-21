# Implementation: Add "Consistency check in normal operations" section to docs

## Goal
Document that RAG consistency is checked on agent startup and available via `/db consistency`,
including output format details and the strict-zero threshold policy.

## Scope
- File: `docs/03_rag_05_configuration_and_operations.md` (operations doc is the best fit;
  alternatively `docs/03_rag_02_ingestion_pipeline.md` under a new subsection)
- Add new subsection: "Consistency checking in normal operations"
- No code changes

## Assumptions
- `docs/03_rag_05_configuration_and_operations.md` is the correct target (operations context)
- If that file does not have a maintenance/diagnostics section, add a new "Operational Diagnostics"
  section; if `03_rag_02_ingestion_pipeline.md` already has maintenance content, add there instead
- Strict-zero threshold: `fts_gap==0 and fts_orphan_count==0 and orphan_vec_count==0 and vec==chunks`
- Threshold tuning is marked "Needs confirmation" per plan

## Implementation

### Target file
`docs/03_rag_05_configuration_and_operations.md`

### Procedure
1. Read the existing file structure to find the best insertion point (maintenance/diagnostics section)
2. Insert the new subsection

### Method
Single edit — insert new subsection.

### Details

**New subsection:**

```markdown
## RAG index consistency checks

The RAG index requires three tables to remain synchronized:
- `chunks` — canonical chunk records
- `chunks_fts` — FTS5 full-text index (populated by SQLite triggers)
- `chunks_vec` — vector embedding index

### Startup warning

On every agent startup, `_check_services()` runs `check_rag_consistency()` (3 COUNT queries,
read-only, fast). If any inconsistency is detected, a warning is emitted to the console:

```
[RAG] Consistency issue: fts_gap=3 (3 chunks missing from FTS index)
```

No warning is shown on a healthy index (only `logger.info("RAG consistency: OK")` is written).

### `/db consistency` command

The `/db consistency` command shows numeric counts followed by an OK or error summary:

```
  chunks: 1042  fts: 1042  vec: 1042  fts_gap: 0  orphan_vec: 0  fts_orphan: 0
RAG consistency: OK (chunks/FTS/vec in sync)
```

On inconsistency:

```
  chunks: 1042  fts: 1039  vec: 1042  fts_gap: 3  orphan_vec: 0  fts_orphan: 0
Consistency issue: fts_gap=3 (3 chunks missing from FTS index)
```

### Threshold policy

The check uses a **strict-zero** threshold: any non-zero `fts_gap`, `fts_orphan_count`,
or `orphan_vec_count` is reported as inconsistent. Configurable thresholds (e.g. allowing
`fts_gap <= 5`) are not implemented. **Needs confirmation** if partial-OK policy is required.

### Fixing inconsistencies

Run `/db fts-rebuild` to resynchronize `chunks_fts` from the `chunks` table.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Section present | `grep "Consistency checking\|RAG index consistency" docs/03_rag_05_configuration_and_operations.md` | 1+ matches |
| Threshold note | `grep "strict-zero\|Needs confirmation" docs/03_rag_05_configuration_and_operations.md` | 1 match |
