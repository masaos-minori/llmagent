## Goal

Compress implementation-derived file structure listings in seven overview documents into Japanese responsibility-oriented summaries while preserving architectural context, responsibility boundaries, and operational constraints.

## Scope

**In**:
- Compress detailed file-by-file listings in 7 overview documents
- Replace with Japanese responsibility-oriented summaries under suggested section headings (`## 主要ディレクトリと責務`, `## レイヤー境界`, `## 変更時の注意点`, `## 実装詳細の参照先`)
- Add source reference note: "完全なファイル一覧はリポジトリの実装ツリーを参照する"

**Out**:
- Modifying source code
- Creating ADR documents
- Modifying `00_index.md`
- Removing design intent, responsibility boundaries, invariants, failure behavior, or operational constraints

## Assumptions

1. All seven target documents exist at their expected paths.
2. The existing file listings can be safely compressed without losing design-relevant information.

## Design decisions

- Group files by responsibility rather than listing them individually.
- Use exact Japanese section headings as specified in the requirement where they improve clarity.
- Preserve all design-relevant content; only compress implementation-level details.
- Add source reference note after the compressed summary.

## Alternatives considered

- Delete file listings entirely: loses architectural context that operators need.
- Keep full listings but add navigation links: doesn't reduce cognitive load.
- Create separate implementation detail documents: fragments documentation unnecessarily.

## Implementation

### Target file

7 overview documents: `docs/01_overview-files-03-scripts-part1.md`, `docs/01_overview-files-03-scripts-part2.md`, `docs/01_overview-files-03-scripts-part3.md`, `docs/01_overview-files-03-scripts-part4.md`, `docs/01_overview-files-03-scripts-part5.md`, `docs/01_overview-files-04-shared-part1.md`, `docs/01_overview-files-04-shared-part2.md`

### Procedure

1. Verify all seven target documents exist at expected paths
2. For each document:
   a. Read the document and identify the file listing section
   b. Assess which files contain design-relevant information vs. pure implementation details
   c. Compress file-by-file listings into responsibility-oriented summaries
   d. Apply suggested section headings where appropriate
   e. Add source reference note

### Method

Replace detailed file-by-file tree listings with responsibility-oriented groupings.

### Details

For Part 1 (Agent Core & Memory), replace the detailed tree listing with:

```markdown
## 主要ディレクトリと責務

### エージェント REPL パッケージ (`scripts/agent/`)

| 責務 | ファイル群 |
|---|---|
| エントリポイント | `__main__.py`, `repl.py` |
| 起動シーケンス | `startup.py`, `context.py` |
| 設定 | `config_builders.py`, `config_dataclasses.py` |
| セッション管理 | `session.py`, `session_message_repo.py` |
| ツーン制御 | `orchestrator.py`, `llm_turn_runner.py` |
| ツール実行 | `tool_runner.py`, `tool_scheduler.py`, `tool_policy.py`, `tool_approval.py` |
| ツールガード | `tool_loop_guard.py` |
| ツール監査 | `security_audit_config.py`, `tool_audit.py` |
| 出力フォーマット | `output_tags.py`, `tool_output.py`, `tool_result_formatter.py` |
| エラー処理 | `llm_transport_errors.py`, `tool_exceptions.py`, `error_injection_service.py` |
| ライフサイクル | `lifecycle.py`, `lifecycle_protocol.py`, `http_lifecycle.py`, `repl_health.py` |
| CLI | `cli_view.py` |
| コンポーネント構築 | `factory.py` |
| 診断 | `diagnostic_store.py` |
| モード分類 | `mdq_rag_classifier.py`, `mode_classification.py` |
| 会話履歴 | `history.py`, `history_selection_policy.py` |

### メモリサブパッケージ (`scripts/agent/memory/`)

| 責務 | ファイル群 |
|---|---|
| データモデル | `types.py`, `models.py`, `enums.py` |
| ストレージ | `store.py`, `jsonl_store.py` |
| 検索 | `retriever.py`, `fts_query.py` |
| 埋め込み | `embedding_client.py` |
| 取り込み | `ingestion.py` |
| 注入 | `injection.py` |
| マッピング | `mapper.py` |
| スコアリング | `scoring.py`, `rrf.py` |
| 操作 | `count_ops.py`, `write_ops.py`, `pin_ops.py`, `import_ops.py`, `rebuild_ops.py` |
| 定数 | `sql_constants.py` |

## 変更時の注意点

- セッション永続化のスキーマ変更時は `store.py` と `sql_constants.py` を併せて確認
- ツール承認フローの変更時は `tool_approval.py` と `repository_gateway.py` の両方を確認
- メモリ検索アルゴリズムの変更時は `retriever.py` と `scoring.py` を併せて確認

## 実装詳細の参照先

完全なファイル一覧はリポジトリの実装ツリーを参照する。
```

Apply similar compression to remaining six documents following the same pattern.

## Compatibility considerations

None — documentation-only change; no behavioral impact.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

Restore original file listings from git history; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Markdown rendering | Manual review | Correct rendering |
| Content preservation | Manual review | No design-relevant content loss |
| Listing reduction | Manual review | Significant reduction achieved |

## Out of scope

- Modifying source code
- Creating ADR documents
- Modifying `00_index.md`
- Removing design intent, responsibility boundaries, invariants, failure behavior, or operational constraints

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-165550_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-174501
- Related target files: Implementation-dependent — overview documents
