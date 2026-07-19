---
title: "Agent State and Persistence - State Model (Part 2)"
category: agent
tags:
  - agent
  - state
  - persistence
  - agentcontext
  - session
related:
  - 05_agent_00_document-guide.md
  - 05_agent_04_02_state-and-persistence-history-compression.md
  - 05_agent_04_03_state-and-persistence-platform-databases.md
source:
  - 05_agent_04_01_state-and-persistence-state-model-part1.md
---

# エージェントの状態と永続化

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md)
- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- データレイヤー (スキーマ) → [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

## セッション永続化 (`AgentSession`)

`AgentSession` (`agent/session.py`) が`session.sqlite`を管理する。

### ターンごとに永続化される内容

| Event | Table | Content |
|---|---|---|
| セッション開始 | `sessions` | session_id, created_at, title |
| 各メッセージ | `messages` | role, content, tool_calls, tool_call_id, session_id |

### セッションのライフサイクル

```
AgentREPL.run()
  → AgentSession.start()              — sessionsへINSERT; session_idを取得
  → each turn: AgentSession.save()    — messagesへINSERT
  → /session load <id>                — fetch_messages() → ctx.conv.historyを再構築
  → /session delete <id>              — sessions + messagesをDELETE (CASCADE)
```

### セッションタイトル生成

最初のユーザーターンにおいて、`cmd_session.py`内のセッションタイトル生成が`SessionTitleService.generate()`を呼び出し、LLMベースの短いタイトルを生成する。これはasyncioのバックグラウンドタスクとして実行される (`asyncio.create_task()`によるfire-and-forget)。

### セッションタイトル生成失敗時の挙動

| Failure case | Fallback title | Log |
|---|---|---|
| LLM HTTP/リクエストエラー | 長さ > 32の場合`first_input[:29] + "..."`、それ以外は`first_input` | WARNING |
| LLMが空または不正なレスポンスを返す | 上記と同様 | WARNING |
| `first_input`が空 | `"(New Session)"` | WARNING |
| `set_title()`のDB書き込みが失敗 | タイトルは永続化されない; エラーがログに記録される | ERROR |

すべての失敗ケースはノンブロッキングであり、セッションは通常通り継続する。
フォールバック時、監査ログエントリが発行される: `session_title_fallback session_id=<id> fallback=<title> reason=<error>`。
`set_title_pending`は結果にかかわらず`finally`ブロックで`False`にリセットされる。

### メッセージ保存ルール

- `save(role, content)`は有効なロールのみを保存する: `user`, `assistant`, `tool`, `system`
- 無効なロールは警告としてログに記録され、カウントされる (`stat_skipped_invalid_role`)
- `session_id`が欠落している場合は警告としてログに記録され、カウントされる (`stat_skipped_no_session`)
- `strict_mode=True`の場合、両条件ともスキップの代わりに`RuntimeError`を発生させる
- カウンタは`session.skipped_no_session_count`と`session.skipped_invalid_role_count`からアクセス可能
- `save_many(messages)`は複数のメッセージを1つのトランザクションでバッチ処理する; 無効なロールは単一の警告ログと共にスキップされる
- `replace_messages(messages)`は圧縮された履歴のスナップショットをDBに書き戻す; session_idがNoneの場合は黙ってスキップする
- 診断データ (LLMトランスポートエラー、ガードヒント、セッションランタイムサマリー) は`DiagnosticStore` (`agent/diagnostic_store.py`) 経由で`session_diagnostics`テーブルに永続化される — `messages`テーブルとは別。部分完了の永続化モデルについては → [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md)
- `DiagnosticStore`のメソッド: `save(session_id, kind, content)`, `fetch(session_id)`, `fetch_all(limit=50)`
- `AgentContext.diagnostics`は初期化時にorchestratorの診断ストアに接続される; `Orchestrator`が構築される前は`None`
- 書き込まれる種別: `"mid_turn_error"` (`ErrorInjectionService`, `LLMTurnRunner`, `Orchestrator`からのLLMトランスポートエラー), `"guard_hint"` (`ToolLoopGuard`からの循環/重複排除/リトライイベント)
- ガードヒントとターン中のエラーは診断データにのみ格納される — `ctx.conv.history`には現れない
- 診断データは`DiagnosticStore`経由で`session_diagnostics`テーブルに格納される; `messages`には決して存在せず、したがって`fetch_messages()`からは返されない

**現在の実装挙動 (`DiagnosticStore`の全種別):** `agent/diagnostic_store.py`が持つ専用書込みメソッドと対応する`kind`は以下の通り。上記の`mid_turn_error`/`guard_hint`は呼び出し元 (`error_injection_service.py`, `llm_transport_errors.py`, `llm_turn_runner.py`, `tool_loop_guard.py`) が`save()`を直接呼んで書く一方、以下は`DiagnosticStore`自身の専用メソッド経由で書かれる。

| Method | `kind` | Caller |
|---|---|---|
| `save_partial_completion()` | `partial_completion` | `llm_transport_errors.handle_partial_completion()` (LLM応答が部分的に切断された場合) |
| `save_serialization_event()` | `serialization_event` | `tool_runner.py` (DAGツール実行のラウンド単位シリアル化イベント) |
| `save_transport_failure()` | `transport_failure` | `tool_runner.py` (ツール実行のトランスポート層失敗) |
| `save_loop_guard_hint()` | `loop_guard_hint` | 呼び出し元なし (grep上、定義のみで未使用) |

**矛盾/未整理点:** `DiagnosticStore.save_loop_guard_hint()`は`kind="loop_guard_hint"`を書き込むメソッドとして定義されているが、実際に`ToolLoopGuard`が使うのは`save()`を直接呼ぶ`kind="guard_hint"`の経路 (ツールループガード関数内) であり、`save_loop_guard_hint()`はコードベース中どこからも呼ばれていない。同一目的のメソッドが2種類存在し、一方が死んでいる状態。

*(根拠分類: Explicit in code — `agent/diagnostic_store.py`, `agent/tool_loop_guard.py`, `agent/llm_transport_errors.py`)*

> **現在の挙動:** DiagnosticStoreは`session_diagnostics`テーブルにのみ書き込む。診断データは`session_diagnostics`を通じてのみ永続化され、`diagnostics.jsonl`への二重永続化は行われない。

---

## 会話履歴とデータベースの関係

```
ctx.conv.history (in-memory list)
    ↕ synchronized per turn
AgentSession (session.sqlite: sessions + messages)
```

- セッション中はhistoryが正となるソースである
- データベースは永続的なバックアップである
- `/session load <id>`はデータベースから`ctx.conv.history`を再構築する
- `delete_last_turn()`はDBから最後の (最大2件の) 行を削除する
- `undo_last_turn()`は最後の`role='user'`メッセージ以降のすべてを削除する

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_04_02_state-and-persistence-history-compression.md`
- `05_agent_04_03_state-and-persistence-platform-databases.md`
- `05_agent_04_01_state-and-persistence-state-model-part1.md`

## Keywords

AgentContext state model
ConversationState
TurnState
WorkflowState
RuntimeStats
session persistence
