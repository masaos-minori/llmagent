# Issue: factory.py - Embedding dimension check method never called

## 概要

`StartupOrchestrator._check_embedding_dimensions()` メソッドが定義されているが、`_check_services()` から呼び出されていない。デッドコード。

## 該当コード

`scripts/agent/startup.py:171-187`

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

`_check_services()` の呼び出しリストには含まれていない。

## 問題点

- メモリ層の埋め込み次元とDBの次元が不一致の場合、起動時に検知されない
- 埋め込みの生成・検索時にランタイムエラーが発生する可能性がある
- メソッドが存在するため「チェック済み」という誤認を招く

## 改善案

- `_check_services()` に embedding_dimensions チェックを追加（既に存在するが、別のメソッドとして実装されている）
- または、このメソッドを削除してデッドコードを解消

## 優先度

中 - 起動時の検証が欠落しているが、ランタイムでも検知される可能性はある
