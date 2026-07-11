# MCP ルーティング、ライフサイクル、実行

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
        3. MCP server dispatch via internal method
             → McpServerHealthRegistry: is_unavailable? → return error immediately (no attempt made)
             → LifecycleProtocol.ensure_ready(server_key)
             → concurrency semaphore acquire (if configured)
             → HttpTransport.call()
             → HealthRegistry.record_success() on success / record_failure() on transport error
             → return ToolCallResult(output, is_error, request_id, server_key)
```

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
| `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs, fts_consistency_check, fts_rebuild) | `mdq` |
| `GIT_TOOLS` (git_status, git_log, git_diff, git_branch, git_show, git_add, git_commit, git_checkout, git_pull, git_push) | `git` |
| 一致なし | `ValueError` |

**重要:** 未知のツールは `ValueError` で即時失敗する。新しいツールは常に `ToolRegistry` を経由して（`tool_constants.py` の frozenset を介して）登録しなければならない。

```python
resolver = ToolRouteResolver(server_configs)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

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

### ドリフト検証

3つの比較関数が設定のドリフトを検出する。

| 関数 | 比較対象 | 呼び出しタイミング |
|---|---|---|
| `validate_routing_against_config()` | config の `tool_names` 対 レジストリ | 起動時（`repl_health.py` の `check_routing_drift()`） |
| `validate_routing_against_live()` | ライブの `/v1/tools` 対 レジストリ | 起動時（`repl_health.py` の `check_routing_drift_vs_live()`） |
| `validate_all_routing()` | 上記両方の組み合わせ | まだ組み込まれていない（将来対応） |

> **起動時検証のセマンティクス** — 上記の `validate_routing_against_live()` および
> `validate_all_routing()` 関数は、ライブの `/v1/tools` を内部ルーティングレジストリと比較する。
> これらは `repl_health.py` のツール定義チェックとは異なる。ツール定義チェックは、
> （`agent.toml` からの）設定済み `tool_definitions` をライブの `/v1/tools` と比較するものである。
> `tool_definitions_strict` の起動失敗時の挙動については、
> [04_mcp_06 §Startup Validation Behavior](04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md#startup-validation-behavior-tool_definitions_strict) を参照。

ドリフト警告はエージェント起動時に表示される。

```
WARNING Routing drift [file_read]: [file_read] tool 'read_multiple_files' in registry but not in config. Update file_read_mcp_server.toml [mcp_servers.file_read] tool_names or the registry to resolve.
```

### 新しいツールの追加

| ステップ | アクション | 必須か |
|---|---|---|
| 1 | `shared/tool_constants.py` の適切な frozenset にツール名を追加する | **[必須]** |
| 2 | レジストリはインポート時にこれらの frozenset から自動構築される — レジストリの手動編集は不要 | （自動） |
| 3 | 所有する MCP サーバー（`mcp/<name>/server.py`）に `dispatch()` ハンドラーを実装する | **[必須]** |
| 4 | `/v1/tools` エンドポイントでツールを公開する（`server_key` フィールドを含むツール定義を返す） | **[推奨]** — `check_routing_drift_vs_live()` による起動時ドリフト検出を可能にする |
| 5 | `config/tools_definitions.toml` に LLM スキーマを追加する（OpenAI function-calling 形式） | **[必須]** — ツールを LLM に見せる場合 |
| 6 | 新ツール用に `config/agent.toml` に `tool_safety_tiers` エントリを追加する | **[必須]** — 全てのツールは安全性ティアを宣言しなければならない |
| 7 | `config/<key>_mcp_server.toml` の `[mcp_servers.<key>]` セクションの `tool_names` にツール名を追加する | **[任意]** — 起動時ドリフト検証のみを可能にする; ルーティングには不要 |

**推奨手順**: ToolRegistry の frozenset に追加する（ステップ1）+ `/v1/tools` エンドポイントで公開する（ステップ4）。config の `tool_names`（ステップ7）はルーティングの入力ではない; あくまでドリフト検証用のメタデータである。未知のツールは即時失敗する — フォールバックは存在しない。`/v1/tools` でツールを公開することで、`check_routing_drift_vs_live()` による起動時ドリフト検出が可能になる; ルーティングには影響しない。

### 検証

登録完了後:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

期待結果: 全てのルーティングテストがパスすること。`tool_definitions_strict = true` の場合、エージェントを再起動し、起動ログに `"Routing: N/N tools mapped"` が表示され、未マッピングの警告がないことを確認する。

### 主要 API

```python
from shared.tool_registry import get_registry, validate_all_routing

