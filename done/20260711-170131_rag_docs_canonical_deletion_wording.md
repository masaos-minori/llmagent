# Implementation Procedure: RAG docs — canonical 2-step deletion wording

Source plan: `plans/20260711-164446_plan.md` — Phase 4 (documentation wording, checkbox 1)

## Goal

Replace the stale 3-step deletion-order wording (`chunks_vec` → `chunks` → `documents`)
with the canonical 2-step contract wording (`chunks_vec` → `documents`, with `ON DELETE
CASCADE` removing `chunks`) across all 3 documentation locations, and add a one-sentence
note (in the two `-part1.md` files) that `chunks_vec_ad` is a defensive backstop, not the
primary mechanism.

## Scope

**In-Scope:**
- `docs/03_rag_90_inconsistencies_and_known_issues-part1.md`: line 53 (the "強制再挿入時の削除順序"
  bullet) — replace wording; add the `chunks_vec_ad` backstop note once
- `docs/03_rag_91_design_notes-part1.md`: line 44 (identical bullet) — replace wording; add
  the `chunks_vec_ad` backstop note once
- `docs/03_rag_91_design_notes-part2.md`: 3 occurrences of stale wording —
  - line 34: TEST-DESIGN3-04 table row description
  - line 90: code-comment "Force re-ingestion (deletes chunks_vec first, then chunks, then
    documents)"
  - line 104 (test docstring/comment area near `test_deletion_order_invariant`): "Deletion
    must follow: chunks_vec → chunks → documents."

**Out-of-Scope:**
- Any other section of these 3 files (e.g. DESIGN-2 content, other test-table rows)
- `docs/03_rag_90_inconsistencies_and_known_issues.md` / `docs/03_rag_91_design_notes.md`
  (predecessor files, not the `-part1`/`-part2` successors — out of scope per the plan)
- Any Python source file (covered by separate implementation docs)

## Assumptions

1. `docs/03_rag_90_inconsistencies_and_known_issues-part1.md` line 53 currently reads:
   "強制再挿入時の削除順序: `chunks_vec`が最初 → `chunks` → `documents` (孤立したベクトルレコードを避けるために必須)。"
   — confirmed by direct read.
2. `docs/03_rag_91_design_notes-part1.md` line 44 has identical wording — confirmed by
   direct read.
3. `docs/03_rag_91_design_notes-part2.md` line 34 (TEST-DESIGN3-04 row), line 90 (code
   comment inside `test_force_reingest_no_orphan_vectors` pseudocode block), and line 104
   area (docstring inside `test_deletion_order_invariant` pseudocode block) all contain the
   stale 3-step phrase — confirmed by direct read.
4. The canonical English phrase per the plan's Design section and Acceptance Criteria is:
   `chunks_vec → documents deletion with ON DELETE CASCADE for chunks`, translated
   in-context where surrounding text is Japanese.

## Implementation

### Target file

- `docs/03_rag_90_inconsistencies_and_known_issues-part1.md`
- `docs/03_rag_91_design_notes-part1.md`
- `docs/03_rag_91_design_notes-part2.md`

### Procedure

1. In `docs/03_rag_90_inconsistencies_and_known_issues-part1.md`, replace line 53's bullet
   with the Japanese canonical phrase:
   `強制再挿入時の削除順序: chunks_vec を明示的に削除した後、documents を削除する（ON DELETE CASCADE により chunks が削除される）。write_mode=True の接続でのみ有効（PRAGMA foreign_keys=ON を有効化するため）。`
   Add, once, near this bullet: a one-sentence note that the `chunks_vec_ad` trigger is a
   defensive backstop for direct `chunks` deletes, not the primary contract.
2. In `docs/03_rag_91_design_notes-part1.md`, apply the identical replacement to line 44,
   plus the same one-sentence backstop note.
3. In `docs/03_rag_91_design_notes-part2.md`:
   - Line 34: update the TEST-DESIGN3-04 table row's Description column from "削除順序の不変条件:
     `chunks_vec` → `chunks` → `documents`" to reflect the 2-step contract, e.g. "削除順序の不変条件:
     `chunks_vec` → `documents`（`ON DELETE CASCADE` により `chunks` を削除）".
   - Line 90: update the code comment "Force re-ingestion (deletes chunks_vec first, then
     chunks, then documents)" to "Force re-ingestion (deletes chunks_vec first, then
     documents; CASCADE removes chunks)".
   - Line 104 area: update the docstring "Deletion must follow: chunks_vec → chunks →
     documents." to "Deletion must follow: chunks_vec → documents (CASCADE removes
     chunks)."; consider whether the function name `test_deletion_order_invariant` in this
     doc's pseudocode should be noted as illustrative-only (this file documents test
     pseudocode, not the actual test file — no rename needed here, only wording).

### Method

Direct text replacement in 3 Markdown files. No structural changes to headings, tables
(beyond the one cell in step 3a), or surrounding prose.

### Details

Canonical Japanese sentence to reuse verbatim across both `-part1.md` files:

```
強制再挿入時の削除順序: chunks_vec を明示的に削除した後、documents を削除する（ON DELETE CASCADE により chunks が削除される）。write_mode=True の接続でのみ有効（PRAGMA foreign_keys=ON を有効化するため）。
```

Backstop note (once per `-part1.md` file, placed adjacent to the sentence above):

```
なお、chunks_vec_ad トリガーは chunks への直接削除に対する防御的なバックストップであり、上記の主経路ではない。
```

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to these doc files:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Manual grep (targeted) | `grep -rn "chunks_vec.*chunks.*documents" docs/03_rag_90_inconsistencies_and_known_issues-part1.md docs/03_rag_91_design_notes-part1.md docs/03_rag_91_design_notes-part2.md` | No matches remain |
| Manual grep (broad, per plan's Risks mitigation) | `grep -rln "chunks_vec.*chunks.*documents" docs/` | No matches remain anywhere in docs/, not just the 3 targeted files |
