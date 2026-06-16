# Implementation: docs/06_shared_00_document-guide.md

## Goal

Create the navigation entry point for the restructured shared/DB documentation set, with
reading order guidance, AI query routing table, and canonical source rules.

## Scope

- New content synthesized from all 4 source files (no single source)
- Output: `docs/06_shared_00_document-guide.md`
- Created last (after all other 7 output files exist)

## Assumptions

- First file a reader (human or AI) opens for the shared/DB layer
- Must link to all 7 other output files with one-line descriptions
- AI routing table is the highest-value section

## Implementation

### Target file

`docs/06_shared_00_document-guide.md`

### Procedure

1. Section 1: Purpose — one sentence on shared layer role
2. Section 2: Reading Order (Human)
   - 01 Overview → 02 Types & Protocols → 03 Runtime & Execution → 04 DB Architecture → 05 DB API → 90 Issues
   - 99 Source Mapping is for audit purposes only
3. Section 3: AI Query Routing Table
   | Question type | File to read |
   |---|---|
   | What does shared/ provide? | 06_shared_01 |
   | LLMMessage / RagConfig / ActionResult fields? | 06_shared_02 |
   | ConfigLoader / Logger / ToolExecutor flow? | 06_shared_03 |
   | DB file targets, schemas, WAL config? | 06_shared_04 |
   | SQLiteHelper API / store.py protocols / maintenance? | 06_shared_05 |
   | Known bugs or spec conflicts? | 06_shared_90 |
4. Section 4: Canonical Source Rules
   - `06_spec_shared.md` canonical for shared/ constraints and module specs
   - `06_shared.md` canonical for LLMMessage / RagHit / RagConfig type definitions
   - `07_spec_db.md` canonical for DB schemas and maintenance specs
   - `07_ref-sqlite.md` canonical for SQLiteHelper API and store.py protocols
5. Section 5: File Index — one-line description per file with link

### Method

- Keep under 60 lines; no API details
- AI Query Routing Table must be visible without scrolling

### Details

- "workflow" target in SQLiteHelper only documented in 07_ref-sqlite.md (not 07_spec_db.md) — note this gap
- LLMMessage has `importance`/`pinned` fields in spec but not in 06_shared.md — note in routing table

## Validation plan

- File exists at `docs/06_shared_00_document-guide.md`
- Links to all 7 other output files
- AI query routing table present
- Canonical source rules present
- File under 60 lines
