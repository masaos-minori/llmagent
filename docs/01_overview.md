# 概要・アーキテクチャ・ファイル構成 (インデックス)

| ファイル | 内容 |
|---|---|
| [01_overview-arch.md](01_overview-arch.md) | 概要・目的・アーキテクチャ (プロセス構成・取込パイプライン・クエリパイプライン・ターン処理順序・MCP サーバ一覧・実装済み機能・実装補足) |
| [01_overview-files.md](01_overview-files.md) | ファイル構成 (デプロイ先 `/opt/llm/` ディレクトリ構造・ソースモジュール一覧) |

## 実装意図

- `01_overview-arch.md` と `01_overview-files.md` を分割している理由: arch は設計・動作・ライフサイクルを記述し、files は `/opt/llm/` 以下の物理配置とソースモジュールの対応を記述する。関心の異なる2種の参照ニーズに対応するための意図的な分離。(根拠: 各ファイルのトップに相互リンクが張られており、分離を前提とした設計になっている)
- `01_overview-arch.md` には単純なアーキテクチャ図に加えて、ターン処理順序・`workflow_mode` の3種・`startup_mode`・プラグインシステム・`AgentContext` の DI ハブ役割・メモリフォールバック等の実装補足セクションが含まれている。これらは `orchestrator.py`・`startup.py`・`factory.py`・`context.py` 等のソースコードから直接裏付けられる。
- 本ファイルはシステム全体の概要インデックス。詳細なドキュメントセットの目次は下記を参照。

## 実装リファレンス

| ファイル | 内容 |
|---|---|
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
| [90_shared_00_document-guide.md](90_shared_00_document-guide.md) | shared/DB ドキュメントセット ガイド |
| [90_shared_01_overview.md](90_shared_01_overview.md) | shared/DB 層概要 |
| [90_shared_02_types_and_protocols.md](90_shared_02_types_and_protocols.md) | 共通型・プロトコル定義 |
| [90_shared_03_runtime_and_execution.md](90_shared_03_runtime_and_execution.md) | 実行インフラ（ConfigLoader・Logger・プラグイン） |
| [90_shared_04_db_architecture_and_schema.md](90_shared_04_db_architecture_and_schema.md) | DB 構造・スキーマ |
| [90_shared_05_db_api_and_operations.md](90_shared_05_db_api_and_operations.md) | DB API・保守運用 |
| [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | shared/DB 既知問題・不整合 |
