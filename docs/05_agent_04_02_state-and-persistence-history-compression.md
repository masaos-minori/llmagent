---
title: "Agent State and Persistence - History Compression"
category: agent
tags:
  - agent
  - state
  - persistence
  - history-compression
  - data-classification
related:
  - 05_agent_00_document-guide.md
  - 05_agent_04_01_state-and-persistence-state-model.md
  - 05_agent_04_03_state-and-persistence-platform-databases.md
source:
  - 05_agent_04_01_state-and-persistence-state-model.md
---

# エージェントの状態と永続化

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- データレイヤー (スキーマ) → [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

## HistoryManagerによる圧縮

`HistoryManager` (`agent/history.py`) が`ctx.conv.history`の圧縮を管理する。

### 圧縮のトリガー

以下のいずれかに該当する場合、各ターンでトリガーされる:
- `len(history_chars) > context_char_limit` (デフォルト8000)
- `token_count > context_token_limit` (0より大きい場合)

### 圧縮対象の選択

`HistorySelectionPolicy.select_turns_to_compress()`は以下によりターンを選択する:
1. 重要度スコアリング (ピン留め → 明示的な重要度 → キーワードベース)
2. カテゴリ分類:
   - `temporary` (toolロール) — 最も削除優先度が高い
   - `temporary_reasoning` (tool_calls付きassistant) — 次点の優先度
   - `factual` (system) — 保持される
   - `history` (user/assistantのテキスト) — 通常優先度
3. 直近の`history_protect_turns` (デフォルト2) 件のuser+assistantペアは対象外

### 圧縮結果

- 選択された古いターン → 1件のLLM要約メッセージに置換される
- `CompressResult.compressed_count` = 置換されたメッセージ数
- `CompressResult.protected_count` = スキップされた (保護された) メッセージ数
- `stat_compress_count`がインクリメントされる

### 圧縮の永続化モデル

各履歴圧縮 (自動または`/compact`) の後、圧縮されたスナップショットは`AgentSession.replace_messages()`経由で`session.sqlite`に書き戻される。これにより`/session load`が意味的に一貫した状態を復元できる — 復元された履歴は次のLLM呼び出し前にコンテキストに実際にあったものと一致する。

主な挙動:
- 圧縮された`[Conversation summary]`のsystemメッセージは`role=system`の行として永続化される; `fetch_messages()` → `LLMMessage`を通じて正しくラウンドトリップする。
- フォールバックの切り詰め (要約なしの破棄) もDBの一貫性を保つため永続化をトリガーする。
- メモリ上の`ctx.conv.history`は現在のセッションの正となるソースであり続ける; DB永続化はリロード時のためのバックアップである。
- `/history`と`/export`は引き続き`ctx.conv.history`に対して動作する; 変更不要。
- `stat_turns`カウンタと他のメモリ上の統計はリロード時にリセットされる (既存の挙動)。

**注:** 圧縮されたセッションのリロード後、`/undo`は圧縮済みのDB行に対して動作する — 元のメッセージが要約メッセージに置き換えられているため、ユーザーが期待するよりも少ないターン数しか取り消せない場合がある。

### トークンカウント

優先順位: (1) LLMの`usage.input_tokens` (正確); (2) `/tokenize`エンドポイント (正確);
(3) `chars // 4`のフォールバック。

### HistoryManager API (主なメソッド)

| Method | Description |
|---|---|
| `count_chars(history)` | 合計文字数 (content + tool_calls JSON) |
| `count_tokens(history, last_input_tokens)` | 同期のトークン数推定 |
| `count_tokens_async(...)` | 非同期のトークン数計算; `(count, is_exact)`を返す |
| `compress(history)` | 上限超過時に圧縮; `(new_history, CompressResult)`を返す |
| `force_compress(history)` | 上限にかかわらず即座に圧縮する (`/compact`コマンド) |
| `apply_config(...)` | ホットリロード: char_limit, compress_turns, token_limit, tokenize_url |

### 圧縮の永続化モデル

各履歴圧縮 (自動または`/compact`) の後、圧縮されたスナップショットは`AgentSession.replace_messages()`経由で`session.sqlite`に書き戻される。これにより`/session load`が意味的に一貫した状態を復元できる — 復元された履歴は次のLLM呼び出し前にコンテキストに実際にあったものと一致する。

主な挙動:
- 圧縮された`[Conversation summary]`のsystemメッセージは`role=system`の行として永続化される; `fetch_messages()` → `LLMMessage`を通じて正しくラウンドトリップする。
- フォールバックの切り詰め (要約なしの破棄) もDBの一貫性を保つため永続化をトリガーする (`CompressResult.is_fallback=True`)。
- メモリ上の`ctx.conv.history`は現在のセッションの正となるソースであり続ける; DB永続化はリロード時のためのバックアップである。
- `/history`と`/export`は引き続き`ctx.conv.history`に対して動作する; 変更不要。
- `stat_turns`カウンタと他のメモリ上の統計はリロード時にリセットされる (既存の挙動)。

**注:** 圧縮されたセッションのリロード後、`/undo`は圧縮済みのDB行に対して動作する — 元のメッセージが要約メッセージに置き換えられているため、ユーザーが期待するよりも少ないターン数しか取り消せない場合がある。

---

## データ分類

| Data type | Scope | Storage | When persisted | Cleared by |
|---|---|---|---|---|
| `ctx.conv.history` | セッション | メモリ上 | メッセージごと (非同期、LLM呼び出し前) | `/clear`またはセッション終了時 |
| `ctx.conv.*`フラグ | セッション | メモリ上 | — (永続化されない) | セッション再起動時 |
| `ctx.turn.current_turn_id` | ターン | メモリ上 | — (永続化されない) | 各ターン終了時 |
| `ctx.stats.*` | セッション | メモリ上 | — (`/stats`経由で報告) | `/clear` |
| `sessions`テーブル | 永続 | SQLite | セッション作成時; タイトルは最初のターンで非同期生成 | `/session delete` |
| `messages`テーブル | 永続 | SQLite | `AgentSession.save()`呼び出しごと | `/session delete`または`/undo` |
| メモリJSONL / `memories`テーブル | 永続 | JSONL + SQLite | メモリ抽出時 (非同期) | `/memory delete`または`/memory prune` |

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_04_01_state-and-persistence-state-model.md`
- `05_agent_04_03_state-and-persistence-platform-databases.md`

## Keywords

HistoryManager compression
compression trigger
compression selection
data classification
