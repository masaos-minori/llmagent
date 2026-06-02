# エージェント

起動・確認・トラブルシューティング → [`docs/05_agent-ops.md`](05_agent-ops.md)

## 3. ツールコーリング (Tool Calling) によるエージェント動作

### 3.1 機能概要

`agent.py` は RAG 検索と MCP ツールコーリング (OpenAI 互換 function calling) を統合した CLI REPL ツール。
`agent[chat]>` / `agent[code]>` プロンプトにモード名を表示しながら対話し、セッション中は会話履歴を保持してマルチターン対話が可能。
スラッシュコマンド (`/help` / `/mcp` / `/mcp install` / `/config` / `/stats` / `/context` / `/compact` / `/clear` / `/chat` / `/code` / `/session` / `/db` / `/ingest` / `/debug` / `/note` / `/tool` / `/plan` / `/undo` / `/history` / `/system` / `/set` / `/reload` / `/export` / `/exit`) と Ctrl-D で操作。
行末が `\` のとき次行に継続し、空行または改行なし行で送信するマルチライン入力に対応。
行編集は Readline ベースで bash と同様のキーバインドを使用可能。セッション履歴は `~/.agent_history` に保存。
DB 接続 (sqlite-vec) は RAG クエリごとにオープン/クローズ (データアクセス単位)。
LLM 応答は SSE (Server-Sent Events: サーバー送信イベント) ストリーミングでトークン逐次表示。
会話メッセージは SQLite の `sessions` / `messages` テーブルに永続化。`/session load <id>` で過去の文脈を復元可能。
会話履歴の文字数が `context_char_limit` を超えたとき、古いターンを LLM で要約して圧縮。

```
agent.py CLI REPL — RAG + MCP ツールコーリング統合フロー

  [1] ユーザーが `agent[chat]>` / `agent[code]>` プロンプトに質問を入力する
  [2] RAG 検索 (use_search=true の場合):
        MQE (Multi-Query Expansion) — 直近 2 件の過去ユーザー発話を history_context として
                                      LLM に渡し、クエリを N 個の言い換えに展開する (use_mqe=true の場合)
                                      ※ history_context は MQE 専用 (LLM 最終回答プロンプトには含めない)
        埋込  — クエリに "query: " プレフィックスを付けて embed-llm (:8003) に送信する
        検索  — KNN (sqlite-vec) + BM25 (FTS5) で上位 top_k_search 件ずつ取得する
        RRF  — 各クエリの結果リストをスコア Σ 1/(60+rank) で統合・重複排除する (use_rrf=true の場合)
        再ランク — LLM が上位 top_k_rerank 件を Cross-Encoder スコアリングする (use_rerank=true の場合)
  [3] ユーザーメッセージに検索結果を付加する:
        "[Reference documents]\n[Source: {title} | {url}]\n{content}\n\nQuestion: {query}"
  [4] 拡張済みメッセージ + ツール定義を LLM に送信する
  [5] LLM が tool_calls を返したら MCP サーバ経由でツールを実行する
  [6] ツール実行結果を tool ロールとして履歴に追加し、LLM に再送信する
  [7] [5]-[6] を繰り返す (最大 max_tool_turns ターン)
  [8] 最終回答をターミナルに表示する; 会話履歴は次のターンに引き継がれる

  MCP サーバは HTTP 経由で呼び出す (ポート 8004/8005/8006)。

  - サブプロセス起動なし (MCP サーバが別途起動済みであること)
  - config/agent.toml の tool_definitions を LLM に提供する (デフォルト: 14 ツール)
  - LLM が tool_calls を返したら各 MCP サーバの統合エンドポイントに POST する:
      search_web → POST :8004/v1/call_tool {name, args}
      list_directory / read_text_file ... → POST :8005/v1/call_tool {name, args}
      github_search_repositories ... → POST :8006/v1/call_tool {name, args}
