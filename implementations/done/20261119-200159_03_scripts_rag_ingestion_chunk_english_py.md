## Goal

Route `ChunkEnglishMixin._merge_paragraphs_en` through the accumulator so it no longer owns buffer state, and drop the undeclared `self._buf` instance attribute (`REQ-003`), leaving paragraph/sentence splitting and filter-driven `min_chunk` enforcement in the mixin (`REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- After `ragcrv005` routes accumulation through its collaborator, `_merge_paragraphs_en` no longer needs a running buffer; the buffer it currently holds (`self._buf`, set at line 55) becomes owned by the accumulator.
- `self._buf` is assigned without declaration at line 55 of `chunk_english.py`; the mixin declares only `_max_chunk`, `_min_chunk`, `_en_stopwords`, `_chunk_overlap` (lines 21–24) plus class-level `_discarded_count`/`_discarded_chars`.
- The `_discarded_count`/`_discarded_chars` accumulators are a separate per-file size-rule discard mechanism (reset in `ChunkSplitter._build_chunk_list`, read in `process_file`, lines 186–201) and are NOT part of this removal — keep them.
- The mixin receives chunking settings via the collaborator added by rows 1–2 instead of reading host attributes.
- Cross-plan overlap: `chunk_english.py` is not targeted by `ragcrv007`; no cross-plan interaction here.

## Design decisions
- `_merge_paragraphs_en` delegates accumulation to the collaborator (ragcrv005) and stops assigning `self._buf`; the split/merge helpers (`_flush_and_split`, `_flush_and_merge`, `_split_sentences_en`) are rewritten to operate on collaborator return values rather than `self._buf`.
- Keep `_chunk_english`'s stopword filtering and `len(stripped) >= self._min_chunk` gate unchanged (lines 40–48).

## Alternatives considered
- Keeping `self._buf` as a declared attribute vs. removing it: the plan removes it because the accumulator owns per-call state (`REQ-003`); chosen.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_english.py`

### Procedure
1. Remove the `self._buf = ""` assignment and all reads of `self._buf` in `_merge_paragraphs_en`, `_flush_and_split`, `_flush_and_merge`.
2. Rewrite those helpers to drive the collaborator (ragcrv005) instead of a running buffer.
3. Keep `_split_sentences_en`, `_filter_stopwords_en`, and `_chunk_english` logic unchanged.

### Method
- Reproduce the current output exactly: grow a buffer while paragraphs fit under `max_chunk`, split an overlong paragraph via `_split_sentences_en`, flush-and-merge with overlap via `start_next_buf`, append the final buffer. The collaborator now owns this; the mixin supplies the strategy inputs.

### Details
- Verify no other method in `chunk_english.py` reads `self._buf` before removing it (grep for `_buf`); only `_merge_paragraphs_en` and its two flush helpers reference it.

## Compatibility considerations
- `_chunk_english`'s signature and return type (`list[str]`) are unchanged; the public chunk output is unchanged (`REQ-006`).

## Security considerations
N/A: text accumulation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Regression: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` English cases produce zero diff from baseline.
- `grep` finds no `self._buf` instance attribute in `scripts/rag/ingestion/`.

## Completion criteria
- `_merge_paragraphs_en` delegates accumulation to the collaborator; `self._buf` removed; English chunk output byte-identical.

## Out of Scope
- The value object definition — row 1.
- The tokenizer `Protocol` — row 4.
- Test-construction rework — row 5.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Superseded | — | — | Superseded: ragcrv005 (commit 57ee0494d, already merged) routed ChunkEnglishMixin._merge_paragraphs_en through the shared accumulate_items collaborator and removed the undeclared self._buf instance attribute; the work this procedure describes is fully subsumed. Re-implementing would violate minimal-scope (AGENTS.md Global Rule 5). |
| 2 | Add or update tests per Validation plan | Superseded | — | — | Superseded: ragcrv005 (commit 57ee0494d, already merged) routed ChunkEnglishMixin._merge_paragraphs_en through the shared accumulate_items collaborator and removed the undeclared self._buf instance attribute; the work this procedure describes is fully subsumed. Re-implementing would violate minimal-scope (AGENTS.md Global Rule 5). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Superseded | — | — | Superseded: ragcrv005 (commit 57ee0494d, already merged) routed ChunkEnglishMixin._merge_paragraphs_en through the shared accumulate_items collaborator and removed the undeclared self._buf instance attribute; the work this procedure describes is fully subsumed. Re-implementing would violate minimal-scope (AGENTS.md Global Rule 5). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Superseded | — | — | Superseded: ragcrv005 (commit 57ee0494d, already merged) routed ChunkEnglishMixin._merge_paragraphs_en through the shared accumulate_items collaborator and removed the undeclared self._buf instance attribute; the work this procedure describes is fully subsumed. Re-implementing would violate minimal-scope (AGENTS.md Global Rule 5). |

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
- **Requirement ID**: `REQ-003` (remove undeclared buffer state), `REQ-005`/`REQ-006` (output unchanged)
- **Source issue**: `issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-190454_ragcrv006_chunk-mixin-state-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-200159
- **Related target files**: `scripts/rag/ingestion/chunk_english.py`