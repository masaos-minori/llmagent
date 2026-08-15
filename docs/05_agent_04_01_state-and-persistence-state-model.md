
title: "Agent State and Persistence - State Model (Part 1)"
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
  - 05_agent_04_01_state-and-persistence-state-model.md


# エージェントの状態と永続化

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- データレイヤー (スキーマ) → [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

## Purpose

エージェントの状態モデルを定義する: セッションスコープ/ターンスコープ/永続化対象の区分、
履歴圧縮がデータベースとどう相互作用するか、どのデータを誰が所有するか。

## Design Intent

### 状態のスコープ区別

`AgentContext`はセッションごとのDIハブであり、すべての可変状態を保持する。各コンポーネントのスコープは以下の通り：

- **セッションスコープ** — REPLのライフタイム中は保持される（`ConversationState`, `WorkflowState`, `RuntimeStats`, `AppServices`）
- **ターンスコープ** — ターン間でリセットされる（`TurnState`）

### 検証付き履歴変更メソッド

`ConversationState`は`history`への生の`list.append()`/`list.extend()`/直接代入の代わりに、
`agent/message_schema.py::validate_message()`経由で検証を強制する3つのメソッドを持つ：

- `append_message(msg, *, source="")` — メッセージを検証してから追加
- `extend_messages(msgs, *, source="")` — 複数メッセージを個別に検証して追加
- `replace_history(msgs, *, source="")` — 履歴全体を一括置き換え

`source`パラメータは検証時のみ使用され、信頼済みソースからのエフェメラルキーを許可するために一時的なコピーに付与される。`source`自体は`history`に保存されたメッセージやLLMへのペイロードに含まれない。

`replace_history()`はセッション復元時に多層防御として使われる。改ざん・破損したDB行が予約済みエフェメラルキーを持ち込むケースに対し、当該行はサニタイズまたは破棄されるため`SessionRestoreResult.n_messages`(元の取得件数)が実際の保存件数をわずかに上回りうる。

### RepositoryGatewayの責任境界

RepositoryGatewayはすべてのリポジトリ書込み/削除/API書込み操作の単一の強制境界。読み取り専用ツール呼び出しはノーチェックで`ToolExecutor`に直接転送される。書込み系操作は次の順で通過する：

1. ポリシー事前チェック (`tool_policy.check_preflight`)
2. `ToolExecutor`による実行
3. 監査ログ出力

承認プロンプトはRepositoryGateway自身では発行しない。`tool_runner.execute_all_tool_calls()`のバッチレベルゲートが、書込み/リスクのあるツール呼び出しを実行前に一度だけ承認を強制する前提の上に成り立つ。この前提を経由しない直接呼び出しは、非対話的な`check_preflight()`以外の承認チェックを受けない。

## Responsibility Boundary

### ConversationState (`ctx.conv`)

セッションスコープ。REPLのライフタイム中は保持される。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### TurnState (`ctx.turn`)

ターンスコープ。ターン間でリセットされる。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### WorkflowState (`ctx.workflow`)

セッションスコープのワークフローランタイム状態。一時的なもので、REPL再起動をまたいで永続化されない。永続的なタスク状態は`StateStore`経由で`workflow.sqlite`に存在する。

### RuntimeStats (`ctx.stats`)

セッション累積のカウンタとレイテンシサンプル。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### AppServices (`ctx.services`)

`factory.build_agent_context()`が構築する、完全初期化済みのサービス参照の集合体。ランタイム集計フィールドを持つが、`ctx.stats`とは別枠。

## Key Constraints

### 状態スコープの分離

セッションスコープとターンスコープは明確に分離されている。ターンスコープの値は各ターン終了時にリセットされ、セッションスコープの値はREPLのライフタイム中に保持される。

### 検証付き履歴変更

すべての履歴変更は検証付きメソッドを経由する必要がある。生のリスト操作は禁止。

### RepositoryGatewayの単一境界

書込み系操作はすべてRepositoryGatewayを経由する必要がある。この前提を経由しない直接呼び出しは、承認チェックを受けない。

## Operational Notes

- `replace_history()`はセッション復元時に多層防御として使われる。改ざん・破損したDB行が予約済みエフェメラルキーを持ち込むケースに対し、当該行はサニタイズまたは破棄される。
- RepositoryGatewayの承認プロンプトはバッチレベルゲートが強制する前提の上にある。

## Known Limitations

- `replace_history()`経由のセッション復元時、改ざん・破損したDB行が予約済みエフェメラルキーを持ち込むケースはまれだが許容されている。

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_04_02_state-and-persistence-history-compression.md`
- `05_agent_04_03_state-and-persistence-platform-databases.md`
- `05_agent_04_01_state-and-persistence-state-model.md`

## Keywords

AgentContext state model
ConversationState
append_message
extend_messages
replace_history
validate_message
TurnState
WorkflowState
RuntimeStats
AppServices
RepositoryGateway
session persistence
StartupOrchestrator._setup_prompt
session_restore.restore_session
bulk history replacement defense-in-depth

# エージェントの状態と永続化

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- データレイヤー (スキーマ) → [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

## Purpose

エージェントの状態モデルを定義する: セッションスコープ/ターンスコープ/永続化対象の区分、
履歴圧縮がデータベースとどう相互作用するか、どのデータを誰が所有するか。

## Design Intent

### 状態のスコープ区別

`AgentContext`はセッションごとのDIハブであり、すべての可変状態を保持する。各コンポーネントのスコープは以下の通り：

- **セッションスコープ** — REPLのライフタイム中は保持される（`ConversationState`, `WorkflowState`, `RuntimeStats`, `AppServices`）
- **ターンスコープ** — ターン間でリセットされる（`TurnState`）

### 検証付き履歴変更メソッド

`ConversationState`は`history`への生の`list.append()`/`list.extend()`/直接代入の代わりに、
`agent/message_schema.py::validate_message()`経由で検証を強制する3つのメソッドを持つ：

- `append_message(msg, *, source="")` — メッセージを検証してから追加
- `extend_messages(msgs, *, source="")` — 複数メッセージを個別に検証して追加
- `replace_history(msgs, *, source="")` — 履歴全体を一括置き換え

`source`パラメータは検証時のみ使用され、信頼済みソースからのエフェメラルキーを許可するために一時的なコピーに付与される。`source`自体は`history`に保存されたメッセージやLLMへのペイロードに含まれない。

`replace_history()`はセッション復元時に多層防御として使われる。改ざん・破損したDB行が予約済みエフェメラルキーを持ち込むケースに対し、当該行はサニタイズまたは破棄されるため`SessionRestoreResult.n_messages`(元の取得件数)が実際の保存件数をわずかに上回りうる。

### RepositoryGatewayの責任境界

RepositoryGatewayはすべてのリポジトリ書込み/削除/API書込み操作の単一の強制境界。読み取り専用ツール呼び出しはノーチェックで`ToolExecutor`に直接転送される。書込み系操作は次の順で通過する：

1. ポリシー事前チェック (`tool_policy.check_preflight`)
2. `ToolExecutor`による実行
3. 監査ログ出力

承認プロンプトはRepositoryGateway自身では発行しない。`tool_runner.execute_all_tool_calls()`のバッチレベルゲートが、書込み/リスクのあるツール呼び出しを実行前に一度だけ承認を強制する前提の上に成り立つ。この前提を経由しない直接呼び出しは、非対話的な`check_preflight()`以外の承認チェックを受けない。

## Responsibility Boundary

### ConversationState (`ctx.conv`)

セッションスコープ。REPLのライフタイム中は保持される。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### TurnState (`ctx.turn`)

ターンスコープ。ターン間でリセットされる。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### WorkflowState (`ctx.workflow`)

セッションスコープのワークフローランタイム状態。一時的なもので、REPL再起動をまたいで永続化されない。永続的なタスク状態は`StateStore`経由で`workflow.sqlite`に存在する。

### RuntimeStats (`ctx.stats`)

セッション累積のカウンタとレイテンシサンプル。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### AppServices (`ctx.services`)

`factory.build_agent_context()`が構築する、完全初期化済みのサービス参照の集合体。ランタイム集計フィールドを持つが、`ctx.stats`とは別枠。

## Key Constraints

### 状態スコープの分離

セッションスコープとターンスコープは明確に分離されている。ターンスコープの値は各ターン終了時にリセットされ、セッションスコープの値はREPLのライフタイム中に保持される。

### 検証付き履歴変更

すべての履歴変更は検証付きメソッドを経由する必要がある。生のリスト操作は禁止。

### RepositoryGatewayの単一境界

書込み系操作はすべてRepositoryGatewayを経由する必要がある。この前提を経由しない直接呼び出しは、承認チェックを受けない。

## Operational Notes

- `replace_history()`はセッション復元時に多層防御として使われる。改ざん・破損したDB行が予約済みエフェメラルキーを持ち込むケースに対し、当該行はサニタイズまたは破棄される。
- RepositoryGatewayの承認プロンプトはバッチレベルゲートが強制する前提の上にある。

## Known Limitations

- `replace_history()`経由のセッション復元時、改ざん・破損したDB行が予約済みエフェメラルキーを持ち込むケースはまれだが許容されている。

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_04_02_state-and-persistence-history-compression.md`
- `05_agent_04_03_state-and-persistence-platform-databases.md`
- `05_agent_04_01_state-and-persistence-state-model.md`

## Keywords

AgentContext state model
ConversationState
append_message
extend_messages
replace_history
validate_message
TurnState
WorkflowState
RuntimeStats
AppServices
RepositoryGateway
session persistence
StartupOrchestrator._setup_prompt
session_restore.restore_session
bulk history replacement defense-in-depth



# エージェントの状態と永続化

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
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
- `05_agent_04_01_state-and-persistence-state-model.md`

## Keywords

AgentContext state model
ConversationState
TurnState
WorkflowState
RuntimeStats
session persistence

# エージェントの状態と永続化

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
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
- `05_agent_04_01_state-and-persistence-state-model.md`

## Keywords

AgentContext state model
ConversationState
TurnState
WorkflowState
RuntimeStats
session persistence

