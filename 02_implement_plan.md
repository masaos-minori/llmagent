# 02_implement_plan.md
# MCP トランスポート透過化とデュアル起動モード — 実装計画

---

## Goal

エージェントが MCP サーバのトランスポート種別（HTTP / stdio）と起動ポリシー（persistent / ondemand）を意識せずにツールを呼び出せるようにする。

具体的な達成条件:
- `ToolExecutor` がトランスポートを透過的に扱い、呼び出し元は `(tool_name, args)` のみ指定する
- 各 MCP サーバが `persistent`（常時稼働）または `ondemand`（初回呼び出し時に起動）のどちらかの起動ポリシーで動作する
- `/mcp`、watchdog、tool-definition チェックがトランスポートと起動ポリシーの両方に対応する

---

## Scope

### 対象ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/shared/mcp_config.py` | `McpServerConfig` に `startup_mode` / `healthcheck_mode` / `idle_timeout_sec` / `working_dir` / `env` を追加 |
| `scripts/shared/tool_executor.py` | `_route()` を `ToolRouteResolver` に置換; `ServerLifecycleManager.ensure_ready()` 呼び出しを挿入 |
| `scripts/agent/repl.py` | `_start_stdio_servers()` を lifecycle manager 経由に変更; ondemand サーバをスキップ |
| `scripts/agent/repl_health.py` | `watchdog_loop()` に stdio 用 ping/list_tools 健全性チェックを追加; `check_tool_definitions()` を stdio 対応に拡張 |
| `scripts/agent/commands/cmd_mcp.py` | `/mcp` 表示に `startup_mode` / `healthcheck_mode` 列を追加 |
| `scripts/mcp/server.py` | `list_tools()` メソッドと `health()` メソッドを追加 |
| `config/agent.toml` (参考) | `mcp_servers.*` に `startup_mode` / `healthcheck_mode` / `tool_names` を追記する例を文書化 |

### 新規ファイル

| ファイル | 内容 |
|---|---|
| `scripts/agent/lifecycle.py` | `ServerLifecycleManager` クラス |
| `scripts/shared/route_resolver.py` | `ToolRouteResolver` クラス |

### スコープ外

- 本計画は設計と起動ポリシー制御の変更に限定する
- MCP サーバのビジネスロジック（ファイル操作・GitHub・Web 検索の実装）は変更しない
- `idle_timeout_sec` によるアイドル自動停止は Step 3 で骨格のみ設置し、実動作は別タスクとする
- OpenRC サービス定義ファイルの変更はなし（HTTP + persistent は現行モデルを維持）

---

## Assumptions

1. **既存実装の活用**: `HttpTransport` / `StdioTransport` / `MCPServer.run_stdio()` / `--stdio` フラグはすべてのサーバで実装済みであり、今回は手を加えない
2. **後方互換**: `startup_mode` フィールドが `config/agent.toml` に存在しない場合、`http` サーバは `persistent`、`stdio` サーバは `persistent` をデフォルトとする（現行動作を保持）
3. **ルーティング**: 現行の `_route()` は tool 名の prefix / frozenset マッチングで server_key を返す。`ToolRouteResolver` は `McpServerConfig` に `tool_names: list[str]` フィールドを追加することで config 駆動ルーティングを実現する
4. **tool_definitions_strict**: stdio サーバに対する `check_tool_definitions()` 拡張は、stdio が起動していない場合はスキップする（HTTP サーバと同じ「unreachable は無視」ポリシーを踏襲）
5. **list_tools プロトコル**: stdio サーバへの `list_tools` 問い合わせは `StdioTransport.call("__list_tools__", {})` という予約ツール名で実装する。`MCPServer.run_stdio()` のループがこの名前を `list_tools()` に振り向ける
6. **Python バージョン**: 3.13。型ヒントに `dataclasses.field` / `typing` を使用

---

## Unknowns

| # | 不明点 | 判断 |
|---|---|---|
| U1 | `tool_names` フィールドを `McpServerConfig` に追加する場合、既存の `_build_mcp_servers()` 後方互換パスで `tool_names` が空のとき `ToolRouteResolver` は旧 frozenset 静的マッピングにフォールバックするか | **解消済み**: `tool_names=[]` のとき旧 frozenset フォールバックを維持する方針で確定 |
| U2 | `ServerLifecycleManager` は `ToolExecutor` に注入するか、`AgentContext.services` に配置するか | **解消済み**: `AgentContext.services.lifecycle` に配置し、`ToolExecutor` には `LifecycleProtocol`（Protocol 型）として注入する方針で確定。`agent/repl.py` のコンストラクタ呼び出し変更を伴う |
| U3 | `config/agent.toml` の `mcp_servers` に `tool_names` を手書きするのは煩雑。自動的に `/v1/tools` または `__list_tools__` から取得して設定を生成する仕組みが必要か | **解消済み**: `tool_names` は手動設定とし、空のとき旧ルーティングにフォールバック。stdio の tool 一覧問い合わせは `StdioTransport.call("__list_tools__", {})` 予約ツール名方式で確定。自動生成は別タスク |

