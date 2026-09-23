# P0-005: INV-024 (ADR-014) の明示的な違反 — Orchestrator に未使用の LlmTurnExecutor インスタンス

## Priority
High

## Summary
`adr-index.md:93` で ADR-014 の invariant INV-024 が「Violated」として記録されている。`Orchestrator.__init__` (`scripts/agent/orchestrator.py`) が未使用の `self._llm_runner` を構築しており、ADR-014 が規定する「LlmTurnExecutor インスタンスの構築は LLM/tool-call ループを駆動するコンポーネントに集中させる」原則に違反している。

## Background
ADR-014（Agent制御プレーンの責任境界）は、非 WorkflowEngine コンポーネント（Orchestrator, LlmTurnExecutor, ToolExecutor）の責任境界を規定している。INV-024 は特に、「LlmTurnExecutor インスタンスの構築は LLM/tool-call ループを駆動するコンポーネントに集中させ、他のコンポーネントが未使用または重複インスタンスを持たないこと」を要求している。この違反は既に `issues/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md` で追跡されている。

## Problem
`Orchestrator.__init__` が `self._llm_runner` を構築しているが、これは実際に LLM/tool-call ループを駆動する `LlmTurnExecutor` が構築するインスタンスと重複している。未使用のインスタンスはメモリリークの原因となり、将来の保守者が誤って参照するリスクがある。

## Reason for Change
未使用のインスタンスの構築はメモリ効率の問題だけでなく、アーキテクチャの意図の混乱を招く。Orchestrator が LlmTurnExecutor の構築に関与することは、ADR-014 の責任境界に反し、将来の機能追加時に誤った依存関係を生む可能性がある。

## Implementation Intent
1. `scripts/agent/orchestrator.py` の `Orchestrator.__init__` で `self._llm_runner` が構築される箇所を確認する
2. `self._llm_runner` が未使用であることを検証する
3. `self._llm_runner` の構築を削除し、LlmTurnExecutor のみがインスタンスを構築するようにする
4. 関連するテストを更新し、動作変更がないことを確認する
5. 関連する issue ファイルの状態を更新する

## Target Files or Areas
- `scripts/agent/orchestrator.py`
- `scripts/agent/llm_turn_executor.py` （または同等の LlmTurnExecutor 実装ファイル）
- `issues/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md`
- `adr-index.md`
- `adr/ADR-014-agent-control-plane-responsibility-boundaries.md`

## Required Changes
- `Orchestrator.__init__` から `self._llm_runner` の構築を削除
- 関連するテストの更新
- INV-024 の検証ステータスを Resolved に更新

## Constraints
- Orchestrator の public API を変更してはならない
- LlmTurnExecutor の動作を変更してはならない
- 既存のテストを壊してはならない

## Acceptance Criteria
- [ ] `Orchestrator.__init__` に `self._llm_runner` の構築が残っていない
- [ ] LlmTurnExecutor のみが LlmTurnExecutor インスタンスを構築していることを確認
- [ ] 関連テストが全てパスすることを確認
- [ ] INV-024 の検証ステータスが Resolved に更新されている
- [ ] 関連する issue ファイルが Closed に更新されている

## Testing Expectations
- 既存の Orchestrator テストの全テストパス確認
- LlmTurnExecutor のユニットテストパス確認
- 統合テストのパス確認
- メモリプロファイリング（オプション）— 未使用インスタンスの解放によりメモリ使用量が改善することを確認

## Documentation Impact
- `adr-index.md` の INV-024 セクションの更新が必要
- ADR-014 の Completion Checklist の更新が必要
- 関連する issue ファイルのステータス更新が必要

## Out of Scope
- Orchestrator の public API の変更
- LlmTurnExecutor の内部構造の変更
- 他の invariant の是正
- ADR-014 の責任境界の再設計

## Dependencies
- 関連 issue: `issues/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md`

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- `scripts/agent/orchestrator.py` のみ修正する
- `self._llm_runner` の構築を削除する
- LlmTurnExecutor の動作を変更しない
- 既存のテストを壊さない
- 関連ドキュメント（adr-index.md, ADR-014）の更新を行う

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-100004
- **Related target files**: scripts/agent/orchestrator.py, scripts/agent/llm_turn_executor.py, issues/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md
