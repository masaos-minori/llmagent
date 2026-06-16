# 02 Runtime Architecture — Agent Documentation Restructuring

## Goal
実行時のクラス構造・依存関係・オブジェクト生成順序を詳述する1章を作成する。

## Scope
- AgentREPL / Orchestrator / ToolExecutor の構造と相互関係
- AgentContext およびサービスロケータ群の役割
- 実行時オブジェクトグラフの全体像

## Assumptions
- 05_ref-agent-repl.md §1-2 および 05_ref-agent-context.md §2-6 が構造の正典
- 05_agent-impl-class.md §1.7 のクラスサマリーテーブルを補足として使用
## Implementation

### Target file
`docs/05_agent/02_runtime-architecture.md`

### Procedure
- 05_ref-agent-repl.md §1 (AgentREPL クラス定義・初期化) から構成要素を抽出
- 05_ref-agent-repl.md §2 (Orchestrator 定義・依存注入) から依存関係を抽出
- 05_ref-agent-context.md §2 (AgentContext) から保持フィールドを抽出
- 05_ref-agent-context.md §3-6 (ConversationState, TurnState, RuntimeStats, AppServices) を補足
- 05_agent-impl-class.md §1.7 のテーブルで全クラスの所属レイヤーを確認

### Method
- H2: クラス階層 / AgentContext詳細 / AppServicesとDI / オブジェクト初期化順序
- クラス階層はインデント付き箇条書き(親→子→依存)で表現
- 初期化順序は番号付きステップで記述

### Details
- AgentREPL → Orchestrator → (ToolExecutor, LLMClient, AgentContext) の保持関係
- AgentContext: conversation_state, turn_state, runtime_stats, app_services の4フィールド構成
- AppServices: HistoryManager, AgentSession, CLIView, CommandRegistry への参照を集約
- 初期化順: config読み込み → AppServices → AgentContext → Orchestrator → AgentREPL起動

## Validation plan
- 05_ref-agent-repl.md に記載の全パブリックフィールドが漏れなく言及されていること
- AgentContext の4フィールドが正確に記述されていること
- 初期化順序が05_agent-impl-flow.md の起動シーケンスと一致していること
