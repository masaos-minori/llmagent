# エージェント実装詳細 — REPL パイプラインフロー

クラス API 詳細 → [`05_agent-impl-class.md`](05_agent-impl-class.md)

## 2. REPL パイプライン処理フロー

1ターンのリクエスト処理フロー:

```
ユーザー入力
  ① Memory   — MemoryInjectionService.on_user_prompt() で関連メモリを system ロールとして履歴注入 (use_memory_layer=True のとき)
  ② Append   — ユーザーメッセージをそのまま履歴に追記 (Orchestrator._append_user_message)
  ③ Compress — HistoryManager.compress() が char/token 上限超過時に古いターンを LLM 要約に置換
  ④ LLM      — ツール定義と会話履歴を SSE ストリーミングで送信 (全ターン共通)
  ⑤ Tool loop — tool_calls があれば MCP 実行 → 履歴追記 → 再送信 (MAX_TOOL_TURNS=5 上限)
```

RAG パイプラインは `mcp/rag_pipeline/` (port 8010) 経由で MCP ツールとして提供。in-process RagPipeline / 自動 RAG 挿入 / two-stage fetch はすべて削除済み。

---

## 3. 実装詳細

### 3.1 設定パラメータとホットリロード

- `/reload` ホットリロード: `agent/commands/cmd_config.py` の `_apply_config_params()` が `ctx.cfg.xxx = new_val` でフィールドを更新し、`_sync_services_to_cfg()` → `ConfigReloadService(ctx).apply_config_dict(new_cfg)` を呼び出す。`ConfigReloadService` (`agent/services/config_reload.py`) が各サービスの `apply_config()` を経由して同期 — `ctx.services.llm` (retries / temperature / max_tokens / SSE 設定) / `ctx.services.hist_mgr` (char_limit / compress_turns / token_limit / tokenize_url) / `ctx.services.tools` (cache_ttl)。transport 変更 (http/stdio 切り替え) には再起動が必要

### 3.2 LLM 生成パラメータ

主要パラメータは `AgentConfig` dataclass のフィールドとして `agent/config.py` で管理される（`llm_temperature`, `llm_max_tokens` 等）。モジュールレベル定数は圧縮専用 (`_COMPRESS_TEMPERATURE=0.3`, `_COMPRESS_MAX_TOKENS=300`: `factory.py:35-36`) のみ。

| ファイル | 定数/フィールド | 用途 |
|---|---|---|
| `agent/config.py` | `LLMConfig.llm_temperature` / `llm_max_tokens` | 通常 LLM 呼び出し (agent.toml で設定) |
| `agent/factory.py` | `_COMPRESS_TEMPERATURE=0.3` / `_COMPRESS_MAX_TOKENS=300` | 会話履歴圧縮専用 |
| `agent/commands/cmd_session.py` | `ctx.cfg.title_llm_temperature` / `ctx.cfg.title_llm_max_tokens` | セッションタイトル生成 (デフォルト 0.1 / 20) |
| `rag/pipeline.py` | `_MQE_TEMPERATURE=0.6` / `_MQE_MAX_TOKENS=300` | MQE クエリ展開 |
| `rag/pipeline.py` | `_RERANK_TEMPERATURE=0.0` / `_RERANK_MAX_TOKENS=256` | Cross-Encoder Rerank |
| `rag/pipeline.py` | `_SUMMARIZE_TEMPERATURE=0.2` / `_SUMMARIZE_MAX_TOKENS=256` | ツール結果要約 |

`/set temperature <val>` で `ctx.cfg.llm.llm_temperature` と `ctx.services.llm._temperature` を即時同期。

### 3.3 コンテキスト管理

- コンテキスト予算管理: `agent/services/context_view.py` の `budget_breakdown()` がメッセージリストを system / rag / history / tool_results の 4 カテゴリに分類して文字数を算出。`Orchestrator._warn_budget()` が `_run_turn()` 内のツールループ最初の反復 (`turn==0`) のみ呼び出され、`budget_warn_ratio` (デフォルト 0.8) 超過時に `logger.warning` で内訳付き警告を出力。`/context` で表示
- 会話履歴圧縮: `HistoryManager` が `context_char_limit` を超えたとき `context_compress_turns` 件ずつ古いターンを LLM で圧縮
- `SQLiteHelper` コンテキストマネージャ: `open()` が `self` を返すため `with SQLiteHelper().open(...) as db:` パターンで使用。`write_mode=True` → WAL + 外部キー有効。`row_factory=True` → カラム名アクセス有効。DB_PATH / SQLITE_VEC_SO は `open()` 内部で遅延初期化

