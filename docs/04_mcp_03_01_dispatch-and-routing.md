---
title: "Tool Call Dispatch Flow and Routing Resolution"
category: mcp
tags:
  - mcp
  - routing
  - lifecycle
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_03_03_transport-and-health-part1.md
  - 04_mcp_03_03_transport-and-health-part2.md
  - 04_mcp_03_04_tool-call-tracing-and-watchdog.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
---

# MCP ツール呼び出しディスパッチフローとルーティング解決

- システム概要 → [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md)

## 目的

ツールルーティング、サーバー起動/停止のライフサイクル、ToolExecutor の内部構造、
ウォッチドッグの挙動、アイドルタイムアウト、および新規サーバー追加手順を文書化する。

---

## ツール呼び出しディスパッチフロー

エージェントはディスパッチログのコンテキストに `server_key` と `tool_name` を設定する。`X-Request-Id`（サーバーレスポンスヘッダーから取得）は、エージェントのディスパッチログとトランスポート、サーバー audit ログを相関付ける。

```
LLM returns tool_call
   → ToolRouteResolver.resolve(tool_name) → server_key
   → ToolExecutor.execute(tool_name, args)
        1. Plugin tool check (@register_tool)   — bypasses cache and MCP
        2. Cache check (TTL + LRU)             — returns cached result if hit; no HealthRegistry update
           (cache miss: inflight future で同一キーの同時実行を1回に集約 — stampede protection)
        3. MCP server dispatch (ToolExecutor._raw_execute)
             → startup_mode==none ゲート → 即時エラー ("disabled (startup_mode=none)")
             → McpServerHealthRegistry: is_unavailable? → return error immediately (no attempt made)
               (HALF_OPEN の場合はトライアルディスパッチとして通過させる)
             → LifecycleProtocol.ensure_ready(server_key)
             → concurrency semaphore acquire (if configured)
             → HttpTransport.call()
             → HealthRegistry.record_success() on success / record_failure() on transport error
             → return ToolCallResult(output, is_error, request_id, server_key)
```

### 実装上の補足 (Current behavior)

- キャッシュミス時、同一 `cache_key`（`tool_name:json(args)`）への同時呼び出しは `asyncio.Future` を共有し、実処理は1回のみ実行される（stampede protection）。実行元が例外を送出した場合、待機中の全呼び出しに同じ例外が伝播する。（Explicit in code: `shared/tool_executor.py::_execute_with_stampede_protection`）
- `startup_mode=none` のサーバー宛てのツール呼び出しは、ヘルスチェックやライフサイクル起動を試みる前に即座にエラーを返す。（Explicit in code: `shared/tool_executor.py::_check_startup_mode`）
- ヘルスレジストリが `HALF_OPEN` 状態を返す場合、`is_unavailable` によるブロックをスキップして1回のトライアルディスパッチを許可する（サーキットブレーカーの半開試行）。（Explicit in code: `shared/tool_transport_invoker.py::_check_health`）
- `ToolTransportInvoker.invoke()` は `ToolExecutor._raw_execute()` とほぼ同等の健全性チェック・ライフサイクル起動・セマフォ制御を提供する汎用メソッドとして別途存在するが、`startup_mode` ゲートは含まない。（Explicit in code）

---

## ToolRouteResolver (`shared/route_resolver.py`)

`ToolRegistry` を**唯一のルーティング権威**として `tool_name → server_key` を解決する。
ライブの `/v1/tools` discovery は起動時のドリフト検証のみに使用され、ルーティングには使用しない。

1. **ツールレジストリ（唯一のルーティング権威）:** `shared/tool_registry.py` の `ToolRegistry` シングルトン。
    各ツール名を正確に1つのサーバーキーにマッピングする。内部レジストリ登録関数によって、`tool_constants.py` の frozenset からインポート時に構築される。

2. **未知のツールは即時失敗する:** ツール名がレジストリに見つからない場合、`"Unknown tool: <tool_name>"` というメッセージで `ValueError` が発生する。フォールバックは存在しない — 全てのツールは `tool_constants.py` に明示的に登録されなければならない。

| ツールセット | サーバーキー |
|---|---|
| `READ_TOOLS` (9 tools: list_directory, read_text_file, etc.) | `file_read` |
| `WRITE_TOOLS` (write_file, edit_file, create_directory, move_file) | `file_write` |
| `DELETE_TOOLS` (delete_file, delete_directory) | `file_delete` |
| `shell_run` | `shell` |
| `search_web` | `web_search` |
| `GITHUB_TOOLS` (github_search_repositories, github_get_file_contents) | `github` |
| `RAG_TOOLS` (rag_run_pipeline, rag_debug_pipeline) | `rag_pipeline` |
| `CICD_TOOLS` (trigger_workflow, get_workflow_runs, get_workflow_status, get_workflow_logs) | `cicd` |
| `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs) | `mdq` |
| `GIT_TOOLS` (git_status, git_log, git_diff, git_branch, git_show, git_add, git_commit, git_checkout, git_pull, git_push) | `git` |
| 一致なし | `ValueError` |

**重要:** 未知のツールは `ValueError` で即時失敗する。新しいツールは常に `ToolRegistry` を経由して（`tool_constants.py` の frozenset を介して）登録しなければならない。

```python
resolver = ToolRouteResolver(server_configs)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