registry = get_registry()
server_key = registry.get_server_for_tool("read_text_file")  # → "file_read"
tool_names = registry.get_tool_names("file_read")  # → ["read_text_file", ...]
all_tools = registry.get_all_tool_names()  # → frozenset of all tool names
mismatches = validate_all_routing(server_configs, live_tool_lists)  # → dict[str, list[str]]
```

```python
executor = ToolExecutor(
    http=httpx.AsyncClient(...),
    cache_ttl=300.0,
    server_configs=server_configs,
    cache_max_size=200,
    concurrency_limits={"file_write": 1},
    lifecycle=lifecycle_router,
)
result = await executor.execute("read_text_file", {"path": "/opt/llm/..."})
# result: ToolCallResult(output, is_error, request_id, server_key)
```

### キャッシュの挙動

- `is_error=False` の結果のみキャッシュする
- キャッシュキー: `"tool_name:args_json"`（プレーンな文字列; MD5 ではない）
- エントリは `cache_ttl` 秒後に失効する
- `cache_max_size > 0` の場合は LRU により削除される（`0` = 無制限）
- キャッシュヒット時: `request_id=""`（ライブリクエストは行われない）
- 統計: `stat_cache_hits: int`

### 並行数制限

`concurrency_limits={"server_key": N}` は、サーバーごとの同時呼び出しを N 件に制限する。
遅延生成される `asyncio.Semaphore` として実装されている。未知のキーの場合 → warning ログのみ出力。

### 副作用検出

```python
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
is_side_effect(tool_name: str) -> bool
```

`execute_all_tool_calls()` が副作用を持つツールを1つでも検出した場合、`serial_tool_calls`
の設定に関わらず、そのラウンドの全ての呼び出し（副作用のないツールを含む）を直列化する。

---

## HttpTransport (`shared/tool_executor.py`)

```python
HttpTransport(http, base_url, server_key, cfg=McpServerConfig)
result = await transport.call("tool_name", {"arg": "val"})
```

- `cfg.auth_token` が空でない場合、`Authorization: Bearer <token>` を追加する
- 全てのトランスポートレベルの障害（タイムアウト、HTTP 非 2xx、不正な形式のレスポンス、リトライ消尽）で `TransportError` を発生させる; `is_error=True` を直接返すことはない
- トランスポートエラーハンドラーが `TransportError` を捕捉し、`ToolCallResult(error_type="transport")` に変換する
- `set_session_id(session_id)` はリクエストごとに `X-Session-Id` ヘッダーを注入する
- **リトライ:** HTTP 429/502/503/504 でリトライを行う。最大3回の試行で、遅延時間は減少していく: 試行0回目は4秒待機、試行1回目は2秒待機、試行2回目は1秒待機した後、最終的な消尽エラーとなる。計算式: 2^(RETRY_MAX - attempt - 1)。これは指数バックオフではない（試行ごとに遅延が減少する）。HealthRegistry に記録されるのは最終結果のみ（成功、または全リトライ消尽後の TransportError）。
- **リトライ不可のエラー:** HTTP タイムアウト（`httpx.TimeoutException`）と、429/502/503/504 以外のステータスコードによる HTTPStatusError は、リトライなしで即時に伝播する。

---

## McpServerHealthRegistry (`shared/mcp_config.py`)

`_build_tool_executor()`（factory.py）内で作成され、`ToolExecutor`（`set_health_registry()` 経由）と
`AppServices.health_registry` の間で共有される、サーバーごとの失敗トラッカー。
両者は同一のオブジェクトを保持するため、`ToolExecutor` によって記録されたヘルス状態は
`AppServices.health_registry` を通じて即座に可視化される。

**状態遷移:**

```
HEALTHY ──(failure × threshold)──→ UNAVAILABLE
   ↑                                    │
   │                            (cooldown 30s elapsed)
   │                                    ↓
   └──(record_success)────────── HALF_OPEN (trial probe)
                                        │
                              (failure)─┘ → UNAVAILABLE (cooldown reset)
