# 06 Tool Execution and Approval — Agent Documentation Restructuring

## Goal
ツール呼び出しの実行フロー・承認ゲート・結果処理を1章にまとめる。

## Scope
- ToolExecutor の構造と実行ロジック
- 承認ポリシー(auto-approve / prompt / deny)
- ツール結果のLLMへの返却フロー

## Assumptions
- 05_agent-impl-flow.md §3.4 がツール実行の詳細フローの正典
- 05_ref-agent-repl.md §4 が ToolExecutor API の正典
- 05_agent.md §3 のツール一覧を参照してツール種別を確認
## Implementation

### Target file
`docs/05_agent/06_tool-execution-and-approval.md`

### Procedure
- 05_agent-impl-flow.md §3.4 からツール実行の全ステップを抽出
- 05_ref-agent-repl.md §4 の ToolExecutor クラス定義・メソッドを抽出
- 05_agent.md §3 のツール一覧(名称・用途)を引用
- 承認ゲートのロジックは 05_agent-impl-flow.md §3.4 の承認セクションから抽出
### Method
- H2: ToolExecutor概要 / ツール一覧 / 実行ステップ / 承認ポリシー / 結果処理
- ツール一覧は「ツール名 — 用途(1行)」の箇条書き
- 承認ポリシーは条件ごとの動作を表形式で記述

### Details
- ToolExecutor: execute(), get_tool_definition(), list_tools() の主要メソッド
- 実行ステップ: ツール名解決 → 引数バリデーション → 承認判定 → 実行 → 結果フォーマット → LLMへ返却
- 承認ポリシー: always_allow リスト / interactive prompt / 設定による自動拒否
- ツール結果: tool_result コンテンツブロックとして次のLLMリクエストに追加
- タイムアウト処理: tool_timeout_sec 超過時の中断と error 結果返却

## Validation plan
- 05_ref-agent-repl.md §4 の全メソッドが記述されていること
- 承認ポリシーの3条件が網羅されていること
- ツール結果のフォーマット仕様が05_agent-impl-flow.mdと一致していること
