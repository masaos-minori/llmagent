# 02_implement_plan.md

## Goal

`00_llm_spec_tobe.md` に記載された 3 つの仕様変更を実装する。

1. LLM モデルを Qwen3-Coder-30B-A3B-Instruct Q4_K_M に統一し、切換機能を除去
2. REPL パイプライン内 RAG 処理フロー (②MQE〜⑦Augment) を RAG MCP 呼出に変更し、呼出実行をオプションで選択
3. MCP サーバをエージェント起動時にサブプロセスとして自動起動 (OpenRC 不要)

---

## Scope

### In scope

- `scripts/agent.py`: docstring から `/chat`/`/code` コマンドの記述を削除
- `scripts/agent/commands/registry.py`: `/help` 出力から `/chat`/`/code` 行を削除
- `config/llm.toml`, `config/agent.toml`: LLM URL / モデル設定を Qwen3-Coder に統一
- `docs/05_agent-impl-flow.md`: REPL フロー図の gemma-4-e4b 記述を修正
- `scripts/agent/orchestrator.py`: RAG 呼出を in-process から MCP 優先に変更
- `scripts/agent/config.py`: `use_rag_mcp: bool` フィールド追加 (RAG MCP 呼出の on/off 制御)
- `scripts/agent/commands/cmd_rag.py` / `cmd_config.py`: `/rag` コマンド + `/reload` の同期対応
- `scripts/agent/lifecycle.py`: HTTP サーバーのサブプロセス起動サポート (`startup_mode="subprocess"`)
- `scripts/agent/repl.py`: HTTP サーバーの自動起動 + 起動待機ロジック
- `scripts/shared/mcp_config.py` / `agent/config.py`: `McpServerConfig` に `startup_mode="subprocess"` の追加バリデーション
- `config/agent.toml` (`mcp_servers`): 各 HTTP MCP サーバーに `cmd` / `startup_mode = "subprocess"` を追加
- `docs/04_mcp-protocol.md`: `startup_mode="subprocess"` の仕様追記
- `docs/06_ref-agent-config.md`: `McpServerConfig.startup_mode` 新値の説明追加

### Out of scope

- in-process `RagPipeline` の実装コード削除 (後方互換として維持)
- OpenRC スクリプト (`init.d/`) の削除
- 新 MCP サーバー追加
- テスト以外のインフラ変更

---

## Assumptions

- Qwen3-Coder-30B-A3B-Instruct Q4_K_M のエンドポイントは現行と同じ `http://127.0.0.1:8002/v1/chat/completions` を使用 (llama.cpp サーバーのモデル差し替えで対応)
- `/chat`/`/code` スラッシュコマンドはコードに実装がなく docstring のみに存在する (確認済み)
- `rag-pipeline-mcp` (port 8010) は既に実装済みで稼働可能
- RAG MCP 呼出の "オプション" は既存の `use_search` フラグで実現 (`use_search=false` で全 RAG 無効化)、または新フィールド `use_rag_mcp` で in-process と MCP を切り替え可能
- HTTP MCP サーバーのサブプロセス起動は `cmd` (起動コマンド) + ヘルスチェックポーリング (`/health`) で実現
- `startup_mode="subprocess"` は HTTP トランスポートにのみ適用 (stdio はすでに `persistent`/`ondemand` で対応)

---

## Unknowns

### U1: RAG MCP 呼出の "オプション" の意味

**問題:** "呼出実行をオプションで選択" が何を指すか不明確。

候補:
- **A**: 既存 `use_search: bool` の on/off のみで十分 (`use_search=false` → RAG 完全無効、`true` → MCP 経由)
- **B**: 新フィールド `use_rag_mcp: bool` を追加し、`true` → MCP 呼出、`false` → in-process パイプライン
- **C**: `use_search=true` + `rag_service_url` 設定で MCP、未設定で in-process (現行挙動を明示化するだけ)

**分析結果:** 現在の実装では `rag_service_url` が設定されると自動的に MCP モードになる。spec の intent は MCP をデフォルトにし、in-process を廃止または optional にすることと推測される。
→ 候補 B (`use_rag_mcp: bool`) が最も明示的で設計意図に合う。

