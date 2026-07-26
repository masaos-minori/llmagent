---
title: "Scripts File Structure: Agent Core & Memory (Part 1/5)"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts-part2.md
  - 01_overview-files-03-scripts-part3.md
  - 01_overview-files-03-scripts-part4.md
  - 01_overview-files-03-scripts-part5.md
  - 01_overview.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

### 主要ディレクトリと責務

#### エージェント REPL パッケージ (`scripts/agent/`)

| 責務 | ファイル群 |
|---|---|
| エントリポイント | `__main__.py`, `repl.py` |
| 起動シーケンス | `startup.py`, `context.py` |
| 設定 | `config_builders.py`, `config_dataclasses.py` |
| セッション管理 | `session.py`, `session_message_repo.py` |
| ターン制御 | `orchestrator.py`, `llm_turn_runner.py` |
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
| ツール列挙型 | `tool_enums.py` |
| ツールデータモデル | `tool_models.py` |
| ツール引数検証 | `tool_arg_validator.py` |
| メッセージスキーマ | `message_schema.py` |
| ターン結果 | `turn_result.py` |

#### メモリサブパッケージ (`scripts/agent/memory/`)

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

### 変更時の注意点

- セッション永続化のスキーマ変更時は `store.py` と `sql_constants.py` を併せて確認
- ツール承認フローの変更時は `tool_approval.py` と `repository_gateway.py` の両方を確認
- メモリ検索アルゴリズムの変更時は `retriever.py` と `scoring.py` を併せて確認

### 実装詳細の参照先

完全なファイル一覧はリポジトリの実装ツリーを参照する。

## Related Documents

- `01_overview-files-03-scripts-part2.md`
- `01_overview-files-03-scripts-part3.md`
- `01_overview-files-03-scripts-part4.md`
- `01_overview-files-03-scripts-part5.md`

## Keywords

scripts
agent
mcp-server
file-structure
