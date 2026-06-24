# Implementation Procedure: scripts/eventbus/schema.sql + docs/06_eventbus_90_inconsistencies_and_known_issues.md

## Goal

スキーマと実装の差異を明示した不整合ドキュメントを作成し、schema.sql に `acked_at` コメントを追加する。

## Scope

**In:**
- `scripts/eventbus/schema.sql` — `acked_at` にコメント追加 (110003 と統合)
- `docs/06_eventbus_90_inconsistencies_and_known_issues.md` (新規) — 既知の差異一覧

**Out:** ランタイム動作の変更

## Implementation

### docs/06_eventbus_90_inconsistencies_and_known_issues.md

```markdown
# Event Bus — 既知の不整合と課題

## スキーマ vs 実装の差異

| フィールド | スキーマ定義 | ランタイム | ステータス |
|---|---|---|---|
| `acked_at` | TEXT | 一切セットされない | Reserved/未使用 — schema.sql にコメントあり |
| `retry_count` | INTEGER DEFAULT 0 | publish フローでは加算されない | 要対応 (req 19 参照) |
| `/subscribe` | SSE エンドポイント | ポーリングベース (push ではない) | 設計上; ドキュメント済み |

## 未確認事項 (Needs Confirmation)

| 項目 | 確認方法 |
|---|---|
| `/health` の劣化時 HTTP ステータス (200 vs 503) | 運用要件の確認 |
| FastAPI スレッドプールワーカー使用有無 | アプリ起動設定の確認 |
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| コード変更なし | `git diff scripts/eventbus/*.py` | no changes |