---

## Affected areas

```
scripts/shared/
  mcp_config.py          ← McpServerConfig 拡張
  tool_executor.py       ← _route() 廃止, ToolRouteResolver 注入, ensure_ready() 呼び出し
  route_resolver.py      ← 新規

scripts/agent/
  lifecycle.py           ← 新規 (ServerLifecycleManager)
  repl.py                ← _start_stdio_servers() 変更, lifecycle manager 生成
  repl_health.py         ← watchdog_loop() / check_tool_definitions() 拡張
  context.py             ← ServiceContainer.lifecycle フィールド追加
  commands/cmd_mcp.py    ← /mcp 表示拡張

scripts/mcp/
  server.py              ← list_tools() / health() メソッド追加

tests/
  test_tool_executor.py  ← ルーティング変更に対するテスト追加
  test_mcp_config.py     ← 新フィールドのバリデーションテスト追加
  test_lifecycle.py      ← 新規

docs/
  06_ref-agent-config.md ← McpServerConfig 新フィールドの説明追加
  docs/04_mcp-servers.md ← startup_mode 設定例追加
```

---

## Design

### McpServerConfig 拡張

```python
# scripts/shared/mcp_config.py

@dataclass
class McpServerConfig:
    transport: str          # "http" | "stdio"
    startup_mode: str       # "persistent" | "ondemand"  (新規)
    url: str                # HTTP base URL
    cmd: list[str]          # stdio subprocess command
    openrc_service: str     # OpenRC service name (HTTP watchdog 用)
    tool_names: list[str]   # このサーバが担うツール名一覧 (新規; 空=旧ルーティング)
    healthcheck_mode: str   # "http" | "process" | "ping_tool"  (新規)
    idle_timeout_sec: int   # ondemand auto-stop 猶予秒 (新規; 0=無効)
    working_dir: str        # stdio subprocess の作業ディレクトリ (新規; ""=継承)
    env: dict[str, str]     # stdio subprocess への環境変数注入 (新規)
```

デフォルト値:
- `startup_mode`: `http` サーバ → `"persistent"`, `stdio` サーバ → `"persistent"`
- `healthcheck_mode`: `http` サーバ → `"http"`, `stdio` サーバ → `"process"`
- `tool_names`: `[]`（旧 frozenset ルーティングへフォールバック）

### ToolRouteResolver

```
scripts/shared/route_resolver.py

class ToolRouteResolver:
    __init__(server_configs: dict[str, McpServerConfig]) -> None
    resolve(tool_name: str) -> str   # server_key を返す。未解決は ValueError
```

解決ロジック:
1. `tool_names` が空でないサーバから `tool_name` を逆引き（O(n)、起動時に `dict[tool_name→server_key]` を構築して O(1) に）
2. 全サーバの `tool_names` が空の場合、旧 frozenset 静的マッピングにフォールバック

### ServerLifecycleManager

```
scripts/agent/lifecycle.py

class ServerLifecycleManager:
    ensure_ready(server_key: str) -> None (async)
      - persistent: 既に起動済みなら no-op
      - ondemand  : 未起動なら StdioTransport.start() を呼び出し ToolExecutor に登録
    shutdown_all() -> None (async)
      - 全 stdio プロセスを StdioTransport.stop() で停止
    shutdown_idle() -> None (async)
      - idle_timeout_sec > 0 のサーバのうち、最終呼び出しから規定秒経過したものを停止
      - 本計画では骨格のみ実装（呼び出し元からは未接続）
```

`ToolExecutor` への注入:
- `ToolExecutor.__init__` に `lifecycle: LifecycleProtocol | None = None` を追加
- `_raw_execute()` の先頭で `await self._lifecycle.ensure_ready(server_key)` を呼ぶ
- `LifecycleProtocol` は `shared/` で定義し `agent/lifecycle.py` が実装する（依存方向を保持）

### check_tool_definitions() — stdio 対応

