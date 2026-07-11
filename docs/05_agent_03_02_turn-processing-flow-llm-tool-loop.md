---
title: "Agent Turn Processing Flow - LLM and Tool Loop"
category: agent
tags:
  - agent
  - turn
  - llm-invocation
  - tool-loop
  - error-handling
related:
  - 05_agent_00_document-guide.md
  - 05_agent_03_01_turn-processing-flow-overview.md
  - 05_agent_03_03_turn-processing-flow-workflow-engine.md
source:
  - 05_agent_03_01_turn-processing-flow-overview.md
---

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## LLM呼び出しとツールループ

`LLMTurnRunner.run(llm_url)`が内部ループを管理する:

1. ペイロードを構築: `history + tool_definitions + temperature + max_tokens + stream=True`
2. SSEストリーミングでLLMに送信
3. `content_parts` (テキスト) と `tool_calls_map` (関数呼び出し) を収集
4. `finish_reason == "tool_calls"`の場合:
   - ツールを実行 → 結果を追加 → LLMに再送信
   - `max_tool_turns`回まで繰り返す
5. `finish_reason == "stop"`または`max_tool_turns`超過の場合: 最終回答を返す



`ToolLoopGuard`は各ツールループの反復中に以下をガードする:
- **重複排除:** 同一の`(name, args)`が`tool_dedup_max_repeats`回以上検出された場合 → ループを終了;
  ユーザーには`"Repeated tool call detected."`が表示される; ヒントは`session_diagnostics`に格納される
  (`kind='guard_hint'`, `guard_type='dedup'`)。
- **循環検出:** 直近の`tool_cycle_detect_window`ラウンド内で同一のツール呼び出しフィンガープリントが
  繰り返された場合 → ループを終了;
  ユーザーには`"Cyclic tool call pattern detected."`が表示される;
  ヒントは`session_diagnostics`に格納される (`kind='guard_hint'`, `guard_type='cycle'`)。
- **リトライ:** エラーとなった`(name, args)`が再度呼び出された場合 → ループを終了;
  ユーザーには`"Repeated failed tool call detected."`が表示される;
  ヒントは`session_diagnostics`に格納される (`kind='guard_hint'`, `guard_type='retry'`)。
- **連続エラー:** あるラウンドの全ツールが`tool_error_max_consecutive`回連続でエラーとなった場合
   → ループを終了; ユーザーには`"Too many consecutive tool errors."`が表示される。

### TurnLoopState dataclass

ターンごとのループ状態を保持する:

| Field | Type | Description |
|---|---|---|
| `seen_calls` | `set[str]` | 現在のターンで検出されたツール呼び出しフィンガープリント |
| `failed_calls` | `set[str]` | 失敗したツール呼び出しフィンガープリント |
| `consecutive_errors` | `int` | 全ツールが失敗した連続ラウンド数 |
| `round_fingerprints` | `list[str]` | 直近N ラウンド分のフィンガープリント (循環検出ウィンドウ) |

### ガードメソッド

| Method | Responsibility |
|---|---|
| `check_all(seen_calls, round_fingerprints, failed_calls, message)` | 重複排除・循環・リトライの各チェックを実行し、いずれかのガードが発動した場合ヒントを返す |
| `check_error_limit(consecutive_errors)` | 連続エラー上限をチェックし、超過時はメッセージを返す |

### ガード定数

| Constant | Value | Purpose |
|---|---|---|
| `DEDUP_HINT` | `"Repeated tool call detected. Use /context to see conversation."` | 重複排除ガード発動時のメッセージ |
| `CYCLE_HINT` | `"Cyclic tool call pattern detected."` | 循環検出ガード発動時のメッセージ |
| `RETRY_HINT` | `"Repeated failed tool call detected."` | リトライガード発動時のメッセージ |

> **Note:** ガードヒント (`DEDUP_HINT`, `CYCLE_HINT`, `RETRY_HINT`) はオフライン診断専用として
> `session_diagnostics`に`kind='guard_hint'`で格納される。
> これらは`ctx.conv.history`には注入されず、LLMからは見えない。
> いずれかのガードが発動した時点でループは即座に終了する。

---

## エラーハンドリング

### LLMトランスポートエラー (ストリーム開始前)

条件: コンテンツを受信する前に`LLMTransportError`が発生 (`partial_text == ""`)。

処理:
- assistantメッセージを履歴に保存しない
- ユーザーメッセージを履歴からポップする (履歴汚染を防止)
- ユーザーにエラーを表示; REPLは継続

### LLMトランスポートエラー (部分完了)

条件: `partial_text`が空でない状態で`LLMTransportError`が発生。

処理:
- **診断チャンネルのみ**: `ctx.session.save_diagnostic()`経由で`[INCOMPLETE: {kind}]`プレフィックス付きメッセージを永続化 — `ctx.conv.history`には追加されない (`DiagnosticStore`経由で`session_diagnostics`テーブルに格納)
- `stat_partial_completions += 1`

不完全な出力は通常の会話履歴から分離されるため、以降のLLMコンテキストを汚染しない。部分的なコンテンツは`session_diagnostics`テーブルへのDBクエリを通じてアクセス可能なまま残る。

各ターンの後、REPLの行ディスパッチャーが`handle_turn()`の前後で`stat_partial_completions`を比較する。増加していれば、ユーザーに見える警告が出力される:

```
[warn] Partial LLM completion stored. Use /stats to see count or query session_diagnostics table.
```

`/stats`も0より大きい場合はカウントを表示する: `Partial compl : N  (stored in session_diagnostics)`。

### ツール継続の失敗 (turn > 0)

条件: ツール継続ターン中にLLMトランスポートエラーが発生。

処理:
- 合成された`tool`ロールのエラーメッセージ (`name="llm_transport_error"`) を履歴に追加
- 失敗を`session_diagnostics`に格納
- 会話は継続する (LLMはこのエラーをツール実行結果として認識する)

### 連続ツールエラー

条件: あるラウンドの全ツールが`tool_error_max_consecutive`回連続で失敗。

処理:
- ツールループを抜ける
- `"Too many consecutive tool errors."`メッセージを返す

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`

## Keywords

LLM invocation and tool loop
TurnLoopState
guard methods
error handling
