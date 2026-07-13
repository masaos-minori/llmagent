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
  - 05_agent_03_03_turn-processing-flow-workflow-engine-part1.md
source:
  - 05_agent_03_01_turn-processing-flow-overview.md
---

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md)

## LLM呼び出しとツールループ

`LLMTurnRunner.run(llm_url)`が内部ループを管理する:

1. ペイロードを構築: `history + tool_definitions + temperature + max_tokens + stream=True`
2. SSEストリーミングでLLMに送信
3. `content_parts` (テキスト) と `tool_calls_map` (関数呼び出し) を収集
4. `finish_reason == "tool_calls"`の場合:
   - ツールを実行 → 結果を追加 → LLMに再送信
   - `max_tool_turns`回まで繰り返す
5. `finish_reason == "stop"`または`max_tool_turns`超過の場合: 最終回答を返す



`ToolLoopGuard`は各ツールループの反復中に以下をガードする。実行順序は
`check_all()`内で **循環検出 → 重複排除 → リトライ** の順 (Explicit in code、`tool_loop_guard.py`の
`check_all`)。いずれかが発動した時点でそれ以降のチェックは行われずループを終了する。

- **循環検出:** 直近の`tool_cycle_detect_window`ラウンド内で同一のツール呼び出しセットのフィンガープリント
  (ラウンド内の全`(name, args)`をソートしMD5化したもの) が繰り返された場合 → ループを終了;
  ユーザーには`"Cyclic tool call pattern detected."`が表示される;
  ヒントは`session_diagnostics`に格納される (`kind='guard_hint'`, `guard_type='cycle'`)。
- **重複排除:** 同一の`(name, args)`が`tool_dedup_max_repeats`回以上検出された場合 → ループを終了;
  ユーザーには`"Repeated tool call detected."`が表示される; ヒントは`session_diagnostics`に格納される
  (`kind='guard_hint'`, `guard_type='dedup'`)。
- **リトライ:** エラーとなった`(name, args)`が再度呼び出された場合 (`tool_error_retry_max > 0`の場合のみ有効)
  → ループを終了; ユーザーには`"Repeated failed tool call detected."`が表示される;
  ヒントは`session_diagnostics`に格納される (`kind='guard_hint'`, `guard_type='retry'`)。
- **連続エラー:** あるラウンドの全ツールが`tool_error_max_consecutive`回連続でエラーとなった場合
   → ループを終了; ユーザーには`"Too many consecutive tool errors."`が表示される。
   部分的な失敗 (一部のみエラー) の場合はカウンタを維持し、全成功ラウンドでリセットされる
   (`ToolLoopGuard.update_errors`)。

### ガードメソッドの構成 (Current behavior)

`check_all()`は内部で`check_cycle()` → `check_dedup()` → `check_retry()`を個別に呼び出す複合メソッドである
(3つの個別メソッドはpublicとして存在する)。`check_error_limit()`は`check_all()`とは別に、
ツール実行後の連続エラー数に対して呼び出される。

### TurnLoopState dataclass

ターンごとのループ状態を保持する (Explicit in code; `tool_loop_guard.py`):

| Field | Type | Description |
|---|---|---|
| `seen_calls` | `dict[str, int]` | 現在のターンで検出されたツール呼び出しフィンガープリントごとの出現回数 |
| `failed_calls` | `set[str]` | 失敗したツール呼び出しフィンガープリント |
| `consecutive_errors` | `int` | 全ツールが失敗した連続ラウンド数 |
| `round_fingerprints` | `list[str]` | 直近N ラウンド分のフィンガープリント (循環検出ウィンドウ) |

> **Doc/code差異:** 旧版では`seen_calls`を`set[str]`と記載していたが、実装は`dict[str, int]`であり
> 呼び出し回数を値として保持する (`tool_dedup_max_repeats`との比較に使用)。

### ガードメソッド

| Method | Responsibility |
|---|---|
| `check_cycle(round_fingerprints, message)` | 循環検出のみを実行 |
| `check_dedup(seen_calls, message)` | 重複排除のみを実行 |
| `check_retry(failed_calls, message)` | リトライ抑制のみを実行 |
| `check_all(seen_calls, round_fingerprints, failed_calls, message)` | 循環・重複排除・リトライの順に各チェックを実行し、いずれかのガードが発動した場合ヒントを返す |
| `check_error_limit(consecutive_errors)` | 連続エラー上限をチェックし、超過時はメッセージを返す |

### ガード定数 (Explicit in code)

`DEDUP_HINT` / `CYCLE_HINT` / `RETRY_HINT`は、ループ終了時にユーザーへ表示される短い文言
(`"Repeated tool call detected."`等、上記ガード説明を参照)とは**別物**であり、
`session_diagnostics`にのみ保存されるLLM向けの長い指示文である:

| Constant | Value | Purpose |
|---|---|---|
| `DEDUP_HINT` | `"[System] The same tool was called with identical arguments multiple times. Stop retrying and provide your best answer with the information already available."` | 重複排除ガード発動時、診断チャンネルに保存されるヒント |
| `CYCLE_HINT` | `"[System] A cyclic planning pattern was detected: the same set of tool calls is being requested repeatedly across multiple rounds. Stop and provide your best answer with the information already available."` | 循環検出ガード発動時のヒント |
| `RETRY_HINT` | `"[System] A tool call that previously failed is being retried with the same arguments. Stop retrying and provide your best answer with the information already available."` | リトライガード発動時のヒント |

> **Note:** ガードヒント (`DEDUP_HINT`, `CYCLE_HINT`, `RETRY_HINT`) はオフライン診断専用として
> `session_diagnostics`に`kind='guard_hint'`で格納される (`hint`フィールドとして)。
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
- `05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`

## Keywords

LLM invocation and tool loop
TurnLoopState
guard methods
error handling
