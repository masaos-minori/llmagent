# Implementation: Add "Validated by" note at normalized_content/FTS5 section in docs/03_rag_04_data_model_and_interfaces.md

## Goal
Append `Validated by \`tests/test_fts_fallback.py\`.` to the English/code
`normalized_content=NULL` description near line 107 in
`docs/03_rag_04_data_model_and_interfaces.md`.

## Scope
- File: `docs/03_rag_04_data_model_and_interfaces.md`
- One sentence appended to the relevant paragraph or table cell
- No behavior change

## Assumptions
- "Near line 107" — the exact line needs confirmation by reading the file
- The note should be appended inline (end of sentence) or as a follow-up sentence on the same
  bullet or table row describing `normalized_content=NULL` fallback behavior
- Consistent with project convention of citing test files in documentation

## Implementation

### Target file
`docs/03_rag_04_data_model_and_interfaces.md`

### Procedure
1. Read lines 100-115 to locate the exact `normalized_content=NULL` description text
2. Append "Validated by `tests/test_fts_fallback.py`." to the end of the relevant sentence
   or bullet point

### Method
Single edit — append to existing line or bullet.

### Details

**Expected target text (approximate):**
```
For English and code chunks, `normalized_content` is left as `NULL`; the FTS5 COALESCE
trigger falls back to `content` for indexing.
```

**Updated text:**
```
For English and code chunks, `normalized_content` is left as `NULL`; the FTS5 COALESCE
trigger falls back to `content` for indexing. Validated by `tests/test_fts_fallback.py`.
```

If the text is in a table cell, append the note at the end of the cell content, before `|`.

The implementer must read the actual line content before editing to ensure exact match.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Note present | `grep "test_fts_fallback" docs/03_rag_04_data_model_and_interfaces.md` | 1 match |
| File readable | `head -120 docs/03_rag_04_data_model_and_interfaces.md` | no parse errors |
