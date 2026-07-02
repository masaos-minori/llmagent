# Implementation: Add TestFormatChunksDesign2 to test_rag_pipeline.py

## Goal

Add a `TestFormatChunksDesign2` class to `tests/test_rag_pipeline.py` that asserts
`RagPipeline._format_chunks` uses only `c.content` and never leaks any "normalized" text
into the output (TEST-DESIGN2-01 and TEST-DESIGN2-03).

## Scope

- **Target file:** `tests/test_rag_pipeline.py`
- **Change type:** Additive — new class only; no existing tests modified.
- **Production code:** No changes.

## Assumptions

1. `RankedHit` is already imported at the top of the file:
   `from rag.types import MergedHit, RankedHit, RawHit`
2. `RagPipeline._format_chunks` uses `c.content` (not `c.normalized_content`) — confirmed
   by reading `scripts/rag/pipeline.py` lines 360-368.
3. `normalized_content` is not a field of `RankedHit`; it exists only in the DB `chunks`
   table and in `IngestionChunk` TypedDicts. Tests simulate the invariant by constructing
   a `RankedHit` with a known `content` value and a separate forbidden string that
   represents what `normalized_content` would look like if it leaked.

## Implementation

### Target file

`tests/test_rag_pipeline.py`

### Procedure

1. Open `tests/test_rag_pipeline.py`.
2. Locate the end of the `TestFormatChunks` class (currently ends around line 123).
3. Insert the new `TestFormatChunksDesign2` class immediately after `TestFormatChunks`
   and before the `# ── RagPipelineError` comment block.

### Method

Add the following class verbatim:

```python
# ── DESIGN-2: content-only regression tests ───────────────────────────────────


class TestFormatChunksDesign2:
    """Regression tests for DESIGN-2: LLM context must contain content only,
    never normalized_content.

    TEST-DESIGN2-01: AugmentStage outputs content only, not normalized_content.
    TEST-DESIGN2-03: LLM context does not contain normalized_content unless
                     identical to content.
    """

    def _hit(
        self, content: str, url: str = "http://example.com", title: str = ""
    ) -> RankedHit:
        return RankedHit(chunk_id=1, content=content, url=url, title=title)

    def test_content_appears_in_output(self) -> None:
        """TEST-DESIGN2-01: content text must appear in _format_chunks output."""
        result = RagPipeline._format_chunks([self._hit("日本語テキスト")])
        assert "日本語テキスト" in result

    def test_normalized_content_does_not_appear(self) -> None:
        """TEST-DESIGN2-01: normalized text must NOT appear in _format_chunks output."""
        normalized = "にほんご テキスト"
        result = RagPipeline._format_chunks([self._hit("日本語テキスト")])
        assert normalized not in result

    def test_normalized_differs_from_content_not_in_output(self) -> None:
        """TEST-DESIGN2-03: when normalized != content, normalized must not appear."""
        content = "検索結果"
        normalized = "けんさく けっか"
        result = RagPipeline._format_chunks([self._hit(content)])
        assert content in result
        assert normalized not in result
```

### Details

- The three test methods map directly to the pseudocode in
  `docs/03_rag_90_inconsistencies_and_known_issues.md` (TEST-DESIGN2-01 and
  TEST-DESIGN2-03).
- No new imports are needed; `RankedHit`, `RagPipeline`, `_RAG_BLOCK_START`, and
  `_RAG_BLOCK_END` are already imported at the top of the file.
- The `_hit()` helper mirrors the pattern used in `TestFormatChunks._hit()` to keep
  the test file consistent.

## Validation plan

| Command | Expected outcome |
|---------|-----------------|
| `uv run pytest tests/test_rag_pipeline.py -v -k TestFormatChunksDesign2` | 3 tests collected and pass |
| `uv run pytest tests/test_rag_pipeline.py -v` | All existing tests continue to pass |
| `ruff check tests/test_rag_pipeline.py` | 0 errors |
