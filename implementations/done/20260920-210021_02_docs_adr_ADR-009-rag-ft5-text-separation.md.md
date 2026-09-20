## Goal
Add a paragraph documenting INV-09's actual behavior (Markdown heading chunks get
`normalized_content = NULL`, falling back to `content`), and correct ADR-009's
Verification section's stale flat-`tests/` file-path citations to their current
`tests/rag/`/`tests/agent/services/` locations.

## Scope
In scope: (1) add an INV-09 behavior paragraph; (2) correct all stale file-path
citations in the Verification section's "Implementation" bullets (REQ-003, REQ-004 of
`plans/20260920-203952_plan.md`).
Out of scope: `tests/rag/test_fts_sync.py` and
`docs/00_governance_03_issue-and-uncertainty-management.md` edits — this Plan's Rows 1
and 3, separate implementation procedure documents.

## Assumptions
- Row 1 (`tests/rag/test_fts_sync.py`) determines the final name of the INV-07 test —
  this row's Verification-section correction for INV-07's "Implementation" bullet must
  cite whatever name Row 1 actually lands with (the source Plan's Requirements keep
  the same test function name,
  `test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`, only rewriting
  its body — confirm this is still true when this row is implemented, in case Row 1's
  implementation diverged from its own procedure document).

## Design decisions
- Adversarial re-verification during this row's own investigation (see Details) found
  a **fourth** stale path beyond the three the source Plan's REQ-004 named:
  `tests/test_rag_pipeline_stage.py::TestAugmentStage::test_augment_stage_content_only_invariant`
  (INV-10's Verification row) is also a flat-`tests/` path; the actual file is
  `tests/rag/test_rag_pipeline_stage.py` (confirmed via `fd`). This is corrected in the
  same pass as the other three, since it is the same class of stale-path defect in the
  same document section this row already targets — not an additional target file
  (still `docs/adr/ADR-009-rag-ft5-text-separation.md`, the one row this document
  covers) and not a scope change to the Plan's Requirements, only a broader instance of
  REQ-004's own "correct the stale paths" intent applied to a citation the Plan's own
  investigation had not enumerated. Recorded here rather than silently expanded
  without note, per `rules/ai-execution.md` Adversarial Verification (Base).
- Place the INV-09 paragraph directly after the Invariants list (after line 226, before
  "## Exceptions") rather than inside the Verification section, since INV-09's
  requirement is about the *invariant's own definition* needing a documented behavior,
  not a test citation — the Verification section's own row for INV-09 (if one is
  added) would cite a test, not restate the behavior itself.

## Alternatives considered
- Leaving the newly-discovered fourth stale path (`test_rag_pipeline_stage.py`)
  uncorrected and reporting it as a separate Plan Gap: rejected — per this workflow's
  own guidance, a same-file scope addition that keeps a document's own citations
  internally consistent (all four stale paths are the identical defect pattern, in the
  identical document section) does not require a Plan amendment, unlike a genuinely
  new target file.

## Implementation
### Target file
`docs/adr/ADR-009-rag-ft5-text-separation.md`

### Procedure
1. Add a new paragraph after the Invariants list (after INV-10 at line 226) describing
   INV-09's actual behavior: Markdown heading chunks (and any other
   non-Japanese/non-code text routed through `_is_markdown_source()`) receive
   `normalized_content = NULL` at ingestion time
   (`scripts/rag/ingestion/chunk_splitter.py::_build_text_triples()`), and FTS5 falls
   back to `content` via the same `COALESCE(normalized_content, content)` rule INV-04
   documents for English/code chunks.