**→ 解決済み。** ユーザー確認: `use_rag_mcp: bool` 方式 (候補 B) を採用。

### U2: HTTP MCP サーバーのサブプロセス起動待機方法

**問題:** HTTP サーバーをサブプロセスで起動した後、`/health` が OK になるまで待機する必要がある。タイムアウトと再試行回数が不明。

**分析結果:** 既存の `repl_health.py` が `/health` ポーリングロジックを持つ。
`startup_timeout_sec` (デフォルト 30 秒) を `McpServerConfig` に追加し、ヘルスチェックポーリングに流用するのが自然。
→ **解決済み。** `startup_timeout_sec: int = 30` を `McpServerConfig` に追加し、0.5 秒間隔でポーリング。

### U3: 既存 in-process RAG の扱い

**問題:** `use_rag_mcp=false` のとき in-process パイプラインを残すか、廃止するか。

**分析結果:** spec に「呼出実行をオプションで選択」とあり、in-process の廃止は明示されていない。
後方互換のため in-process コードは維持し、`use_rag_mcp=false` で切り替え可能とする。
→ **解決済み。** in-process コードを維持し、`use_rag_mcp: bool` で切り替える設計を採用。

### U4: HTTP サブプロセス起動コマンドの標準化

**問題:** 各 HTTP MCP サーバーの `cmd` をどう設定するか。
例: `["/opt/llm/venv/bin/python", "-m", "mcp.file.server"]` (HTTP モード = `--stdio` なし)

**分析結果:** 全サーバーが `if "--stdio" in sys.argv: run_stdio() else: run_http()` パターンを持つ。HTTP モードは `--stdio` なしで起動すれば良い。ポート番号は各サーバーの固定値を使用。
→ **解決済み。** `cmd = ["/opt/llm/venv/bin/python", "-m", "mcp.<name>.server"]` のパターンに統一。ポートは各サーバーの固定値を継続使用。

---

## Affected areas

| エリア | 変更種別 | 主なファイル |
|---|---|---|
| LLM モデル統一 | docstring/config のみ | `scripts/agent.py`, `config/llm.toml`, `config/agent.toml`, `docs/05_agent-impl-flow.md` |
| RAG MCP 切替 | 機能追加 (config フィールド + orchestrator 分岐) | `scripts/agent/orchestrator.py`, `scripts/agent/config.py`, `scripts/agent/commands/cmd_rag.py`, `scripts/agent/commands/cmd_config.py` |
| MCP サブプロセス起動 | 機能追加 (startup_mode 新値) | `scripts/agent/lifecycle.py`, `scripts/agent/repl.py`, `scripts/shared/mcp_config.py`, `config/agent.toml` |
| ドキュメント更新 | 記述追加/修正 | `docs/04_mcp-protocol.md`, `docs/06_ref-agent-config.md`, `docs/05_agent-impl-flow.md` |

---

## Design

### Phase 1 — LLM モデル統一 (config/docstring のみ)

`/chat`/`/code` コマンドは実装されていないため、以下の docstring/ドキュメント修正のみ:

- `scripts/agent.py` (L18-19): `/chat`/`/code` 行を削除
- `docs/05_agent-impl-flow.md` (REPL フロー ② MQE): `(gemma-4-e4b :8002)` 表記を `(:8002)` に変更、モデル名記述を除去
- `config/llm.toml`: コメントで Qwen3-Coder モデル名を明記

コード変更なし。

---

### Phase 2 — RAG MCP 呼出への変更

#### 2.1 AgentConfig に `use_rag_mcp: bool` を追加

```python
# agent/config.py
use_rag_mcp: bool = False
# True のとき Orchestrator が RAG 処理を rag-pipeline-mcp MCP ツール (rag_run_pipeline) 経由で実行
# False のとき in-process RagPipeline.augment() を使用 (現行動作)
```

`/reload` ホットリロード対応: `cmd_config.py` の `_apply_config_params()` に追加。

#### 2.2 Orchestrator の `_augment_with_rag()` を変更

```
use_rag_mcp=True  → ToolExecutor.execute("rag_run_pipeline", {"query": query, "history_context": ...}) 呼出
use_rag_mcp=False → 現行 RagPipeline.augment() 呼出 (変更なし)
```

