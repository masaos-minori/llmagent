## Goal

Append a new subsection to `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` immediately after the "3.1.4 Markdown Heading Chunking Behavior" section (after line 119, Evidence note), before "### 3.2 Splitting Strategies" (line 121), stating: (1) the fallback triggers per individual heading-delimited section (checked against `md_snippet_max_chars`); (2) the two strategies combine sequentially — heading-boundary splitting runs first across the entire text, sentence-based splitting (`_chunk_english()`) is a second pass applied only to sections that exceeded the size limit; (3) chunk metadata: `chunking_strategy` remains `"heading"` regardless of whether a given output chunk came from the size-fitting path or the sentence-split fallback path, `normalized_content` stays `null` for both, sections below `min_chunk` from either path are silently discarded as noise; (4) the known edge case already stated in section 3.1.4 (Japanese content loses Sudachi normalization when routed through heading chunking). Per REQ-001.

## Scope

- Append exactly one new subsection into `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
  after line 119 (end of Evidence note) and before line 121 ("### 3.2 Splitting Strategies")
- Cover four items requested in the Issue's Recommended Action:
  (1) Fallback trigger condition (per-section, not whole-document);
  (2) Sequential combination of two strategies (not parallel);
  (3) Chunk metadata during fallback (chunking_strategy, normalized_content, min_chunk discard);
  (4) Known edge case (Japanese content loses Sudachi normalization)
- Each item backed by `_chunk_markdown_by_heading()`'s implementation or the document's own existing evidence notes — no invented guidance beyond what the existing code pattern supports

## Assumptions

- `_chunk_markdown_by_heading()`'s current implementation (lines 158-174) is the authoritative source for the fallback mechanism — this Plan restates its actual behavior rather than inferring additional rules not present in the code
- The sub-`min_chunk` discard behavior for heading-chunked sections follows the same noise-discard convention already established for other chunking paths in this codebase (confirmed at `chunk_splitter.py` line 168-169's `if len(section) >= self._min_chunk` guard) — this Plan cites the code directly rather than assuming parity with `docs/03_rag_05_1-configuration-reference.md`'s `min_chunk` description without verification

## Design decisions

- Append the new subsection immediately after the Evidence note (line 119) and before "### 3.2 Splitting Strategies" (line 121)
- Quote or closely paraphrase each constraint's enforcement mechanism rather than summarizing loosely, minimizing near-term drift risk if source files are edited later
- Cite the specific file:line locations in Reference Files above
- Do NOT invent additional rationale beyond what the existing code/ADR evidence supports

## Alternatives considered

- Placing the subsection elsewhere in the document: rejected — appending after the Evidence note keeps it as a natural continuation of the Markdown heading chunking discussion rather than a disconnected addition
- Deriving new distinguishing rules for exception selection instead of citing docstrings: rejected — the Issue's Recommended Action asks for connecting existing accepted evidence, not inventing new claims

## Implementation

### Target file

`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure

1. **Locate the insertion point** — between line 119 (end of Evidence note) and line 121 ("### 3.2 Splitting Strategies")

2. **Insert the new subsection** covering all four acceptance criteria with explicit citations

### Method

1. Read `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` around lines 119-121
2. Read `scripts/rag/ingestion/chunk_splitter.py` around lines 158-175 (_chunk_markdown_by_heading() method)
3. Insert the new subsection after line 119
4. Verify all four acceptance criteria are met

### Details

**Step 1 — Locate the insertion point:**

Current content around lines 119-121:
```
> Evidence: Explicit in code — Markdown heading chunking falls back to English sentence boundary splitting for overflowing sections. Even if `lang` is `"ja"`, Japanese morphological analysis (Sudachi) is NOT applied, and `normalized_content` is NOT generated (the entire heading chunk's `normalized_content` is always treated as empty, as described below).

### 3.2 Splitting Strategies
```

**Step 2 — Insert the new subsection:**

