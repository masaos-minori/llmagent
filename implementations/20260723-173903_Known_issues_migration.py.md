## Goal

Normalize issue tracking format across all five major area Known Issues documents by migrating them to the common template defined in the governance documentation, preserving all existing entries and their technical meaning.

## Scope

**In**:
- Migrate 5 area Known Issues documents to the common template
- Preserve all existing entries and IDs
- Add missing fields (Status, Severity, Type, Area, Owner) using `未確認` where unknown
- Add migration notes with migration date and source format
- Preserve links to related governance documents

**Out**:
- Resolving any existing issues
- Adding new issues beyond migration status
- Changing the common template itself
- Modifying non-Known Issues documents

## Assumptions

1. The common Known Issues template exists in the governance documentation.
2. All five target Known Issues documents exist at their expected paths.
3. The recommended migration order (Agent → MCP → RAG → EventBus → Shared/DB) is correct.

## Design decisions

- Preserve original entry content verbatim; only reformat into the 17-field structure.
- Use `未確認` for any field that cannot be confidently determined from the existing document.
- Add migration note section at top of each migrated document with migration date and source format description.
- Keep front-matter unchanged unless it conflicts with the common template.

## Alternatives considered

- Rewrite entries to fit the 17-field structure exactly: risks losing nuance or introducing errors.
- Create a mapping layer instead of migrating: adds unnecessary complexity and maintenance burden.
- Migrate only high-severity entries first: delays normalization without clear benefit.

## Implementation

### Target file

5 area Known Issues documents: `docs/05_agent_90_inconsistencies_and_known_issues.md`, `docs/04_mcp_90_inconsistencies_and_known_issues.md`, `docs/03_rag_90_inconsistencies_and_known_issues.md`, `docs/06_eventbus_90_inconsistencies_and_known_issues.md`, `docs/90_shared_90_inconsistencies_and_known_issues.md`

### Procedure

1. Verify the common Known Issues template exists and is accessible at `docs/00_governance_04_known-issues-template.md`
2. Verify all five target documents exist at expected paths
3. For each document in order (Agent → MCP → RAG → EventBus → Shared/DB):
   a. Read the existing Known Issues document
   b. Map existing fields to the 17-field common template structure
   c. Fill missing fields with `未確認` where appropriate
   d. Add migration note section with migration date and source format description
   e. Write the migrated document

### Method

Reformat existing Known Issues entries into the 17-field common template structure.

### Details

For each entry in each document, map as follows:

```markdown
# Migration note (add after front-matter):

## 移行ノート

- 移行日: 2026-07-23
- 移行元フォーマット: 既存のバレット形式（Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference）
- 移行先フォーマット: 共通テンプレート（17フィールド）
- 注: 既存のエントリ内容は維持。不足フィールドは「未確認」で埋める。
```

Field mapping example for Agent Known Issues entry:

```markdown
### AGENT-001: use_memory_layer デフォルト値の文書間不一致

- **ID**: AGENT-001
- **Title**: use_memory_layer デフォルト値の文書間不一致
- **Status**: fixed
- **Severity**: Medium
- **Area**: Agent
- **Type**: document-document-mismatch
- **Source**: 05_agent_08_03, 05_agent_09_02, 05_agent_12_02_part1 vs 05_agent_08_01, 05_agent_12_05, 05_agent_13_part2
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: 05_agent_08_03, 05_agent_09_02, 05_agent_12_02_part1
- **Related**: 未確認
- **Summary**: use_memory_layer のデフォルト値について文書間で矛盾がある
- **Current Description**: 一部ドキュメントで False、他で True と記載
- **Observed Implementation**: コード上のデータクラスデフォルトは True
- **Impact**: 実装者と文書の理解の乖離
- **Recommended Action**: 05_agent_08_03, 05_agent_09_02, 05_agent_12_02_part1 を修正して True に統一
- **Resolution Notes**: 完了済み
```

## Compatibility considerations

None — documentation-only change; no behavioral impact.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

Restore original documents from git history; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Markdown rendering | Manual review | Correct rendering |
| Entry preservation | Manual review | All entries present |
| Template compliance | Manual review | Entries follow common template |

## Out of scope

- Resolving any existing issues
- Adding new issues beyond migration status
- Changing the common template itself
- Modifying non-Known Issues documents

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-165202_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-173903
- Related target files: Implementation-dependent — Known Issues documents
