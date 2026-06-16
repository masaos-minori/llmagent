# 03 Turn Processing Flow — Agent Documentation Restructuring

## Goal
ユーザー入力1件が応答として返るまでの処理フロー全体をステップごとに記述する。

## Scope
- ターン開始〜終了の処理ステップ
- LLM呼び出しループとツール呼び出し分岐
- エラーハンドリングポイント

## Assumptions
- 05_agent-impl-flow.md §1 がターンフローの正典
- 05_ref-agent-repl.md §3 (run_turn) と §6 (エラー処理) で補足

## Implementation

### Target file
`docs/05_agent/03_turn-processing-flow.md`

### Procedure
- 05_agent-impl-flow.md §1 からターン処理の全ステップを順番に抽出
- 05_ref-agent-repl.md §3 の run_turn メソッドシグネチャと処理概要を引用
- 05_ref-agent-repl.md §6 のエラー分類と回復ポリシーを参照
- ツール呼び出し分岐は 05_agent-impl-flow.md §3 の概要部分を参照(詳細は06章)

### Method
- H2: ターンライフサイクル / LLMループ / ツール分岐 / エラー処理ポイント
- ターンライフサイクルは番号付きステップ(1〜N)で記述
- LLMループは「LLM応答 → tool_use含む? → Yes: ツール実行→再LLM / No: 応答出力」のテキストフロー

### Details
- ステップ例: 1.入力受付 2.TurnState初期化 3.履歴構築 4.LLM呼び出し 5.応答パース 6.ツール判定 7.ツール実行(任意) 8.応答出力 9.状態保存
- LLMループ: max_iterations 超過時の強制終了ロジックを明記
- ツール分岐: content_type == "tool_use" の条件で06章へ委譲
- エラーポイント: LLM通信エラー, ツールタイムアウト, コンテキスト長超過

## Validation plan
- 05_agent-impl-flow.md §1 に記載の全ステップが網羅されていること
- ループ終了条件(stop_reason, max_iterations)が明記されていること
- エラーハンドリング箇所が05_ref-agent-repl.md §6 と一致していること
