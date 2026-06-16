# 05 LLM and Streaming — Agent Documentation Restructuring

## Goal
LLMClient の API・ストリーミング処理・エラー回復の仕組みを1章にまとめる。

## Scope
- LLMClient のインタフェースと主要メソッド
- SSEストリーミングのパース処理(RobustSSEParser)
- 通信エラー(LLMTransportError)と回復ポリシー

## Assumptions
- 05_ref-agent-llm.md 全体が本章の唯一のソース
- ストリーミングプロトコルはAnthropic Messages API SSE形式

## Implementation

### Target file
`docs/05_agent/05_llm-and-streaming.md`

### Procedure
- 05_ref-agent-llm.md の LLMClient クラス定義・メソッドシグネチャを全件抽出
- 05_ref-agent-llm.md の RobustSSEParser クラス定義とパースロジックを抽出
- 05_ref-agent-llm.md の LLMTransportError 定義・エラーコード・回復ポリシーを抽出

### Method
- H2: LLMClient概要 / ストリーミングフロー / RobustSSEParser / エラー処理
- メソッドは「シグネチャ — 説明(1行)」形式の箇条書き
- ストリーミングフローはSSEイベント種別ごとの処理を箇条書きで記述

### Details
- LLMClient: create_message(), stream_message() の2系統を区別
- ストリーミングイベント: message_start, content_block_start, content_block_delta, message_stop
- RobustSSEParser: 不完全チャンク・再接続時の重複除去・JSON解析エラーの吸収
- LLMTransportError: status_code, retry_after, is_retryable の属性
- 回復ポリシー: リトライ上限(max_retries)、指数バックオフ、コンテキスト長超過時の履歴圧縮トリガー

## Validation plan
- LLMClientの全パブリックメソッドが05_ref-agent-llm.mdと一致していること
- SSEイベント種別の列挙に漏れがないこと
- LLMTransportErrorの属性が05_ref-agent-llm.mdの定義と一致していること
