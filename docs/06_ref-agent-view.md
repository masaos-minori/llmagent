# agent/cli_view.py

## 1. 機能概要

readline 設定・RAG 進捗表示・マルチライン入力を担うプレゼンテーション層。`RagPipeline` へ `on_status` / `on_clear` コールバックとして渡すことで UI 依存を排除。

## 2. API

```python
from agent.cli_view import CLIView

view = CLIView(slash_commands=["/help", "/exit", ...])
view.setup_readline()
view.rag_status("expanding query...")
view.rag_clear()
line = await view.read_multiline(loop, first_line)
```

| メソッド | 説明 |
|---|---|
| `setup_readline() -> None` | readline タブ補完・履歴ファイル読み込みを設定 |
| `write_history() -> None` | readline 履歴を `~/.agent_history` に保存 |
| `rag_status(msg: str) -> None` | `[rag] {msg}` をインプレース表示 (`\r` 上書き) |
| `rag_clear() -> None` | RAG 進捗表示行をクリア |
| `read_multiline(loop, first_line) -> str` | 行末 `\` の継続入力を収集し `\n` で連結して返す |
