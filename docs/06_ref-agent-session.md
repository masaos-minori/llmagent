# agent_session.py

## 1. 機能概要

REPL セッションとメッセージの SQLite 永続化を担当するモジュール。`agent_repl.py` から import して使用。
セッション ID の保持と全 DB 操作 (`sessions` / `messages` テーブルへの読み書き) をカプセル化し、`AgentREPL` から永続化ロジックを分離 (SOLID の単一責任原則)。

## 2. API

```python
from agent_session import AgentSession

session = AgentSession()
session.start()                            # sessions テーブルに INSERT してセッション ID を取得
session.save("user", "こんにちは")         # messages テーブルにメッセージを保存
session.set_title("最初のユーザー入力")     # sessions.title を更新 (50 文字以内)
session.list_sessions()                    # 直近 20 件を画面表示
msgs = session.fetch_messages(3)           # セッション ID=3 のメッセージリストを取得
```

| メソッド / 属性 | 説明 |
|---|---|
| `session_id: int \| None` | 現在のセッション DB 行 ID (start() 後に設定される) |
| `start() -> None` | `sessions` テーブルに新行を INSERT して `session_id` を設定。失敗時は `session_id = None` |
| `save(role, content, tool_calls=None, tool_call_id=None) -> None` | `messages` テーブルにメッセージを保存。`tool_call_id` は role="tool" のメッセージに使用。`session_id` が `None` のときは無操作 |
| `save_many(messages) -> None` | `list[tuple[role, content, tool_calls, tool_call_id]]` を 1 接続・1 トランザクションで一括 INSERT。`session_id` が `None` または空リストのときは無操作 |
| `set_title(title) -> None` | `sessions.title` を更新 (50 文字以内)。`session_id` が `None` のときは無操作 |
| `list_sessions(limit=20) -> None` | `sessions` テーブルから最新 `limit` 件を取得して表形式で表示 (デフォルト: 20 件) |
| `delete_document(url) -> bool` | 指定 URL のドキュメントとチャンク (`chunks_vec` → `documents` ON DELETE CASCADE) を DB から削除。削除できた場合 `True`、URL が未登録の場合 `False` を返す |
| `delete_last_turn() -> None` | 現在のセッションの末尾 user+assistant メッセージ対を DB から削除する (最大 2 行)。`session_id` が `None` のときは無操作 |
| `delete_session(session_id) -> bool` | 指定セッションとメッセージを DB から削除。`sessions` の ON DELETE CASCADE で `messages` も自動削除。削除できた場合 `True`、未発見またはエラー時は `False` を返す |
| `fetch_messages(session_id) -> list[LLMMessage] \| None` | 指定セッションの `messages` を `role / content / tool_calls` 形式の `LLMMessage` リストで返す。未発見またはエラー時は `None` |
| `list_documents(lang=None, limit=20) -> None` | 登録済みドキュメントの URL・タイトル・言語・チャンク数・取込日時を表形式で表示。`lang` で言語フィルタ (`"ja"` / `"en"`) 指定可 |
| `add_note(content) -> int \| None` | `notes` テーブルに新規ノートを INSERT して `note_id` を返す。失敗時は `None` |
| `list_notes() -> list[dict]` | `notes` テーブルの全ノートを `note_id` 昇順で返す。各要素は `{note_id, content, created_at}` |
| `delete_note(note_id) -> bool` | 指定 `note_id` のノートを削除。削除できた場合 `True`、未発見時は `False` |
| `get_all_note_contents() -> list[str]` | 全ノートのコンテンツ文字列リストを作成順で返す。`auto_inject_notes` によるシステムプロンプト注入用 |

## 3. 設計上の注意

- `AgentREPL` が `session_id` を直接変更する必要がある場合 (`/session load`) は `session.session_id = new_id` で直接代入する
- `list_sessions()` は REPL コマンド表示のため `print()` で直接出力する
- `fetch_messages()` はデータのみを返す。会話履歴への統合は呼び出し元 (`CommandRegistry._load_session()`) が担当
- `delete_last_turn()` は最大 2 行を削除 (ターン完結時: user+assistant、LLM 失敗時: user のみ)

## 4. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent_repl.py` | `self._session` として保持。全セッション・メッセージ DB 操作を委譲する |
