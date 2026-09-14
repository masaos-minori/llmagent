## Goal

Append a new subsection to `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` immediately after "3.1.4 Markdown Heading Chunking Behavior" (after line 117, before "### 3.2 Splitting Strategies" at line 119), stating: (a) there is no override — `.md`/`.markdown`/`.mdx` URLs unconditionally use heading chunking regardless of `md_index_enable` (per `_is_markdown_source()`, `chunk_splitter.py` lines 146-148, which checks the URL extension before even reading `self._md_index_enable`); (b) the known edge case already stated in section 3.1.4 (Japanese content in Markdown skips Sudachi normalization), explicitly labeled as the answer to "known edge cases where this behavior causes problems." Per REQ-001.

## Scope

- Append exactly one new subsection into `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
  after line 117 (end of "3.1.4 Markdown Heading Chunking Behavior") and before line 119
  ("### 3.2 Splitting Strategies")
- Cover two items requested in the Issue's Recommended Action:
  (1) No override exists for `.md`/`.markdown`/`.mdx` unconditional behavior;
  (2) Label the existing Sudachi-normalization-skip note (section 3.1.4) as the known edge case
- Each item backed by `scripts/rag/ingestion/chunk_splitter.py`'s `_is_markdown_source()` method or
  the existing document's section 3.1.4 — no invented guidance beyond what the existing code
  pattern supports

## Assumptions

- `_is_markdown_source()`'s extension-first check order (`chunk_splitter.py` lines 146-148: extension check, then `self._md_index_enable` check only reached for non-`.md`-extension URLs) is sufficient evidence that no override path exists in the current codebase — this Plan does not search for a separate configuration flag elsewhere, since `md_index_enable` is `ChunkSplitterConfig`'s only Markdown-detection-related setting (per section 3.1.1, line 65)
- The historical reason for this design decision is not recoverable from git history within this Plan's Path A analysis scope (Path A skips historical/blame analysis per `SKILL.md` Routing) — if a future Owner review resolves the open question, it would update the NC entry directly, not this Plan

## Design decisions

- Append the new subsection immediately after "3.1.4 Markdown Heading Chunking Behavior"
  (line 117) and before "### 3.2 Splitting Strategies" (line 119)
- Quote or closely paraphrase each sibling class's docstring rather than summarizing
  loosely, minimizing near-term drift risk if `scripts/rag/ingestion/chunk_splitter.py` is edited later
- Cite the specific catch-site file:line locations in Reference Files above
- Do NOT invent additional hierarchy deviations beyond the one documented at Implementation Notes line 79

## Alternatives considered

- Placing the subsection elsewhere in the document: rejected — appending after
  "3.1.4 Markdown Heading Chunking Behavior" keeps it as a natural continuation of the
  Markdown source detection discussion rather than a disconnected addition
- Deriving new distinguishing rules for exception selection instead of citing docstrings:
  rejected — the Issue's Recommended Action asks for connecting existing accepted evidence,
  not inventing new claims

## Implementation

### Target file

`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure

1. **Locate the insertion point** — between line 117 (end of "3.1.4 Markdown Heading Chunking Behavior")
   and line 119 ("### 3.2 Splitting Strategies")

2. **Insert the new subsection** covering all four acceptance criteria with explicit citations

### Method

1. Read `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` around lines 117-119
2. Read `scripts/rag/ingestion/chunk_splitter.py` around lines 138-154 (_is_markdown_source() method)
3. Insert the new subsection after line 117
4. Verify all four acceptance criteria are met

### Details

**Step 1 — Locate the insertion point:**

Current content around lines 117-119:
```
Text is split by Markdown headings (# through ######). Sections exceeding `md_snippet_max_chars` characters are further split using sentence-based chunking.

> Evidence: Explicit in code — Markdown heading chunking falls back to English sentence boundary splitting for overflowing sections. Even if `lang` is `"ja"`, Japanese morphological analysis (Sudachi) is NOT applied, and `normalized_content` is NOT generated (the entire heading chunk's `normalized_content` is always treated as empty, as described below).

### 3.2 Splitting Strategies
```

**Step 2 — Insert the new subsection:**

After edit, lines 117-135:
```
Text is split by Markdown headings (# through ######). Sections exceeding `md_snippet_max_chars` characters are further split using sentence-based chunking.

> Evidence: Explicit in code — Markdown heading chunking falls back to English sentence boundary splitting for overflowing sections. Even if `lang` is `"ja"`, Japanese morphological analysis (Sudachi) is NOT applied, and `normalized_content` is NOT generated (the entire heading chunk's `normalized_content` is always treated as empty, as described below).

### 3.1.5 Override Behavior and Known Edge Cases

#### No override for `.md`/`.markdown`/`.mdx` sources

There is no configuration or per-source override for `.md`/`.markdown`/`.mdx` URLs'
unconditional heading chunking. `_is_markdown_source()` (lines 138-154 of
`scripts/rag/ingestion/chunk_splitter.py`) checks the URL extension first (line 146:
`if url.endswith((".md", ".markdown", ".mdx")):` returns `True` immediately), and only
reaches the `self._md_index_enable` check (line 148) for non-`.md`-extension URLs. This
means any source ending in `.md`, `.markdown`, or `.mdx` — whether a remote URL or a local
`file://` source — always uses heading chunking regardless of `md_index_enable`.

#### Known edge case: Japanese content skips Sudachi normalization

The existing note in section 3.1.4 (above) states that even when `lang` is `"ja"`, Japanese
morphological analysis (Sudachi) is NOT applied for Markdown heading chunking, and
`normalized_content` is NOT generated. This is the only known edge case where the Markdown
heading chunking behavior causes problems — Japanese text processing relies on Sudachi
normalization for accurate segmentation, but the heading chunking path bypasses it entirely.

### 3.2 Splitting Strategies
```

## Compatibility considerations

- Documentation-only change: no production code affected
- Restating `_is_markdown_source()`'s docstring could drift from the actual docstring text if
  `scripts/rag/ingestion/chunk_splitter.py` is edited later without a corresponding doc update
  (documented as a risk in the Plan)
- If a future code change adds an override mechanism for `.md`/`.markdown`/`.mdx` sources
  (deviating from the documented "no override" claim), this subsection's AC-1 guidance would
  become stale (documented as a risk in the Plan)

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

- [ ] New subsection appended after line 117 and before line 119
- [ ] AC-1: States there is no configuration or per-source override for `.md`/`.markdown`/`.mdx` URLs' unconditional heading chunking, citing `_is_markdown_source()`'s extension-first check order
- [ ] AC-2: Explicitly labels the existing Sudachi-normalization-skip note (section 3.1.4) as the known edge case, without introducing any additional invented edge case
- [ ] `uv run python tools/check_docs_quality.py` reports no new findings
- [ ] `uv run python tools/check_docs_structure.py docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` reports no new findings
- [ ] `uv run python tools/check_docs_consistency.py --domain rag` reports no new findings

## Out of scope

- Modifying `scripts/rag/ingestion/chunk_splitter.py` or any file that raises/catches ChunkFormatError
- Determining or documenting the actual rationale/historical reason for why `.md`/`.markdown`/`.mdx` URLs unconditionally use heading chunking — this is an Owner/design-review decision with no answer available anywhere in the repository
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
- **Source issue**: issues/20260913-183038_missing_chunksplitter_markdown_source_detection_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-093116_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-122358
- **Related target files**: docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md
