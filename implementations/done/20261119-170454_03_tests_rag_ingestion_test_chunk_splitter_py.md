## Goal

Add logger-capture unit tests that assert the structured discard fields for below-`min_chunk` English, Markdown, and short-code inputs, plus a mixed (kept + discarded) case (REQ-001, REQ-002, AC-001, AC-002).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Reuse the `_ListHandler` pattern from `tests/rag/ingestion/test_chunk_grouping.py` (attach to the module logger, run, remove, inspect `handler.records`).
- The discard fields land on the `LogRecord` via `extra=` (see the `chunk_splitter.py` procedure caveat about JSON serialization); assertions read the record attributes and/or message text, not the serialized JSON line.
- Test inputs are constructed so the English/Markdown paths produce a below-`min_chunk` result and the code path produces a block shorter than `min_chunk` that cannot be merged.
- A non-blocking caveat: the structured discard fields are attached via `extra=` following the existing ingestion-logger pattern; the current `_JsonFormatter` does not serialize arbitrary extra fields to the JSON line, so assertions read the record attributes/message, consistent with how existing structured fields behave.

## Design decisions
- One test class `TestDiscardLogging` (new) with four methods mapping to T-001..T-004. Each builds a source via the splitter's public/protected entry (`process_file` against a temp crawl JSON, or the relevant `_chunk_*` method directly) and captures the module logger.
- Assert on `record.discarded_count`, `record.discarded_chars`, `record.discard_reason == "below_min_chunk"`, and the log level (WARNING for zero-chunks, INFO for mixed).

## Alternatives considered
- Using `caplog`: the established RAG pattern here is `_ListHandler` on `propagate=False` loggers, so `_ListHandler` is used for consistency.

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
1. Add a `_ListHandler` capture helper (mirror `tests/rag/ingestion/test_chunk_grouping.py`): attach to `chunk_splitter_module.logger`, run, remove, return captured records.
2. Add `TestDiscardLogging` (new) with:
   - `T-001`: below-`min_chunk` English document → one WARNING record with `discard_reason == "below_min_chunk"`, `discarded_count >= 1`, and the file name in the message.
   - `T-002`: below-`min_chunk` Markdown document → same assertions.
   - `T-003`: short code block shorter than `min_chunk` that cannot be merged → a record exists with `discard_reason == "below_min_chunk"` and `discarded_chars > 0` (approximate count accepted, UNK-01).
   - `T-004`: mixed (kept + discarded) source → an INFO record carrying `discarded_count` and `discarded_chars`.
3. For each, assert no document text content appears in the record/message (REQ-004).

### Method
- Construct inputs through the smallest surface that exercises the discard point without side effects: prefer calling `_chunk_english` / `_chunk_markdown_by_heading` / `_chunk_code` directly with a configured splitter (reuse the existing fixture pattern at line 165 for `_chunk_code`), or drive `process_file` on a temp crawl JSON when the per-file aggregation/logging path must be exercised (T-004).
- Read `min_chunk`/`max_chunk` from the test config fixture and craft inputs accordingly.

### Details
- `discard_reason` is always `"below_min_chunk"` (single size rule) per the Plan's Assumptions.
- Keep the new methods isolated in `TestDiscardLogging` (new); do not modify existing test methods.

## Compatibility considerations
- Purely additive test methods; existing tests are untouched. The new methods exercise the same chunkers whose return signatures are preserved by the code change.

## Security considerations
- N/A: test-only additions.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` — new and existing tests pass.
- Full suite: `uv run pytest tests/rag/`.

## Completion criteria
Four new assertions pass: English/Markdown below-`min_chunk` produce a WARNING naming the reason, short-code produces a discard record with positive chars, mixed source logs count+length at INFO, and no method asserts document content. Existing suite stays green.

## Out of Scope
- Code changes (`chunk_english.py`, `chunk_splitter.py` procedures).
- Documentation updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | 20261119-175837 | 20261119-175837 | `_ListHandler`-based discard assertions |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-175837 | 20261119-175837 | pytest targeted + full RAG suite |

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
- **Requirement ID**: REQ-001, REQ-002 (logger-capture coverage of the discard summary)
- **Source issue**: issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-164553_ragcrv004_silent-chunk-discard-logging.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-170454
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`
