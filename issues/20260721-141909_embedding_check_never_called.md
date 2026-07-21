# Issue: startup.py - Embedding dimension mismatch check exists but is never invoked

## 概要

`StartupOrchestrator._check_embedding_dimensions()` メソッドが定義されており、メモリ層の埋め込み次元とDBの次元の不一致を検出できるが、このメソッドは `_check_services()` から呼び出されていない。つまり、このチェックは実行されない。

## 該当コード

`scripts/agent/startup.py:171-187` — メソッド定義:

```python
def _check_embedding_dimensions(self) -> None:
    """Verify embedding dimension consistency between memory config and db config."""
    from db.config import build_db_config  # noqa: PLC0415 — lazy

    ctx = self._ctx
    memory_dim = ctx.cfg.memory.memory_embed_dim
    db_dim = build_db_config().embedding_dims
    if memory_dim != db_dim:
        logger.error(
            "Embedding dimension mismatch: memory=%d, db=%d. Fix config/memory.toml or db/config.py.",
            memory_dim,
            db_dim,
        )
        raise RuntimeError(
            f"Embedding dimension mismatch: memory={memory_dim}, db={db_dim}"
        )
    logger.info("Embedding dimensions consistent: %d", memory_dim)
```

`_check_services()` の呼び出しリスト（189-287行目）には含まれていない。

## 問題点

- メモリ層の埋め込みベクトル次元とDBの次元が不一致の場合、起動時に検知されない
- 埋め込みの生成・検索時にランタイムエラーが発生する可能性がある
- メソッドがプライベート（`_`プレフィックス）かつ非公開のため、外部からテストできない
- 「チェック済み」という誤認を招く（メソッドが存在するため）

## 再現シナリオ

1. `config/memory.toml` で `memory_embed_dim = 768` を設定
2. `db/config.py` で `embedding_dims = 384` を設定
3. エージェント起動 — `_check_embedding_dimensions()` が呼ばれない
4. 埋め込み生成時に次元不一致エラーが発生
5. エラーメッセージからは設定ファイルの不一致に気づきにくい

## 改善案

- `_check_services()` に `_check_embedding_dimensions()` の呼び出しを追加
- または、このメソッドを削除してデッドコードを解消

```python
async def _check_services(self) -> None:
    # ... existing checks ...

    # Embedding dimensions
    try:
        self._check_embedding_dimensions()
        pipeline.add_ok("embedding_dimensions")
    except RuntimeError as exc:
        pipeline.add_fatal("embedding_dimensions", str(exc))

    # ... rest of checks ...
```

## 優先度

高 - 起動時の検証が欠落しており、ランタイムエラーの原因となる
