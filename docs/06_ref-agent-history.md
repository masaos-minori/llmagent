# history_manager.py

## 1. 機能概要

`AgentREPL` から抽出した会話履歴管理レイヤー。文字数カウントと LLM ベースのコンテキスト圧縮を担当。`AgentREPL().run()` で `HistoryManager` インスタンスを生成し、`self._hist_mgr` として保持。

## 2. API

```python
from history_manager import HistoryManager

mgr = HistoryManager(
    http=httpx.AsyncClient(...),
    chat_url="http://127.0.0.1:8002",
    char_limit=8000,
    compress_turns=4,
    compress_temperature=0.3,
    compress_max_tokens=300,
)
total_chars = mgr.count_chars(history)
history = await mgr.compress(history)
```

| メソッド | 説明 |
|---|---|
| `count_chars(history) -> int` | 会話履歴の総文字数を推定する (content 文字列長 + tool_calls JSON 長の合計) |
| `compress(history) -> list[dict]` | 総文字数が `char_limit` を超えていれば、先頭 `compress_turns * 2` 件を LLM 要約に置換して新しい履歴リストを返す。閾値以内なら入力をそのまま返す |
| `_select_turns_to_compress(history) -> tuple \| None` | history を `(system_msgs, to_compress, remaining)` に分割。ターン数が不足する場合は `None` を返す |
| `_build_history_text(messages) -> str` | 圧縮 LLM への入力テキストを `ROLE: content` 形式で生成 |

統計属性:
- `stat_compress_count: int` — セッション通算圧縮実行回数

## 3. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent_repl.py` | `self._hist_mgr = HistoryManager(...)` を `run()` で生成し、`_compress_history()` から委譲 |
