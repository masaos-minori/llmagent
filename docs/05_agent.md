# エージェント

起動・確認・トラブルシューティング → [`docs/05_agent-ops.md`](05_agent-ops.md)

クラス API 詳細 → [`docs/05_agent-impl-class.md`](05_agent-impl-class.md)

## 1. 概要

`python -m agent` (`scripts/agent/__main__.py`) がエントリポイント。MCP ツールコーリング (OpenAI 互換 function calling) を統合した CLI REPL ツール。
`agent>` (または `agent[:#N]>`) プロンプトで対話し、セッション中は会話履歴を保持してマルチターン対話が可能。
行編集は Readline ベースで bash と同様のキーバインドを使用可能。セッション履歴は `~/.agent_history` に保存。
LLM 応答は SSE (Server-Sent Events: サーバー送信イベント) ストリーミングでトークン逐次表示。
会話メッセージは SQLite の `sessions` / `messages` テーブルに永続化。`/session load <id>` で過去の文脈を復元可能。
会話履歴の文字数が `context_char_limit` を超えたとき、古いターンを LLM で要約して圧縮。

## 2. ツールコーリングフロー

```
  [1] ユーザーが agent プロンプトに質問を入力する
  [2] ユーザーメッセージ + ツール定義を LLM に送信する
  [3] LLM が tool_calls を返したら MCP サーバ経由でツールを実行する
  [4] ツール実行結果を tool ロールとして履歴に追加し、LLM に再送信する
  [5] [3]-[4] を繰り返す (最大 max_tool_turns ターン)
  [6] 最終回答をターミナルに表示する; 会話履歴は次のターンに引き継がれる

  MCP サーバは HTTP または stdio 経由で呼び出す。
  LLM が tool_calls を返したら各 MCP サーバの統合エンドポイントに POST する。
```

## 3. スラッシュコマンド一覧

| コマンド | 動作 |
|---|---|
| `/help` | 利用可能なスラッシュコマンドの一覧を表示 |
| `/mcp` | MCP サーバの状態・ツール一覧・疎通確認を表示 |
| `/mcp install <name>` | 新規 MCP サーバのテンプレートファイルを生成するウィザード |
| `/config` | 設定ファイルのパスと主要設定値を表示 |
| `/stats` | セッション統計 (ターン数・ツール呼び出し数・RAG ヒット数・LLM メトリクス: retries/reconnects/heartbeat_timeouts/partial_completions/parse_errors) を表示 |
| `/context` | ランタイム・コンテキスト状態 (メッセージ数・総文字数・圧縮閾値残余・system/history/tool_results 別内訳) を表示 |
| `/compact` | `context_char_limit` の閾値に関わらず会話履歴を即時圧縮 |
| `/clear [new]` | 会話履歴をリセットし統計をクリア。`new` を付けると新規 DB セッションも開始 |
| `/session list [n]` | 過去のセッション一覧を表示 (デフォルト: 直近 20 件) |
| `/session load <id>` | 過去セッションの会話履歴を復元 |
| `/session rename <title>` | 現在のセッションタイトルを変更 (50 文字以内) |
| `/session delete <id>` | 指定セッションとそのメッセージを DB から削除 |
| `/db stats` | ドキュメント・チャンク・セッション・メッセージの件数を表示 |
| `/db urls [--lang ja\|en] [--limit N]` | 登録済みドキュメントの URL 一覧を表示 |
| `/db clean <url>` | 指定 URL のドキュメントとチャンクを DB から削除 |
| `/db rebuild-fts` | FTS5 の `chunks_fts` インデックスを再構築 |
| `/ingest <path_or_url> [lang] [--snippets-only]` | URL またはローカルファイルをクロール → チャンク分割 → DB 投入まで一括実行 |
| `/debug [audit\|verbose\|normal]` | デバッグ出力を ON/OFF。`audit` で audit.log 末尾表示、`verbose`/`normal` でログレベル変更 |
| `/note add <text>` | 永続クロスセッションノートを追加 |
| `/note list` | 全ノートを表示 |
| `/note delete <id>` | ノートを削除 |
| `/memory list [semantic\|episodic] [n]` | メモリエントリ一覧を表示 |
| `/memory search <query>` | FTS5 でメモリ全体を検索 |
| `/memory show <id>` | 1 件のメモリエントリ全文を表示 |
| `/memory pin <id>` | エントリをピン留め (セッション開始時に常時注入) |
| `/memory unpin <id>` | ピン留めを解除 |
| `/memory delete <id>` | 1 件のメモリエントリを削除 |
| `/memory prune [days]` | N 日より古いエントリを削除 |
| `/tool list` | 保存済みツール結果一覧を表示 (現在のセッション) |
| `/tool show <idx>` | 保存済みツール結果の全文を表示 |
| `/plan` | プランモードをトグル。ON 時は `plan_blocked_tools` を自動ブロック |
| `/undo` | 直前の user+assistant ターン対をロールバック |
| `/history [n]` | 直近 N 件の user/assistant メッセージを表示 (デフォルト: 5) |
| `/system [name]` | システムプロンプトプレセットを切り替え |
| `/set temperature <f>` | LLM 生成温度をランタイムで変更 (0.0–2.0) |
| `/set max_tokens <n>` | LLM 最大トークン数をランタイムで変更 |
| `/reload` | 分割設定ファイル群を再読み込みしてランタイムパラメータを即時反映 |
| `/export [md\|json] [file]` | 会話履歴をエクスポート。省略時は stdout に出力 |
| `/exit` | エージェントを終了 (Ctrl-D でも可) |

