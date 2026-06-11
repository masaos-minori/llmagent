# agent/cli_view.py

## 1. 機能概要

`CLIView` は CLI プレゼンテーション層。readline 設定・進捗表示・マルチライン入力を一元管理する。`Orchestrator` / `HistoryManager` / `LLMClient` へコールバックとして渡すことで UI 依存を排除する。

テスト容易性のため `Writer` / `Reader` の 2 つの Protocol インターフェースを定義しており、実装はこれらのプロトコルに準拠している。

## 2. コンストラクタ

```python
CLIView(slash_commands: list[str]) -> None
```

- `slash_commands`: タブ補完の候補として登録するスラッシュコマンドのリスト (`["/help", "/exit", ...]`)

### クラス定数

| 定数 | 値 | 説明 |
|---|---|---|
| `HISTORY_FILE` | `Path.home() / ".agent_history"` | readline 履歴ファイルのパス |

## 3. Protocol インターフェース

テスト容易性のため、出力側 (`Writer`) と入力側 (`Reader`) の 2 つの Protocol を定義。

### Writer Protocol

```python
@runtime_checkable
class Writer(Protocol):
    def write_token(self, token: str) -> None: ...
    def write_compress_notice(self, n: int) -> None: ...
    def write_turn_start(self) -> None: ...
    def write_turn_end(self) -> None: ...
    def write_llm_error(self, e: Exception) -> None: ...
    def write_progress(self, msg: str) -> None: ...
    def clear_progress(self) -> None: ...
    def write_warning(self, msg: str) -> None: ...
    def write_startup_banner(self, chunk_count: str, n_tools: int) -> None: ...
```

### Reader Protocol

```python
@runtime_checkable
class Reader(Protocol):
    async def read_multiline(
        self,
        loop: asyncio.AbstractEventLoop,
        first_line: str,
    ) -> str: ...
```

## 4. メソッド一覧

```python
from agent.cli_view import CLIView

view = CLIView(slash_commands=["/help", "/exit", ...])
view.setup_readline()
view.write_progress("expanding query...")
view.clear_progress()
line = await view.read_multiline(loop, first_line)
```

| メソッド | 説明 |
|---|---|
| `setup_readline() -> None` | readline タブ補完 (区切り文字: スペース・タブ・改行のみ)・編集モード (emacs)・履歴ファイル読み込みを設定。履歴上限は 1000 件 |
| `write_history() -> None` | readline 履歴を `HISTORY_FILE` (`~/.agent_history`) に保存 |
| `write_token(token: str) -> None` | ストリーミングトークン 1 件を末尾改行なしで stdout に出力 |
| `write_compress_notice(n: int) -> None` | 履歴圧縮完了通知 (`  [context] history compressed (n messages summarized)`) を表示。先頭にスペース 2 つ |
| `write_turn_start() -> None` | LLM ストリーミングターン開始前に空行を出力 |
| `write_turn_end() -> None` | LLM 最終回答後に空行を出力 |
| `write_llm_error(e: Exception) -> None` | LLM リクエスト失敗を `\nError: {e}\n` の形式でユーザに通知 |
| `write_progress(msg: str) -> None` | `  [rag] {msg:<24}` をインプレース表示 (`\r` 上書き)。`msg` は 24 文字幅に左詰め |
| `clear_progress() -> None` | 進捗表示行をスペース 32 文字で上書きしてクリア (`\r` で行頭に戻る) |
| `write_warning(msg: str) -> None` | スタートアップ/Runtime 警告を `[warn] {msg}` の形式で出力 |
| `write_startup_banner(chunk_count: str, n_tools: int) -> None` | エージェント起動時に表示するバナー (`DB: {n} chunks \| Tools: {n}`) |
| `write_debug_rag(data: dict) -> None` | RAG パイプラインのデバッグデータを構造化して stdout に出力 (MQE queries, search results, RRF merge, reranked top-N) |
| `read_multiline(loop: asyncio.AbstractEventLoop, first_line: str) -> str` | 行末 `\` の継続入力をプロンプト `"... "` で収集し `\n` で連結して返す (async) |

## 5. コールバック仕様

`Orchestrator` は `on_turn_start` / `on_turn_end` / `on_error` キーワード引数でコールバックを受け取る。

```python
orchestrator = Orchestrator(
    ctx, cmds,
    on_turn_start=view.write_turn_start,   # () -> None — ツールループ各ターン開始時
    on_turn_end=view.write_turn_end,        # () -> None — LLM 最終回答確定時
    on_error=view.write_llm_error,          # (Exception) -> None — LLM エラー通知
)
```

`HistoryManager` は `on_compress` キーワード引数でコールバックを受け取る。

```python
hist_mgr = HistoryManager(
    ...,
    on_compress=view.write_compress_notice,  # (n: int) -> None — 圧縮したメッセージ数を渡す
)
```

`LLMClient` は `on_token` キーワード引数でコールバックを受け取る。

```python
llm = LLMClient(
    ...,
    on_token=view.write_token,   # (token: str) -> None — SSE トークン到着ごとに呼ばれる
)
```

## 6. read_multiline の動作詳細

- `first_line` の末尾 `\` を除いた文字列をパーツ先頭に追加
- 以降の行を `"... "` プロンプトで `loop.run_in_executor` (同期 `input()`) にて取得
- 継続条件: 入力行の末尾が `\` → 末尾を除いてパーツに追加し継続
- 終了条件: 末尾 `\` なし・空行・`EOFError` / `KeyboardInterrupt` のいずれか
- 収集したパーツを `"\n".join(parts)` して返す