```

| 状態 | 条件 |
|---|---|
| `HEALTHY` | 失敗なし、または呼び出し成功後 |
| `DEGRADED` | 失敗回数 < しきい値（デフォルト3） |
| `UNAVAILABLE` | 失敗回数 ≥ しきい値; ディスパッチはブロックされる |
| `HALF_OPEN` | 30秒のクールダウン経過後; 1回の試行ディスパッチが許可される |

| メソッド | 説明 |
|---|---|
| `record_failure(server_key)` | 失敗回数をインクリメント; `HALF_OPEN → UNAVAILABLE`（クールダウンリセット); しきい値到達時 → `UNAVAILABLE` |
| `record_degraded(server_key, reason)` | オプションの理由文字列とともに、状態を明示的に `DEGRADED` に設定する; 到達可能だが再起動不可なサーバーに対してウォッチドッグから呼び出される |
| `get_degraded_reason(server_key)` | 最後に記録された degraded の理由文字列を返す。設定されていない場合は `None` |
| `record_success(server_key)` | 失敗回数、unavailable タイムスタンプ、degraded の理由をリセット; `HALF_OPEN → HEALTHY` |
| `get_state(server_key)` | 現在の状態; 未知のキーの場合は `HEALTHY` を返す |
| `is_unavailable(server_key)` | `UNAVAILABLE` であり、かつクールダウンがまだ経過していない場合 `True`; 副作用として、クールダウン経過時に `HALF_OPEN` へ遷移する |

**コンストラクタ:** `McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=30.0)`
- `half_open_cooldown_sec`: `UNAVAILABLE` に入ってから試行ディスパッチが許可されるまでの秒数（デフォルト30秒、固定値 — 指数バックオフではない）

---

## エンドツーエンドのツール呼び出し追跡

### 相関キー

| キー | 生成元 | 出現箇所 |
|---|---|---|
| `X-Session-Id` | エージェント（`ctx.session.session_id`） | HTTP リクエストヘッダー; MCP サーバーアクセスログ; エージェント audit ログ |
| `X-Request-Id` | MCP サーバー（リクエストごとの UUID） | HTTP レスポンスヘッダー; MCP サーバーアクセスログ; エージェント audit ログ（`x_request_id`） |
| `server_key` | `McpServerConfig.key` | エージェントルーティングログ; `ToolCallResult.server_key`; health registry; トランスポートエラーカウンター |
| `tool_name` | LLM のツール呼び出し | エージェント audit ログ; MCP サーバーリクエストログ; ツールエラーカウンター |

1つのツール呼び出しを追跡するには、`X-Request-Id`（呼び出しごとに一意）と `X-Session-Id`（セッション全体に及ぶ）を結合する。

---

### 成功パスの例

```
1. Agent: LLM emits tool_use for "read_text_file"
   → tool_runner.execute_one_tool_call(ctx, name="read_text_file", ...)
   → ToolRouteResolver.resolve("read_text_file") → server_key="file_read"

2. Agent → Server (HTTP):
   POST /v1/call_tool
   X-Session-Id: 42
   body: {"name": "read_text_file", "args": {...}}

3. MCP server (file-read-mcp):
   Server log: INFO [42] read_text_file args=... → OK
   Response: X-Request-Id: abc-123, is_error=false, result="..."