## 4. 使用可能なツール一覧

以下の表は各 MCP サーバが実装する全ツールの一覧。LLM に提供するツールは `config/tools_definitions.toml` の `tool_definitions` で選択する。

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

## 5. チューニング指針

主要パラメータの概要。詳細な設定フィールドは `docs/06_ref-agent-config.md` を参照。

| パラメータ | ファイル | デフォルト | 調整方針 |
|---|---|---|---|
| `serial_tool_calls` | `config/tools.toml` | `false` | `true` のとき tool_calls を直列ループで実行; write→read 等の依存関係がある場合に使用 |
| `auto_inject_notes` | `config/tools.toml` | `true` | `true` のとき起動時に全ノートをシステムプロンプト末尾に付加 |
| `use_tool_summarize` | `config/tools.toml` | `false` | `true` のとき長いツール結果を LLM で要約してから LLM コンテキストに追加 |
| `tool_summarize_threshold` | `config/tools.toml` | `3000` | ツール結果を要約対象とする文字数の下限 |
| `require_approval_tools` | `config/security.toml` | (GitHub 書き込み系) | 実行前に `y/N` 確認を要求するツール名リスト |
| `context_char_limit` | `config/context.toml` | `8000` | 会話履歴の総文字数がこの値を超えたとき古いターンを要約・圧縮 |
| `context_compress_turns` | `config/context.toml` | `4` | 一度に圧縮する最古ターン数 (user+assistant ペア単位) |
| `http_timeout` | `config/http.toml` | 120 秒 | 生成が遅い場合は増やす |
| `llm_max_retries` | `config/llm.toml` | 3 | HTTP 503/429・接続エラー時のリトライ上限 |
| `max_tool_turns` | `config/tools.toml` | 5 | ツールコーリング最大ターン数; 超過時は最後の assistant メッセージを返す |

## 6. 前提条件

- LLM サービスが起動済みであること (`llm_url` のエンドポイントが疎通可能)
- MCP サーバが必要な分だけ起動済みであること
  - `web-search-mcp` (:8004), `file-mcp` (:8005), `github-mcp` (:8006) 等
- GitHub 操作を使う場合: 実行環境に `GITHUB_TOKEN` が設定されていること
- llama.cpp のモデルがツールコーリングに対応していること