```
for key, srv_cfg in ctx.cfg.mcp_servers.items():
    if srv_cfg.transport == "http":
        # 従来通り GET /v1/tools
    elif srv_cfg.transport == "stdio":
        transport = ctx.services.stdio_procs.get(key)
        if transport is None or not transport.is_alive():
            continue   # 未起動はスキップ
        result, is_error = await transport.call("__list_tools__", {})
        if not is_error:
            server_names.update(orjson.loads(result)["tools"])
```

`MCPServer.list_tools()` はサブクラスで `[t["function"]["name"] for t in self.mcp_tools]` を返す。
`MCPServer.run_stdio()` の dispatch ループで `name == "__list_tools__"` を捕捉し `list_tools()` の JSON を返す。

### watchdog_loop() — stdio 健全性

```
elif srv_cfg.transport == "stdio":
    transport = ctx.services.stdio_procs.get(key)
    if transport is None:
        continue
    if transport.is_alive():
        # healthcheck_mode == "ping_tool" のとき __list_tools__ を送信して応答を確認
        if srv_cfg.healthcheck_mode == "ping_tool":
            result, err = await transport.call("__list_tools__", {})
            ok = not err
        else:
            ok = True  # process モード: is_alive() のみで OK
```

### /mcp 表示拡張

```
/mcp status 出力例:

SERVER        TRANSPORT  MODE        STATUS   TOOLS
web_search    http       persistent  OK       1
file_read     http       persistent  OK       9
github        stdio      ondemand    STOPPED  12
shell         stdio      persistent  RUNNING  1
```

---

## Implementation steps

### Step 1: `McpServerConfig` 拡張と `ToolRouteResolver` 導入

1. `scripts/shared/mcp_config.py` に `startup_mode` / `healthcheck_mode` / `idle_timeout_sec` / `working_dir` / `env` / `tool_names` を追加
2. `_build_mcp_servers()` で新フィールドをパース; 後方互換デフォルト適用
3. `scripts/shared/route_resolver.py` を新規作成; `ToolRouteResolver` 実装
4. `scripts/shared/tool_executor.py`: `_route()` を `ToolRouteResolver.resolve()` に置換; `LifecycleProtocol` 定義と注入口を追加（lifecycle はこの時点では None）
5. `tests/test_tool_executor.py` を更新 (ルーティング変更); `tests/test_mcp_config.py` を更新 (新フィールド)
6. バリデーション: `ruff format / check`, `mypy`, `pytest`

### Step 2: `ServerLifecycleManager` 導入

1. `scripts/agent/lifecycle.py` を新規作成; `ServerLifecycleManager` 実装
   - `ensure_ready()`: ondemand かつ未起動なら `StdioTransport.start()` → `ToolExecutor.set_transport()` の順で起動
   - `shutdown_all()`: 全 stdio プロセスを停止
   - `shutdown_idle()`: 骨格のみ (pass 相当)
2. `scripts/agent/context.py`: `ServiceContainer` に `lifecycle: ServerLifecycleManager | None = None` を追加
3. `scripts/agent/repl.py`:
   - `_init_components()` で `ServerLifecycleManager` を生成し `ctx.services.lifecycle` に設定
   - `ToolExecutor` コンストラクタに `lifecycle=ctx.services.lifecycle` を渡す
   - `_start_stdio_servers()` を `startup_mode=persistent` のサーバのみ対象に変更
4. `tests/test_lifecycle.py` を新規作成
5. バリデーション: `ruff format / check`, `mypy`, `pytest`

### Step 3: watchdog と `check_tool_definitions()` の拡張

1. `scripts/agent/repl_health.py`:
   - `check_tool_definitions()`: stdio サーバに `__list_tools__` RPC を送信して tool 名を収集
   - `watchdog_loop()`: `healthcheck_mode == "ping_tool"` のとき `__list_tools__` で応答確認
2. `scripts/mcp/server.py`:
   - `list_tools()` を追加 (デフォルト: `[t["function"]["name"] for t in self.mcp_tools]`)
   - `health()` を追加 (デフォルト: `{"status": "ok"}` — HTTP サーバ用ダミー)
   - `run_stdio()` ループで `name == "__list_tools__"` を捕捉し `list_tools()` の JSON を返す
3. バリデーション: `ruff format / check`, `mypy`, `pytest`

### Step 4: `/mcp` 表示拡張

1. `scripts/agent/commands/cmd_mcp.py`:
   - `_cmd_mcp_http()` を `_cmd_mcp_status()` にリネーム
   - `startup_mode` / `healthcheck_mode` 列を出力テーブルに追加
   - stdio サーバのステータスを `RUNNING` / `STOPPED` / `STARTING` で表示
