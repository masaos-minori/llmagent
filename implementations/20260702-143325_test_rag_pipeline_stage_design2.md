# Implementation: Add DESIGN-2 tests to TestAugmentStage in test_rag_pipeline_stage.py

## Goal

Add two async test methods to the existing `TestAugmentStage` class in
`tests/test_rag_pipeline_stage.py` that assert `AugmentStage` (via `augment._format_chunks`)
injects only `content`, never any "normalized" text, into `ctx.augment_result`
(TEST-DESIGN2-01 and TEST-DESIGN2-03).

## Scope

- **Target file:** `tests/test_rag_pipeline_stage.py`
- **Change type:** Additive — two new methods appended to `TestAugmentStage`; no
  existing tests modified.
- **Production code:** No changes.

## Assumptions

1. `AugmentStage.run()` calls `augment._format_chunks(ctx.reranked)` and stores the
   result in `ctx.augment_result` — confirmed by reading
   `scripts/rag/stages/augment.py`.
2. `augment._format_chunks` uses `c.content` (line 16: `sanitize_document(c.content)`) —
   confirmed by reading `scripts/rag/stages/augment.py`.
3. `RankedHit` is NOT imported at the top of `test_rag_pipeline_stage.py`. The existing
   test `test_augment_formats_hits_into_block` imports it inline
   (`from rag.types import RankedHit` inside the method body). The two new methods must
   follow the same pattern.
4. `PipelineContext` and `AugmentStage` are already imported at the top of the file.

## Implementation

### Target file

`tests/test_rag_pipeline_stage.py`

### Procedure

1. Open `tests/test_rag_pipeline_stage.py`.
2. Locate the end of `TestAugmentStage` class. The last method is
   `test_augment_formats_hits_into_block` (ends around line 258).
3. Append the two new methods inside the `TestAugmentStage` class body, after
   `test_augment_formats_hits_into_block` and before the
   `# ── RagPipeline.last_timings` comment block.

### Method

Append the following two methods to `TestAugmentStage`:

```python
    @pytest.mark.asyncio
    async def test_augment_stage_content_only_invariant(self) -> None:
        """TEST-DESIGN2-01: AugmentStage must output content only, not
        normalized_content.

        Simulates a Japanese chunk where content='日本語テキスト' and
        normalized_content would be 'にほんご テキスト'. Because RagHit carries
        only content, the forbidden string must never appear in augment_result.
        """
        from rag.types import RankedHit

        stage = AugmentStage()
        ctx = PipelineContext(query="q")
        ctx.reranked = [  # type: ignore[assignment]
            RankedHit(
                chunk_id=1,
                content="日本語テキスト",
                url="http://example.com",
                title="",
            )
        ]
        await stage.run(ctx)
        assert "日本語テキスト" in ctx.augment_result
        assert "にほんご テキスト" not in ctx.augment_result

    @pytest.mark.asyncio
    async def test_augment_stage_normalized_does_not_leak(self) -> None:
        """TEST-DESIGN2-03: LLM context must not contain normalized_content
        when it differs from content.

        content='検索結果', simulated normalized_content='けんさく けっか'.
        """
        from rag.types import RankedHit

        stage = AugmentStage()
        ctx = PipelineContext(query="q")
        forbidden = "けんさく けっか"
        ctx.reranked = [  # type: ignore[assignment]
            RankedHit(
                chunk_id=2,
                content="検索結果",
                url="http://example.com",
                title="",
            )
        ]
        await stage.run(ctx)
        assert "検索結果" in ctx.augment_result
        assert forbidden not in ctx.augment_result
```

### Details

- Both methods use inline `from rag.types import RankedHit` to match the style of the
  existing `test_augment_formats_hits_into_block` method in the same class.
- `# type: ignore[assignment]` on `ctx.reranked = [...]` matches the existing test
  pattern (line 255 of the original file).
- The docstrings reference TEST-DESIGN2-01 and TEST-DESIGN2-03 to make the intent
  traceable to the design document.
- No new top-level imports are needed.

## Validation plan

| Command | Expected outcome |
|---------|-----------------|
| `uv run pytest tests/test_rag_pipeline_stage.py -v -k TestAugmentStage` | 4 tests collected (2 existing + 2 new), all pass |
| `uv run pytest tests/test_rag_pipeline_stage.py -v` | All tests pass |
| `ruff check tests/test_rag_pipeline_stage.py` | 0 errors |
