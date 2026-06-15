# ローカル LLM + llama.cpp 高精度 RAG 実装手順書

> 本ファイルはドキュメント群の目次（インデックス）。
> 各ドキュメントの詳細は下記リンク先を参照。

## 実装リファレンス

| ファイル | 内容 |
|---|---|
| [01_overview.md](01_overview.md) | 概要（トップレベル） |
| [01_overview-arch.md](01_overview-arch.md) | システム全体アーキテクチャ |
| [01_overview-files.md](01_overview-files.md) | ファイル／モジュール構成 |
| [02_deployment.md](02_deployment.md) | 導入手順・デプロイ |
| [03_rag-ingestion-run.md](03_rag-ingestion-run.md) | 取込実行ガイド (コマンド・ファイルライフサイクル) |
| [03_spec_rag.md](03_spec_rag.md) | RAG スキーマ仕様 |
| [03_rag-ref-ingestion.md](03_rag-ref-ingestion.md) | RAG 取込 API リファレンス (web_crawler / chunk_splitter / rag_ingester) |
| [03_rag-ref-ingester.md](03_rag-ref-ingester.md) | rag_ingester 詳細 |
| [03_rag-ref-crawler.md](03_rag-ref-crawler.md) | web_crawler 詳細 |
| [03_rag-ref-splitter.md](03_rag-ref-splitter.md) | chunk_splitter 詳細 |
| [04_mcp-servers.md](04_mcp-servers.md) | MCP サーバ インデックス |
| [04_mcp-web-search.md](04_mcp-web-search.md) | web-search-mcp 詳細 |
| [04_mcp-file.md](04_mcp-file.md) | file-mcp 詳細 |
| [04_mcp-github.md](04_mcp-github.md) | github-mcp 詳細 |
| [04_mcp-sqlite.md](04_mcp-sqlite.md) | sqlite-mcp 詳細 |
| [04_mcp-shell.md](04_mcp-shell.md) | shell-mcp 詳細 |
| [04_mcp-git.md](04_mcp-git.md) | git-mcp 詳細 |
| [04_mcp-cicd.md](04_mcp-cicd.md) | cicd-mcp 詳細 |
| [04_mcp-mdq.md](04_mcp-mdq.md) | mdq-mcp 詳細 |
| [04_mcp-rag.md](04_mcp-rag.md) | rag-pipeline-mcp 詳細 |
| [04_mcp-protocol.md](04_mcp-protocol.md) | HTTP API / トランスポート / 追加手順 |
| [04_spec_mcp.md](04_spec_mcp.md) | MCP プロトコル仕様 |
| [05_agent.md](05_agent.md) | エージェント ツール仕様・チューニング・実装注意 |
| [05_spec_agent.md](05_spec_agent.md) | エージェント仕様 |
| [05_agent-ops.md](05_agent-ops.md) | エージェント 起動・確認・トラブルシューティング |
| [05_agent-impl-flow.md](05_agent-impl-flow.md) | エージェント実装詳細 - フロー |
| [05_agent-impl-class.md](05_agent-impl-class.md) | エージェント実装詳細 - クラス |
| [05_ref-agent-context.md](05_ref-agent-context.md) | AgentContext / AppServices 詳細 |
| [05_ref-agent-session.md](05_ref-agent-session.md) | AgentSession 詳細 |
| [05_ref-agent-commands.md](05_ref-agent-commands.md) | コマンドレジストリ詳細 |
| [05_ref-agent-view.md](05_ref-agent-view.md) | CLI ビュー詳細 |
| [06_shared.md](06_shared.md) | 共通モジュール インデックス |
| [06_spec_shared.md](06_spec_shared.md) | 共有モジュール仕様 |
| [06_ref-infra.md](06_ref-infra.md) | インフラ共通モジュール (shared/config_loader / rag/utils / formatters) |
| [06_ref-mcp.md](06_ref-mcp.md) | MCP プロトコル層モジュール (mcp/models.py / shared/tool_executor.py 等) |
| [05_ref-rag.md](05_ref-rag.md) | RAG パイプラインモジュール (rag/pipeline.py) |
| [05_ref-agent-config.md](05_ref-agent-config.md) | AgentConfig / MemoryConfig / MCPConfig 詳細 |
| [05_ref-agent-llm.md](05_ref-agent-llm.md) | LLMClient (SSE ストリーミング・リトライ) 詳細 |
| [05_ref-agent-repl.md](05_ref-agent-repl.md) | AgentREPL / Orchestrator / ToolExecutor 詳細 |
| [05_ref-agent-history.md](05_ref-agent-history.md) | HistoryManager (会話履歴管理) 詳細 |
| [07_spec_db.md](07_spec_db.md) | DB スキーマ仕様 |
| [07_ref-sqlite.md](07_ref-sqlite.md) | db/helper.py (DB 接続・WAL・トランザクション) |