2. バリデーション: `ruff format / check`, `mypy`, `pytest`

### Step 5: ドキュメント更新

1. `docs/06_ref-agent-config.md`: `McpServerConfig` 新フィールドの説明を追記
2. `docs/04_mcp-servers.md`: `startup_mode` / `healthcheck_mode` 設定例を追記
3. `CLAUDE.md` Architecture 欄 — 変更ファイルを参照

---

## Validation plan

各 Step 完了後に以下を必ず通過してから次 Step に進む。

```bash
ruff format scripts/ tests/
ruff check scripts/ tests/ --fix && ruff check scripts/ tests/
mypy scripts/ tests/
PYTHONPATH=scripts lint-imports
pytest tests/ -v
```

Step 2 以降は追加で:

```bash
coverage run -m pytest tests/ && coverage xml
diff-cover coverage.xml --compare-branch=main --fail-under=90
```

Step 4 完了後は手動動作確認:

```bash
# HTTP + persistent サーバが通常通り起動することを確認
python scripts/agent.py

# /mcp status で transport / startup_mode / status が正しく表示されることを確認
# (REPL 内で) /mcp status

# stdio + ondemand サーバが初回ツール呼び出し時に起動することを確認
# (config/agent.toml に stdio + ondemand サーバを追加して検証)
```

---

## Risks

| # | リスク | 深刻度 | 対処 |
|---|---|---|---|
| R1 | `ToolRouteResolver` 切り替えで `tool_names=[]` のサーバのルーティングが旧 frozenset フォールバックに依存。フォールバックが壊れると全ツールが `ValueError` を投げる | 高 | Step 1 で旧 `_route()` のロジックを `ToolRouteResolver._fallback_route()` として保持し、既存テストで全ツール名を網羅した回帰テストを追加する |
| R2 | `LifecycleProtocol` の注入を誤り、`lifecycle=None` のまま `_raw_execute()` が `ensure_ready` を呼ぼうとすると `AttributeError` | 高 | `_raw_execute()` では `if self._lifecycle is not None` ガードを入れる; `lifecycle=None` のとき ondemand サーバへの初回呼び出しは「未起動」エラーを返す（現行動作と同等） |
| R3 | `__list_tools__` 予約ツール名が既存のサーバに同名ツールとして登録されていると衝突する | 低 | **確認済み**: 全 MCP サーバの `mcp_tools` に `__list_tools__` は存在しない。`__` プレフィックスを予約名規約としてドキュメントに明記する |
| R4 | ondemand stdio サーバの `ensure_ready()` が並行ツール呼び出し時に複数回 `start()` を発火する | 中 | `ServerLifecycleManager` に per-server `asyncio.Lock` を持たせ、`ensure_ready()` を Lock 内で実行する |
| R5 | `startup_mode` デフォルトが `persistent` なので既存の `stdio` サーバ設定は動作が変わらないが、`_build_mcp_servers()` の後方互換パス（`tool_names` / `startup_mode` なし）のテストが不十分だと新設定のみテスト済みになる | 中 | Step 1 のテストで「旧形式 dict → `McpServerConfig` 変換」を既存 fixture で動作確認する |
| R6 | `check_tool_definitions()` の stdio 拡張は、ondemand サーバが起動していない場合スキップするが、`tool_definitions_strict=true` 環境でスキップ扱いのサーバが多いと検証が空振りになる | 低 | strict モードの運用では persistent stdio サーバのみ `healthcheck_mode: ping_tool` を指定することを規約化してドキュメントに明記 |
| R7 | Step 3 の `watchdog_loop()` 変更でバグが混入すると watchdog が無限 ping ループになる | 中 | `healthcheck_mode: ping_tool` は watchdog 1 サイクルに 1 回のみ `__list_tools__` を送信し、タイムアウト（5s）を設定する。既存の `probe_mcp_health()` と同様に例外を catch してログに残す |
| R8 | `MCPServer.list_tools()` が `self.mcp_tools` を参照するが、`MCPServer` 基底クラスの `mcp_tools` は型注釈のみで値を持たない。基底クラスで直接呼ばれると `AttributeError` になる | 低 | `list_tools()` の実装を `[t["name"] for t in getattr(self, "mcp_tools", [])]` とするか、`mcp_tools: list[dict] = []` をデフォルト値付きで基底クラスに定義する。mypy は既存のサブクラスが `mcp_tools` を定義していないケースも検出するため、Step 3 の `mypy` 通過を確認する |
