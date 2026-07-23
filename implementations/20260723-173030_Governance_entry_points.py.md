## Goal

Strengthen governance rules for canonical entry points and AI-readable Markdown formatting by adding a Japanese area entry-point table and a Japanese Markdown formatting rule section to existing governance documents.

## Scope

**In**:
- Add Japanese section `## 領域別の正典入口` to `00_governance_02_canonical-source-rule.md` with area entry-point table
- Add Japanese section `## Markdown記法ルール` to `00_governance_06_ai-reading-metadata.md` with code block, table, keyword, and document boundary guidance

**Out**:
- Creating `00_canonical_sources.md`
- Creating a new Markdown formatting governance file
- Modifying `00_index.md`
- Introducing ADR documents
- Changing any other governance documents

## Assumptions

1. Both governance documents exist and are accessible at their expected paths.
2. The existing governance documents use Japanese for non-front-matter content.
3. The area entry-point table values are correct as stated in the requirement.

## Design decisions

- Append new sections to end of existing documents rather than inserting mid-document to minimize diff churn.
- Use exact section headings specified in the requirement.
- Preserve all existing content — no deletions or rewrites.

## Alternatives considered

- Create new governance file for area entry points: adds navigation overhead for operators.
- Modify `00_index.md`: increases blast radius beyond scope.
- Rewrite existing documents: unnecessary churn when append-only is sufficient.

## Implementation

### Target file

`docs/00_governance_02_canonical-source-rule.md`, `docs/00_governance_06_ai-reading-metadata.md`

### Procedure

1. Verify both governance documents exist at expected paths
2. Read `00_governance_02_canonical-source-rule.md` and locate end of document
3. Append `## 領域別の正典入口` section with area entry-point table to `00_governance_02_canonical-source-rule.md`
4. Read `00_governance_06_ai-reading-metadata.md` and locate end of document
5. Append `## Markdown記法ルール` section with subsections (code block, table, keyword, document boundary) to `00_governance_06_ai-reading-metadata.md`

### Method

Append new sections to end of existing governance documents.

### Details

```markdown
# In 00_governance_02_canonical-source-rule.md (append):

## 領域別の正典入口

| 領域 | 正典 |
|---|---|
| エージェント | `scripts/agent/` |
| MCP サーバー | `mcp_servers/` |
| DB | `db/` |
| RAG | `rag/` |
| シェアード | `scripts/shared/` |
| テスト | `tests/` |
| ルール | `rules/` |
| ドキュメント | `docs/` |
| ADR | `adr/` |
| 設定 | `config/` |
| スクリプト | `scripts/` |
| デプロイ | `deploy/` |
```

```markdown
# In 00_governance_06_ai-reading-metadata.md (append):

## Markdown記法ルール

### コードブロック
- Pythonコードは ```python で囲む
- Shellコマンドは ```bash で囲む
- JSONは ```json で囲む

### テーブル
- 日本語見出しは日本語で記載
- 技術用語は原文（英語）を併記

### キーワード
- 必須事項: 必須、禁止、必ず
- 推奨事項: 推奨、すべき、避けるべき
- 任意事項: 任意、必要に応じて

### ドキュメントの境界
- 各セクションは `##` で区切る
- セクション内にセクションは入れない
- 空行でセクションを明確に分離
```

## Compatibility considerations

None — only appends to existing documents; no behavioral changes.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

Remove appended sections from both documents; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Markdown rendering | Manual review | Correct rendering |
| Governance consistency | Manual review | No contradictions with existing rules |

## Out of scope

- Creating `00_canonical_sources.md`
- Creating a new Markdown formatting governance file
- Modifying `00_index.md`
- Introducing ADR documents
- Changing any other governance documents

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-164934_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-173030
- Related target files: Implementation-dependent — governance documents