### 3.4 ツール実行

- 並列実行: `execute_all_tool_calls()` が `asyncio.gather()` で全 tool_calls を並列実行。`serial_tool_calls=True` または side-effect ツール (write / delete / shell_run) が含まれる場合は自動的に逐次実行へダウングレード
- 承認フロー (`check_approval()`): pre-flight チェック → リスク分類 → プロンプトの順に処理
  - pre-flight ① `allowed_tools` ホワイトリスト: リストが非空でツール名が含まれない場合は即時 denied
  - pre-flight ② `allowed_root` ルートジェイル: パス引数が `cfg.allowed_root` 外のとき即時 denied
  - pre-flight ③ GitHub リポジトリ許可リスト: `approval_github_allowed_repos` に含まれないリポジトリへの書き込みは即時 denied (Fail-Closed)
  - リスク分類: `approval_risk_rules` テーブル優先 → `tool_safety_tiers` フォールバック → `_TIER_TO_RISK` マッピング
    - `none` → 自動承認 (プロンプトなし)
    - `medium` → プレビュー + y/N プロンプト
    - `high` → プレビュー + `yes` (全文字列) 入力要求
  - `approval_dry_run_tools` リストにあるツールは承認前に `dry_run=True` で試し実行しプレビューに追記
  - 拒否ツールは `"Tool execution denied by user."` を履歴追加して LLM に通知
- 連続エラーガード: あるラウンドの全ツール呼び出しがすべてエラーになった場合に `consecutive_errors` をインクリメント。`tool_error_max_consecutive` 回以上連続した場合はループを打ち切り `"Too many consecutive tool errors."` を返す。1 本でも成功ツールがあればカウントをリセット
- ツール結果要約 (`use_tool_summarize`): 結果が `tool_summarize_threshold` 文字超のとき `summarize_tool_result()` で LLM 要約を生成し履歴追加。全文は `ctx.tool_result_store` に保持し `/tool list` / `/tool show` で参照可能
- TTL キャッシュ: `ToolExecutor` が `tool_cache_ttl` 秒の TTL キャッシュを保持 (同一ツール名+引数の結果を再利用)。キャッシュ統計は `/stats` の `Cache hits` で確認可能。キャッシュのクリアは `/clear` で行う

### 3.5 RAG 機能

RAG は `mcp/rag_pipeline/` サービス (port 8010) がすべて担当。エージェント側に in-process RagPipeline はない。

- ステップ別レイテンシ計測: `_run_turn()` の初回 LLM 呼び出し時間は `stat_latency["llm"]` に追記。`/stats` で平均・最大を表示

### 3.6 セッション管理・ノート

- セッション横断ノート (`/note`): `AgentSession.add_note()` / `list_notes()` / `delete_note()` / `get_all_note_contents()` が `notes` テーブルを操作。`auto_inject_notes=True` のとき `AgentREPL.run()` 起動時に全ノートを `[Notes]` ブロックとしてシステムプロンプトへ追記
- システムプロンプト切り替え: `_system_prompt_name` で現在プレセットを管理。`SYSTEM_PROMPTS` は `agent/config.py` のモジュールレベルで `agent.toml["system_prompts"]` から読み込み。`/system <name>` で切り替え
- 起動時サービス疎通確認: `AgentREPL._check_service_health()` が `agent/repl_health.py` の `check_service_health()` に委譲し、LLM / Embed 各エンドポイントへの疎通確認を行う。失敗時は `logger.warning` で通知するが起動は続行

### 3.7 運用・保守

- `deploy.sh` コピーリスト: `scripts/` にモジュールを追加・削除したときは `deploy/deploy.sh` のコピーリストも同時に更新
- グレースフルシャットダウン: `agent.py` が `SIGTERM` を `SystemExit(0)` に変換。`AgentREPL._repl_loop()` の `_shutdown_requested` フラグが入力待ち後にループを自然終了させ、`run()` の `finally` でリソースをクローズ