4. Agent receives:
   ToolCallResult(output="...", is_error=False, request_id="abc-123", server_key="file_read")

5. Agent audit_tool_exec():
    audit log entry (JSON-lines): {"event":"tool_exec","task_id":"...","tool":"read_text_file","mcp_request_id":"abc-123","is_error":false,"error_type":"","ts":...}

6. Health registry:
   HealthRegistry.record_success("file_read") → state remains HEALTHY
```

---

### 失敗パスの例（トランスポートエラー）

```
1-2. Same as above.

3. MCP server unreachable (timeout / 5xx):
   HttpTransport raises TransportError.

4. Agent:
   Transport error handler records the error for "file_read"
   → stat_transport_errors["file_read"] += 1
   → HealthRegistry.record_failure("file_read") → state: HEALTHY → DEGRADED

5. ToolCallResult:
   (output=str(error), is_error=True, server_key="file_read", error_type="transport")

6. audit_tool_exec():
    audit log (JSON-lines): {"event":"tool_exec","task_id":"...","tool":"read_text_file","mcp_request_id":"","is_error":true,"error_type":"transport","ts":...}
    Note: mcp_request_id="" because no response was received.

7. Watchdog (next interval):
   repl_health.watchdog_loop() polls file-read-mcp /health
   → if alive: HealthRegistry.record_success("file_read") → HALF_OPEN → HEALTHY
   → if dead: HealthRegistry.record_failure("file_read") → DEGRADED → UNAVAILABLE
```

---

### 追跡におけるツールエラーとトランスポートエラーの違い

| フィールド | ツールエラー | トランスポートエラー |
|---|---|---|
| `is_error` | `True` | `True` |
| `error_type` | `"tool"` | `"transport"` |
| `mcp_request_id` | 設定される（サーバーが応答した） | `""`（レスポンスを受信していない） |
| `HealthRegistry` | `record_success()`（サーバーが応答した） | `record_failure()`（サーバーに到達不可） |
| `stat_tool_errors` | インクリメントされる | 変化なし |
| `stat_transport_errors` | 変化なし | インクリメントされる |

ツールエラーとは、サーバーがリクエストを処理したがエラーを返したことを意味する。
トランスポートエラーとは、エージェントがサーバーからのレスポンスを一度も受信しなかったことを意味する。

運用上の追跡手順については [04_mcp_06 §End-to-End Tool Call Tracing](04_mcp_06_08_end-to-end-tool-call-tracing.md#end-to-end-tool-call-tracing) を参照。

---

## ウォッチドッグ

MCP 障害の診断手順については `04_mcp_06` §MCP Failure Diagnosis を参照。

asyncio のバックグラウンドタスクとして実行される。`mcp_watchdog_interval > 0` の場合に有効化される。

**プロファイルに応じたデフォルト値:**

| `security_profile` | `mcp_watchdog_interval` のデフォルト |
|---|---|
| `local`（デフォルト） | `0.0` — ウォッチドッグ無効 |
| `production` | `30.0` — ウォッチドッグ有効 |

プロファイルのデフォルト値を上書きするには、`config/agent.toml` で `mcp_watchdog_interval` を明示的に設定する。

起動時、エージェントは以下のいずれかをログに記録する。
- `Watchdog enabled: interval=<N>s, max_restarts=<M>` — interval > 0 の場合
- `Watchdog disabled (mcp_watchdog_interval=0)` — interval が 0 の場合

- `mcp_watchdog_interval` 秒ごとにポーリングする
- HTTP サーバーに対して `GET /health` を呼び出す（subprocess、persistent、外部管理の全モード）
- **再起動は `restart_recommended` の本文フィールドによって制御される:**
  - `reachable=False`（HTTP レスポンスなし）: `mcp_watchdog_max_restarts` 未満であれば subprocess モードのサーバーの再起動を試みる
  - `reachable=True` かつ `restart_recommended=true`: 上記と同様に再起動を試みる
  - `reachable=True` かつ `restart_recommended=false`: 再起動なし; `operator_action_required=true` の場合は WARNING をログに記録（認証情報の欠落、バイナリの欠落など）
- 再起動時: subprocess を終了させ（`proc.terminate()`）、3秒待機し、必要であれば kill する; その後新しい HTTP subprocess を起動し `/health` をポーリングする
- 外部管理サーバー（非subprocess）: warning のみをログに記録し、再起動は行わない
- 最大再起動回数: `mcp_watchdog_max_restarts`（デフォルト3）

---

## ライフサイクルフロー

ツール定義の起動時バリデーション動作については `04_mcp_06` §Startup Validation Behavior を参照。

```
AgentREPL.run()
  → MCP server startup
       → startup_mode="subprocess" (http): start_http_subprocess() + health poll
            stderr → /opt/llm/logs/mcp/{server_key}.stderr.log (append mode)
       → startup_mode="persistent" (http): no lifecycle action needed
       → startup_mode="none": no subprocess spawn, no health check — server is disabled
   → [REPL loop]
        → tool call → ToolExecutor._raw_execute()
             → _check_startup_mode(server_key): startup_mode="none" rejects immediately
                  with a "disabled" tool error, before health check or transport
             → ensure_ready(server_key):
                  if _shutting_down: return immediately (shutdown guard)
                  if subprocess-mode and not running: start() [auto-restart on demand]
        → watchdog task: health check + restart on failure
   → finally: lifecycle.shutdown_all()
                  sets _shutting_down=True (blocks further start/restart calls)
                + close stderr log file handles
                + AsyncClient.close()