```

### 3.2 使用可能なツール一覧

`config/agent.toml` の `tool_definitions` に定義済みの 14 ツール (`search_web`、`list_directory`、`read_text_file`、`directory_tree`、`search_files`、`write_file`、`create_directory`、`delete_file`、`delete_directory`、`grep_files`、`github_search_repositories`、`github_get_file_contents`、`github_list_issues`、`github_search_code`) が LLM に提供される。

以下の表は各 MCP サーバが実装する全ツールの一覧。LLM に提供するツールは `config/agent.toml` の `tool_definitions` で選択する。

| ツール名 | 呼び出し先 | 説明 |
|---|---|---|
| `search_web` | `web-search-mcp (HTTP :8004)` | Web 検索を実行する (Brave/Bing/DuckDuckGo) |
| `list_directory` | `file-mcp (HTTP :8005)` | ローカルディレクトリの直下一覧を取得する |
| `list_directory_with_sizes` | `file-mcp (HTTP :8005)` | サイズ付きのディレクトリ一覧を取得する |
| `directory_tree` | `file-mcp (HTTP :8005)` | ディレクトリツリーを再帰取得する |
| `read_text_file` | `file-mcp (HTTP :8005)` | ローカルファイルを読み込む (head/tail 対応) |
| `read_media_file` | `file-mcp (HTTP :8005)` | メディアファイルを base64 で取得する |
| `read_multiple_files` | `file-mcp (HTTP :8005)` | 複数のローカルファイルを一括で読み込む |
| `write_file` | `file-mcp (HTTP :8005)` | ローカルファイルを新規作成または上書きする |
| `edit_file` | `file-mcp (HTTP :8005)` | ファイルの特定テキストを置換編集する (dry_run 対応) |
| `create_directory` | `file-mcp (HTTP :8005)` | ディレクトリを作成する |
| `move_file` | `file-mcp (HTTP :8005)` | ファイルまたはディレクトリを移動する |
| `search_files` | `file-mcp (HTTP :8005)` | glob パターンでファイル名を検索する |
| `grep_files` | `file-mcp (HTTP :8005)` | 正規表現でファイル内容を検索する |
| `delete_file` | `file-mcp (HTTP :8005)` | ファイルを削除する |
| `delete_directory` | `file-mcp (HTTP :8005)` | ディレクトリを削除する |
| `get_file_info` | `file-mcp (HTTP :8005)` | ファイル・ディレクトリのメタ情報を取得する |
| `github_search_repositories` | `github-mcp (HTTP :8006)` | GitHub リポジトリを検索する |
| `github_get_file_contents` | `github-mcp (HTTP :8006)` | GitHub リポジトリのファイルを取得する |
| `github_list_issues` | `github-mcp (HTTP :8006)` | GitHub イシュー一覧を取得する |
| `github_get_issue` | `github-mcp (HTTP :8006)` | GitHub イシューの詳細を取得する |
| `github_create_issue` | `github-mcp (HTTP :8006)` | GitHub イシューを作成する |
| `github_list_pull_requests` | `github-mcp (HTTP :8006)` | GitHub プルリクエスト一覧を取得する |
| `github_get_pull_request` | `github-mcp (HTTP :8006)` | GitHub プルリクエストの詳細を取得する |
| `github_list_commits` | `github-mcp (HTTP :8006)` | GitHub リポジトリのコミット一覧を取得する |
| `github_search_code` | `github-mcp (HTTP :8006)` | GitHub 上のコードを検索する |
| `github_create_pull_request` | `github-mcp (HTTP :8006)` | GitHub プルリクエストを作成する |
| `github_create_branch` | `github-mcp (HTTP :8006)` | GitHub にブランチを作成する |
| `github_create_or_update_file` | `github-mcp (HTTP :8006)` | GitHub リポジトリのファイルを作成または更新する |
| `github_add_issue_comment` | `github-mcp (HTTP :8006)` | GitHub イシューにコメントを投稿する |
| `github_push_files` | `github-mcp (HTTP :8006)` | 複数ファイルを単一コミットとして GitHub に push する |
| `github_delete_file` | `github-mcp (HTTP :8006)` | GitHub リポジトリのファイルを削除する |
| `github_list_branches` | `github-mcp (HTTP :8006)` | GitHub リポジトリのブランチ一覧を取得する |
| `github_get_commit` | `github-mcp (HTTP :8006)` | GitHub リポジトリの特定コミット詳細を取得する |
| `github_search_issues` | `github-mcp (HTTP :8006)` | GitHub 全体でイシュー/PR をキーワード検索する |
| `github_search_pull_requests` | `github-mcp (HTTP :8006)` | GitHub 全体でプルリクエストをキーワード検索する |
| `github_update_pull_request` | `github-mcp (HTTP :8006)` | GitHub プルリクエストのタイトル/本文/状態を更新する |
| `github_merge_pull_request` | `github-mcp (HTTP :8006)` | GitHub プルリクエストをマージする |

### 3.3 使用方法

```bash
# エージェントを起動する
source /opt/llm/venv/bin/activate
python /opt/llm/scripts/agent.py
```

起動後は `agent[chat]>` / `agent[code]>` プロンプトに質問を入力。RAG 検索が有効な場合は各ステップの進捗 (`[rag] expanding query...` → `[rag] searching...` → `[rag] merging results...` → `[rag] reranking...`) が表示され、検索結果で拡張されたメッセージが LLM に送信。ツール実行結果が長い場合は行数・文字数の要約を表示し、全文はログに記録。

```
agent[chat]> sqlite-vec の KNN 検索の使い方を教えてください
  [rag] expanding query...
  [rag] searching...
  [rag] reranking...
