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
  - 04_mcp_03_03_transport-and-health.md
  - 04_mcp_03_03_transport-and-health.md
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

``` text
LLM returns tool_call
   → ToolRouteResolver.resolve(tool_name) → server_key
   → ToolExecutor.execute(tool_name, args)
        1. Cache check (TTL + LRU)             — returns cached result if hit; no HealthRegistry update
           (cache miss: inflight future で同一キーの同時実行を1回に集約 — stampede protection)
        2. MCP server dispatch (内部ディスパッチ)
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

- キャッシュミス時、同一 `cache_key`（`tool_name:json(args)`）への同時呼び出しは `asyncio.Future` を共有し、実処理は1回のみ実行される（stampede protection）。実行元が例外を送出した場合、待機中の全呼び出しに同じ例外が伝播する。（Explicit in code）
- `startup_mode=none` のサーバー宛てのツール呼び出しは、ヘルスチェックやライフサイクル起動を試みる前に即座にエラーを返す。（Explicit in code）
- ヘルスレジストリが `HALF_OPEN` 状態を返す場合、`is_unavailable` によるブロックをスキップして1回のトライアルディスパッチを許可する（サーキットブレーカーの半開試行）。（Explicit in code）
- `ToolTransportInvoker.invoke()` は内部ディスパッチとほぼ同等の健全性チェック・ライフサイクル起動・セマフォ制御を提供する汎用メソッドとして別途存在するが、`startup_mode` ゲートは含まない。（Explicit in code）

---

## Two-stage tool resolution

Tools go through two distinct resolution stages before being available for execution:

**Stage 1: LLM Visibility** (`RuntimeToolRegistry.llm_tool_definitions()`)

- Tools returned here are visible to the LLM as potential tool calls
- This stage determines what tools the LLM can propose
- Disabled tools may still appear at this stage depending on configuration

**Stage 2: Runtime Routability** (`LLMTurnRunner._filter_disabled_tool_definitions()`)

- After the LLM proposes a tool call, this stage determines whether the tool can actually be routed to its handler
- Disabled tools are filtered out at this stage
- A tool can be LLM-visible but not runtime-routable (e.g., disabled due to config)

**Critical failure mode:** If `RuntimeToolRegistry` is missing entirely, the LLM sees no tools at all, resulting in "Unknown tool" errors even when tools exist in the system.

## Data source for DAG scheduling

The DAG scheduler reads its metadata from `RuntimeToolRegistry`, the same registry that
backs routing and LLM visibility. For each approved call, `agent/tool_runner.py::_execute_with_dag()`
builds a call-id-keyed `ToolSpec` via `RuntimeToolRegistry.tool_spec_for_call(call_id, name, args)`
(`shared/runtime_tool_registry.py`), which resolves per-call resource scopes from the tool's
declared `resource_scope_kind`/`resource_scope_keys` and the call's actual arguments
(`shared/resource_scope.py::resolve_resource_scopes()`). `agent/tool_scheduler.py::build_execution_groups()`
consumes this `dict[str, ToolSpec]` keyed by `call_id` (not tool name) and raises
`MissingToolSpecError` if a call's `call_id` has no entry, instead of silently defaulting.

### Fields used by the DAG scheduler

The following `ToolSpec` fields (resolved per call from the tool's `/v1/tools` schema-2.0
declaration) drive scheduling:

- `requires_serial`: Controls whether the tool requires serialized execution (forms a solo serial-barrier group)
- `resource_scopes`: Tuple of kind-prefixed resource-scope strings (e.g. `"filesystem:/a/b.txt"`) the call occupies; conflicting scopes across calls form a serialized conflict-graph group (`shared/resource_scope.py::_scopes_conflict()` — exact match, or ancestor/descendant for `"filesystem:"` scopes)
- `is_write`: Indicates whether the tool performs write operations (a write tool with no resolved scope is treated as occupying the synthetic `"global:write"` scope, so it still participates in — and can conflict within — the same resource-scope conflict graph as scoped writes; there is no separate `write_first` bucket)

### Key distinction

- **RuntimeToolRegistry**: Sole authority for both routing/LLM visibility (`/v1/tools`) AND DAG scheduling metadata (`ToolSpec` via `tool_spec_for_call()`).
- **config/agent.toml `[[tool_definitions]]`**: Only the LLM-facing function-calling schema (name/description/parameters) exposed to the model; carries no scheduling metadata of its own.

There is a single data source for scheduling metadata today: a tool's `/v1/tools` schema-2.0
declaration (`is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys`).
Updating `config/agent.toml`'s tool definitions does not affect DAG scheduling.

---

## ToolRouteResolver (`shared/route_resolver.py`)

`RuntimeToolRegistry` を用いて `tool_name → server_key` を解決する。`ToolRegistry` はルーティング
判断には使われない。解決手順は以下の通り:

1. **RuntimeToolRegistry（唯一のルーティング権威）:** `shared/runtime_tool_registry.py` の
    `RuntimeToolRegistry`。McpToolDiscoveryService によるライブ `/v1/tools` discovery で構築される。
    `startup.py` で `ToolExecutor.set_runtime_registry()` 経由で接続される。

2. **未知のツールは即時失敗する:** ツール名が RuntimeToolRegistry に見つからない場合、`"Unknown tool: <tool_name>"` というメッセージで `ValueError` が発生する。フォールバックは存在しない — 全てのツールはライブ discovery によって検出されなければならない。

| ツールセット | サーバーキー |
|---|---|
| `READ_TOOLS` (9 tools: list_directory, read_text_file, etc.) | `file_read` |
| `WRITE_TOOLS` (write_file, edit_file, create_directory, move_file) | `file_write` |
| `DELETE_TOOLS` (delete_file, delete_directory) | `file_delete` |
| `shell_run` | `shell` |
| `WEB_SEARCH_TOOLS` (search_web, browser_fetch) | `web_search` |
| `GITHUB_TOOLS` (github_search_repositories, github_get_file_contents) | `github` |
| `RAG_TOOLS` (rag_run_pipeline, rag_debug_pipeline) | `rag_pipeline` |
| `CICD_TOOLS` (trigger_workflow, get_workflow_runs, get_workflow_status, get_workflow_logs) | `cicd` |
| `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs) | `mdq` |
| `GIT_TOOLS` (git_status, git_log, git_diff, git_branch, git_show, git_add, git_commit, git_checkout, git_pull, git_push) | `git` |
| 一致なし | `ValueError` |

