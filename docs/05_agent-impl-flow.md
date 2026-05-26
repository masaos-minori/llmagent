# エージェント実装詳細 — REPL パイプラインフロー

クラス API 詳細 → [`05_agent-impl-class.md`](05_agent-impl-class.md)

## 2. REPL パイプライン処理フロー

1ターンのリクエスト処理フロー:

```
ユーザー入力
  ① MQE      — 直近 2 件の過去ユーザー発話 (history_context) を補助情報としてクエリをN通りに言い換え (gemma-4-e4b :8002)
               ※ history_context は MQE 検索専用; LLM 最終回答プロンプトには含めない
  ② Search   — 各クエリ: KNN (sqlite-vec) + BM25 (FTS5), TOP_K_SEARCH=20 件ずつ
  ③ RRF      — score = Σ 1/(60 + rank) で統合・重複排除
  ④ Rerank   — LLM が上位 TOP_K_RERANK=15 件をスコアリング (Cross-Encoder プロンプト); rag_min_score 未満を除外
  ⑤ Dedup    — 同一 doc (URL) から最大 MAX_CHUNKS_PER_DOC=2 件に絞り多様性を確保
  ⑥ Augment  — 上位 RAG_TOP_K=5 件を "[Source: {title} | {url}]\n{content}" 形式でユーザー入力に付加
  ⑦ LLM      — ツール定義と会話履歴を SSE ストリーミングで送信 (全ターン共通)
  ⑧ Tool loop — tool_calls があれば MCP 実行 → 履歴追記 → 再送信 (MAX_TOOL_TURNS=5 上限)
  ⑨ [option] Two-stage — LLM が追加コンテキスト要求を示した場合 fetch_full_document() で全文展開 → 再送信
```

セマンティックキャッシュが有効 (`use_semantic_cache=true`) な場合、クエリ埋め込みのコサイン類似度が `semantic_cache_threshold` 以上のとき ②〜⑥ をスキップし前回コンテキストを再利用。

---

## 3. 実装詳細

### 3.1 RAG パラメータとホットリロード

- `RAG_TOP_K`: `agent_config.py` のモジュールレベル定数 (初期値)。`agent.json` の `"rag_top_k"` で設定可能 (デフォルト: 5)。実行時は `ctx.cfg.rag_top_k` を参照 (`AgentConfig` 経由でホットリロード対応)
- `/reload` ホットリロード: `agent_commands._cmd_reload()` が `ctx.cfg.xxx = new_val` でフィールドを更新し、`ctx.llm._max_retries` / `ctx.hist_mgr._char_limit` / `ctx.tools._cache_ttl` を同期。`CHAT_URL` / `CODE_URL` は起動時確定のためホットリロード対象外
- `/rag on|off`: `_cmd_rag()` が `ctx.cfg.use_search` / `use_mqe` / `use_rerank` を直接書き換えるため再起動不要。`/rag` 単体で全フラグの現在値を表示

### 3.2 LLM 生成パラメータ

各 LLM 呼び出しのパラメータは `agent_config.py` ではなく各実装ファイルのモジュールレベル定数で管理:

| ファイル | 定数 | 用途 |
|---|---|---|
| `agent_repl.py` | `_COMPRESS_TEMPERATURE=0.3` / `_COMPRESS_MAX_TOKENS=300` | 会話履歴圧縮 |
| `agent_commands.py` | `_TITLE_TEMPERATURE=0.1` / `_TITLE_MAX_TOKENS=20` | セッションタイトル生成 |
| `agent_rag.py` | `_MQE_TEMPERATURE=0.6` / `_MQE_MAX_TOKENS=300` | MQE クエリ展開 |
| `agent_rag.py` | `_RERANK_TEMPERATURE=0.0` / `_RERANK_MAX_TOKENS=256` | Cross-Encoder Rerank |
| `agent_rag.py` | `_SUMMARIZE_TEMPERATURE=0.2` / `_SUMMARIZE_MAX_TOKENS=256` | ツール結果要約 |

`llm_temperature` / `llm_max_tokens` の初期値は `agent.json` から読み込む。`/set temperature <val>` で `ctx.cfg.llm_temperature` と `ctx.llm._temperature` を即時同期。

### 3.3 コンテキスト管理

