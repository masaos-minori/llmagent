# agent_repl.py / orchestrator.py

## 1. 機能概要

`AgentREPL` (`agent/repl.py`) は全コンポーネントを `AgentContext` へ依存性注入し、REPL ループを駆動する薄いコーディネータ。ターンレベルのロジック (RAG 付加・LLM ループ・ツールディスパッチ) は `Orchestrator` (`agent/orchestrator.py`) に委譲。`agent.py` が `AgentREPL().run()` で起動。

実装は 3 つのサテライトモジュールに分割:
- `agent/repl_health.py` — MCP 死活監視・ウォッチドッグループ
- `agent/repl_tool_exec.py` — ツール呼び出し承認・実行 (→ §4)
- `agent/repl_debug.py` — RAG デバッグプリンタ・コンテキストユーティリティ (純粋関数)

## 2. AgentREPL API

```python
from agent.repl import AgentREPL

await AgentREPL().run()
```

| メソッド | 説明 |
|---|---|
| `run() -> None` | readline 初期化 → `_init_components()` → セッション開始 → REPL ループ → リソースクローズ |
| `_init_components() -> None` | `LLMClient` / `ToolExecutor` / `HistoryManager` / `RagPipeline` / `CommandRegistry` / `Orchestrator` を生成して `AgentContext` に注入 |
| `_print_startup_banner() -> None` | 起動時バナー (DB チャンク数・ツール数・モード) を表示 |
| `_start_stdio_servers() -> None` | stdio トランスポートのサブプロセスを起動し `ToolExecutor.set_transport()` で登録 |
| `_repl_loop() -> None` | ユーザ入力待機 → スラッシュコマンドまたは `ctx.services.orchestrator.handle_turn()` に委譲 |
| `_close_resources() -> None` | readline 履歴保存・`AsyncClient` クローズ |

## 3. Orchestrator API

```python
from agent.orchestrator import Orchestrator

orch = Orchestrator(ctx, cmds, on_turn_start=..., on_turn_end=..., on_error=..., tracer=...)
await orch.handle_turn(line)
```

| メソッド | 説明 |
|---|---|
| `handle_turn(line) -> None` | RAG 付加 → 履歴圧縮 → `_run_turn()` → 結果を DB 保存。`LLMTransportError` を捕捉し partial/pre-stream の 2 ブランチで処理 |
| `_run_turn(llm_url) -> str` | SSE ストリーミングで LLM を呼び出し、tool_calls があれば `execute_all_tool_calls()` 後に再送信。最大 `max_tool_turns` 回ループ。最終回答テキストを返す |
| `_augment_with_rag(line) -> tuple[str, bool]` | RAG パイプライン実行 + セマンティックキャッシュ参照。`(context_text, cache_hit)` を返す |
| `_maybe_two_stage_fetch(answer) -> str \| None` | LLM の回答に不十分なコンテキストシグナルがあれば全文展開コンテキストを返す |

**`_run_turn()` 安全ガード**

| ガード | 設定フィールド | 動作 |
|---|---|---|
| ツール呼び出し dedup | `tool_dedup_max_repeats` | 同一 (name, args) が指定回数を超えたら `_DEDUP_HINT` を注入してスキップ |
| 循環プランニング検出 | `tool_cycle_detect_window` | 同一 round fingerprint が `window` 回繰り返されたら `_CYCLE_DETECT_HINT` を注入してループ脱出 |
| 連続エラーガード | `tool_error_max_consecutive` | 全ツールがエラーになったターンが指定回数連続したらループ脱出 |
| エラー retry 抑制 | `tool_error_retry_max` | 同一 (name, args) がこのターンですでにエラーになっていた場合、retry 制限内で再試行 |

**`handle_turn()` LLM エラー処理**

| 条件 | 対処 |
|---|---|
| `LLMTransportError` (partial_text あり) | `[INCOMPLETE: {kind}]` 付きで assistant メッセージを保存 |
| `LLMTransportError` (partial_text なし, turn==0) | history から user メッセージを pop して整合性を保つ |
| `LLMTransportError` (turn > 0) | synthetic tool error を history に追加して `_run_turn()` から return |

## 4. agent_repl_tool_exec.py API

