# エージェント実装詳細 — クラス API

REPL パイプラインフロー・実装詳細 → [`05_agent-impl-flow.md`](05_agent-impl-flow.md)

## 1. agent.py 実装詳細

### 1.1 機能概要

CLI REPL ツール。`agent>` (または `agent[:#N]>`) プロンプトで対話し、HTTP 経由で MCP サーバと通信。LLM が必要なツールを自律選択・実行し、最終回答をターミナルに表示。セッション中は会話履歴を保持してマルチターン対話に対応。

### 1.2 実装方式

| 機能 | 実装 |
|---|---|
| エントリポイント | `python agent.py` (uvicorn 不要; foreground CLI プロセス) |
| 行編集・補完 | Readline ベース; タブ補完でスラッシュコマンドを補完; 履歴は `~/.agent_history` に保存 |
| スラッシュコマンド | `/help` / `/mcp` / `/mcp install` / `/config` / `/stats` / `/context` / `/compact` / `/clear [new]` / `/session` / `/db` / `/ingest` / `/debug` / `/note` / `/tool` / `/plan` / `/undo` / `/history` / `/system` / `/set` / `/reload` / `/memory` / `/export` / `/exit` (Ctrl-D も終了) |
| マルチライン入力 | 行末が `\` のとき次行に継続し、空行または `\` のない行で確定。継続プロンプトは `... ` |
| 会話履歴 | セッション中はメッセージリストを保持してマルチターン対話に対応 |
| HTTP クライアント | `httpx.AsyncClient` を起動時生成・終了時クローズ。`ctx.services.http` に保持 |
| DB 接続 | `SQLiteHelper().open(row_factory=True)` をクエリごとにオープン/クローズ |
| MCP http 通信 | `ToolExecutor.execute()` が tool 名に応じて MCP サーバに HTTP POST。TTL キャッシュ・エラーハンドリングも担当 |
| REPL 本体 | 依存性注入による責務分離: `AgentContext` (共有 mutable state)、`CLIView` (readline・進捗表示)、`LLMClient` (SSE ストリーミング)、`ToolExecutor` (MCP ルーティング)、`HistoryManager` (履歴圧縮)、`CommandRegistry` (スラッシュコマンドディスパッチ)、`AgentConfig` (ホットリロード対象設定)。`AgentREPL` はこれらのコーディネータ。`agent.py` はエントリポイントのみ |
| 起動ディレクトリ | 任意のディレクトリから起動可能。`agent.py` 先頭の `sys.path.insert(0, str(Path(__file__).parent))` がスクリプトの親ディレクトリを `sys.path` に追加するため、CWD に依存しない |

### 1.3 入出力インタフェース

通常入力

`agent>` (または `agent[:#N]>`) プロンプトに任意のテキストを入力。LLM が応答し、ツール呼び出しがあれば実行後に最終回答を表示。

スラッシュコマンド

| コマンド | 動作 |
|---|---|
| `/help` | 利用可能なスラッシュコマンドの一覧を表示 |
| `/mcp` | MCP サーバの状態・ツール一覧・疎通確認を表示 |
| `/mcp install <name>` | 新規 MCP サーバのテンプレートファイルを生成するウィザード。スクリプト骨格・設定 JSON・OpenRC スクリプト・任意で conf.d テンプレートを生成し、手動対応手順 (agent.json への tool 定義追加、deploy.sh への追記等) を表示 |
| `/config` | 設定ファイルのパスと主要設定値を表示 |
| `/stats` | セッション統計 (ターン数・ツール呼び出し数・LLM リトライ回数・ツールエラー回数・入出力トークン数等) を表示 |
| `/context` | ランタイム・コンテキスト状態 (メッセージ数・総文字数・圧縮閾値残余量・圧縮回数・現在のシステムプロンプト名・冒頭) を表示。Budget breakdown として system / history / tool_results のカテゴリ別文字数と割合も表示 |
| `/compact` | `context_char_limit` の閾値に関わらず会話履歴を即時圧縮。ターン数が `context_compress_turns * 2` 以下の場合はメッセージを表示してスキップ |
| `/clear [new]` | 会話履歴をシステムプロンプトのみにリセットし、セッション統計・ツールキャッシュをクリア。`new` を付けると新規 DB セッションも開始 |
| `/session list [n]` | 過去のセッション一覧を表示 (デフォルト: 直近 20 件。件数指定可) |
| `/session load <id>` | 過去セッションの会話履歴を復元 |
| `/session rename <title>` | 現在のセッションタイトルを指定した文字列に変更 (50 文字以内) |
| `/session delete <id>` | 指定セッションとそのメッセージを DB から削除。現在のセッション ID を指定した場合は警告を表示 |
| `/db stats` | ドキュメント・チャンク・セッション・メッセージの件数を表示 |
| `/db urls [--lang ja\|en] [--limit N]` | 登録済みドキュメントの URL・タイトル・言語・チャンク数・取込日時を一覧表示 |
| `/db clean <url>` | 指定 URL のドキュメントとチャンクを DB から削除 |
| `/db rebuild-fts` | FTS5 の `chunks_fts` インデックスを再構築 |
| `/ingest <path_or_url> [lang] [--snippets-only]` | URL またはローカルファイルパスをクロール → チャンク分割 → DB 投入まで一括実行。`--snippets-only` で Markdown 見出しベースのスニペットチャンキングを強制 |
| `/debug` | デバッグ出力 (ログレベル切替・audit.log 表示) を ON/OFF |
| `/plan` | プランモードをトグル。ON 時は `plan_blocked_tools` に含まれるツールを自動ブロックし、計画立案に専念させる |
| `/undo` | 直前の user+assistant ターン対をメモリ履歴と DB からロールバック |
| `/history [n]` | 直近 N 件の user/assistant メッセージを先頭 120 文字プレビューで表示 (デフォルト: 5) |
| `/system [name]` | `agent.json` の `system_prompts` で定義したプレセットに切り替え。name 省略時は現在のプレセットと候補一覧を表示 |
| `/set temperature <f>` | LLM 生成温度をランタイムで変更 (0.0–2.0)。`/set` 単体で現在値を表示 |
| `/set max_tokens <n>` | LLM 最大トークン数をランタイムで変更 (≥1) |
| `/reload` | 分割設定ファイル群を再読み込みしてランタイムパラメータ (コンテキスト圧縮 / LLM リトライ / ツールキャッシュ / temperature / max_tokens / SSE 設定 / 承認ルール) を即時反映 |
| `/export [md\|json] [file]` | 会話履歴を Markdown または JSON でエクスポート。ファイル名省略時は stdout に出力 |
| `/exit` | エージェントを終了 (Ctrl-D でも可) |

ログファイル: `/opt/llm/logs/agent.log`

### 1.4 エラーハンドリング

| ケース | 対処 |
|---|---|
| LLM リクエスト失敗 (HTTP 503/429・接続エラー) | `_llm_request_with_retry()` が指数バックオフで最大 `llm_max_retries` 回リトライし、全試行失敗時にエラーをターミナルに表示して REPL を継続 |
| LLM リクエスト失敗 (その他) | エラーメッセージをターミナルに表示して REPL を継続 |
| MCP ツール実行失敗 | エラー内容を tool ロールとして LLM に返し、会話を継続 |
| `MAX_TOOL_TURNS` 超過 | 最後の assistant メッセージを表示して終了 |
| 全体例外 | `run()` の `finally` でリソースをクリーンアップし、未捕捉の例外はイベントループに伝播してスタックトレースを標準エラーに出力 |

### 1.5 ログ出力

- ファイル: `/opt/llm/logs/agent.log` + 標準エラー出力
- フォーマット: `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 起動・終了、ツール呼び出し (ターン数・ツール名・引数)、LLM 応答テキスト (`LLM response: ...`)、LLM モード切り替え |
| `WARNING` | MCP ツール実行失敗、`MAX_TOOL_TURNS` 超過 |
| `ERROR` | 全体例外 (`logger.exception`) |

### 1.6 設定項目

→ [`docs/06_ref-agent-config.md`](06_ref-agent-config.md) を参照。`common.toml` / `llm.toml` / `tools.toml` 等の全設定パラメータ、デフォルト値、バリデーション仕様を記載している。


### 1.7 クラス API

完全な API 仕様・フィールド定義・メソッド一覧は以下の参照ドキュメントを参照。

| クラス | 概要 | 参照ドキュメント |
|---|---|---|
| `AgentREPL` | 全コンポーネントを AgentContext へ DI し REPL ループを駆動する薄いコーディネータ | [06_ref-agent-repl.md](06_ref-agent-repl.md) |
| `Orchestrator` | ターンレベルのファサード（メモリ注入 → 圧縮 → LLM → ツール実行） | [06_ref-agent-repl.md](06_ref-agent-repl.md) |
| `ServerLifecycleManager` | MCP サーバーサブプロセスの起動・停止・アイドルタイムアウト管理 | [04_mcp-protocol.md](04_mcp-protocol.md) |
| `AgentContext` | 全コンポーネント参照と per-session state を一元管理する DI ハブ | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `CLIView` | readline・進捗表示・マルチライン入力を担うプレゼンテーション層 | [06_ref-agent-view.md](06_ref-agent-view.md) |
| `CommandRegistry` | スラッシュコマンドディスパッチャ（10 個のミックスインで構成） | [06_ref-agent-commands.md](06_ref-agent-commands.md) |