2. In the Verification section's "Implementation" bullets, correct:
   - `tests/test_fts_fallback.py::TestEnglishFtsFallback` → `tests/rag/test_fts_fallback.py::TestEnglishFtsFallback`
   - `tests/test_rag_pipeline.py::TestFormatChunksDesign2::test_content_appears_in_output` → `tests/rag/test_rag_pipeline.py::TestFormatChunksDesign2::test_content_appears_in_output`
   - `tests/test_fts_fallback.py::TestCodeFtsFallback::test_code_search_returns_original_content` → `tests/rag/test_fts_fallback.py::TestCodeFtsFallback::test_code_search_returns_original_content`
   - `tests/test_rag_index_integrity.py::test_fts_rebuild_uses_cascade` (TEST-DESIGN3-01) → `tests/rag/test_fts_sync.py::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule` (confirm this Plan's Row 1 landed under this exact name before finalizing; see Assumptions)
   - `tests/test_rag_pipeline.py::TestFormatChunksDesign2::test_normalized_content_does_not_appear` → `tests/rag/test_rag_pipeline.py::TestFormatChunksDesign2::test_normalized_content_does_not_appear`
   - `tests/test_rag_pipeline_stage.py::TestAugmentStage::test_augment_stage_content_only_invariant` → `tests/rag/test_rag_pipeline_stage.py::TestAugmentStage::test_augment_stage_content_only_invariant` (the fourth stale path found during this row's own investigation — see Design decisions)

### Method
Direct file edit (`Edit` tool) — one new paragraph, six corrected file-path citations
(all within the existing Verification section's bullet list); no restructuring.

### Details
Current Invariants section end (confirmed via Read, lines 222-230):
```
- INV-09: Markdown見出しチャンクなど、日本語正規化を行わないケースの挙動を明記する。
- INV-10: AugmentStageは`content`のみを出力し、`normalized_content`をLLM Contextへ出力しない。

## Exceptions

なし
```

Target shape after adding the INV-09 paragraph (illustrative — write in the document's
existing Japanese prose style, consistent with the surrounding sections, per
`skills/DESIGN.md` Output language's rule that ADR content in this repository already
established as Japanese stays Japanese unless the whole document is being translated,
which this row does not do):
```
- INV-09: Markdown見出しチャンクなど、日本語正規化を行わないケースの挙動を明記する。
- INV-10: AugmentStageは`content`のみを出力し、`normalized_content`をLLM Contextへ出力しない。

INV-09の挙動: Markdown見出しチャンク（および日本語正規化対象外のその他のテキスト、
`_is_markdown_source()`分岐で判定）は、取り込み時に`normalized_content = NULL`となる
（`scripts/rag/ingestion/chunk_splitter.py::_build_text_triples()`）。FTS5はINV-04が
定義する英語・コードチャンクと同じ`COALESCE(normalized_content, content)`規則により
`content`へFallbackする。

## Exceptions

なし
```

Current Verification section (confirmed via Read, lines 274-311) has the 6 stale-path
bullets listed in Procedure step 2 above — apply each substitution exactly as listed,
confirming the corrected path actually exists via `fd`/Read before finalizing (already
confirmed during this row's own investigation: all 6 target paths verified to exist,
except the INV-07 row, which depends on Row 1's actual landed test name per
Assumptions).

## Compatibility considerations
N/A: documentation-only change; no code/API surface affected. The corrected file
paths make the ADR's own citations resolvable again (`fd`-verifiable), which is itself
a compatibility improvement for any future reader/tool that tries to open these
citations.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Trivially revertable: reverting the new paragraph and the 6 path corrections restores
the prior (stale but previously-committed) text exactly.

## Validation plan
- `uv run python tools/check_docs_quality.py` — structural check (REQ-003, REQ-004,
  AC-3, AC-4 of `plans/20260920-203952_plan.md`).
- `uv run python tools/check_docs_structure.py docs/adr/ADR-009-rag-ft5-text-separation.md`.
- Manually re-verify each of the 6 corrected paths resolves via `fd`/Read after the
  edit (repeat the same confirmation this row's own investigation already performed,
  against the post-edit file).

## Completion criteria
- The Invariants section (or a location immediately after it) contains an explicit
  paragraph describing INV-09's Markdown-heading-chunk behavior, cross-referencing
  INV-04's `COALESCE` rule.
- All 6 stale file-path citations in the Verification section are corrected to paths
  confirmed to exist.
- `uv run python tools/check_docs_quality.py` reports no new finding for this file.

## Out of scope
- `tests/rag/test_fts_sync.py` — this Plan's Row 1.
- `docs/00_governance_03_issue-and-uncertainty-management.md` — this Plan's Row 3.
- Any other section of ADR-009 not named above (Data Ownership, Failure Policy, etc.).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the INV-09 behavior paragraph | Completed | 20260920-212459 | 20260920-212459 |  |
| 2 | Correct all 6 stale file-path citations (including the 4th one found during this row's investigation) | Completed | 20260920-212459 | 20260920-212459 | Confirmed Row 1 landed test name matches; corrected all 6 stale paths including the 4th one found during Plan investigation |
| 3 | Run `check_docs_quality.py` / `check_docs_structure.py` and manually re-verify all corrected paths | Completed | 20260920-212459 | 20260920-212459 | check_docs_quality.py/check_docs_structure.py warnings confirmed pre-existing and identical before/after via git stash comparison (all 12 findings, unrelated sections/links) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004 (INV-09 behavior documentation; stale Verification-section path correction)
- **Source issue**: issues/20260920-191952_ci007_validate-fts5-rebuild-rules-from-adr-009-against-implementation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203952_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-210021
- **Related target files**: docs/adr/ADR-009-rag-ft5-text-separation.md