| 関数 | 説明 |
|---|---|
| `check_approval(ctx, tool_name, args) -> bool` | 事前チェック → リスク分類 → dry_run 実行 → ユーザ確認プロンプト → 承認/拒否を返す |
| `_classify_risk(cfg, tool_name, args) -> str` | ツールのリスクレベルを `"none"` / `"medium"` / `"high"` で返す |
| `_check_allowed_root(cfg, tool_name, args) -> bool` | パス引数が `allowed_root` 内に収まるか検証。False = 即時拒否 |
| `_check_allowed_repo(cfg, tool_name, args) -> bool` | GitHub 書き込みツールのリポジトリが `approval_github_allowed_repos` に含まれるか検証。False = 即時拒否 |
| `execute_one_tool_call(ctx, tc) -> tuple[str, str, dict, str, bool]` | 1 件の tool_call を実行し `(id, name, args, text, is_error)` を返す。長い結果は LLM 要約 |
| `execute_all_tool_calls(ctx, tool_calls, turn) -> None` | 全 tool_call を `asyncio.gather()` (副作用なし) または直列 (副作用あり / serial_tool_calls=True) で実行し、承認・dedup・per-turn 上限チェックを経て履歴に追記 |

### 4-tier ツール安全性分類

ツールは `agent.json` の `tool_safety_tiers` で 4 段階に分類する。`approval_risk_rules` が設定されているツールはそちらが優先される。

| tier | `_TIER_TO_RISK` | 説明 |
|---|---|---|
| `READ_ONLY` | `"none"` | 副作用なし読み取り専用 (例: `read_text_file`, `list_directory`) |
| `WRITE_SAFE` | `"none"` | 低リスク書き込み (例: `write_file`, `create_directory`, `github_get_file_contents`) |
| `WRITE_DANGEROUS` | `"medium"` | 破壊的書き込み・削除 (例: `delete_file`, `github_push_files`) |
| `ADMIN` | `"high"` | システム管理・シェル実行 (例: `shell_run`) |

**フォールバック (Fail-Safe):** `approval_risk_rules` にも `tool_safety_tiers` にも未登録のツールは `WRITE_DANGEROUS` とみなし、リスク `"medium"` を返す。

**エスカレーション:** `delete_directory` かつ `recursive=True` の場合、ベースリスクが何であれ `"high"` に引き上げる。

### check_approval() 処理フロー

```
check_approval(ctx, tool_name, args)
  ├─ _check_allowed_root()  — allowed_root 外なら即時 denied_root_jail (audit ログ + False 返却)
  ├─ _check_allowed_repo()  — allowlist 外 GitHub 書き込みなら即時 denied_repo_allowlist (audit ログ + False 返却)
  ├─ _classify_risk()       — approval_risk_rules → tier fallback → delete_directory escalation
  ├─ risk == "none"         — 自動承認 (audit: "auto")
  ├─ approval_dry_run_tools — dry_run=True でプレビュー実行、結果を表示
  ├─ risk == "medium"       — [y/N] プロンプト (audit: "approved" / "denied")
  └─ risk == "high"         — [yes/N] プロンプト (audit: "approved" / "denied")
```

## 5. 処理フロー

```
AgentREPL.run()
  └─ _view.setup_readline()        — readline 設定・補完・履歴ファイル読み込み
  └─ _init_components()            — 全コンポーネントを AgentContext に注入
  └─ _print_startup_banner()       — DB チャンク数・ツール数・モードを表示
  └─ ctx.session.start()           — sessions テーブルに INSERT
  └─ _repl_loop()
       └─ input()                  — ユーザ入力待機
       └─ Orchestrator.handle_turn(line)
            └─ _augment_with_rag() — MQE → KNN+BM25 → RRF → Rerank (± semantic cache)
            └─ ctx.session.save()  — messages テーブルに保存
            └─ asyncio.create_task(_cmds._generate_session_title())  ← 第1ターンのみ
            └─ hist_mgr.compress() — 履歴圧縮 (context_char_limit / context_token_limit)
            └─ _run_turn()         — LLM SSE ストリーム + ツールループ (max_tool_turns 回)
                 └─ execute_all_tool_calls()  — 承認・並列/直列実行・結果追記
                 └─ _maybe_two_stage_fetch()  — 不十分時のみ全文展開 (1回限り)
  └─ _close_resources()            — readline 履歴保存・AsyncClient クローズ
```

## 6. 使用スクリプト

`agent.py` が `asyncio.run(AgentREPL().run())` で呼び出す唯一のエントリポイント。