After edit, lines 119-135:
```
> Evidence: Explicit in code — Markdown heading chunking falls back to English sentence boundary splitting for overflowing sections. Even if `lang` is `"ja"`, Japanese morphological analysis (Sudachi) is NOT applied, and `normalized_content` is NOT generated (the entire heading chunk's `normalized_content` is always treated as empty, as described below).

### 3.1.5 Markdown Heading Chunking Fallback Mechanism

#### Trigger condition

The fallback to sentence-based chunking triggers **per individual heading-delimited section**, not for the document as a whole. `_chunk_markdown_by_heading()` (lines 158-175 of `scripts/rag/ingestion/chunk_splitter.py`) splits the entire text at heading boundaries first (one pass), then for each resulting section checks `len(section) <= self._md_snippet_max_chars` individually (line 169). Only sections exceeding `md_snippet_max_chars` are re-split via `_chunk_english()` (line 174).

#### Sequential combination

The two strategies combine **sequentially**, not in parallel. Heading-boundary splitting always runs first across the entire text (line 161-163: `re.split(rf"(?={MARKDOWN_HEADING_RE} )", text.strip(), flags=re.MULTILINE)`). Sentence-based splitting (`_chunk_english()`) is a second pass applied only to whichever individual sections exceed the size limit (line 174: `chunks.extend(self._chunk_english(section))`). It is not a parallel or whole-alternative strategy.

#### Chunk metadata during fallback

- `chunking_strategy`: Remains `"heading"` for the overall Markdown source regardless of which sections fell back to sentence splitting (per the document's existing note at line 134: "Heading chunking (`chunking_strategy="heading"`)... regardless of `lang`").
- `normalized_content`: Stays `null` for both non-fallback sections (size-fitting path) and fallback sections (sentence-split path), consistent with the Evidence note at line 119.
- Sections below `min_chunk` after either path are silently discarded as noise (per `chunk_splitter.py` line 168-169: `if len(section) >= self._min_chunk` guard).

#### Known edge case

Japanese content loses Sudachi normalization when routed through heading chunking, including its sentence-split fallback portion — explicitly stated in the Evidence note at line 119. This is the only documented edge case for this behavior.

### 3.2 Splitting Strategies
```

## Compatibility considerations

- Documentation-only change: no production code affected
- Restating `_chunk_markdown_by_heading()`'s implementation could drift from actual behavior if the method is refactored (e.g. the discard threshold or split order changes) — noted as a risk in the Plan
- If a future code change adds a parallel/alternative strategy for oversized sections (deviating from the documented sequential mechanism), this subsection's AC-2 guidance would become stale

## Security considerations

N/A: documentation update, no security-sensitive operations.

## Rollback considerations

- Revert the single insert step above to restore original document
- No data loss risk — only additive documentation change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md | Documentation structure/quality check | uv run python tools/check_docs_quality.py && uv run python tools/check_docs_structure.py docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md | No new structural/formatting findings |
| docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md | RAG-domain consistency check | uv run python tools/check_docs_consistency.py --domain rag | No new broken-link or drift findings |

## Completion criteria

- [ ] New subsection appended after line 119 and before line 121
- [ ] AC-1: States the fallback triggers per individual heading-delimited section (checked against `md_snippet_max_chars`), not for the document as a whole
- [ ] AC-2: States the two strategies combine sequentially — heading-boundary splitting runs first across the entire text; sentence-based splitting is a second pass applied only to sections that exceeded the size limit
- [ ] AC-3: States that `chunking_strategy` remains `"heading"` regardless of fallback path, `normalized_content` stays `null` for both, sections below `min_chunk` are discarded as noise
- [ ] AC-4: Restates the existing known edge case (Japanese content loses Sudachi normalization when routed through heading chunking) explicitly as the answer to "known edge cases," without inventing an additional one
- [ ] `uv run python tools/check_docs_quality.py` reports no new findings
- [ ] `uv run python tools/check_docs_structure.py docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` reports no new findings
- [ ] `uv run python tools/check_docs_consistency.py --domain rag` reports no new findings

## Out of scope

- Modifying `scripts/rag/ingestion/chunk_splitter.py` or any other source code
- Determining or documenting the actual rationale/historical reason for why `md_snippet_max_chars`/`min_chunk` threshold values have their specific values — this is tracked separately as NC-027/a prior batch's NC-034 provisional entry for related Markdown-chunking rationale questions
- Adding a Needs Confirmation entry to `docs/00_governance_03_issue-and-uncertainty-management.md` (covered by a separate implementation procedure)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation validated by tooling |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring update in Phase 2 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-183051_missing_chunksplitter_markdown_heading_chunking_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-094736_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-123925
- **Related target files**: docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md
