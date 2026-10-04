# HIGH: MCP サーバー呼出のエッジケーステストカバレッジ不足

## Priority
High

## Summary
MCP サーバー呼出関連の複雑なパス（リトライ exhausted、セマフォ競合、strict_mode エラー）に対するユニットテストが存在するか不明。

## Background
以下のファイルの複雑なパスに対するテストカバレッジを確認する必要あり：
- `scripts/shared/http_transport.py` — retry ロジック
- `scripts/shared/tool_transport_invoker.py` — セマフォ処理
- `scripts/shared/route_resolver.py` — strict_mode パス

## Problem
エッジケース発生時にこれらのパスが正しく動作する保証がない。

## Evidence
- 各ファイルのテストファイルの有無を確認する必要あり
- 現在のテストカバレッジレポートを確認する必要あり

## Impact
- 本番環境でのエッジケース発生時に、予期せぬ挙動の可能性
- 障害復旧時間の増加

## Acceptance Criteria
- [ ] リトライ exhausted パスのユニットテスト追加
- [ ] セマフォ競合時の挙動テスト追加
- [ ] strict_mode/non-strict_mode のエラーメッセージ差異テスト追加
- [ ] テストカバレッジレポートを更新

## Related Tests
- `tests/tools/test_check_needs_confirmation_inventory.py`
- 該当する MCP トランスポートテスト

## Related Files
- `scripts/shared/http_transport.py`
- `scripts/shared/tool_transport_invoker.py`
- `scripts/shared/route_resolver.py`
