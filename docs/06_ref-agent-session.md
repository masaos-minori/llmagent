# agent/session.py

## 1. 機能概要

REPL セッション・メッセージ・ノートの SQLite 永続化と、RAG ドキュメント操作 (削除・一覧) を担当するモジュール。`agent/repl.py` から import して使用。

**主な責務:**
- `sessions` / `messages` テーブルへの読み書き (セッション CRUD・メッセージ保存)
- `notes` テーブルの CRUD (ノートの追加・一覧・削除)
- `documents` / `chunks` テーブルのドキュメント削除・一覧 (RAG DB 側の操作を agent コマンドから委譲)

RAG ドキュメント管理は本来 RAG 層の責務だが、`/db clean` 等の agent コマンドから呼ぶ利便性のため `AgentSession` に集約している。将来的には RAG MCP サービス側への責務移管を検討。

## 2. API

```python
from agent.session import AgentSession

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
| `save(role, content, tool_calls=None, tool_call_id=None) -> None` | `messages` テーブルにメッセージを保存。`tool_call_id` は role="tool" のメッセージに使用。`session_id` が `None` のときは無操作。`role` が `_VALID_ROLES` (`"user"` / `"assistant"` / `"tool"` / `"system"`) 以外の場合は保存せずに終了 |
| `save_many(messages) -> None` | `list[tuple[role, content, tool_calls, tool_call_id]]` を 1 接続・1 トランザクションで一括 INSERT。`session_id` が `None` または空リストのときは無操作。無効な role の行はサイレントにスキップされる |
| `set_title(title) -> None` | `sessions.title` を更新 (50 文字以内)。`session_id` が `None` のときは無操作 |
| `list_sessions(limit=20) -> list[dict]` | `sessions` テーブルから最新 `limit` 件を取得して返す (デフォルト: 20 件)。各要素は `{session_id, created_at, title, is_current}` |
| `delete_document(url) -> bool` | 指定 URL のドキュメントとチャンク (`chunks_vec` → `documents` ON DELETE CASCADE) を DB から削除。削除できた場合 `True`、URL が未登録の場合 `False` を返す |
| `delete_last_turn() -> None` | 現在のセッションの末尾 2 行を `message_id` 降順で DB から削除する (最大 2 行)。role に依存せず最新 2 行を削除する。`session_id` が `None` のときは無操作 |
| `undo_last_turn() -> int` | DBから最後の `role='user'` メッセージ以降の全メッセージを削除し、削除件数を返す。tool_call / memory injection メッセージを含むターンも正しく処理する。`session_id` が `None` のとき 0 を返す |
| `delete_session(session_id) -> bool` | 指定セッションとメッセージを DB から削除。`sessions` の ON DELETE CASCADE で `messages` も自動削除。削除できた場合 `True`、未発見またはエラー時は `False` を返す |
| `fetch_messages(session_id) -> list[LLMMessage] \| None` | 指定セッションの `messages` を `role / content / tool_calls / tool_call_id` 形式の `LLMMessage` リストで返す (`message_id` 昇順)。セッションが存在しない・メッセージが 0 件・DB エラー時はいずれも `None` を返す |
| `list_documents(lang=None, limit=20) -> list[dict]` | 登録済みドキュメントを返す。各要素は `{url, title, lang, fetched_at, chunk_count}`。`lang` で言語フィルタ (`"ja"` / `"en"`) 指定可 |
| `add_note(content) -> int \| None` | `notes` テーブルに新規ノートを INSERT して `note_id` を返す。失敗時は `None` |
| `list_notes() -> list[dict]` | `notes` テーブルの全ノートを `note_id` 昇順で返す。各要素は `{note_id, content, created_at}` |
| `delete_note(note_id) -> bool` | 指定 `note_id` のノートを削除。削除できた場合 `True`、未発見時は `False` |
| `get_all_note_contents() -> list[str]` | 全ノートのコンテンツ文字列リストを作成順で返す。`auto_inject_notes` によるシステムプロンプト注入用 |

## 3. 設計上の注意

- `AgentREPL` が `session_id` を直接変更する必要がある場合 (`/session load`) は `session.session_id = new_id` で直接代入する
- `list_sessions()` は REPL コマンド表示のため `print()` で直接出力する
- `fetch_messages()` はデータのみを返す。会話履歴への統合は呼び出し元 (`_SessionMixin._load_session()`) が担当
- `delete_last_turn()` は最大 2 行を削除 (ターン完結時: user+assistant、LLM 失敗時: user のみ)
- `undo_last_turn()` は最後の `role='user'` から後ろの全行を削除する。tool_call / memory injection など複数メッセージを含むターンにも対応

## 4. スラッシュコマンド (`_SessionMixin`)

`agent/commands/cmd_session.py` の `_SessionMixin` が `/session` コマンドのハンドラを提供する。`CommandRegistry` がこの Mixin を継承することで利用可能になる。

```
/session list [n]        — 直近 n 件のセッション一覧を表示 (デフォルト: 20)
/session load <id>       — 指定セッションを復元して会話履歴を差し替える
/session rename <title>  — 現在セッションのタイトルを変更する
/session delete <id>     — 指定セッションを削除する (現在セッションは削除不可)
```

| メソッド | 説明 |
|---|---|
| `_cmd_session(args: str) -> None` | `/session` コマンドのディスパッチャ。サブコマンドを解析して下記ハンドラに委譲する |
| `_session_load_safe(arg: str) -> None` | `arg` を整数セッション ID として解析し `_load_session()` を呼ぶ。変換失敗時はエラーメッセージを表示 |
| `_session_delete(arg: str) -> None` | `arg` を整数セッション ID として解析してセッションを削除。現在のセッション (`ctx.session.session_id`) と一致する場合は削除を拒否する |
| `_load_session(session_id: int) -> None` | `ctx.session.fetch_messages()` でメッセージを取得し、`ctx.conv.history` を system メッセージ + 取得メッセージで再構築する。`ctx.session.session_id` も新 ID に更新する |
| `_generate_session_title(first_input: str) -> None` (async) | `SessionTitleService` (`agent/services/session_title.py`) に委譲。LLM で 8 単語以内のタイトルを生成して保存。失敗時は `first_input[:50]` にフォールバック |

### セッション復元の挙動詳細

`_load_session()` は以下の順で処理する:

1. `ctx.session.fetch_messages(session_id)` を呼び出す
2. `None` が返った場合 (セッション未発見またはメッセージ 0 件) は「not found」メッセージを表示して終了
3. `ctx.conv.history` の system メッセージ (`role == "system"`) のみを抽出し、取得メッセージを後続に連結する
4. `ctx.session.session_id = session_id` で現在セッション ID を上書きする

## 5. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/repl.py` | `self._session` として保持。全セッション・メッセージ DB 操作を委譲する |