**MDQ ツール定義の4層責務:** MDQ (`mdq`) のツール定義は4つの独立したファイル
に分散しており、それぞれが単一の責務を持つ。いずれか1つを変更する際は、
他の3つも同期して更新する必要がある（`tests/test_mdq_tool_layer_consistency.py`
がこの整合性を検証する）。

| レイヤー | ファイル・シンボル | 責務 |
|---|---|---|
| スキーマ定義 | `scripts/mcp_servers/mdq/tools.py::TOOL_LIST` | LLM に公開するツール名・入力スキーマ・ステータス |
| 実行時ディスパッチ | `scripts/mcp_servers/mdq/server.py::_DISPATCH_TABLE` | ツール名 → ハンドラ関数のマッピング |
| レジストリ登録 | `scripts/shared/tool_constants.py::MDQ_TOOLS` | `ToolRegistry` にツールを登録するための正典集合 |
| デプロイ許可リスト | `config/agent.toml` の `[mcp_servers.mdq].tool_names` | 実際に起動・利用可能なツール名の一覧 |

---

## ルーティングの信頼できる情報源

`ToolRegistry` が**唯一のルーティング権威**である。ライブの `/v1/tools` discovery は検証専用であり、ルーティングの判断には影響しない。

| 入力 | 役割 | 要件 |
|---|---|---|
| `shared/tool_registry.py` | **唯一のルーティング権威** | `tool_constants.py` の frozenset からインポート時に構築される |
| ライブの `/v1/tools` discovery | **検証専用のソース** | 任意; 起動時に `check_routing_drift_vs_live()` によってドリフト検出に使用 — ルーティングには影響しない |

**所有ルールの要約:**
- ツールを追加する場合: `tool_constants.py` の適切な frozenset に追加する。レジストリはインポート時に自動構築される。
- ライブの `/v1/tools` は起動時のドリフト検証にのみ使用され、レジストリのルーティングを上書きすることはない。
- config の `tool_names` はルーティングの入力ではない; あくまでドリフト検証用のメタデータである。
- 未知のツールは `ValueError` で即時失敗する — フォールバックは存在しない。
- config の `tool_names` 省略 / 空リスト / 設定済み の3つの状態のTOML例は [`docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`](04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md) を参照。
- 同じツール名が複数のサーバーの `/v1/tools` レスポンスで報告される重複所有権は、`shared/route_resolver.py::build_discovery_map()` で検出され、`agent/repl_health.py::check_routing_drift_vs_live()` が `ServiceWarning` として表示する — レジストリの自身によるサーバー間検証ではない。

---

## Tool Registry (`shared/tool_registry.py`)

MCP ツール定義と所有権に関する単一の信頼できる情報源。

| ソース | 種別 | 説明 |
|---|---|---|
| `shared/tool_registry.py` | **唯一のルーティング権威** | ツール→サーバー逆引き; `tool_constants.py` frozensetからimport時に自動構築 |
| Live `/v1/tools` discovery | **起動時バリデーションのみ** | ルーティングには使用しない; `check_routing_drift_vs_live()` でドリフト検出に使用 |

### 所有権モデル

- 各ツールは**正確に1つのサーバー**に属する（`server_key` で識別される）。
- レジストリは `tool_constants.py` の frozenset からインポート時に構築される。
- config の `*_mcp_server.toml` の `tool_names` リスト（各 `[mcp_servers.<key>]` セクション内）はレジストリに対して検証されるが、信頼できる情報源として必須ではない。
- サーバーの `/v1/tools` レスポンスは、ドリフト検出のため起動時にレジストリと照合される。
- **重要:** ライブ discovery はレジストリを上書きしない。`/v1/tools` がツールに対してレジストリと異なる `server_key` を返す場合、起動時に `check_routing_drift_vs_live()` によってドリフトとしてフラグが立てられる。

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_02_tool-registry.md`
- `04_mcp_03_03_transport-and-health-part1.md`
- `04_mcp_03_03_transport-and-health-part2.md`
- `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`

## Keywords

mcp
routing
lifecycle
ToolRouteResolver
ToolRegistry
tool dispatch
routing drift
stampede protection
startup_mode gate
HALF_OPEN trial dispatch
