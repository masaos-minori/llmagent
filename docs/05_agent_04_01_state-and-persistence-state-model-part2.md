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

## Purpose

セッション永続化と会話履歴のデータベース間関係について文書化する。

## Design Intent

### セッション永続化の設計意図

`AgentSession`が`session.sqlite`を管理する。セッションのライフサイクルは以下の通り：

``` text
AgentREPL.run()
  → AgentSession.start()              — sessionsへINSERT; session_idを取得
  → each turn: AgentSession.save()    — messagesへINSERT
  → /session load <id>                — fetch_messages() → ctx.conv.historyを再構築
  → /session delete <id>              — sessions + messagesをDELETE (CASCADE)
```

### メッセージ保存ルール

`save(role, content)`は有効なロールのみを保存する：`user`, `assistant`, `tool`, `system`。無効なロールや`session_id`欠落は警告としてログに記録され、カウントされる。`strict_mode=True`の場合、両条件ともスキップの代わりに`RuntimeError`を発生させる。

`save_many(messages)`は複数のメッセージを1つのトランザクションでバッチ処理する。`replace_messages(messages)`は圧縮された履歴のスナップショットをDBに書き戻す。

### DiagnosticStoreの分離設計

診断データ（LLMトランスポートエラー、ガードヒント、セッションランタイムサマリー）は`DiagnosticStore`経由で`session_diagnostics`テーブルに永続化される。`messages`テーブルとは別であり、部分完了の永続化モデルについては[05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md)を参照。

**現在の実装挙動:** DiagnosticStoreは`session_diagnostics`テーブルにのみ書き込む。診断データは`session_diagnostics`を通じてのみ永続化され、`diagnostics.jsonl`への二重永続化は行われない。

### セッションタイトル生成のフォールバック判断

最初のユーザーターンにおいて、セッションタイトル生成が失敗した場合のフォールバック：

| Failure case | Fallback title | Log |
|---|---|---|
| LLM HTTP/リクエストエラー | 長さ > 32の場合`first_input[:29] + "..."`、それ以外は`first_input` | WARNING |
| LLMが空または不正なレスポンスを返す | 上記と同様 | WARNING |
| `first_input`が空 | `"(New Session)"` | WARNING |
| `set_title()`のDB書き込みが失敗 | タイトルは永続化されない; エラーがログに記録される | ERROR |

すべての失敗ケースはノンブロッキングであり、セッションは通常通り継続する。フォールバック時、監査ログエントリが発行される：`session_title_fallback session_id=<id> fallback=<title> reason=<error>`。`set_title_pending`は結果にかかわらず`finally`ブロックで`False`にリセットされる。

## Responsibility Boundary

### セッション永続化

`AgentSession`が`session.sqlite`の`sessions`テーブルと`messages`テーブルを管理する。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### 会話履歴とデータベースの関係

``` text
ctx.conv.history (in-memory list)
    ↕ synchronized per turn
AgentSession (session.sqlite: sessions + messages)
```

- セッション中はhistoryが正となるソースである
- データベースは永続的なバックアップである
- `/session load <id>`はデータベースから`ctx.conv.history`を再構築する
- `delete_last_turn()`はDBから最後の（最大2件の）行を削除する
- `undo_last_turn()`は最後の`role='user'`メッセージ以降のすべてを削除する

## Key Constraints

### 有効なロールのみ保存

`user`, `assistant`, `tool`, `system`以外のロールは保存されない。

### strict_modeの動作

`strict_mode=True`の場合、無効なロールや`session_id`欠落は例外を発生させる。

### DiagnosticStoreの分離

診断データは`session_diagnostics`テーブルにのみ書き込まれる。`messages`には決して存在しない。

## Operational Notes

- セッションタイトル生成の失敗はノンブロッキングであり、セッションは通常通り継続する。
- DiagnosticStoreは`session_diagnostics`テーブルにのみ書き込む。`diagnostics.jsonl`への二重永続化は行われない。

## Known Limitations

- 不明

## Related Docs

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
