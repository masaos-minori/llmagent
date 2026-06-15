# Implementation: Phase E — history.py compress failure fail-fast

## Goal

`agent/history.py` の `_compress_with_llm()` で、LLM API 失敗時に
`logger.warning + return None` で継続するのをやめ、
`HistoryCompressionError` を raise して呼び出し側に通知する。

## Scope

**In**: `scripts/agent/history.py` の `_compress_with_llm()` メソッド
**Out**: `force_compress()` のシグネチャは変更しない。
  呼び出し側 (`cmd_ingest.py`) も変更して例外を適切に処理する。

## Assumptions

1. `HistoryCompressionError` は `agent/history.py` または
   `agent/exceptions.py` に定義する。
2. `cmd_ingest.py` の `/compact` コマンドが `HistoryCompressionError` を
   キャッチして `self._out.write_error(...)` で表示する。
3. 空 summary（`"Context compression: LLM returned empty summary"`）も
   エラーとして扱う。

## Implementation

### Target files

- `scripts/agent/history.py`
- `scripts/agent/commands/cmd_ingest.py`

### Method

**history.py**:

```python
# 追加: モジュールレベル例外定義
class HistoryCompressionError(RuntimeError):
    """Raised when LLM-based history compression fails."""

# _compress_with_llm() の変更:
# 変更前
except (httpx.HTTPError, orjson.JSONDecodeError, KeyError, TypeError) as e:
    logger.warning("Context compression failed: %s", e)
    return None

# 変更後
except (httpx.HTTPError, orjson.JSONDecodeError, KeyError, TypeError) as e:
    raise HistoryCompressionError(f"Context compression failed: {e}") from e

# 空 summary も例外化:
# 変更前
if not raw_content:
    logger.warning("Context compression: LLM returned empty summary")
    return None

# 変更後
if not raw_content:
    raise HistoryCompressionError("Context compression: LLM returned empty summary")
```

**cmd_ingest.py**:

```python
# _cmd_compact() の変更:
try:
    ctx.conv.history = await ctx.services.hist_mgr.force_compress(ctx.conv.history)
    self._out.write_success("History compacted.")
except HistoryCompressionError as e:
    self._out.write_error(f"Compression failed: {e}")
```

## Validation plan

1. `ruff check scripts/agent/history.py scripts/agent/commands/cmd_ingest.py`
2. `uv run mypy scripts/`
3. `uv run pytest -q` → no regressions
