---
title: "MCP Server Catalog: rag-pipeline-mcp / cicd-mcp"
category: mcp
tags:
  - mcp
  - server-catalog
  - rag-pipeline
  - cicd
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_04_01_web-search-file-read-github.md
  - 04_mcp_04_02_file-write-file-delete-shell.md
  - 04_mcp_04_04_mdq.md
  - 04_mcp_04_05_git.md
---

# MCP Server Catalog: rag-pipeline-mcp / cicd-mcp

## rag-pipeline-mcp（ポート 8010）

**目的:** RAG 検索パイプライン（MQE → 検索 → RRF → リランク → 重複排除 → 拡張）。
**起動モード:** persistent（HTTP）
**設定:** `config/rag_pipeline_mcp_server.toml`

**ツール（4個）:**

| ツール | 入力 | 出力 |
|---|---|---|
| `rag_run_pipeline` | `{query, history_context?, debug?}` | `augmented_text` + `selected_hits` |
| `rag_debug_pipeline` | `{query, history_context?}` | 全ての中間ステージ出力 |
| `rag_list_documents` | `{lang?, limit?}` | インデックス済みドキュメントの一覧 |
| `rag_delete_document` | `{url}` | 削除確認 |

**設定パラメータ（`RagPipelineConfig` dataclass）:**

| キー | デフォルト | 説明 |
|---|---|---|
| `use_mqe` | `true` | マルチクエリ拡張を有効化 |
| `use_rrf` | `true` | RRF 融合を有効化 |
| `rrf_k` | `60` | RRF 定数 |
| `use_rerank` | `true` | クロスエンコーダーによるリランクを有効化 |
| `use_refiner` | `false` | コンテキストの精緻化/圧縮を有効化 |
| `top_k_search` | `20` | クエリごとの KNN/BM25 上位k件 |
| `top_k_rerank` | `15` | クロスエンコーダーの上位k件 |
| `rag_top_k` | `5` | 最終結果件数 |
| `rag_min_score` | `2.0` | リランクスコアの最小しきい値 |
| `max_chunks_per_doc` | `3` | 最終結果におけるドキュメントあたりの最大チャンク数 |
| `semantic_cache_max_size` | `100` | セマンティックキャッシュのエントリ数上限 |
| `semantic_cache_threshold` | `0.92` | セマンティックキャッシュのコサイン類似度しきい値 |
| `refiner_max_tokens` | `512` | コンテキスト精緻化の最大トークン数 |
| `refiner_max_chars_per_chunk` | `300` | コンテキスト精緻化のチャンクあたりの文字数 |
| `refiner_timeout` | `30.0` | コンテキスト精緻化のタイムアウト（秒） |

**設定フィールド（単体）:** `llm_url`, `embed_url`, `rag_db_path`, `sqlite_vec_so`, `mqe_n_queries`, `mqe_prompt_template`, `rerank_prompt_template`, `use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`, `rrf_k`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`, `max_chunks_per_doc`, `semantic_cache_max_size`, `semantic_cache_threshold`, `refiner_max_tokens`, `refiner_max_chars_per_chunk`, `refiner_timeout`

**注記（2026-07-13）:** `host`/`port`/`http_timeout` は `config/rag_pipeline_mcp_server.toml` から削除した。いずれも `RagPipelineConfig` に読み込まれず実装からも一切参照されていなかった。実際の値はハードコード: `http_host="127.0.0.1"`（`MCPServer` 基底クラス）、`http_port=8010`（`rag_pipeline/server.py`）、`http_timeout=120.0`（`rag_pipeline/service.py`）。

**ヘルス:** embed_url が設定されている場合は `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; 未設定の場合は `"status":"degraded","ready":false,"dependencies":{"embed_url":"not configured"}}` または `"dependencies":{"config":"check failed"}}` — ready 時は HTTP 200、degraded 時は 503。
**設計上の注記:** HTTP ループを防ぐため、`build_rag_cfg_adapter()` では `rag_service_url = ""` がハードコードされている。
**ログ:** `/opt/llm/logs/rag-mcp.log`
**使用場面:** 全ての RAG 検索; `/rag search` コマンドはこのサーバーを経由する。

**ツールステータス:** 全4ツールとも `"production"`（stub/experimental ではない）。

---

## cicd-mcp（ポート 8012）

**目的:** GitHub Actions ワークフロー管理。
**起動モード:** persistent（HTTP）
**設定:** `config/cicd_mcp_server.toml`
**認証:** `GITHUB_TOKEN`（`conf.d/cicd-mcp` 経由）

**ツール（4個）:**

| ツール | ティア | 入力 | `requires_config` |
|---|---|---|---|
| `trigger_workflow` | WRITE_DANGEROUS | `{repo, workflow, ref?, inputs?}` | yes |
| `get_workflow_runs` | READ_ONLY | `{repo, workflow, limit?}` | yes |
| `get_workflow_status` | READ_ONLY | `{repo, run_id}` | yes |
| `get_workflow_logs` | READ_ONLY | `{repo, run_id}` | yes |

**セキュリティ:**
- `repo_allowlist`: fail-closed（空 = 全て拒否; 起動時に warning をログ出力）
- `workflow_allowlist`: fail-closed（空 = 全て拒否; 起動時に warning をログ出力）
- `trigger_workflow` は `dry_run` 引数をサポート（ツールスキーマ経由で公開）

**設定フィールド:** `repo_allowlist`, `workflow_allowlist`, `max_log_size_kb`（デフォルト: 256 KB）, `auth_token`, `github_token`

**ヘルス:** トークン設定時は `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; 未設定時は `"status":"degraded","ready":false,"dependencies":{"github_token":"not_set"}}` または `"dependencies":{"config":"check failed"}}` — ready 時は HTTP 200、degraded 時は 503。
**ログ上限:** 最大5ジョブ、`max_log_size_kb` で設定可能（デフォルト: 合計256 KB）
**アーキテクチャ:** `CiCdService → CiBackend (Protocol) → GitHubActionsBackend`
**注記:** `CiBackend` Protocol は将来的な GitLab CI / Jenkins バックエンドへの対応を可能にする。

---

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_04_01_web-search-file-read-github.md`
- `04_mcp_04_02_file-write-file-delete-shell.md`
- `04_mcp_04_04_mdq.md`
- `04_mcp_04_05_git.md`

## Keywords

mcp
server-catalog
rag-pipeline-mcp, cicd-mcp, port 8010, port 8012
