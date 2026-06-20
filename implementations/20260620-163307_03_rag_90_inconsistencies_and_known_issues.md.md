# Implementation: Close OQ-6 as RESOLVED in docs/03_rag_90_inconsistencies_and_known_issues.md

## Goal
Update OQ-6 in `docs/03_rag_90_inconsistencies_and_known_issues.md` from
`OPEN_QUESTION` to `RESOLVED`, adding a resolution block that references
`tests/test_fts_fallback.py` and describes what was validated.

## Scope
- File: `docs/03_rag_90_inconsistencies_and_known_issues.md`
- OQ-6 entry only (confirmed at line 33)
- Two changes: type field update + resolution block addition

## Assumptions
- OQ-6 is at line 33 with `- **Type:** OPEN_QUESTION`
- There is also an OQ at line 23 — only line 33 (OQ-6) is the target; line 23 is a different issue
- The resolution block should immediately follow the existing OQ-6 body
- "All tests use trigger-backed indexing path" — confirmed: tests use `INSERT INTO chunks`,
  not direct `chunks_fts` inserts
- SQLite version = Python built-in `sqlite3` module (runtime version, not cross-version matrix)

## Implementation

### Target file
`docs/03_rag_90_inconsistencies_and_known_issues.md`

### Procedure
1. Read lines 31-50 to identify the full OQ-6 block structure
2. Replace `- **Type:** OPEN_QUESTION` (the OQ-6 one at line 33) with `- **Type:** RESOLVED`
3. Append resolution block after the existing OQ-6 content

### Method
Two edits: type field replacement and resolution block insertion.

### Details

**Step 1 — change type (line 33):**
```
- **Type:** OPEN_QUESTION
```
→
```
- **Type:** RESOLVED
```

**Step 2 — append resolution block after OQ-6 body:**
```markdown
- **Resolution:** Validated by `tests/test_fts_fallback.py` — 8 integration tests
  covering English chunks, code chunks, NULL/empty COALESCE semantics, and mixed-language
  documents. All tests use trigger-backed indexing path (INSERT INTO chunks → trigger fires
  → chunks_fts populated; no direct FTS5 inserts). Verified on runtime SQLite version
  (Python built-in sqlite3 module). Recommended action in this entry is complete.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| OQ-6 type updated | `grep -A2 "OQ-6" docs/03_rag_90_inconsistencies_and_known_issues.md` | `Type: RESOLVED` |
| Resolution block present | `grep "test_fts_fallback" docs/03_rag_90_inconsistencies_and_known_issues.md` | 1+ matches |
| No OPEN_QUESTION for OQ-6 | `grep -c "OPEN_QUESTION" docs/03_rag_90_inconsistencies_and_known_issues.md` | count excludes OQ-6 |