- コンテキスト予算管理: `agent_commands._budget_breakdown()` がメッセージリストを system / rag / history / tool_results の 4 カテゴリに分類して文字数を算出。`AgentREPL._run_turn()` が `turn == 0` のとき算出し、`BUDGET_WARN_RATIO` (0.8) 超過時に `logger.warning` で内訳付き警告を出力。`/context` で表示
- 会話履歴圧縮: `HistoryManager` が `context_char_limit` を超えたとき `context_compress_turns` 件ずつ古いターンを LLM で圧縮
- `SQLiteHelper` コンテキストマネージャ: `open()` が `self` を返すため `with SQLiteHelper().open(...) as db:` パターンで使用。`write_mode=True` → WAL + 外部キー有効。`row_factory=True` → カラム名アクセス有効。DB_PATH / SQLITE_VEC_SO は `open()` 内部で遅延初期化

### 3.4 ツール実行

- 並列実行: `_execute_all_tool_calls()` が `asyncio.gather()` で全 tool_calls を並列実行。`serial_tool_calls=True` のとき逐次ループに切り替え (write→read 等の依存関係がある呼び出し用)
- 書き込み承認フロー: `require_approval_tools` リストにあるツールは `asyncio.to_thread(input, ...)` で y/N 確認を要求。拒否ツールは `"Tool execution denied by user."` を履歴追加して LLM に通知
- ツール結果要約 (`use_tool_summarize`): 結果が `tool_summarize_threshold` 文字超のとき `RagLLM.summarize_tool_result()` で LLM 要約を生成し履歴追加。全文は `ctx.tool_result_store` (FIFO 上限 20 件) に保持し `/tool list` / `/tool show` で参照可能
- TTL キャッシュ: `ToolExecutor` が `tool_cache_ttl` 秒の TTL キャッシュを保持 (同一ツール名+引数の結果を再利用)。キャッシュ統計は `/stats` の `Cache hits` で確認可能。キャッシュのクリアは `/clear` で行う

### 3.5 高度な RAG 機能

- 二段階取得 (`use_two_stage_fetch`): `_run_turn()` で最初の LLM 応答が `_needs_more_context()` で追加コンテキスト要求と判定されたとき、`_fetch_two_stage_context()` がトップ hits の周辺チャンク (±2) を展開して再送信。1 ターン 1 回のみ実行
- RAG Refiner (`use_refiner`): `RagPipeline.augment()` が Rerank 後チャンクを `RagLLM.refine_context()` に渡し、1 回の LLM 呼び出しでクエリ関連要点に圧縮。`refiner_max_chars_per_chunk` でチャンクを切り詰め後にプロンプトを構築。空出力・例外時は原文チャンクにフォールバック
- セマンティックキャッシュ (`use_semantic_cache`): `SemanticCache.lookup()` がコサイン類似度 >= `semantic_cache_threshold` のとき RAG をスキップし前回コンテキストを返す。`put()` でパイプライン実行後に格納、`prune()` で `semantic_cache_max_size` 上限管理
- ステップ別レイテンシ計測: `RagPipeline.run()` が MQE/Search/RRF/Rerank の所要秒数を `last_timings` に格納。`_run_turn()` の初回 LLM 呼び出し時間も `stat_latency["llm"]` に追記。`/stats` で平均・最大を表示

### 3.6 セッション管理・ノート

- セッション横断ノート (`/note`): `AgentSession.add_note()` / `list_notes()` / `delete_note()` / `get_all_note_contents()` が `notes` テーブルを操作。`auto_inject_notes=True` のとき `AgentREPL.run()` 起動時に全ノートを `[Notes]` ブロックとしてシステムプロンプトへ追記
- システムプロンプト切り替え: `_system_prompt_name` で現在プレセットを管理。`SYSTEM_PROMPTS` は `agent_config.py` のモジュールレベルで `agent.json["system_prompts"]` から読み込み。`/system <name>` で切り替え
- 起動時サービス疎通確認: `AgentREPL._check_service_health()` が `CHAT_URL` / `CODE_URL` / `EMBED_URL` に HTTP GET (タイムアウト 2 秒) を試みる。失敗時は `logger.warning` で通知するが起動は続行

### 3.7 運用・保守

- `deploy.sh` コピーリスト: `scripts/` にモジュールを追加・削除したときは `deploy/deploy.sh` のコピーリストも同時に更新
- グレースフルシャットダウン: `agent.py` が `SIGTERM` を `SystemExit(0)` に変換。`AgentREPL._repl_loop()` の `_shutdown_requested` フラグが入力待ち後にループを自然終了させ、`run()` の `finally` でリソースをクローズ
