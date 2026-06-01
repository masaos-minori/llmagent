# エージェント実装詳細 — REPL パイプラインフロー

クラス API 詳細 → [`05_agent-impl-class.md`](05_agent-impl-class.md)

## 2. REPL パイプライン処理フロー

1ターンのリクエスト処理フロー:

```
ユーザー入力
  ① Memory   — MemoryLayer.on_user_prompt() で関連メモリを system ロールとして履歴注入 (use_memory_layer=True のとき)
  ②〜⑦ RAG  — use_rag_mcp フラグで 2 経路に分岐:
    [use_rag_mcp=false (デフォルト): in-process]
      ② MQE      — 直近 2 件の過去ユーザー発話 (history_context) を補助情報としてクエリをN通りに言い換え (:8002)
                   ※ history_context は MQE 検索専用; LLM 最終回答プロンプトには含めない
      ③ Search   — 各クエリ: KNN (sqlite-vec) + BM25 (FTS5), TOP_K_SEARCH=20 件ずつ
      ④ RRF      — score = Σ 1/(60 + rank) で統合・重複排除
      ⑤ Rerank   — LLM が上位 TOP_K_RERANK=15 件をスコアリング (Cross-Encoder プロンプト); rag_min_score 未満を除外
      ⑥ Dedup    — 同一 doc (URL) から最大 MAX_CHUNKS_PER_DOC=2 件に絞り多様性を確保
      ⑦ Augment  — 上位 RAG_TOP_K=5 件を "[Source: {title} | {url}]\n{content}" 形式でユーザー入力に付加
    [use_rag_mcp=true: MCP 経由]
      ② MCP      — Orchestrator._augment_via_mcp() が rag_run_pipeline ツールを呼び augmented_text を受け取る
                   MCP 呼び出し失敗時は in-process フォールバック
  ⑧ Compress — HistoryManager.compress() が char/token 上限超過時に古いターンを LLM 要約に置換
  ⑨ LLM      — ツール定義と会話履歴を SSE ストリーミングで送信 (全ターン共通)
  ⑩ Tool loop — tool_calls があれば MCP 実行 → 履歴追記 → 再送信 (MAX_TOOL_TURNS=5 上限)
  ⑪ [option] Two-stage — LLM が追加コンテキスト要求フレーズを含む場合 fetch_full_document() で全文展開 → 再送信
```

セマンティックキャッシュが有効 (`use_semantic_cache=true`) な場合、クエリ埋め込みのコサイン類似度が `semantic_cache_threshold` 以上のとき ②〜⑥ (in-process) または ② MCP呼び出し をスキップし前回コンテキストを再利用。

---

## 3. 実装詳細

### 3.1 RAG パラメータとホットリロード

- `RAG_TOP_K`: `agent/config.py` のモジュールレベル定数 (初期値)。`agent.toml` の `"rag_top_k"` で設定可能 (デフォルト: 5)。実行時は `ctx.cfg.rag_top_k` を参照 (`AgentConfig` 経由でホットリロード対応)
- `/reload` ホットリロード: `agent/commands/cmd_config.py` の `_apply_config_params()` が `ctx.cfg.xxx = new_val` でフィールドを更新し、`_sync_services_to_cfg()` が `ctx.services.llm` (retries / temperature / max_tokens / SSE 設定) / `ctx.services.hist_mgr` (char_limit / compress_turns / token_limit / tokenize_url) / `ctx.services.tools` (cache_ttl) を同期。transport 変更 (http/stdio 切り替え) には再起動が必要
- `/rag on|off`: `_cmd_rag()` が `ctx.cfg.use_search` / `use_mqe` / `use_rerank` を直接書き換えるため再起動不要。`/rag` 単体で全フラグの現在値を表示

### 3.2 LLM 生成パラメータ

各 LLM 呼び出しのパラメータは `agent/config.py` ではなく各実装ファイルのモジュールレベル定数で管理:

| ファイル | 定数 | 用途 |
|---|---|---|
| `agent/repl.py` | `_COMPRESS_TEMPERATURE=0.3` / `_COMPRESS_MAX_TOKENS=300` | 会話履歴圧縮 |
| `agent/commands/registry.py` | `_TITLE_TEMPERATURE=0.1` / `_TITLE_MAX_TOKENS=20` | セッションタイトル生成 |
| `rag/pipeline.py` | `_MQE_TEMPERATURE=0.6` / `_MQE_MAX_TOKENS=300` | MQE クエリ展開 |
| `rag/pipeline.py` | `_RERANK_TEMPERATURE=0.0` / `_RERANK_MAX_TOKENS=256` | Cross-Encoder Rerank |
| `rag/pipeline.py` | `_SUMMARIZE_TEMPERATURE=0.2` / `_SUMMARIZE_MAX_TOKENS=256` | ツール結果要約 |

`llm_temperature` / `llm_max_tokens` の初期値は `agent.toml` から読み込む。`/set temperature <val>` で `ctx.cfg.llm_temperature` と `ctx.services.llm._temperature` を即時同期。

### 3.3 コンテキスト管理

- コンテキスト予算管理: `agent/commands/registry.py` の `_budget_breakdown()` がメッセージリストを system / rag / history / tool_results の 4 カテゴリに分類して文字数を算出。`Orchestrator._warn_budget()` が `_run_turn()` 内のツールループ最初の反復 (`turn==0`) のみ呼び出され、`budget_warn_ratio` (デフォルト 0.8) 超過時に `logger.warning` で内訳付き警告を出力。`/context` で表示
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

### 3.5 高度な RAG 機能

- 二段階取得 (`use_two_stage_fetch`): `_run_turn()` 内の `_finalize_answer()` で最初の LLM 応答が `_needs_more_context()` によるフレーズマッチング (`"追加情報が必要"` / `"need more context"` 等) で追加コンテキスト要求と判定されたとき、`_fetch_two_stage_context()` がトップ hits の周辺チャンク (±2) を展開して再送信。1 ターン 1 回のみ実行
- RAG Refiner (`use_refiner`): `RagPipeline.augment()` が Rerank 後チャンクを `RagLLM.refine_context()` に渡し、1 回の LLM 呼び出しでクエリ関連要点に圧縮。`refiner_max_chars_per_chunk` でチャンクを切り詰め後にプロンプトを構築。空出力・例外時は原文チャンクにフォールバック
- セマンティックキャッシュ (`use_semantic_cache`): `SemanticCache.lookup()` がコサイン類似度 >= `semantic_cache_threshold` のとき RAG をスキップし前回コンテキストを返す。`put()` でパイプライン実行後に格納、`prune()` で `semantic_cache_max_size` 上限管理
- ステップ別レイテンシ計測: `RagPipeline.run()` が MQE/Search/RRF/Rerank の所要秒数を `last_timings` に格納。`_run_turn()` の初回 LLM 呼び出し時間も `stat_latency["llm"]` に追記。`/stats` で平均・最大を表示

### 3.6 セッション管理・ノート

- セッション横断ノート (`/note`): `AgentSession.add_note()` / `list_notes()` / `delete_note()` / `get_all_note_contents()` が `notes` テーブルを操作。`auto_inject_notes=True` のとき `AgentREPL.run()` 起動時に全ノートを `[Notes]` ブロックとしてシステムプロンプトへ追記
- システムプロンプト切り替え: `_system_prompt_name` で現在プレセットを管理。`SYSTEM_PROMPTS` は `agent/config.py` のモジュールレベルで `agent.toml["system_prompts"]` から読み込み。`/system <name>` で切り替え
- 起動時サービス疎通確認: `AgentREPL._check_service_health()` が `agent/repl_health.py` の `check_service_health()` に委譲し、LLM / Embed 各エンドポイントへの疎通確認を行う。失敗時は `logger.warning` で通知するが起動は続行

### 3.7 運用・保守

- `deploy.sh` コピーリスト: `scripts/` にモジュールを追加・削除したときは `deploy/deploy.sh` のコピーリストも同時に更新
- グレースフルシャットダウン: `agent.py` が `SIGTERM` を `SystemExit(0)` に変換。`AgentREPL._repl_loop()` の `_shutdown_requested` フラグが入力待ち後にループを自然終了させ、`run()` の `finally` でリソースをクローズ