```

`_ServerLifecycleRouter._shutting_down` は `ensure_ready()`, `start_http_subprocess()`,
`restart()`, `shutdown_idle()` を保護する: `shutdown_all()` が呼び出された後は、これらのメソッドは
ログ行を出力して即座にリターンし、`HttpServerLifecycleManager` への委譲は行わない。

### プロセスの内部確認

`HttpServerLifecycleManager` は診断用途（例: `/mcp status` コマンド、`mcp_status.py`）のために、
管理下の subprocess の読み取り専用スナップショットを公開する。

- `get_process_snapshot(server_key) -> dict | None` — 既知の `server_key` に対して
  `{pid, pgid, running, last_exit_code}` を返す。未知の場合は `None`。`pgid` は `_http_pgids`
  から取得される（`start()` 時に `os.getpgid()` によって設定される、H-8 プロセスグループシャットダウン）。
- `get_process_info(server_key) -> ProcessInfoSnapshot | None` — 同じフィールドに加えて
  `managed` と `stderr_log` を含む型付き dataclass。
- `list_processes() -> list[ProcessInfoSnapshot]` — 現在管理されている全 subprocess サーバーの
  スナップショット。

これらのメソッドは `proc.poll()` やキャッシュ状態の読み取りのみを行う; プロセスの終了や
再起動は一切行わない。

`_ServerLifecycleRouter`（`factory.py` 内のファサード）はこれら3つ全てを
`HttpServerLifecycleManager` への薄い委譲として公開しているため、`McpStatusService` などの
呼び出し元は `_http_mgr` の内部に直接アクセスすることなく、
`getattr(lifecycle, "get_process_snapshot", None)` のダックタイピングでアクセスできる。

---

## 新しい MCP サーバーの追加

### 新しいツールを安全に追加する方法

新しいツールを追加する際は、上記の [Adding a new tool](#adding-a-new-tool) セクションにある
標準的な7ステップの手順に従うこと。

要点:
1. **`shared/tool_constants.py` の frozenset にツール名を追加する** [必須] — 内部レジストリ登録関数がインポート時にこれらの frozenset を読み込み、ルーティングレジストリを自動的に構築する。レジストリの手動編集は不要。
2. **`GET /v1/tools` エンドポイントを追加する** [推奨] — `check_routing_drift_vs_live()` による起動時ドリフト検証を可能にする; ルーティングには影響しない。
3. **サーバー設定に `tool_names` を追加する** [任意] — ドリフト検証のヒントのみ; ルーティングには不要。
4. **`config/tools_definitions.toml` に LLM スキーマを追加する** [ツールを LLM に見せる場合は必須]
5. **`config/agent.toml` に `tool_safety_tiers` エントリを追加する** [必須 — 全てのツールは安全性ティアを宣言しなければならない]

```toml
[mcp_servers.my_server]
transport = "http"
url = "http://127.0.0.1:8015"
tool_names = ["my_tool_a", "my_tool_b"]
```

### ルーティング優先度の要約

| 層 | 役割 | ルーティングに使用するか |
|---|---|---|
| `ToolRegistry`（`tool_constants.py` の frozenset からインポート時に自動構築） | **唯一のルーティング権威**; 内部レジストリ登録関数によって構築される | Yes |
| ライブの `/v1/tools` discovery | **検証専用のソース**; 起動時に `check_routing_drift_vs_live()` によってドリフト検出に使用 | No |

**重要なルール:**
- **新しいツールは常に `ToolRegistry` を経由して登録しなければならない**。未知のツールは `ValueError` で即時失敗する。
- **ライブ discovery はルーティングに影響しない** — `/v1/tools` が異なる `server_key` を返す場合、ルーティングの上書きとしてではなく、ドリフトとしてフラグが立てられる。
- **config の `tool_names` はルーティングの入力ではない** — あくまでドリフト検出用の検証ヒントである。

### 新規サーバー/ツール登録チェックリスト

| 対象物 | 必須か | 備考 |
|---|---|---|
| `shared/tool_constants.py` — frozenset にツールを追加 | **必須** | レジストリはインポート時に frozenset を読み込む |
| `config/tools_definitions.toml` — LLM スキーマを追加 | **必須**（ツールを LLM に見せる場合） | OpenAI function-calling 形式; LLM がツールを呼び出すために必要 |
| `config/agent.toml` — `tool_safety_tiers` エントリを追加 | **必須** | 全てのツールは安全性ティアを宣言しなければならない |
| `config/<key>_mcp_server.toml` — サーバー設定ファイル | **必須** | サーバーアプリ設定 + `[mcp_servers.<key>]` トランスポートセクション |
| `deploy/deploy.sh` — インストール/コピーステップを追加 | **必須**（新規サーバーの場合） | デプロイに新規サーバーを含める必要がある |
| `routing.md` の更新 | **必須** | ドキュメントガイドは新規サーバーを参照する必要がある |

### 手動での作業手順

1. `mcp/<name>/server.py` で `MCPServer` をサブクラス化し、`dispatch()` をオーバーライドする
2. `server_key` フィールドを含むツール定義を返す `GET /v1/tools` エンドポイントを追加する
3. `shared/tool_constants.py` の frozenset にツール名を追加する（このサーバーが所有）
4. `config/tools_definitions.toml` に LLM スキーマを追加する（OpenAI function-calling 形式）
5. 各ツールについて `config/agent.toml` に `tool_safety_tiers` エントリを追加する
6. アプリ設定と `[mcp_servers.<key>]` トランスポートセクションを含む `config/<key>_mcp_server.toml` を作成する
7. `deploy/deploy.sh` のコピーリストに新しいファイルを追加する
8. `deploy/setup_services.sh` に起動ステップを追加する

### Tool_names の設定（ドリフト検出専用）

ツールレジストリは `tool_constants.py` の frozenset からインポート時に自動構築される。
ドリフト検出のため、`mcp_servers.toml` のサーバー設定に任意で `tool_names` を追加できる。

```toml
[mcp_servers.my_server]
transport = "http"
url = "http://127.0.0.1:8015"
tool_names = ["my_tool_a", "my_tool_b"]
```

`tool_names` が省略されている、または不完全であっても、レジストリは引き続き正しくルーティングする
（優先度2）が、起動時のドリフト検証で警告が出力される。