sqlite-vec の KNN 検索は vec_each() 関数を使い、クエリベクトルに近い上位 K 件を取得します。...

agent[chat]> llama.cpp の最新バージョンを調べて教えてください
  [rag] expanding query...
  [rag] searching...
  [rag] reranking...
  [tool] search_web({"query": "llama.cpp latest version"})
  [tool] search_web → 28 lines / 1842 chars (truncated)
llama.cpp の最新バージョンは b5210 (2025-05 時点) です。...

agent[chat]> /help
Agent REPL — type a question and press Enter.
...
Slash commands:
  /help                    Show this help
  /mcp                     MCP server status, tool list, connectivity check
  /mcp install <name>      Scaffold a new MCP server template files (wizard)
  /config                  Current configuration and config file paths
  /stats                   Session statistics (turns, tool calls, RAG hits, error counts)
  /context                 Runtime context state (messages, chars, compression info, system prompt name, budget breakdown)
  /compact                 Force immediate compression of conversation history
  /clear [new]             Reset conversation history and session stats; [new] also starts a new DB session
  /chat                    Switch to chat LLM (gemma-4-e4b)
  /code                    Switch to code LLM (qwen2.5-coder-7b)
  /session list [n]        List past sessions (default: 20)
  /session load <id>       Restore a past session's conversation history
  /session rename <title>  Rename the current session
  /session delete <id>     Delete a session and all its messages
  /db stats                Show document/chunk/session/message counts
  /db urls [--lang ja|en] [--limit N]  List registered document URLs
  /db clean <url>          Delete a document and its chunks from the DB
  /db rebuild-fts          Rebuild the FTS5 chunks_fts index
  /ingest <url|path>       Crawl/ingest a URL or local file into the RAG DB
  /debug                   Toggle debug output ON/OFF (log level / audit.log tail)
  /note add <text>         Add a persistent cross-session note
  /note list               List all notes
  /note delete <id>        Delete a note by ID
  /memory list [semantic|episodic] [n]  List memory entries
  /memory search <query>   FTS5 search across all memory entries
  /memory show <id>        Show full content of one memory entry
  /memory pin <id>         Pin an entry (always injected at session start)
  /memory unpin <id>       Remove pin from an entry
  /memory delete <id>      Delete one entry by memory_id
  /memory prune [days]     Delete entries older than N days
  /tool list               List stored tool results (current session)
  /tool show <idx>         Show full text of a stored tool result
  /undo                    Roll back the last user+assistant turn
  /history [n]             Show last N user/assistant messages (default: 5)
  /system [name]           Switch system prompt preset; list presets if no name given
  /reload                  Reload config/agent.toml and apply runtime parameters
  /export [md|json] [file] Export conversation history
  /exit                    Exit (Ctrl-D also works)

agent[chat]> /mcp
# 各 MCP サーバの /health エンドポイントへの疎通確認とツール一覧を表示する
Transport : http
  web-search-mcp  :8004  (1 tool)
    - search_web
  file-mcp        :8005  (8 tools)
    - list_directory
    - ...
  github-mcp      :8006  (5 tools)
    - github_search_repositories
    - ...
