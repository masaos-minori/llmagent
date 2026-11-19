# Discarded chunk content is not reported

## Priority
Medium

## Summary
Every chunking path silently drops content that fails a size rule, and the run reports only the number of
chunks written. An operator cannot tell "the source produced nothing" from "the source was discarded".

## Background
- `ChunkEnglishMixin._chunk_english` discards every merged chunk shorter than `min_chunk` after stopword
  filtering.
- `ChunkSplitter._chunk_markdown_by_heading` skips empty sections and sections shorter than `min_chunk`,
  and logs nothing.
- `ChunkSplitter._chunk_code` delegates to `chunk_utils.merge_text_items`, which drops a single short block.
- Reproduced at head `6bdced7bb` with `min_chunk=40`, `max_chunk=120`: a two-heading Markdown document
  produced 0 chunks, and a code block shorter than `min_chunk` produced 0 chunks; in both cases the only
  log line was INFO `chunked 0 chunks from x.json`.
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` documents the discard as intended behavior
  ("discarded as noise") but the discard itself leaves no trace.
- `docs/21_rag/rag_05_03-logging.md` defines structured log fields already used elsewhere
  (`url`, `source_type`, `stage_name`).

## Problem
Silent content loss is indistinguishable from a successful empty run. Corpus completeness can only be
checked by re-running the splitter manually and comparing files.

## Reason for Change
The chunker is the only stage that sees the crawled text, so the discard decision must be observable at the
point where it happens.

## Implementation Intent
Report the discard decision where it is made: a per-file summary of discarded items with the reason and
their total size, using the structured fields the ingestion loggers already use. Keep the discard behavior
unchanged; only its observability changes.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_english.py`
- `scripts/rag/ingestion/chunk_splitter.py` (`_chunk_markdown_by_heading`, `_chunk_code`, `process_file`)
- `tests/rag/ingestion/test_chunk_splitter.py`
- `docs/21_rag/rag_05_03-logging.md`

## Required Changes
- Record the count and combined length of items discarded by a size rule for each source file.
- Log that summary at WARNING when a source yields zero chunks, and at INFO otherwise.
- Include the rule that caused the discard (`below_min_chunk`) and the source identity in the structured
  fields.
- Document the new log record shape in the logging reference.

## Constraints
- No change to which content is kept or discarded.
- Log volume must stay bounded: one summary per file, not one line per discarded item.
- Must not log document text content.

## Acceptance Criteria
- A source whose content is entirely below `min_chunk` produces a WARNING naming the file and the reason.
- A source with both kept and discarded content reports the discarded count and length.
- Existing log-based tests stay green.

## Testing Expectations
- Unit: capture the module logger (the `_ListHandler` pattern already used in
  `tests/rag/ingestion/test_chunk_grouping.py`) and assert the structured fields for a
  below-`min_chunk` English document, a below-`min_chunk` Markdown document, and a short code block.
- Regression: the current chunk test suite stays green.

## Documentation Impact
`docs/21_rag/rag_05_03-logging.md`: add the discard summary record and when it appears.
`docs/21_rag/rag_05_04-error-handling-reference.md`: state that a size-rule discard is not an error and
how it is reported.

## Out of Scope
- Changing the discard thresholds.
- Changing English stopword behavior (issues/20261119-112014_ragcrv002_english-content-stopword-loss.md).
- Adding a quarantine directory for discarded sources.

## Dependencies
- Sibling: issues/20261119-112015_ragcrv003_chunk-config-validation.md removes the misconfiguration path that produces the most common zero-chunk case.

## Unresolved Questions
- Whether the operational runbook should treat a zero-chunk source as a run failure — needs confirmation
  together with issues/20261119-112019_ragcrv007_chunk-failure-exit-reporting.md.

## AI Implementation Instruction
Log a per-file summary only. Do not log raw chunk text. Do not change which items are discarded.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-004`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112016
- **Related target files**: `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`, `docs/21_rag/rag_05_03-logging.md`