`rag_run_pipeline` の結果 (JSON) から `augmented_text` フィールドを取り出してコンテキスト文字列として返す。

#### 2.3 `/rag` コマンドに `use_rag_mcp` の表示/制御を追加

```
/rag                   現在の全フラグ + rag_mcp on/off を表示
/rag mcp on|off        use_rag_mcp を切り替え
```

---

### Phase 3 — MCP サーバーサブプロセス自動起動

#### 3.1 `McpServerConfig` に `startup_mode="subprocess"` を追加

```python
# startup_mode の有効値: "persistent" | "ondemand" | "subprocess"
# "subprocess": transport="http" のサーバーをエージェント起動時にサブプロセスで起動し、
#               /health が 200 を返すまで startup_timeout_sec 秒ポーリングする
startup_timeout_sec: int = 30   # 起動待機タイムアウト秒数 (デフォルト 30)
```

#### 3.2 `ServerLifecycleManager` の変更

`_start_http_subprocess(server_key, cfg)` メソッドを追加:

```
1. subprocess.Popen(cfg.cmd, ...) でサーバープロセスを起動
2. /health に対して最大 startup_timeout_sec 秒ポーリング (0.5 秒間隔)
3. タイムアウト時は ValueError を送出 (既存 stderr ログ付き)
4. 成功時は self._http_procs[server_key] = proc に保持
```

`ensure_ready()` の拡張: `startup_mode="subprocess"` + `transport="http"` の場合に `_start_http_subprocess()` を呼ぶ。

`shutdown_all()` の拡張: `_http_procs` の全プロセスを `terminate()` → `wait()` でクリーンアップ。

#### 3.3 `AgentREPL._start_stdio_servers()` の変更

`startup_mode="subprocess"` の HTTP サーバーも `persistent` 相当として起動時に処理する。

#### 3.4 `config/agent.toml` の各 HTTP サーバーに `cmd` と `startup_mode` を追加

```toml
[mcp_servers.file_read]
transport = "http"
url = "http://127.0.0.1:8005"
cmd = ["/opt/llm/venv/bin/python", "-m", "mcp.file.server"]
startup_mode = "subprocess"
startup_timeout_sec = 30
openrc_service = "file-mcp"   # 後方互換のため維持 (watchdog 対象外に)
```

---

## Implementation steps

### Step 1: LLM 統一 (config/docstring)

1. `scripts/agent.py` L18-19: `/chat`/`/code` 行削除
2. `docs/05_agent-impl-flow.md` ② MQE 行: `(gemma-4-e4b :8002)` → `(:8002)`
3. `config/llm.toml`: コメントに `# Model: Qwen3-Coder-30B-A3B-Instruct Q4_K_M` を追記

検証: ruff/mypy/pytest

---

### Step 2: `use_rag_mcp` フィールド追加

1. `scripts/agent/config.py`: `use_rag_mcp: bool = False` を RAG フィールドグループに追加
2. `scripts/agent/commands/cmd_config.py`: `_apply_config_params()` に `ctx.cfg.use_rag_mcp = new_cfg.use_rag_mcp` を追加
3. `config/agent.toml`: `use_rag_mcp = false` のコメント付きエントリを追加

検証: ruff/mypy/pytest

---

### Step 3: Orchestrator の RAG 分岐

1. `scripts/agent/orchestrator.py` の `_augment_with_rag()` を修正:
   - `ctx.cfg.use_rag_mcp=True` のとき `ctx.services.tools.execute("rag_run_pipeline", ...)` を呼出
   - JSON レスポンスから `augmented_text` を抽出してコンテキスト文字列として返す
   - エラー時は in-process にフォールバック (`logger.warning` 付き)
2. `scripts/agent/commands/cmd_rag.py`: `/rag mcp on|off` サブコマンドを追加

検証: ruff/mypy/pytest + 手動 `/rag mcp on` でのスモークテスト

---

### Step 4: `McpServerConfig` と `ServerLifecycleManager` の拡張

