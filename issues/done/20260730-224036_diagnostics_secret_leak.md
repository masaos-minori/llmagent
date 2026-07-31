# 診断情報の保存時に機密データが漏洩する可能性がある

## Summary

セッションダイアグノスティクスに `artifacts` (URI配列) と `rag_stage_outcomes` が含まれる。これらのフィールドには機密情報（ファイルパス、検索結果）が含まれる可能性があるが、暗号化なしで `DiagnosticStore.save()` に渡される。`encryption_key` が空の場合、機密データが平文で保存される。

## Severity

Medium

## Confidence

Medium

## Evidence

- `agent/repl.py:206-235` — セッションダイアグノスティクスに `artifacts` (URI配列) と `rag_stage_outcomes` が含まれる
- これらのフィールドには機密情報（ファイルパス、検索結果）が含まれる可能性がある
- `logger.warning()` で「機密フィールドを含む」という警告が出るが、データ自体は暗号化なしで `DiagnosticStore.save()` に渡される
- `encryption_key` が空の場合、機密データが平文で保存される

## Current behavior

`artifacts` や `rag_stage_outcomes` が存在する場合、`logger.warning()` で「機密フィールドを含む」という警告が出るが、データ自体は暗号化なしで `DiagnosticStore.save()` に渡される。

## Impact

- 診断情報が暗号化されていない状態で永続化される
- `encryption_key` が空の場合、機密データが平文で保存される
- セキュリティポリシー違反の可能性

## Recommended action

- ダイアグノスティクス保存時に `encrypt=True` を強制する
- または `artifacts`/`rag_stage_outcomes` フィールドを暗号化する

## Suggested Tests

- **Test target:** `agent/repl.py::AgentREPL._save_session_diagnostic()`
- **Behavior to verify:** `encryption_key` が設定されている場合、機密フィールドが暗号化されて保存されること
- **Failure mode:** `encryption_key` が空の場合、機密データが平文で保存される
