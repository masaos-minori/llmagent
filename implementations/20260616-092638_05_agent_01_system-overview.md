# 01 System Overview — Agent Documentation Restructuring

## Goal
Agentシステムの全体像・設計思想・主要コンポーネントの概要を1章にまとめる。

## Scope
- システムの目的と動作概要
- 主要コンポーネントの列挙と役割説明
- 他章への橋渡し

## Assumptions
- 05_agent.md §1-3 および 05_agent-impl-class.md §1.1-1.2 が最新の正
- 図は既存のアーキテクチャ概念図を流用可能

## Implementation

### Target file
`docs/05_agent/01_system-overview.md`

### Procedure
- 05_agent.md §1 (Introduction) からシステム目的・設計原則を抽出
- 05_agent.md §2 (Architecture overview) からコンポーネント一覧と依存関係を抽出
- 05_agent.md §3 (Key concepts) から用語定義を抽出
- 05_agent-impl-class.md §1.1 (AgentREPL概要) と §1.2 (主要クラス図) を補足として使用

### Method
- H2セクション構成: 目的 / 主要コンポーネント / データフロー概要 / 関連章リンク
- コンポーネント説明は「名前 — 役割(1行)」の箇条書き形式
- データフロー概要はテキストによるシーケンス(user input → REPL → LLM → tool → response)

### Details
- システム目的: 対話型LLMエージェントとして、ユーザー入力をLLMに渡し、ツール呼び出しを経て応答を返す
- 主要コンポーネント: AgentREPL, Orchestrator, ToolExecutor, LLMClient, CLIView, AgentContext, HistoryManager, AgentSession
- 設計原則: 単一責任、プラグイン拡張、非同期I/O
- 関連章: 02(ランタイムアーキテクチャ), 03(ターン処理フロー), 08(設定)

## Validation plan
- 主要8コンポーネントがすべて言及されていること
- 05_agent.md §1-3 に記載の設計原則と矛盾しないこと
- 関連章リンクが正しい章番号を指していること
