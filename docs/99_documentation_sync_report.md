---
title: "Documentation Sync Report"
category: meta
tags:
  - documentation-sync
  - run-report
  - known-issues
related:
  - index.md
source:
  - 08_document_refactor.md
---

# ドキュメント同期レポート

`08_document_refactor.md` の指示に基づき、`docs/*.md` 全202ファイルを `scripts/` 配下の実装コードと突き合わせ、実装意図の追記・矛盾の修正を行った実行記録。

## 実行範囲

- 対象: `docs/` 配下の全202ファイル(01_overview〜90_shared、index.md含む)
- 手法: ドメイン単位(overview/deployment, 03_rag, 04_mcp, 05_agent×3分割, 06_eventbus, 90_shared)で並行エージェント + 直接調査を組み合わせ
- 更新ファイル数: 153 / 202(残り49件は既存記述がコードと一致しており変更不要と確認)
- ソースコードは一切変更していない(docs/*.md のみが対象)

## 追記(2026-07-13、修正実施)

本レポートで「持ち越し」としていた実装バグ・ツール不具合を修正した。

| 項目 | 修正内容 | 検証 |
|---|---|---|
| `scripts/eventbus/app.py::_dlq_loop()` のクラッシュ | `get_config(type("Req", (), {"app": app})())` / `get_db(...)` を `get_config(app)` / `get_db(app)` に修正(`route_helpers` の app 引数版ヘルパーを直接呼ぶよう是正) | `uv run pytest tests/test_eventbus*.py` → **148 passed**(修正前: 5 failed, 97 errors)。`ruff check` / `mypy` も引き続き成功 |
| `tools/check_mcp_docs_consistency.py` の `_SERVER_TOOLS_MAP["github-mcp"]` が古い | read-only 系10ツール(`github_list_branches` 等)を追加し、実装コードと一致する21件のフルセットに更新 | `python tools/check_mcp_docs_consistency.py` → **No issues found** |

`06_eventbus_90_inconsistencies_and_known_issues.md` と `06_eventbus_05_07_validation-status.md` を修正後の状態に更新済み。

## 追記2(2026-07-13、設定ファイルと実装の不整合を修正)

「設定ファイルにキーがある →(dataclassに読み込まれる場合もある)→ しかしその後どこからも参照されない」というデッド設定を、直接調査とバックグラウンドエージェントによる13設定ファイルの棚卸しの両方で計8件確認し、**設定ファイル側を削除**して実装(挙動)に合わせた(ソースコードは変更していない)。各ファイルには削除理由・削除日を記したコメントを残している。

| 設定ファイル | 削除したキー | 根拠 |
|---|---|---|
| `config/git_mcp_server.toml` | `audit_log_path` | `GitConfig.audit_log_path` に読み込まれるが `GitService`/`server.py` のどこからも参照されない |
| `config/mdq_mcp_server.toml` | `audit_log_path` | `MdqService.audit_log_path` に読み込まれるが以降未使用。監査イベントは実際には `_audit_log()` 経由で `mdq-mcp.log`(アプリログ)にJSON-linesで書き込まれており、専用の `mdq_audit.log` ファイルは存在しない |
| `config/mdq_mcp_server.toml` | `concurrency_limit` | リポジトリ全体で未参照。直列化は `MdqService._index_lock`(固定の `asyncio.Lock`)で実現され設定値に依存しない |
| `config/file_delete_mcp_server.toml` | `audit_log_path` | `FileDeleteConfig`(`delete_models.py`)には`allowed_dirs`しかフィールドが無く、そもそもdataclassに読み込まれない。実際の監査ログパスは`delete_service.py`にハードコード(値はTOMLと偶然一致) |
| `config/ingester.toml` | `strict_artifact_validation` | `RagIngester.__init__`が読み込まず、`_validate_artifact()`呼び出し2箇所とも`strict`引数省略でPythonデフォルト`strict=True`が常時適用される |
| `config/github_mcp_server.toml` | `default_per_page` | `service_security.py`の`self._default_per_page`に代入されるのみで以降未参照。実際のデフォルト件数はモジュール定数`DEFAULT_PER_PAGE=10`を各リクエストモデルが直接参照。`max_per_page`は実際に使われる別キーのため維持 |
| `config/rag_pipeline_mcp_server.toml` | `host`, `port`, `http_timeout` | `RagPipelineConfig`にフィールドが無く未参照。実際の値は`http_host="127.0.0.1"`(`MCPServer`基底クラス)、`http_port=8010`(`server.py`)、`http_timeout=120.0`(`service.py`)としてハードコード。他のMCPサーバーtomlにはそもそも`host`/`port`キーが存在せず、rag-pipeline-mcp固有の記載漏れだったと判断 |
| `config/agent.toml` | `use_two_stage_fetch`, `two_stage_max_docs` | `RagConfig` Protocol(`shared/types.py`)にフィールドが無く、`scripts/`全体で`"two_stage"`/`"stage_fetch"`のgrepがゼロ件。多数のテストfixtureにボイラープレートとして残存するが、それらは`config/agent.toml`から独立したインラインdictであり本ファイルの削除とは無関係 |

**調査したが対象外(デッドではない)と判断した項目:**
- `config/agent.toml` の `rag_service_url` — `shared/types.py::RagConfig.rag_service_url`として実際に`rag/pipeline.py`から参照され、外部RAGサービスへの委譲要否を判定する現役の設定。`mcp_servers/rag_pipeline/models.py::build_rag_cfg_adapter()`内で空文字列に上書きするのはRAG MCPサーバー自身が自己参照ループに陥るのを防ぐ別の目的の実装であり、別物(既存docsで説明済み)

**検証:** 各修正後にTOML構文チェック(`tomllib.load`)と関連pytestを実行し全て成功。
- `tests/test_eventbus*.py` → 148 passed
- `tests/ -k "mdq"` → 199 passed, 4 skipped
- `tests/ -k "git and not github and not gitops"` → 48 passed
- `tests/ -k "github and not gitops"` → 143 passed
- `tests/ -k "file_delete or delete_service"` → 39 passed
- `tests/ -k "ingester or ingest"` → 86 passed
- `tests/ -k "rag_pipeline_mcp or rag_pipeline_service or rag_pipeline_server"` → 47 passed
- `tests/ -k "config or agent_config or build_agent"` → 413 passed
- `check_docs_consistency.py` / `check_mcp_docs_consistency.py` → 両方とも通過

関連ドキュメントを更新: `04_mcp_04_01_web-search-file-read-github.md`, `04_mcp_04_03_rag-pipeline-and-cicd.md`, `04_mcp_04_04_mdq.md`, `04_mcp_04_05_git.md`, `04_mcp_05_05_mdq-enforcement-and-lockdown.md`, `04_mcp_06_04_major-default-values.md`, `04_mcp_06_07_reading-audit-logs.md`, `03_rag_02_06_ingestion_pipeline-supporting-components.md`, `03_rag_05_1-configuration-reference.md`。特に `04_mcp_06_07` では「mdq-mcp に専用audit logファイルがある」という誤った記載(存在しない `mdq_audit.log` への言及、grepサンプルコマンド含む)も訂正した。

`gitops_force_push_blocked`/`gitops_protected_branches`(下記 Needs Confirmation 参照)は `config/agent.toml` 側にキー自体が存在しないため、今回の「設定ファイル修正」の対象外(dataclass 側のみの未配線フィールドであり、設定ファイルとの不整合ではない)。

## 主要な発見事項(調査時点の記録)

### 1. 実装バグ(調査時点ではスコープ外だったが、上記の通り修正済み)

**`scripts/eventbus/app.py` の `_dlq_loop()` が毎ティッククラッシュする**

`route_helpers.py` の app 引数版ヘルパー(`app_get_config`/`app_get_db`、`get_config`/`get_db` としてエイリアスインポート)を、Request ラッパー版の呼び出し規約(`type("Req", (), {"app": app})()` でラップ)で呼び出しており、`AttributeError: 'Req' object has no attribute 'state'` が発生する。この例外は `except (OSError, sqlite3.Error):` で捕捉されないため、DLQ セーフティスイープのバックグラウンドタスクが初回ティックで停止し、`GET /health` が `dlq_task: stopped` により degraded(HTTP 503)を返し続ける。

2026-07-13 に `uv run pytest tests/test_eventbus*.py` を再実行し確認: **5 failed, 143 passed, 97 errors**(いずれも同一原因)。**→ 上記の通り修正済み。**

### 2. ドキュメント内の矛盾・誤記(修正済み)

| 項目 | 内容 | 修正箇所 |
|---|---|---|
| `use_tool_dag` という存在しないフィールド | コードベース全体に存在しないにも関わらず、複数ファイルが有効な設定フィールドとして記載(デフォルト値・resource_scope規約付きで説明) | `05_agent_08_03`, `05_agent_06_01`(既存の正しい記述を確認済み), `04_mcp_06_13_part2`, `04_mcp_06_16` |
| `config/tools_definitions.toml` という存在しない設定ファイル | 実際は `config/agent.toml` の `[[tool_definitions]]` に統合済み。複数ファイルに残存 | `04_mcp_03_05`, `04_mcp_03_02`, `04_mcp_06_14`, `04_mcp_06_15`, `05_agent_05` |
| `mcp_servers.<key>` トランスポートセクションの所在誤り | `config/<key>_mcp_server.toml` 内にあるかのような記載だったが、実際は `config/agent.toml` 側 | `04_mcp_03_05` |
| ConfigLoader が読み込む「12個のベースファイル」という古い記述 | `_BASE_CONFIG_FILES = ("agent.toml",)` の1件のみ(プロセス分離方針導入後) | `90_shared_03_03_part2`, `90_shared_03_04_part2`, `90_shared_00`(rag_pipeline.toml関連の誤記も含む) |
| Event Bus のポート番号誤記(8010 → 8015) | `06_eventbus_05_05` の curl 例が rag-pipeline-mcp のポート(8010)を使っていた。`06_eventbus_05_02` の TOML 例も同様 | `06_eventbus_05_02`, `06_eventbus_05_05` |
| 壊れた内部リンク・存在しないファイル名参照 | `01_overview-files-05/06` の相互参照が旧ファイル名(`-scripts.md`/`-shared.md`)のまま、`03_rag_02_01` に存在しないファイルへのリンク、`02_deployment-part2` のスキーマ参照ファイル名誤り | `01_overview-files-05/06`, `03_rag_02_01` |
| `mcp/` という改称前のパッケージ名 | PyPI の `mcp` SDK との衝突を避け `mcp_servers/` に改称済みだが、一部ファイルで `mcp/models.py` 等の旧名が残存(**全数はカバーできておらず、追加調査を推奨** — 下記参照) | `90_shared_02_03`, `90_shared_03_03_part2` |
| コードフェンスの欠落・段落の重複 | `03_rag_91_design_notes-part2.md` の未閉じコードブロック、`05_agent_10_04_part2.md` の同一段落2連続 | 両ファイルとも修正 |
| その他の小規模な誤り | 行番号参照のドリフト、ファイル一覧の欠落項目(`cmd_skill.py`, `config_validators.py`, `validate.py`, `db_maintenance.py`, `route_helpers.py` 等)、CommandRegistry のミックスイン数(13/10→14) | 多数(各ドメインで個別修正) |

### 3. 実装挙動としてドキュメント化した既知の重要事項

- `WorkflowDef.require_approval` のデフォルトは `False`。`config/workflows/default.json` にも明示指定がないため、標準デプロイでは承認ゲートが発火しない(`issues/20260711_00_issue.md` で追跡中の未決事項と一致)。[05_agent_03_03](05_agent_03_03_turn-processing-flow-workflow-engine-part1.md) に追記。
- `_dlq_loop()` の実装バグ(前述)。

## Needs Confirmation として残した項目

- `dlq.py::promote_to_dlq()` がデッドコードか、将来の一括運用コマンド用に意図的に残されているか
- `gitops_force_push_blocked` / `gitops_protected_branches` 設定フィールドが将来実装予定なのか削除漏れなのか(`config/agent.toml` にキー自体が存在しないため設定ファイル修正の対象外。dataclass 側のクリーンアップが必要なら別途ソースコード変更として対応)
- `agent/memory/store.py::DiagnosticStore` の `fetch_by_kind`/`fetch_all` が将来のCLI/API用途かどうか

(`mdq_mcp_server.toml` の `concurrency_limit`/`audit_log_path` は上記「追記2」で調査・解決済みのため本リストから除外)

これらは各ファイル内に `Needs confirmation` として明記済み。

## 未対応・追加調査を推奨する領域

- **`mcp/` 旧パッケージ名の残存箇所**: 90_shared 系に加え、`04_mcp_*`, `05_agent_08_01` 等の literal path 表記も修正完了。ただし、`mcp/<server>.field` 形式のログ文字列表記が一部に残る可能性があるため、再度の確認を推奨。
- `05_agent_90_inconsistencies_and_known_issues.md` および `04_mcp_90_inconsistencies_and_known_issues.md` は現時点でほぼ解消済みの記載のみで、新規の恒久的な既知課題エントリは今回追加していない(発見した問題はその場で本文修正、または `06_eventbus_90` にのみ正式追加)。

## 整合性チェックツールの実行結果(2026-07-13、修正後)

- `python tools/check_docs_consistency.py`: 全チェック通過
- `python tools/check_mcp_docs_consistency.py`: **No issues found**(`_SERVER_TOOLS_MAP["github-mcp"]` の修正後)

## memo-doc.md 実行記録 (最新)

プライベートメソッド参照の削除:

| ファイル | 変更内容 | 証拠分類 |
|---|---|---|
| `docs/05_agent_08_01_configuration-loading-agent-config-part2.md` | `_check_workflow_definition()` を機能説明に置換 | コード上の明示 |
| `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md` | `_check_workflow_definition()` ×2 を `_initialize()` / 機能説明に置換 | コード上の明示 |
| `docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md` | `_sync_system_prompt()` を汎用説明に置換 | コード上の明示 |

グループ別サマリー:

| グループ | Pythonファイル数 | プライベートメソッド | ドキュメント記載 | アクション |
|---|---|---|---|---|
| rag → docs/03_*.md | ~15 | 58 | なし | なし |
| mcp_servers → docs/04_*.md | ~20 | 50 | なし | なし |
| agent → docs/05_*.md | ~35 | 70 | 3件 | 3件削除 |
| eventbus → docs/06_*.md | ~9 | 9 | なし | なし |
| db+shared → docs/90_*.md | ~13 | 22 | なし | なし |

## ドメイン別内訳

| ドメイン | 対象ファイル数 | 更新 | 変更不要(確認済み) |
|---|---|---|---|
| 01_overview / 02_deployment | 18 | 11 | 7 |
| 03_rag | 41 | 32 | 9 |
| 04_mcp | 41 | 26 | 15 |
| 05_agent | 59 | 45 | 14 |
| 06_eventbus | 20 | 17 | 3 |
| 90_shared | 23 | 23 | 0 |
| **合計** | **202** | **154** (概算、一部ファイルはPart横断のためタスク番号のみ集計) | **48** |

## 2026-07-16 プライベートメソッド名参照の削除（追加）

プライベートメソッド名の記載をドキュメントから削除:

| ファイル | 変更内容 |
|---|---|
| `docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md` | `_chunk_markdown_by_heading()`, `_chunk_english()`, `_build_text_triples()` の記載を削除 |
| `docs/03_rag_02_05_ingestion_pipeline-document-manager.md` | `_update_etag` の記載を削除 |
| `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md` | `_update_etag` の記載を削除 |
| `docs/03_rag_05_3-logging.md` | `_configure_logger()` の記載を削除 |
| `docs/04_mcp_03_01_dispatch-and-routing.md` | `_execute_with_stampede_protection`, `_check_startup_mode`, `_check_health` の記載を削除 |
| `docs/04_mcp_03_04_tool-call-tracing-and-watchdog.md` | `_raw_execute()`, `_check_startup_mode` の記載を削除 |
| `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md` | `_check_startup_mode()` の記載を削除 |
| `docs/04_mcp_06_09_mcp-failure-diagnosis.md` | `_raw_execute()`, `_check_health()` の記載を削除 |
| `docs/05_agent_13_reference-api-part1.md` | `_log_routing_coverage()` の記載を削除 |
| `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md` | `_initialize()`, `_check_workflow_definition()` の記載を削除 |
| `docs/05_agent_08_01_configuration-loading-agent-config-part2.md` | `_initialize()` の記載を削除 |
| `docs/06_eventbus_06_01_reference-api-core-modules.md` | `_main()` の記載を削除 |
| `docs/06_eventbus_03_persistence_schema_and_replay.md` | `_migrate()` の記載を削除 |
| `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` | `_execute_with_cache()`, `_store_and_evict()` の記載を削除 |
| `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` | `_configure_logger` の記載を削除 |

| `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md` | `_ensure_semaphores()` の記載を削除 |
| `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md` | `_execute_with_cache()`, `_store_and_evict()` の記載を削除 |
| `docs/04_mcp_02_01_endpoints-and-transport.md` | `_health()` の記載を削除 |
| `docs/05_agent_10_05_operations-and-observability-monitoring.md` | `compression_char_threshold` を `context_char_limit` に修正（設定キーの誤記） |
