---
title: "リポジトリ書き込みのポリシープリフライトチェックスキップ"
created: 2026-07-31
severity: medium
area: scripts/agent/repository_gateway.py
status: open
---

## 概要

`repository_gateway.py` で `policy_check_required` がFalseの場合、リポジトリ書き込みがプリフライトチェックなしで許可される。これは意図的かもしれないが、ドキュメント化が必要。

## 証拠

```python
# scripts/agent/repository_gateway.py

if not policy_check_required:
    return True  # チェックなしで許可
```

## 影響

- ポリシーチェックがスキップされた書き込みが検知されない
- セキュリティリスク（意図しないファイル変更）
- 監査証跡の不整合

## 再現手順

1. `policy_check_required` がFalseの条件を満たす構成にする
2. リポジトリ書き込みを試みる
3. プリフライトチェックがスキップされ、書き込みが許可される
4. 意図しないファイル変更が発生する可能性がある

## 修正案

```python
async def write_to_repository(self, path: str, content: str, policy_check_required: bool = False):
    # スキップする場合でもログ出力
    if not policy_check_required:
        logger.info(
            f"Skipping policy check for write to {path} "
            "(policy_check_required=False)"
        )
    
    # チェックが必要な場合は明示的に実行
    if policy_check_required:
        await self._check_policy(path, content)
    
    # 書き込み処理
    await self._perform_write(path, content)
```

`policy_check_required` がFalseの場合でも、ログ出力を追加し、意図的な動作であることを明確にする。また、このパラメータのデフォルト値を `True` に変更することも検討する。

## 関連ファイル

- `scripts/agent/repository_gateway.py`: write_to_repository(), _check_policy()
- `scripts/agent/tool_policy.py`: ツールリスク分類