**重要:** 未知のツールは `ValueError` で即時失敗する。新しいツールは `tool_constants.py` の frozenset に追加しなければならない（`ToolRegistry` がこれをドリフト検出用データとしてインポート時に取り込む）。ただしルーティング自体は `RuntimeToolRegistry` のライブ discovery にのみ基づく — `tool_constants.py`/`ToolRegistry` への登録だけではツールは解決可能にならない。For diagnosis guidance, see [MCP Failure Diagnosis](04_mcp_06_09_mcp-failure-diagnosis.md#llm-called-a-tool-but-execution-failed-with-unknown-tool).

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
| スキーマ定義 | `scripts/mcp_servers/mdq/mdq_tools.py::TOOL_LIST` | LLM に公開するツール名・入力スキーマ・ステータス |
| 実行時ディスパッチ | `scripts/mcp_servers/mdq/mdq_server.py::_DISPATCH_TABLE` | ツール名 → ハンドラ関数のマッピング |
| レジストリ登録 | `scripts/shared/tool_constants.py::MDQ_TOOLS` | `ToolRegistry` にツールを登録するための正典集合 |
| デプロイ許可リスト | `config/agent.toml` の `[mcp_servers.mdq].tool_names` | 実際に起動・利用可能なツール名の一覧 |

**全8サーバーへの一般化:** 上記の4層整合性ガードレールは MDQ 専用だったが、
`tests/test_tool_server_layer_consistency.py` が同じ検証を8つの MCP サーバー
全て（mdq, github, shell, git, cicd, rag_pipeline, file[read/write/delete],
web_search）に一般化している。ディスパッチテーブルの実体は2パターンに分かれる
（file は read/write/delete の3サーバーに分かれるため、レジストリキーは
10個になる）:

| ディスパッチ形態 | 該当サーバー |
|---|---|
| モジュールレベルの辞書（`_DISPATCH_TABLE` 相当） | `mdq`（`server.py::_DISPATCH_TABLE`）、`web_search`（`formatters.py::_WEB_DISPATCH`） |
| サービスインスタンスの `get_dispatch_table()` | `github`, `shell`, `git`, `cicd`, `rag_pipeline`, `file_read`, `file_write`, `file_delete` |

---

## ツールのライフサイクル全体像（schema → dispatch → registry → side-effect → risk → audit）

1つの MCP ツールは、呼び出しから監査記録まで以下の層を必ず一貫して通過する。
いずれかの層だけを更新して他を放置すると、ドリフト（層間の不整合）が発生する。

``` text
① スキーマ定義        各サーバーの tools.py::TOOL_LIST — LLM に公開する名前・入力スキーマ
② 実行時ディスパッチ    server.py の _DISPATCH_TABLE、または service.get_dispatch_table()
③ レジストリ登録       shared/tool_constants.py の frozenset → shared/tool_registry.py（ドリフト検出用）; ルーティングは shared/runtime_tool_registry.py の RuntimeToolRegistry が唯一の権威
④ 副作用検出          唯一の実行パス agent/tool_runner.py::_execute_with_dag() が
                      agent/tool_scheduler.py::build_execution_groups() に委譲し、RuntimeToolRegistry
                      登録済みの is_write（PreparedToolCall.spec 経由、未登録ツールは準備フェーズで
                      フェイルクローズドに却下されるためこの段には到達しない）を参照して並列/直列を判定。
                      shared/tool_executor_helpers.py::is_side_effect() は別用途（shared/tool_executor.py の
                      TTL キャッシュのバイパス判定）にのみ使われ、バッチの並列/直列判定にはもう関与しない
⑤ リスク分類・承認    agent/tool_policy.py::classify_operation_type() / classify_risk()
                      — 優先順位: approval_risk_rules → tool_safety_tiers → tool_constants.py 分類
⑥ 監査ログ           agent/tool_audit.py — classify_operation_type() の結果を operation_type として記録
```

**層③〜⑤は互いに独立したソースを参照する。** ③はレジストリ登録（所有権）、
④はバッチ実行時の並列/直列制御、⑤は承認リスク判定と監査分類であり、いずれも
`shared/tool_constants.py` の frozenset を参照するが、参照漏れがあると各層が
個別にドリフトしうる。`agent/tool_policy.py::classify_operation_type()` は
以前 `WRITE_TOOLS`/`DELETE_TOOLS`/GitHub 系集合のみを参照しており、
`MDQ_WRITE_TOOLS`・`RAG_WRITE_TOOLS`・`CICD_WRITE_TOOLS`・`GIT_WRITE_TOOLS`
に属するツール（`index_paths`, `refresh_index`, `rag_delete_document`,
`trigger_workflow`, `git_add` など）を全て `read` として誤分類していた
（現在は修正済み）。`tests/test_tool_policy_comprehensive.py` と
`tests/test_tool_approval_risk.py` がこの分類の回帰を検証する。

### 直列化メカニズムは単一のスケジューラに統合された

以前は、標準実行パス（`agent/tool_runner.py::_execute_standard()`、`serial_tool_calls=True`時に有効）
による「バッチ内に write ツールが1つでもあれば全体を直列化する」バッチ単位ダウングレードと、
`ToolSpec.requires_serial`によるツール単位の強制シリアル化という、意図的に分離された2つのメカニズムが
併存していた。`_execute_standard()`は削除され、`agent/tool_runner.py::_execute_with_dag()`が
唯一の実行パスになったことで、直列化の判断はすべて`agent/tool_scheduler.py::build_execution_groups()`
（フェーズ構築 + コンフリクトグラフ + `force_serial`入力）に一本化された:

| ソース | 挙動 |
|---|---|
| `ToolSpec.requires_serial`（個々のツール。現状は MDQ の `index_paths`/`refresh_index`、shell の `shell_run` など） | インプレースのバリアとして単独のシリアルフェーズを形成する |
| `resource_scopes`の重複（うち少なくとも1件は`is_write=True`。スコープなしwriteは合成スコープ`"global:write"`として扱われる） | コンフリクトグラフの連結成分としてグループ化され、そのグループ内はシリアル化される |
| `ctx.cfg.tool.serial_tool_calls=True` → `force_serial=True`（バッチ単位の入力） | 上記すべてをバイパスし、呼び出し順に1件ずつの単独シリアルフェーズを強制する |

`shared/tool_executor_helpers.py::is_side_effect()`はもはやこの判断に関与しない — 現在は
`shared/tool_executor.py`のTTLキャッシュのバイパス判定にのみ使われる、無関係な別メカニズムである。

---

## ルーティングの信頼できる情報源

ルーティング権威は単一構成: `RuntimeToolRegistry` のみ。`ToolRegistry` はルーティング判断には一切使われない。

| 入力 | 役割 | 要件 |
|---|---|---|
| `shared/runtime_tool_registry.py` | **唯一のルーティング権威** | McpToolDiscoveryService によりライブ `/v1/tools` discovery で構築 |
| `shared/tool_registry.py` | **ドリフト検出用の入力**（ルーティングには使われない） | `tool_constants.py` の frozenset からインポート時に構築 |
| ライブの `/v1/tools` discovery | **RuntimeToolRegistry のソース** | 起動時に McpToolDiscoveryService によって取得され、RuntimeToolRegistry に投入 |

**所有ルールの要約:**
- ツールを追加する場合: `tool_constants.py` の適切な frozenset に追加する。`ToolRegistry` はインポート時に自動構築される（ドリフト検出用）。
- RuntimeToolRegistry は McpToolDiscoveryService によってライブ `/v1/tools` discovery から構築される、唯一のルーティング権威である。
- config の `tool_names` はルーティングの入力ではない; あくまでドリフト検証用のメタデータである。
- 未知のツールは `ValueError` で即時失敗する — フォールバックは存在しない。
- config の `tool_names` 省略 / 空リスト / 設定済み の3つの状態のTOML例は [`docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`](04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md) を参照。
- 同じツール名が複数のサーバーの `/v1/tools` レスポンスで報告される重複所有権は、`shared/route_resolver.py::build_discovery_map()` で検出され、`McpToolDiscoveryService` が `ServiceWarning` として表示する — レジストリの自身によるサーバー間検証ではない。

---

## Tool Registry (`shared/tool_registry.py`)

MCP ツール定義と所有権に関するドリフト検出用データ。ルーティングには使われない。

| ソース | 種別 | 説明 |
|---|---|---|
| `shared/runtime_tool_registry.py` | **唯一のルーティング権威** | McpToolDiscoveryService によりライブ `/v1/tools` discovery で構築 |
| `shared/tool_registry.py` | **ドリフト検出用の入力**（ルーティングには使われない） | ツール→サーバー逆引き; `tool_constants.py` frozensetからimport時に自動構築 |
| Live `/v1/tools` discovery | **RuntimeToolRegistry のソース** | 起動時に McpToolDiscoveryService によって取得され、RuntimeToolRegistry に投入 |

### 所有権モデル

- 各ツールは**正確に1つのサーバー**に属する（`server_key` で識別される）。
- レジストリは `tool_constants.py` の frozenset からインポート時に構築される。
- config の `*_mcp_server.toml` の `tool_names` リスト（各 `[mcp_servers.<key>]` セクション内）はレジストリに対して検証されるが、信頼できる情報源として必須ではない。
- サーバーの `/v1/tools` レスポンスは、ドリフト検出のため起動時にレジストリと照合される。
- **重要:** ライブ discovery はレジストリを上書きしない。`/v1/tools` がツールに対してレジストリと異なる `server_key` を返す場合、起動時に `check_routing_drift_vs_live()` によってドリフトとしてフラグが立てられる。

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_02_tool-registry.md`
- `04_mcp_03_03_transport-and-health.md`
- `04_mcp_03_03_transport-and-health.md`
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
