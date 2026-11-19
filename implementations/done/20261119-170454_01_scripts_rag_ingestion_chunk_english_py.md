## Goal

Track the size-rule discard made in `ChunkEnglishMixin._chunk_english` and record it on the per-file discard accumulator so `process_file` can log it (REQ-001, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The discard basis is the post-filter (stopword-stripped) length, matching the existing `len(stripped) >= self._min_chunk` gate in `_chunk_english`.
- `_chunk_english` is called only from within a single `_build_chunk_list` invocation (direct English source, and as the oversized-section fallback inside `_chunk_markdown_by_heading`), so appending to the per-file accumulator never spans multiple source files.
- The accumulator is reset at the start of `_build_chunk_list` (see `chunk_splitter.py` procedure), so this row's change reads a fresh per-file total.
- A non-blocking caveat (recorded here and in the sibling `chunk_splitter.py` procedure): the structured discard fields are attached to the `LogRecord` via `extra=` following the existing ingestion-logger pattern (`extra={"url": ...}`, `extra={"source_type": ..., "stage_name": ...}`). The current `_JsonFormatter` serializes only `ts/level/func/msg/context-keys/exc`, so these fields land on the record and in the message text but are not yet written to the JSON line — consistent with every existing structured field. This is observable (message + record attribute) and does not require modifying `shared/logger.py`.

## Design decisions
- Compute the dropped rows directly from the already-built `zip(raw_chunks, filtered)` list; count them and sum their post-filter lengths.
- Append to the shared per-file accumulator (`self._discarded_count`, `self._discarded_chars`) instead of changing the return signature, preserving every existing caller and the direct-call test at `tests/rag/ingestion/test_chunk_splitter.py:165`-style assertions.

## Alternatives considered
- Returning `(items, discarded_count, discarded_chars)` from `_chunk_english`: would change the internal return signature and break the direct-call test and any mock; the accumulator avoids this.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_english.py`

### Procedure
Rewrite `_chunk_english` to compute the discard set from the same `zip` it already returns over, update the accumulator, and return the kept list unchanged.

### Method
Replace the inline list comprehension (lines 33-37) with an explicit keep/discard split:

```python
def _chunk_english(self, text: str) -> list[str]:
    paragraphs = re.split(r"\n{2,}", text.strip())
    raw_chunks = self._merge_paragraphs_en(paragraphs)
    filtered = [self._filter_stopwords_en(r) for r in raw_chunks]
    kept: list[str] = []
    for raw, stripped in zip(raw_chunks, filtered):
        if len(stripped) >= self._min_chunk:
            kept.append(raw)
        else:
            self._discarded_count += 1
            self._discarded_chars += len(stripped)
    return kept
```

### Details
- `discarded_chars` (new) uses `len(stripped)` (post-filter length), per the Plan's Assumptions.
- Keep the return value identical to before (`list[str]` of unfiltered original regions); only side-effect accumulation is added.
- No new import, no public-contract change.

## Compatibility considerations
- Preserves the return type and values of `_chunk_english`; the only additive effect is the accumulator update. Existing callers (`_build_text_triples`, `_chunk_markdown_by_heading` fallback) are unaffected.

## Security considerations
- N/A: no input parsing or data-flow change beyond counting lengths of already-derived strings.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Static: `uv run ruff format --check scripts/rag/ingestion/chunk_english.py` && `uv run ruff check scripts/rag/ingestion/chunk_english.py`.
- Type: `uv run mypy scripts/rag/ingestion/chunk_english.py`.
- Security: `uv run bandit scripts/rag/ingestion/chunk_english.py`.
- Unit: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` (existing tests stay green; the new discard assertions live in the companion test procedure).

## Completion criteria
`_chunk_english` updates `self._discarded_count`/`self._discarded_chars` for every sub-`min_chunk` post-filter row, returns the same kept list as before, and ruff/mypy/bandit are clean.

## Out of Scope
- Aggregation and logging (sibling `chunk_splitter.py` procedure).
- Test authorship (`tests/rag/ingestion/test_chunk_splitter.py`); this row's change is verified by that suite, whose new methods are authored in its own procedure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Track discard in the English path | Completed | 20261119-175837 | 20261119-175837 | Update accumulator in `_chunk_english` |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-175837 | 20261119-175837 | ruff/mypy/bandit + existing suite |
| 3 | Add or update tests | Completed | 20261119-175837 | 20261119-175837 | New discard assertions are in the test-file procedure |
| 4 | Update documentation | Completed | 20261119-175837 | 20261119-175837 | Not in this file's scope |

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
- **Requirement ID**: REQ-001 (count/length of size-rule discards) plus REQ-003 (discard recorded at the point it is made)
- **Source issue**: issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-164553_ragcrv004_silent-chunk-discard-logging.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-170454
- **Related target files**: `scripts/rag/ingestion/chunk_english.py`
