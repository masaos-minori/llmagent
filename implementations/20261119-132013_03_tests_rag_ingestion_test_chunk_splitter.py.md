## Goal

Add the first test asserting both the stored English `content` and
`normalized_content` for a **non-empty** `en_stopwords` configuration, so the Shape B
behavior (`content` retains every word; `normalized_content` is `NULL`) is pinned and
cannot silently regress (`REQ-006`).

## Scope
**Release unit**: english-content-stopword-loss

## Assumptions

- The sibling `chunk_english.py` procedure makes `_chunk_english` return the unfiltered
  original; this test pins that outcome end-to-end through `process_file`.
- `_CRAWL_CONFIG` (`test_chunk_splitter.py:405`) supplies a non-empty `en_stopwords` list,
  but no existing test asserts the stored values for it.
- The existing `test_process_file_end_to_end_english` (`test_chunk_splitter.py:804`) uses
  `en_stopwords: []` and only checks `"Hello world" in reassembled`; it does not pin the
  stored values and stays as-is.

## Design decisions

- **Non-empty stopwords + whole-word presence.** The test feeds English text that
  contains the configured stopwords and asserts every one is still present in the stored
  `content` (Shape B never strips them). This fails under the current buggy code
  (which strips them) and passes only after the `chunk_english.py` fix.
- **Assert `normalized_content is None`.** Pins Shape B (`REQ-002`).

## Alternatives considered

- `N/A: the shape (A vs B) is locked to Shape B by the owner decision (UNK-01); the test
  asserts Shape B only.`

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
Add a new test method that runs `ChunkSplitter.process_file` on an English crawl record
with a **non-empty** `en_stopwords` config and asserts both stored fields:

1. Build an English `content` string that includes the configured stopwords (e.g.
   `"the", "a", "is", "and"`) repeated enough to survive `min_chunk`.
2. Construct `ChunkSplitter` with `en_stopwords` set to that non-empty list (reuse the
   `_CRAWL_CONFIG` stopwords or a small literal) and a `min_chunk`/`max_chunk` that keep
   the text in a single chunk so `content` maps directly to the input.
3. Call `process_file` and read the produced chunk JSON.
4. Assert, for the chunk payload:
   - `payload["content"]` contains every configured stopword (no word removed) and equals
     the input region whitespace-normalized (`REQ-001`);
   - `payload["normalized_content"] is None` (`REQ-002`, Shape B).

### Method

Model the new method on `test_process_file_end_to_end_english`
(`test_chunk_splitter.py:804`) — same `tmp_path`, `_make_crawl_json(lang="en", ...)`,
`process_file(src, force=True)`, and glob-over-output pattern — but with a non-empty
`en_stopwords` and the two value assertions above. Keep the input short and single
paragraph so exactly one chunk is produced and `content` equals the input verbatim
(after whitespace normalization), making the presence assertion exact.

Place the new method adjacent to the existing English end-to-end test. Do not modify any
existing test.

### Details

- No symbols or imports are created beyond what the existing methods already use
  (`json`, `Path`).
- The test targets only the English path; the Japanese path is covered by the sibling
  Japanese regression expectation (`REQ-004`).

## Compatibility considerations

- The new test must pass only after the sibling `chunk_english.py` fix; run it together
  with `tests/rag/test_fts_fallback.py`, `tests/rag/test_fts_sync.py`,
  `TestChunkPayloadKeyContract`, and the Japanese chunking tests (`REQ-002`, `REQ-004`).

## Security considerations

`N/A: test-only change; no runtime behavior, auth, secrets, or network changes.`

## Rollback considerations

Revert the single commit that adds the test.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` — the new test passes;
  `content` retains every stopword and `normalized_content` is `NULL`.
- Full RAG suite stays green (`REQ-002`, `REQ-004`).

## Completion criteria

- A test exists that, for a non-empty `en_stopwords` config, asserts the stored English
  `content` has no words removed and `normalized_content` is `None`.
- All listed tests pass.

## Out of Scope

- The production code change (`chunk_english.py`, `chunk_splitter.py`) — covered by the
  sibling procedures.
- Docs updates (`REQ-005`, `REQ-007`) — covered by the sibling docs procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (first test asserting both `content` and
  `normalized_content` for a non-empty `en_stopwords` config)
- **Source issue**: `issues/20261119-112014_ragcrv002_english-content-stopword-loss.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-123746_ragcrv002_english-content-stopword-loss.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-132013
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`
