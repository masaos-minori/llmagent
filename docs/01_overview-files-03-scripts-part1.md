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

デプロイ先のディレクトリ構成:


``` text
/opt/llm/
├─ scripts/
│   ├─ agent/                               # エージェント REPL パッケージ
│   │   ├─ __init__.py                      # agent パッケージ初期化
│   │   ├─ __main__.py                      # python -m agent エントリポイント
│   │   ├─ repl.py                          # AgentREPL: 全コンポーネントを AgentContext に注入し REPL ループを駆動
│   │   ├─ startup.py                       # StartupOrchestrator: 起動シーケンス
│   │   ├─ config_builders.py               # 設定ビルダ群
│   │   ├─ config_dataclasses.py            # 設定データクラス
│   │   ├─ context.py                       # AgentContext: per-session mutable state / DI ハブ
│   │   ├─ session.py                       # AgentSession: セッション CRUD (SQLite 永続化)
│   │   ├─ session_message_repo.py          # セッションメッセージリポジトリ
│   │   ├─ security_audit_config.py         # セキュリティ監査用 MCP サーバ設定モデル narrow API
│   │   ├─ history.py                       # 会話履歴バッファ・圧縮フック
│   │   ├─ history_selection_policy.py      # 履歴圧縮選択ポリシー
│   │   ├─ orchestrator.py                  # Orchestrator: ターンレベル制御 (RAG → 圧縮 → LLM → ツール)
│   │   ├─ llm_turn_runner.py               # LLMTurnRunner: SSE ストリーミング + ツールループ
│   │   ├─ tool_loop_guard.py               # ToolLoopGuard: dedup/cycle/retry/error ガード
│   │   ├─ tool_runner.py                   # ツール実行
│   │   ├─ tool_scheduler.py                # ツールスケジューラ (並列/直列)
│   │   ├─ tool_policy.py                   # ツールポリシー
│   │   ├─ tool_approval.py                 # ツール承認
│   │   ├─ tool_audit.py                    # ツール監査
│   │   ├─ tool_enums.py                    # ツール列挙型
│   │   ├─ tool_exceptions.py               # ツール例外定義
│   │   ├─ tool_models.py                   # ツールデータモデル
│   │   ├─ tool_output.py                   # ツール出力フォーマット
│   │   ├─ output_tags.py                   # OutputTag: REPL/CLI 出力の角括弧プレフィックス列挙型 ([warn]/[fatal]/[error] 等)
│   │   ├─ tool_result_formatter.py         # ツール結果整形
│   │   ├─ repository_gateway.py            # RepositoryGateway: 書込/削除/API-write の単一強制境界 (policy → approval → exec → audit)
│   │   ├─ turn_result.py                   # ターン結果データクラス
│   │   ├─ diagnostic_store.py              # 部分完了診断情報保存
│   │   ├─ error_injection_service.py       # エラー注入サービス
│   │   ├─ mdq_rag_classifier.py            # MDQ RAG 分類エンジン
│   │   ├─ mode_classification.py           # MDQ/RAG モード分類 + システムプロンプト注入
│   │   ├─ lifecycle_protocol.py            # ライフサイクルプロトコル
│   │   ├─ llm_transport_errors.py          # LLM トランスポートエラー処理
│   │   ├─ lifecycle.py                     # LifecycleState enum
│   │   ├─ http_lifecycle.py                # HTTP ライフサイクル管理
│   │   ├─ repl_health.py                   # ヘルスチェックサテライト
│   │   ├─ cli_view.py                      # CLIView: readline 設定・RAG 進捗表示・マルチライン入力
│   │   ├─ factory.py                       # AgentFactory: エージェントコンポーネント構築
│   │   ├─ memory/
│   │   │   └─ __init__.py                  # memory パッケージ初期化
│   │   │   ├─ types.py                     # MemoryEntry / MemoryQuery / MemoryHit / EmbeddingResult データクラス
│   │   │   ├─ services.py                  # MemoryServices: memory サブサービスコンテナ (AppServices.memory の型)
│   │   │   ├─ store.py                     # MemoryStore: SQLite CRUD (`memories` / `memories_fts` / `memories_vec`)
│   │   │   ├─ retriever.py                 # FtsRetriever / VectorRetriever / HybridRetriever: FTS5 + KNN RRF 検索
│   │   │   ├─ extract.py                   # extract_memories(): ルールベース履歴抽出
│   │   │   ├─ jsonl_store.py               # JsonlMemoryStore: 追記専用 JSONL ソース (write() 1 本)
│   │   │   ├─ embedding_client.py          # 埋め込みクライアント
│   │   │   ├─ ingestion.py                 # メモリ取り込み
│   │   │   ├─ injection.py                 # メモリ注入
│   │   │   ├─ mapper.py                    # メモリマッパー
│   │   │   ├─ enums.py                     # メモリ列挙型
│   │   │   ├─ exceptions.py                # メモリ例外定義
│   │   │   ├─ models.py                    # HistoryMessage / JsonlRecord / ConsistencyReport / MemorySnippet データクラス
│   │   │   ├─ count_ops.py                 # memories テーブルの行数カウント (type/source_type 別)
│   │   │   ├─ write_ops.py                 # メモリ書き込み操作
│   │   │   ├─ pin_ops.py                   # メモリピン留め操作
│   │   │   ├─ import_ops.py                # メモリインポート操作
│   │   │   ├─ rebuild_ops.py               # メモリ再構築操作
│   │   │   ├─ fts_query.py                 # FTS クエリヘルパー
│   │   │   ├─ scoring.py                   # メモリスコアリング
│   │   │   ├─ rrf.py                       # RRF (Reciprocal Rank Fusion) マージ
│   │   │   └─ sql_constants.py             # SQL定数
```

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
