# Issue: factory.py - Memory branch resolution silently falls back to global scope

## 概要

メモリサービスのブランチコンテキスト解決で、Gitレポジトリの情報取得に失敗した場合、ブランチが空文字列（グローバルスコープ）にフォールバックする。警告やエラーログは一切出力されない。

## 該当コード

`scripts/agent/factory.py:297-301`

```python
# Resolve branch context at build time; default to "" (global) on any failure.
_git = get_repo_info()
_branch = ""
if _git.success and _git.data:
    _raw = _git.data.get("branch", "")
    _branch = "" if _raw == "HEAD (detached)" else _raw
```

## 問題点

- `get_repo_info()` が失敗した場合、`_git.success` が False になり `_branch = ""` が適用される
- このフォールバックは「静かに」行われ、警告ログも出力されない
- オペレーターはブランチスコープのメモリ注入が無効になっていることに気づかない
- 「グローバルスコープ」にフォールバックすることで、意図しないメモリが注入されるリスク

## 再現シナリオ

1. Gitレポジトリでないディレクトリでエージェントを実行
2. `get_repo_info()` が失敗
3. `_branch = ""` が適用される
4. メモリ注入がグローバルスコープで行われる（意図しないメモリが注入される可能性）
5. オペレーターは何のエラーもなく、動作を確認できる

## 改善案

- `get_repo_info()` が失敗した場合、WARNINGレベルでログ出力
- または、フォールバック先を明示的にドキュメントし、デフォルト値を変更する

```python
if _git.success and _git.data:
    _raw = _git.data.get("branch", "")
    _branch = "" if _raw == "HEAD (detached)" else _raw
else:
    logger.warning(
        "Memory branch resolution failed: %s. Using global scope.",
        str(_git.error) if hasattr(_git, 'error') else "unknown error",
    )
```

## 優先度

中 - 意図しないメモリ注入の原因となりうる
