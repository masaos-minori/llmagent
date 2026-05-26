# ローカル LLM + llama.cpp 高精度 RAG 実装手順書

> 本ファイルはドキュメント群の目次（インデックス）。
> 各ドキュメントの詳細は下記リンク先を参照。

## 実装リファレンス

| ファイル | 内容 |
|---|---|
| [01_overview.md](01_overview.md) | 概要・アーキテクチャ・ファイル構成 |
| [02_deployment.md](02_deployment.md) | 導入手順・デプロイ |
| [03_ingestion-pipeline.md](03_ingestion-pipeline.md) | 取込パイプライン インデックス |
| [03_ingestion-run.md](03_ingestion-run.md) | 取込実行ガイド (コマンド・ファイルライフサイクル) |
| [03_ref-ingestion.md](03_ref-ingestion.md) | 取込 API リファレンス (web_crawler / chunk_splitter / rag_ingester) |
| [04_mcp-servers.md](04_mcp-servers.md) | MCP サーバ インデックス |
| [04_mcp-web-search.md](04_mcp-web-search.md) | web-search-mcp 詳細 |
| [04_mcp-file.md](04_mcp-file.md) | file-mcp 詳細 |
| [04_mcp-github.md](04_mcp-github.md) | github-mcp 詳細 |
| [04_mcp-protocol.md](04_mcp-protocol.md) | HTTP API / トランスポート / 追加手順 |
| [05_agent.md](05_agent.md) | エージェント ツール仕様・チューニング・実装注意 |
| [05_agent-ops.md](05_agent-ops.md) | エージェント 起動・確認・トラブルシューティング |
| [05_agent-impl.md](05_agent-impl.md) | エージェント実装詳細・REPL フロー |
| [06_common.md](06_common.md) | 共通モジュール インデックス |
| [06_ref-sqlite.md](06_ref-sqlite.md) | sqlite_helper.py (DB 接続・WAL・トランザクション) |
| [06_ref-infra.md](06_ref-infra.md) | インフラ共通モジュール (config_loader / rag_utils / logger / formatters) |
| [06_ref-mcp.md](06_ref-mcp.md) | MCP プロトコル層モジュール (mcp_models / tool_executor 等) |
| [06_ref-rag.md](06_ref-rag.md) | RAG パイプラインモジュール (agent_rag) |
| [06_ref-agent.md](06_ref-agent.md) | エージェント実行層モジュール (agent_repl / agent_config 等) |
