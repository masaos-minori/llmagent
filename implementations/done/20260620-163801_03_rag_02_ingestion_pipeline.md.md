# Implementation: Add artifact format note to docs/03_rag_02_ingestion_pipeline.md

## Goal
Add a prominent "Artifact format note" blockquote immediately after the artifacts table
(lines 64-65) in `docs/03_rag_02_ingestion_pipeline.md`, clarifying that `.txt` files
contain JSON payloads and must be parsed with `json.loads()` / `orjson.loads()`.
Also add a "Future compatibility note" about `.json` rename.

## Scope
- File: `docs/03_rag_02_ingestion_pipeline.md`
- Insert two blockquote sections after the artifacts table
- No behavior change; documentation only

## Assumptions
- Lines 64-65 contain the artifacts table; the note should follow immediately after
- The artifacts table ends at line 65 (or 66 if there is a trailing blank line)
- Blockquote style (`>`) is consistent with existing doc conventions
- "Historical/compatibility reasons" for `.txt` extension — unconfirmed; label as such

## Implementation

### Target file
`docs/03_rag_02_ingestion_pipeline.md`

### Procedure
1. Read lines 60-70 to confirm exact table end position
2. Insert the two blockquote blocks after the table

### Method
Single edit — insert new content after the table.

### Details

**Content to insert (after line 65 or the last table row):**

```markdown

> **Artifact format note:** All `.txt` files listed above contain JSON payloads,
> not plain text. The `.txt` extension is retained for historical/compatibility reasons.
> Always parse with `orjson.loads()` or `json.loads()`. Plain-text tools (grep, wc,
> editors that assume UTF-8 text) will work on the raw bytes but will not interpret
> the structure. To inspect a file:
> ```
> python -c "import orjson; print(orjson.loads(open('FILE', 'rb').read()))"
> ```
> Do NOT pass `.txt` artifacts to tools that assume plain-text format.

> **Future compatibility note (Needs confirmation):** Renaming artifacts to `.json` is
> feasible but requires updating all `glob("*.txt")` calls in `ingester.py` and
> `chunk_splitter.py`, the sentinel filename check (`{stem}-0000.txt`), and a migration
> script for existing files in `rag-src/registered/`. Not implemented; requires
> explicit confirmation before proceeding.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Format note present | `grep "Artifact format note" docs/03_rag_02_ingestion_pipeline.md` | 1 match |
| orjson.loads note present | `grep "orjson.loads" docs/03_rag_02_ingestion_pipeline.md` | 1 match |
| Future note present | `grep "Needs confirmation" docs/03_rag_02_ingestion_pipeline.md` | 1 match |
