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
| [03_rag_00_document-guide.md](03_rag_00_document-guide.md) | RAG ドキュメントセット ガイド |
| [03_rag_01_system_overview.md](03_rag_01_system_overview.md) | RAG システム概要 |
| [03_rag_02_ingestion_pipeline.md](03_rag_02_ingestion_pipeline.md) | 取込パイプライン（CLI・API・設定） |
| [03_rag_03_query_pipeline.md](03_rag_03_query_pipeline.md) | クエリパイプライン |
| [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md) | データモデル・インターフェース |
| [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md) | RAG 設定・運用 |
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | RAG 既知問題・不整合 |
| [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) | MCP ドキュメントセット ガイド |
| [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md) | MCP システム概要 |
| [04_mcp_02_protocol_and_transport.md](04_mcp_02_protocol_and_transport.md) | MCP プロトコル・トランスポート |
| [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) | ルーティング・ライフサイクル・実行 |
| [04_mcp_04_server_catalog.md](04_mcp_04_server_catalog.md) | MCP サーバカタログ（全11サーバ） |
| [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md) | MCP セキュリティ・安全モデル |
| [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md) | MCP 設定・運用 |
| [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) | MCP 既知問題・不整合 |
| [05_agent_00_document-guide.md](05_agent_00_document-guide.md) | エージェント ドキュメントセット ガイド |
| [05_agent_01_system-overview.md](05_agent_01_system-overview.md) | エージェント システム概要 |
| [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md) | ランタイムアーキテクチャ |
| [05_agent_03_turn-processing-flow.md](05_agent_03_turn-processing-flow.md) | ターン処理フロー |
| [05_agent_04_state-and-persistence.md](05_agent_04_state-and-persistence.md) | 状態・永続化 |
| [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) | LLM・SSE ストリーミング |
| [05_agent_06_tool-execution-and-approval.md](05_agent_06_tool-execution-and-approval.md) | ツール実行・承認フロー |
| [05_agent_07_cli-and-commands.md](05_agent_07_cli-and-commands.md) | CLI・スラッシュコマンド |
| [05_agent_08_configuration.md](05_agent_08_configuration.md) | エージェント設定 |
| [05_agent_09_data-layer.md](05_agent_09_data-layer.md) | データレイヤー |
| [05_agent_10_operations-and-observability.md](05_agent_10_operations-and-observability.md) | 起動・確認・トラブルシューティング・OTel |
| [05_agent_11_extension-points.md](05_agent_11_extension-points.md) | 拡張ポイント（プラグイン） |
| [05_agent_12_reference-api.md](05_agent_12_reference-api.md) | API リファレンス |
| [06_shared_00_document-guide.md](06_shared_00_document-guide.md) | shared/DB ドキュメントセット ガイド |
| [06_shared_01_overview.md](06_shared_01_overview.md) | shared/DB 層概要 |
| [06_shared_02_types_and_protocols.md](06_shared_02_types_and_protocols.md) | 共通型・プロトコル定義 |
| [06_shared_03_runtime_and_execution.md](06_shared_03_runtime_and_execution.md) | 実行インフラ（ConfigLoader・Logger・プラグイン） |
| [06_shared_04_db_architecture_and_schema.md](06_shared_04_db_architecture_and_schema.md) | DB 構造・スキーマ |
| [06_shared_05_db_api_and_operations.md](06_shared_05_db_api_and_operations.md) | DB API・保守運用 |
| [06_shared_90_inconsistencies_and_known_issues.md](06_shared_90_inconsistencies_and_known_issues.md) | shared/DB 既知問題・不整合 |
