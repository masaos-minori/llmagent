## Goal

Measure the size-rule discard in the Markdown and code paths, aggregate the per-file discard into one summary, reset the accumulator per file, and log the summary at the correct level (REQ-001, REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The accumulator (`self._discarded_count`, `self._discarded_chars`) is reset at the start of `_build_chunk_list`, so text + code discard from one source file aggregate into one total and never leak across files or direct test calls.
- Markdown discard length is the raw section length (`len(section)`), per the Plan's Assumptions.
- Code discard is measured by character difference through `chunk_utils.merge_text_items` without changing its output; the count is a best-effort approximation (UNK-01).
- A non-blocking caveat (also in the `chunk_english.py` procedure): the structured discard fields are attached via `extra=` following the existing ingestion-logger pattern; the current `_JsonFormatter` does not serialize arbitrary extra fields to the JSON line, so they are observable on the record and in the message text, not yet in the JSON output. This matches existing `extra={"url": ...}` usage and does not require modifying `shared/logger.py`.

## Design decisions
- **Accumulator mechanism (Plan design option b).** Add `self._discarded_count: int = 0` and `self._discarded_chars: int = 0` as instance attributes (declared on the class body so mypy sees them; values set in `__init__`/reset in `_build_chunk_list`). Each chunker appends to the accumulator; `process_file` reads it after `_build_chunk_list`. This preserves every existing return signature (`_chunk_markdown_by_heading` still returns `list[tuple[str, str | None]]`, `_chunk_code` still returns `list[str]`), avoiding the breakage that returning `(items, count, chars)` would cause at `tests/rag/ingestion/test_chunk_splitter.py`.
- **Reset location.** Reset the accumulator at the start of `_build_chunk_list` (the fan-out boundary), which is once per source file and safe against direct chunker/build calls in tests.

## Alternatives considered
- Threading `(items, discarded_count, discarded_chars)` up through `_build_text_triples`/`_build_code_triples`/`_build_chunk_list` (Plan option a): changes internal return signatures and breaks the direct-call test and mocks; the accumulator avoids this.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. Add accumulator attributes and reset them in `_build_chunk_list`.
2. Measure Markdown discard in `_chunk_markdown_by_heading`.
3. Measure code discard in `_chunk_code`.
4. Log the aggregated summary in `process_file`.

### Method
**Attributes / reset.** In the class body add:
```python
_discarded_count: int
_discarded_chars: int
```
In `_build_chunk_list`, reset at the very top (before `_read_source_data` is not required — reset right after `lang = data.lang`):
```python
self._discarded_count = 0
self._discarded_chars = 0
```

**Markdown discard** (`_chunk_markdown_by_heading`, lines 265-273). The `else` branch of `if len(section) >= self._min_chunk:` is the drop point; add accumulation there:
```python
if len(section) <= self._md_snippet_max_chars:
    if len(section) >= self._min_chunk:
        ...append (section, normalized)...
    else:
        self._discarded_count += 1
        self._discarded_chars += len(section)
else:
    # oversized -> language chunker, not a discard (unchanged)
```

**Code discard** (`_chunk_code`, lines 284-294). Measure character difference without changing `merge_text_items` output:
```python
def _chunk_code(self, code: str) -> list[str]:
    blocks = re.split(r"\n{2,}", code.strip())
    chunks = merge_text_items(blocks, "\n\n", self._min_chunk, self._max_chunk, self._chunk_overlap)
    diff = sum(len(b) for b in blocks) - sum(len(c) for c in chunks)
    if diff > 0:
        self._discarded_chars += diff
        self._discarded_count += self._approx_discarded_block_count(blocks, chunks)
    return chunks
```
`_approx_discarded_block_count` (new) is a best-effort (UNK-01): count input blocks whose stripped text is not a substring of the concatenated output. Document it as approximate. Clamp `diff` to `> 0` (merging can make the raw negative).

**Logging** (`process_file`, after `written = self._write_chunk_files(...)` and before the `return written`). Add:
```python
if self._discarded_count > 0:
    _level = logging.WARNING if written == 0 else logging.INFO
    logger.log(
        _level,
        "discarded %s item(s) (%s chars) below min_chunk",
        self._discarded_count,
        self._discarded_chars,
        extra={
            "url": chunk_doc.url,
            "source_type": "file",
            "stage_name": "chunk",
            "discard_reason": "below_min_chunk",
            "discarded_count": self._discarded_count,
            "discarded_chars": self._discarded_chars,
        },
    )
```
Use the constants from `scripts/rag/utils.py` (`LOG_KEY_SOURCE_TYPE`, `LOG_KEY_STAGE_NAME`) for the keys and `"file"`/`"chunk"` for the values. Keep the existing INFO `chunked %s chunks from %s` line unchanged.

### Details
- `logging` must be imported (`from shared.logger import Logger` already imports logging transitively; add `import logging` if not present — verify current imports).
- One summary per file: guarded by `if self._discarded_count > 0`; never logs content (only counts, lengths, reason).
- Log level: WARNING when `written == 0` (source yielded nothing), INFO when `written > 0` but some discarded (REQ-002).

## Compatibility considerations
- No change to any return signature consumed elsewhere; `_build_chunk_list` still returns the same triples list. The accumulator is additive state reset per file.
- Existing tests that mock `_build_chunk_list` never touch the accumulator (discard stays 0 → no discard record); existing `_chunk_code` direct-call test still receives a `list[str]`.

## Security considerations
- N/A: no new input parsing; counts are derived from already-derived strings. Content is never logged.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Static: `uv run ruff format --check scripts/rag/ingestion/chunk_splitter.py` && `uv run ruff check scripts/rag/ingestion/chunk_splitter.py`.
- Type: `uv run mypy scripts/rag/ingestion/chunk_splitter.py`.
- Security: `uv run bandit scripts/rag/ingestion/chunk_splitter.py`.
- Unit: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` (full RAG suite regression).

## Completion criteria
Markdown sub-`min_chunk` sections and code-path character-difference discard update the accumulator; `process_file` logs exactly one WARNING (zero chunks) or INFO (kept + discarded) with `discard_reason` (new)/`discarded_count` (new)/`discarded_chars`/`url`/`source_type`/`stage_name`; ruff/mypy/bandit clean; existing suite green.

## Out of Scope
- English-path discard tracking (`chunk_english.py` procedure).
- Test authorship (`tests/rag/ingestion/test_chunk_splitter.py` procedure).
- Documentation updates (`rag_05_03-logging.md` / `rag_05_04-error-handling-reference.md` procedures).
- Japanese path (`chunk_japanese.py`): unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure Markdown and code discard; aggregate per file; log the summary | Completed | 20261119-175837 | 20261119-175837 | Accumulator mechanism (option b); reset in `_build_chunk_list` |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-175837 | 20261119-175837 | ruff/mypy/bandit + full RAG suite |
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
- **Requirement ID**: REQ-001 (count/length), REQ-002 (log level), REQ-003 (structured discard fields)
- **Source issue**: issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-164553_ragcrv004_silent-chunk-discard-logging.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-170454
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`
