## Goal

Add a Japanese governance policy section to `00_governance_06_ai-reading-metadata.md` defining how to handle implementation-derived details in design documents, including removal/compression criteria, preservation requirements, and a decision model for documentation cleanup.

## Scope

**In**:
- Add Japanese section `## 実装参照で確認できる情報の記載方針` to `00_governance_06_ai-reading-metadata.md`
- Define three subsections: Information Usually Removed or Compressed, Information That Must Be Kept, Decision Categories
- Define six decision categories: Remove, Compress, Replace with source reference, Keep, Move to Known Issues, Move to Needs Confirmation

**Out**:
- Creating any new governance document
- Editing any other documents
- Removing or compressing content in this phase

## Assumptions

1. `00_governance_06_ai-reading-metadata.md` exists at its expected path.
2. The existing governance document uses Japanese for non-front-matter content.

## Design decisions

- Append new section after the existing "Related Governance Documents" section rather than inserting mid-document.
- Use exact Japanese section heading as specified in the requirement.
- Preserve all existing content — no deletions or rewrites.
- Use "usually" language rather than absolute mandates to avoid being overly prescriptive.

## Alternatives considered

- Create a separate governance document for this policy: fragments governance unnecessarily.
- Modify existing sections instead of appending: increases diff churn and risk of conflicts.
- Use English headings: inconsistent with project's Japanese-first convention.

## Implementation

### Target file

`docs/00_governance_06_ai-reading-metadata.md`

### Procedure

1. Verify `00_governance_06_ai-reading-metadata.md` exists at expected path
2. Read the document and locate end of existing content
3. Append `## 実装参照で確認できる情報の記載方針` section with three subsections and six decision categories

### Method

Append new section to end of existing governance document.

### Details

```markdown
# In 00_governance_06_ai-reading-metadata.md (append):

## 実装参照で確認できる情報の記載方針

設計文書に実装詳細を記載するかどうかの判断基準。

### 通常削除または圧縮される情報

- ファイルパスや行番号レベルの実装詳細
- コードのインポート構造やモジュール依存関係の詳細
- 設定値のデフォルト値（コードで確認可能）
- 既存のファイル構造の列挙
- CLI引数の完全なリファレンス
- JSON例の冗長な記述
- APIスキーマの完全な定義

### 保持すべき情報

- 設計意図とアーキテクチャ判断の理由
- コンポーネント間の境界と責任分担
- エラー処理の設計判断
- パフォーマンスに関する設計判断
- セキュリティに関する設計判断
- 将来の拡張性に関する判断

### 判断カテゴリ

| カテゴリ | 適用条件 | 例 |
|---|---|---|
| 削除 | 実装だけで確認可能な詳細 | ファイルパス、行番号、インポート構造 |
| 圧縮 | 文脈は必要だが詳細は不要 | CLI引数 → 主要オプションのみ |
| ソース参照への置換 | 実装が唯一の正典 | スキーマ定義 → 「実装参照」 |
| 保持 | 設計判断や意図 | エラーハンドリングの設計判断 |
| 既知の問題へ移動 | 実装と文書の矛盾 | ドキュメントとコードの不一致 |
| Needs Confirmationへ移動 | 不明な事項 | 実装の意図が不明 |
```

## Compatibility considerations

None — only appends to existing document; no behavioral changes.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

Remove appended section from the document; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Markdown rendering | Manual review | Correct rendering |
| Governance consistency | Manual review | No contradictions with existing rules |

## Out of scope

- Creating any new governance document
- Editing any other documents
- Removing or compressing content in this phase

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-165444_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-174310
- Related target files: Implementation-dependent — governance documents
