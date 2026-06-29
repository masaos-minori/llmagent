# Implementation: RAG Known Issues Document Pruning

## Goal

Prune `docs/03_rag_90_inconsistencies_and_known_issues.md` to remove any resolved or stale entries, and correct the stale description in `docs/03_rag_00_document-guide.md`'s File Index.

## Scope

- **In-Scope**:
  - Audit each entry in `03_rag_90_inconsistencies_and_known_issues.md` against current code and docs
  - Remove entries that are confirmed resolved
  - Retain entries that are genuinely unresolved or require confirmation, with `Needs confirmation` label and a concrete confirmation step
  - Fix the stale File Index description in `03_rag_00_document-guide.md` (currently says "resolved issue summaries")
- **Out-of-Scope**:
  - Fixing runtime behavior
  - Creating a resolved-issues archive section
  - Changes to any scripts or test files

## Assumptions

- DESIGN-2 (FTS5 uses `normalized_content`) and DESIGN-3 (table separation) are `Needs confirmation` items; no evidence in git history of resolution, so they remain unless confirmed resolved by code inspection
- The empty "Active Issues" section in `03_rag_90` is correct — prior cleanup commits already removed resolved entries
- `03_rag_00_document-guide.md` File Index description ("Active design notes and resolved issue summaries") is stale and should be updated to match the actual content

## Implementation

### Target file: `docs/03_rag_90_inconsistencies_and_known_issues.md`

#### Procedure

1. **Audit current entries** — read in full and classify each entry
2. **Prune resolved entries** — remove any confirmed as resolved (delete the full entry block)
3. **Update active entries** — for entries confirmed as still active or unresolved, update to `Needs confirmation` with a concrete confirmation command/step if not already present
4. **Clean up empty sections** — remove trailing blank lines at the end of the file

#### Method

Direct file edit — remove resolved entry blocks and clean up formatting.

#### Details

Currently the file has:
- DESIGN-2 (FTS5 uses `normalized_content`; LLM receives `content`) — Type: Needs confirmation — Keep as-is (confirmed active via code inspection)
- DESIGN-3 (Separation of responsibilities among tables) — Type: Needs confirmation — Keep as-is (confirmed active via code inspection)
- Active Issues section — empty, correct as-is

No entries need to be removed. The file is clean.

### Target file: `docs/03_rag_00_document-guide.md`

#### Procedure

Update the File Index description for `03_rag_90` from "Active design notes and resolved issue summaries" to "Active design notes and open known issues".

#### Method

Direct file edit — replace the stale description text.

#### Details

Line 78 of `03_rag_00_document-guide.md`:
```markdown
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | Active design notes and resolved issue summaries |
```

Change to:
```markdown
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | Active design notes and open known issues |
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_90_inconsistencies_and_known_issues.md` | Manual review: no entry marked as both resolved and active; no empty shell sections | `grep -n "Resolved\|TODO\|FIXME" docs/03_rag_90_inconsistencies_and_known_issues.md` | No unintentional resolved markers remain in active sections |
| `docs/03_rag_00_document-guide.md` | Verify File Index row for `03_rag_90` reflects current content | `grep "03_rag_90" docs/03_rag_00_document-guide.md` | Description matches actual content of `03_rag_90` |
| Cross-check with code | Confirm DESIGN-2/DESIGN-3 status against implementation | `grep -n "normalized_content\|chunks_vec\|chunks_fts" scripts/rag/repository.py` | Evidence found matching or contradicting the design note description |