Connectivity:
  web-search-mcp  :8004              OK
  file-mcp        :8005              OK
  github-mcp      :8006              OK

agent[chat]> /config
config: /opt/llm/config/common.toml, /opt/llm/config/agent.toml
chat_url: http://127.0.0.1:8002/v1/chat/completions
max_tool_turns: 5

agent[chat]> /stats
Session statistics:
  Turns      : 3
  Tool calls : 1
  RAG hits   : 2

agent[chat]> /exit
```

### 3.4 前提条件

MCP サーバ
- MCP サーバ 3 本の OpenRC サービスが起動済みであること
  - `web-search-mcp` (:8004), `file-mcp` (:8005), `github-mcp` (:8006)

共通
- Web 検索を使う場合: `agent.py` の実行環境に `BRAVE_API_KEY` 等が設定されていること
- GitHub 操作を使う場合: `agent.py` の実行環境に `GITHUB_TOKEN` が設定されていること
- llama.cpp のモデルがツールコーリングに対応していること
  - `llama-chat-llm` で使用する `gemma-4-e4b` はツールコーリング対応

---

## 4. チューニング指針

| パラメータ | ファイル | デフォルト | 調整方針 |
|---|---|---|---|
| `use_mqe` | `config/agent.toml` | `true` | `false` にすると MQE をスキップして高速化できる |
| `use_search` | `config/agent.toml` | `true` | `false` にすると RAG 検索全体をスキップする |
| `use_rrf` | `config/agent.toml` | `true` | `false` にすると RRF (Reciprocal Rank Fusion: 相互順位融合) をスキップする |
| `use_rerank` | `config/agent.toml` | `true` | `false` にすると Cross-Encoder 再ランクをスキップして高速化できる |
| `rag_min_score` | `config/agent.toml` | `0.0` | Rerank スコア (0–10) がこの値未満のチャンクを除外する; デフォルト 0.0 はフィルタなし |
| `max_chunks_per_doc` | `config/agent.toml` | `2` | 同一ドキュメントから取得するチャンク数の上限; chunk_overlap による近似重複チャンクの多重投入を防ぐ |
| `md_index_enable` | `config/agent.toml` | `false` | `true` にすると `/ingest` で Markdown を見出し単位の snippet チャンキングとする; `--snippets-only` フラグでオーバーライド可能 |
| `md_snippet_max_chars` | `config/rag_pipeline.json` | `600` | Markdown 見出しセクション 1 件の最大文字数; 超過時は通常の text チャンキングにフォールバックする |
| `use_two_stage_fetch` | `config/agent.toml` | `false` | `true` のとき LLM が追加コンテキストを要求したと判断されたターンで全文展開→再送信を実行する |
| `two_stage_max_docs` | `config/agent.toml` | `2` | 2 段階取得で全文展開するドキュメント数の上限 |
| `serial_tool_calls` | `config/agent.toml` | `false` | `true` のとき tool_calls を `asyncio.gather()` の並列ではなく直列ループで実行する; write→read 等の依存関係がある呼び出しで順序保証が必要な場合に使用する |
| `auto_inject_notes` | `config/agent.toml` | `true` | `true` のとき起動時に `notes` テーブルの全メモをシステムプロンプト末尾の `[Notes]` ブロックとして付加する |
| `use_tool_summarize` | `config/agent.toml` | `false` | `true` のとき `tool_summarize_threshold` 文字超のツール結果を LLM で要約してから LLM コンテキストに追加する |
| `tool_summarize_threshold` | `config/agent.toml` | `3000` | ツール結果を要約対象とする文字数の下限 |
| `use_semantic_cache` | `config/agent.toml` | `false` | `true` のとき RAG 検索結果をクエリ埋め込みのコサイン類似度でキャッシュする; `semantic_cache_threshold` 以上の類似度で再利用 |
| `semantic_cache_threshold` | `config/agent.toml` | `0.92` | セマンティックキャッシュのヒット判定閾値 (コサイン類似度 0–1) |
| `semantic_cache_max_size` | `config/agent.toml` | `100` | セマンティックキャッシュの最大エントリ数; 超過時は古いエントリをFIFO削除 |
| `tool_definitions_strict` | `config/agent.toml` | `false` | `true` のとき起動時のツール定義ミスマッチ (agent.json と各 MCP サーバの `/v1/tools` の差分) を RuntimeError として扱い起動を中止する |
| `mcp_watchdog_interval` | `config/agent.toml` | `0` | MCP サーバ死活監視の確認間隔 (秒); `0` で無効; 正値を設定するとバックグラウンドタスクが定期ヘルスチェックを行い失敗時に `rc-service restart` を実行する |
| `mcp_watchdog_max_restarts` | `config/agent.toml` | `3` | ウォッチドッグが同一サーバに対して実行する最大再起動回数; 超過後は警告ログのみ |
| `require_approval_tools` | `config/agent.toml` | (GitHub 書き込み系) | 実行前に `y/N` 確認を要求するツール名リスト; 主に `github_create_*` / `github_push_files` / `github_merge_*` 等を列挙する |
| `context_char_limit` | `config/agent.toml` | `8000` | 会話履歴の総文字数がこの値を超えたとき古いターンを要約・圧縮する |
| `context_compress_turns` | `config/agent.toml` | `4` | 一度に圧縮する最古ターン数 (user+assistant ペア単位) |
| `mqe_n_queries` | `config/agent.toml` | 3 | MQE で生成するクエリ言い換え数; 増やすと再現率が上がるが遅くなる |
| `top_k_search` | `config/agent.toml` | 20 | KNN・BM25 それぞれの取得件数; 増やすと再現率が上がる |
| `top_k_rerank` | `config/agent.toml` | 15 | Cross-Encoder に渡す候補数; 増やすと精度が上がるが遅くなる |
| `rrf_k` | `config/agent.toml` | 60 | RRF の平滑化定数; 通常変更不要 |
| `http_timeout` | `config/agent.toml` | 120 秒 | 生成が遅い場合は増やす |
| `llm_max_retries` | `config/agent.toml` | 3 | HTTP 503/429・接続エラー時のリトライ上限; 増やすと粘り強くなるが応答遅延が増す |
| `llm_retry_base_delay` | `config/agent.toml` | 1.0 秒 | 指数バックオフ基準値; delay = base × 2^attempt (1s, 2s, 4s) |
| `max_tool_turns` | `config/agent.toml` | 5 | ツールコーリング最大ターン数; 超過時は最後の assistant メッセージを返す |
| `mqe_prompt_template` | `config/agent.toml` | (既定テキスト) | MQE クエリ言い換えプロンプトのテンプレート; `{n_queries}` / `{query}` をプレースホルダとして使用する |
| `rerank_prompt_template` | `config/agent.toml` | (既定テキスト) | Cross-Encoder 再ランクスコアリングプロンプトのテンプレート; `{query}` / `{items_text}` をプレースホルダとして使用する |
| `crawl_delay` | `config/rag_pipeline.json` | 1.5 秒 | サーバ負荷に応じて調整 |
| `fetch_timeout` | `config/rag_pipeline.json` | 15 秒 | Crawler の 1 リクエストあたり HTTP タイムアウト秒数 |
| `embed_workers` | `config/rag_pipeline.json` | 4 | RagIngester の埋込並列実行数; CPU コア数に応じて調整 |
| `--threads` | `init.d/` 各スクリプト | 4 | 同時起動モデル数に応じて配分を調整 |
| `--ctx-size` | `init.d/` 各スクリプト | 各設定参照 | RAM 不足の場合は削減 |

---

## 5. 主要な実装注意事項

| 項目 | 内容 |
|---|---|
| E5 プレフィックス | 取込時 `passage: `、クエリ時 `query: ` を必ず付与 |
| float32 バイト順 | `struct.pack("<384f", ...)` でリトルエンディアン BLOB を生成 |
| chunks_vec 外部キー | 削除順: `chunks_vec` → `chunks` → `documents` (外部キー制約なし) |
| FTS5 予約語 | BM25 クエリのトークンは `"token"` とダブルクォートで囲む |
| agent.py 起動 | `agent.py` 先頭で `sys.path` を自動設定するため、任意のディレクトリから起動可能 |
| N100 の AVX2 非対応 | llama.cpp ビルド時は `-DGGML_NATIVE=ON` で命令セットを自動検出 |
