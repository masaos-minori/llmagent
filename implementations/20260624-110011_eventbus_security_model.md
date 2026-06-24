# Implementation Procedure: docs/06_eventbus_01_system-overview.md

## Goal

Event Bus が認証・ACL なしで動作する設計前提を明文化する。

## Scope

**In:**
- `docs/06_eventbus_01_system-overview.md` (新規作成時) — セキュリティモデルセクション追加

**Out:** 認証・ACL の実装

## Implementation

### セキュリティモデルセクション (docs に追加)

```markdown
## セキュリティモデル

Event Bus API は **認証・ACL 機能を持たない**。

- **設計前提**: 内部ネットワーク / 信頼済みホスト上での単独デプロイ
- **アクセス制御**: ネットワーク境界 (ファイアウォール、Docker ネットワーク) で担保
- **公開エンドポイント禁止**: インターネットに直接公開しないこと

### 将来の認証対応

将来的な要件が生じた場合:
- FastAPI の `Depends` による API キー認証
- mTLS によるサービス間認証

現時点では未実装 (Needs confirmation: 実際の脅威モデルに基づいて判断すること)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| コード変更なし | `git diff scripts/` | no changes |