1. `scripts/shared/mcp_config.py`: `startup_mode` の `__post_init__` バリデーションに `"subprocess"` を追加; `startup_timeout_sec: int = 30` フィールドを追加
2. `scripts/agent/lifecycle.py`:
   - `_http_procs: dict[str, asyncio.subprocess.Process]` を追加
   - `_start_http_subprocess()` を実装
   - `ensure_ready()` / `shutdown_all()` を拡張
3. `scripts/agent/repl.py`: `_start_stdio_servers()` を `_start_subprocess_servers()` にリネームし HTTP subprocess も処理
4. `config/agent.toml`: 各 HTTP サーバーに `cmd`/`startup_mode="subprocess"` を追加

検証: ruff/mypy/pytest + 起動テスト

---

### Step 5: ドキュメント更新

1. `docs/04_mcp-protocol.md` §2.3: `startup_mode="subprocess"` の説明を追加
2. `docs/06_ref-agent-config.md` §2: `McpServerConfig` の `startup_mode` 新値、`startup_timeout_sec` フィールドを追加
3. `docs/05_agent-impl-flow.md`: RAG 分岐フローを更新

---

## Validation plan

| ステップ | 検証内容 |
|---|---|
| Step 1 | ruff/mypy/pytest パス、`agent.py --help` に `/chat`/`/code` が消えていること |
| Step 2 | `AgentConfig` が `use_rag_mcp` フィールドを持つこと、`/reload` で反映されること |
| Step 3 | `use_rag_mcp=True` + rag-pipeline-mcp 起動状態で `/rag search <query>` が MCP 経由で結果を返すこと |
| Step 4 | `startup_mode="subprocess"` の HTTP サーバーがエージェント起動時に自動起動され、`/mcp status` で `running` と表示されること |
| Step 5 | docs との整合 (手動確認) |

---

## Risks

### R1: Qwen3-Coder でのMQE/Rerank プロンプト互換性

**リスク:** Qwen3-Coder は chat 用途に最適化されたモデルではなく、MQE や Cross-Encoder Rerank の few-shot プロンプトが期待通りに動作しない可能性がある。

**対処 (計画反映済み):**
- Step 3 の Validation plan に「`/rag search <query>` で MQE 展開クエリ数と Rerank スコアを目視確認」を追加
- プロンプトテンプレート調整が必要な場合は `config/agent.toml` の `mqe_prompt_template` / `rerank_prompt_template` をオーバーライドして対応 (コード変更不要)
- 調整が広範に及ぶ場合は別タスクとして独立させる

### R2: RAG MCP 経由での latency 増加

**リスク:** in-process → HTTP MCP 呼出への変更でターンごとに余分な HTTP ラウンドトリップが発生し、レイテンシが増加する。

**対処 (計画反映済み):**
- `use_rag_mcp: bool = False` をデフォルトに設定し、明示的に有効化したときのみ MCP 経由にする
- `rag-pipeline-mcp` を `startup_mode="subprocess"` で同一ホスト内起動することで HTTP ラウンドトリップを localhost に限定
- Validation plan に「`/stats` のターンレイテンシで in-process と MCP を比較」を追加

### R3: HTTP サブプロセス起動の冪等性

**リスク:** エージェントが再起動したとき、前回のサーバープロセスが残留しポート競合が発生する可能性がある。

**対処 (計画反映済み):**
- `startup_mode="subprocess"` の起動前に `/health` をポーリングし、既に起動済みであれば subprocess 起動をスキップして既存プロセスを再利用する
- `AgentREPL.__init__` で `atexit.register(lifecycle.shutdown_all)` を登録し、正常終了時にサブプロセスを必ず停止する
- プロセスが残留した場合の手動クリーンアップ手順を `docs/05_agent-ops.md` に追記する

### R4: `startup_mode="subprocess"` の HTTP/stdio 混在バリデーション

**リスク:** `transport="stdio"` に `startup_mode="subprocess"` を設定した場合の挙動が未定義。

**対処 (計画反映済み):**
- `McpServerConfig.__post_init__` に `transport="stdio"` + `startup_mode="subprocess"` の組み合わせを `ValueError` にするバリデーションを追加 (Step 4 で実装)
- エラーメッセージに `"startup_mode='subprocess' is only valid for transport='http'"` を明示する
