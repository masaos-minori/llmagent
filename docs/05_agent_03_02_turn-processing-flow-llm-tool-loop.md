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
  - 05_agent_04_01_state-and-persistence-state-model.md
source:
  - 05_agent_03_02_turn-processing-flow-llm-tool-loop.md
---

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

LLM呼び出しとツールループの処理フローを文書化する。ストリーミング応答の収集、
複数回のツール呼び出し、およびそのガード機構について記述する。

## Design Intent

### ToolLoopGuard の役割と設計意図

ツールループ内では、LLMが同一ツールを無限に呼び出す可能性がある。これを防ぐため、
ToolLoopGuard が以下の4つのガードを順次実行する：

1. **循環検出** — 直近Nラウンド内で同一のツール呼び出しセットが繰り返された場合
2. **重複排除** — 同一の`(name, args)`が一定回数以上検出された場合
3. **リトライ抑制** — 失敗したツール呼び出しが再度同じ引数で呼ばれた場合
4. **連続エラー** — あるラウンドの全ツールが一定回数連続でエラーとなった場合

いずれかが発動すると、それ以降のチェックは行われずループを終了する。
ガード発動後は、ツールを一切呼び出さずに最終回答を生成するフォールバックを試みる。

### 不完全な出力の分離

LLMストリーミング中にトランスポートエラーが発生し、部分完了が生じた場合、
その出力は通常の会話履歴から分離される。これにより、以降のLLMコンテキストが
汚染されない。部分的なコンテンツは `session_diagnostics` テーブルに格納され、
`/stats` コマンドで確認できる。

## Responsibility Boundary

### LLM呼び出しとツールループ

`LLMTurnRunner.run(llm_url)`が内部ループを管理する：

- ペイロードを構築: `history + tool_definitions + temperature + max_tokens + stream=True`
- SSEストリーミングでLLMに送信
- `content_parts`（テキスト）と `tool_calls_map`（関数呼び出し）を収集
- `finish_reason == "tool_calls"`の場合：ツールを実行 → 結果を追加 → LLMに再送信
  - `max_tool_turns`回まで繰り返す
- `finish_reason == "stop"`または`max_tool_turns`超過の場合：最終回答を返す

### 履歴への追加

`ctx.conv.append_message()`は検証付きのメソッドであり、生の`list.append()`ではなく
これを介してのみ履歴を変更する（詳細は
[05_agent_04_01_state-and-persistence-state-model.md](05_agent_04_01_state-and-persistence-state-model.md)
§検証付き履歴変更メソッド を参照）。

### ToolLoopGuard発動時の最終回答フォールバック

ガードが発動した場合、一時的なシステムメッセージを注入してLLMに再呼び出しする：

- システムメッセージ: "You are about to produce a final answer without calling any tools. Use only the information already available in the conversation history."
- `tool_defs=[]`でLLM呼び出しを実行
- `finish_reason != "tool_calls"`の場合：回答テキストを返す
- `finish_reason == "tool_calls"`の場合：失敗を返す

元の未実行アシスタントメッセージは永続化しない。

### ガード発動時のヒント

各ガード発動時に `session_diagnostics` に `kind='guard_hint'` でヒントが保存される：

| ガード種別 | ヒント内容 |
|---|---|
| cycle | "A cyclic planning pattern was detected: the same set of tool calls is being requested repeatedly across multiple rounds." |
| dedup | "The same tool was called with identical arguments multiple times." |
| retry | "A tool call that previously failed is being retried with the same arguments." |

これらのヒントはオフライン診断専用として保存され、`ctx.conv.history`には注入されない。
ループ終了時にユーザーに表示される短い文言とは別の情報である。

## Key Constraints

### メッセージ型ホワイトリスト

LLMクライアントのストリーミング集約ロジックが型付きデルタから構築するメッセージは、
`role`/`content`/`tool_calls`のみで構成されるため、検証は常に成功する。
保存内容は以前の生の`.append()`呼び出しと比較して変化しない。

### 不完全な出力の扱い

- トランスポートエラー発生時、`partial_text`が空でない場合は`session_diagnostics`に
  `[INCOMPLETE: {kind}]`プレフィックス付きで永続化する
- `ctx.conv.history`には追加しない
- 各ターン後にREPLが`stat_partial_completions`を比較し、増加していれば警告を出力する

### 連続ツールエラー

- あるラウンドの全ツールが`tool_error_max_consecutive`回連続で失敗した場合、ツールループを抜ける
- 部分的な失敗（一部のみエラー）の場合はカウンタを維持し、全成功ラウンドでリセットされる

## Operational Notes

- ガード発動後の最終回答フォールバックは、一時的なシステムメッセージを注入して
  ツールなしで回答を生成させるアプローチを取る
- 不完全な出力は`/stats`コマンドで確認可能だが、通常の会話履歴からはアクセスできない

## Known Limitations

- 循環検出はフィンガープリントベースのため、順序は異なるが機能的に等価なツール呼び出しは
  別パターンとして検知されない
- リトライ抑制は`tool_error_retry_max > 0`の場合のみ有効

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`
- `05_agent_04_01_state-and-persistence-state-model.md`

## Keywords

LLM invocation and tool loop
TurnLoopState
guard methods
error handling
validated history append
append_message
