---
title: "ADR-014: Agent制御プレーンの責任境界"
area: governance
tags:
  - system
  - workflow-engine
  - architecture
decision_scope:
  - system
related:
  - ADR-001-workflow-engine-mandatory.md
---

# ADR-014: Agent制御プレーンの責任境界

## Status

Accepted

## Summary

Workflow Engineは必須かつ唯一のWorkflow制御経路である（ADR-001）が、実際のAgent処理は`Orchestrator`、`LLMTurnRunner`、`ToolExecutor`、MCP Serverという複数のコンポーネントが層をなして構成しており、これらも実質的に処理順序や検証を担っている。本ADRは、これら5コンポーネントの責任境界を固定し、各コンポーネントが自身の層を超えて他層の責任（永続的業務状態の決定、tool call実行順序の管理、外部操作の技術的安全性判断など）を重複して保持しないことを定める。

## Context

### Problem

ADR-001はWorkflow Engineが必須かつ唯一のWorkflow制御経路であることを定めたが、Workflow Engine以外のコンポーネント（`Orchestrator`、`LLMTurnRunner`、`ToolExecutor`、MCP Server）が実際にどの責任を負うかは文書化されていなかった。責任境界が未文書化のまま実装が積み重なると、同じ責務（例: LLM/Tool呼び出しループの生成・保持）が複数コンポーネントに重複して現れたり、ある層が本来別の層が持つべき判断（例: Orchestratorが個別Tool呼び出しの安全性を判断する）を代行したりするリスクがある。実際、本ADR起草時の実装検証で、`Orchestrator`が使用されない`LLMTurnRunner`インスタンスを自身のコンストラクタで生成し、実際のLLM/Tool呼び出しループは`LlmTurnExecutor`が内部で独自に生成する別インスタンスによって処理されているという重複が見つかった（Known Deviations参照）。

### Constraints

- 単一Host、単一Agentプロセスでの実行を前提とする（ADR-001と同じ前提）
- Workflow Engineが必須かつ唯一のWorkflow制御経路であるというADR-001の決定を変更しない
- 既存コンポーネント間のPublic API（`Orchestrator.handle_turn()`等）の呼び出し形態を破壊しない

## Assumptions

- 対象環境: 単一Host、単一Agentプロセス
- 信頼境界: Agentプロセス内でのみ権限を付与する（ADR-001と同じ）
- 前提が崩れた場合に再評価が必要な事項: 複数Host構成、分散実行、コンポーネント構成の大幅な再設計（例: `LLMTurnRunner`と`ToolExecutor`の統合）

## Decision

### Decision Details

1. 責任境界を次のように固定する。

   - **Workflow Engine**（`scripts/agent/workflow/workflow_engine.py`）: 永続的な業務状態（Task、Attempt）、stage遷移（`plan -> execute -> approval -> verify -> complete/failed`）、再試行、承認を担う。ADR-001が定める必須性・唯一性はそのまま維持する。
   - **Orchestrator**（`scripts/agent/orchestrator.py`）: 1ターン内の処理調停を担う。Workflow Engineへのタスク初期化・起動委譲、会話状態管理、監査イベント発行など、ターン単位で完結する調整のみを行い、永続的な業務状態の決定はWorkflow Engineに委譲する。
   - **LLMTurnRunner**（`scripts/agent/llm_turn_runner.py`）: LLMとTool Callの短期ループ（1ターン内のストリーミングおよびTool呼び出し往復）を担う。このループの生成・保持は、実際にそのループを駆動するコンポーネント（現状は`LlmTurnExecutor`）に一元化し、他のコンポーネントが未使用のインスタンスを重複して保持しない。
   - **ToolExecutor**（`scripts/shared/tool_executor.py`）: 1回のTool Call実行（gate確認、lifecycle確認、transport解決、実行記録）を担う。複数呼び出しにまたがる状態やターン単位の調停はOrchestrator/LLMTurnRunnerに委ねる。
   - **MCP Server**（`scripts/mcp_servers/`配下、例: `shell/shell_service.py`、`tool_validators.py`）: 外部操作の技術的安全性（allowlist検証、path検証、サンドボックス実行、リソース制限、引数バリデーション）を担う。これらの安全性判断をOrchestrator/ToolExecutor層で代行しない。

2. 各コンポーネントは、自身より上位または下位の層が担うべき責任（永続的業務状態の決定、Tool呼び出しループの二重生成、外部操作の技術的安全性判断など）を代行または重複して保持しない。

3. 本ADRはADR-001が定めるWorkflow Engineの必須性・唯一性を変更しない。ADR-001のScope（`Orchestrator`, `WorkflowEngine`, `WorkflowLoader`, `StateStore`）を、本ADRが`LLMTurnRunner`, `ToolExecutor`, MCP Serverまで拡張して補完する位置づけとする。

### Scope

- **対象コンポーネント**: `Orchestrator`, `WorkflowEngine`, `LLMTurnRunner`, `ToolExecutor`, MCP Server（`scripts/mcp_servers/`配下の各サーバー実装）
- **対象プロセス**: Agentプロセス全体
- **対象データ**: なし（本ADRはコンポーネント間の責任配分を定めるものであり、データモデル自体は変更しない）
- **対象Environment Profile**: production（ADR-001と同じ、唯一サポートされる実行モード）
- **対象APIまたは処理経路**: `Orchestrator.handle_turn()`, `WorkflowEngineAdapter.execute_turn()`, `LlmTurnExecutor.handle_llm_turn()`, `LLMTurnRunner.run()`, `ToolExecutor.execute()`（または`_raw_execute()`）, MCP Server側の`validate_tool_args()`

### Out of Scope

- Workflow Engineの必須性・唯一性の再定義（ADR-001が扱う）
- 承認ポリシーのリデザイン
- `LLMTurnRunner`と`ToolExecutor`の統合など、コンポーネント構成自体の再設計
- 個別MCP Serverごとの安全性ポリシー詳細（allowlist内容、サンドボックス種別など）

## Rationale

### 1. 最重要の採用理由 — Maintainability

責任境界が文書化されていない場合、新規実装や既存コードの変更時に、どのコンポーネントが何を判断すべきかが実装者の裁量に委ねられ、重複や漏れが生じやすい。本ADR起草時に発見された`Orchestrator`の未使用`LLMTurnRunner`インスタンス（Known Deviations参照）は、この境界不在が既に実害を生んでいたことを示す。

### 2. 第2の採用理由 — Correctness

各層が自身の責任範囲を超えて判断を代行すると、判断が層をまたいで分散し、どの層の判断が最終的に有効かが曖昧になる（例: 個別Tool呼び出しの安全性をOrchestratorとMCP Serverの両方が別々に判断すると、一方の変更が他方に反映されない不整合リスクがある）。

### 3. 第3の採用理由 — Auditability

ADR-001が定めるWorkflow Engineの必須性・唯一性は、Workflow Engineが管理する層についての規律である。本ADRはそれ以外の層（ターン内調停、LLM/Tool往復、単発Tool実行、外部操作安全性）についても同様に責任を明確化することで、Agent制御プレーン全体の監査可能性を高める。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: 責任境界を文書化せず、実装の暗黙の慣行に委ねる（現状維持）

#### Description

各コンポーネントの責任範囲を明文化せず、既存コードの構造をそのまま暗黙の契約として扱う。

#### Advantages

- 追加のドキュメント作業が不要
- 既存実装への影響がない

#### Disadvantages

- 本ADR起草時に発見された`Orchestrator`の未使用`LLMTurnRunner`重複のような問題を事前に防げない
- 新規実装者が誤って層をまたいだ責任を実装するリスクが残る

#### Reason for Rejection

Maintainabilityを優先し、境界の明文化により再発を防ぐため不採用とした。

#### Reconsideration Conditions

- コンポーネント構成が大幅に単純化され、境界文書化のコストに見合わなくなった場合

### Alternative B: `Orchestrator`と`LLMTurnRunner`を単一コンポーネントへ統合する

#### Description

ターン調停とLLM/Tool往復ループを1つのクラスに統合し、責任境界の問題自体を構造的に解消する。

#### Advantages

- コンポーネント間の重複生成リスクが構造的になくなる
- 呼び出し経路が単純化される

#### Disadvantages

- 既存の抽出済みconcernクラス（`TurnCoordinator`、`WorkflowEngineAdapter`、`LlmTurnExecutor`等）への大規模なリファクタリングが必要
- 単一クラスの責務が肥大化し、かえって可読性が低下するリスクがある

#### Reason for Rejection

本ADRは責任境界の明確化を目的とし、コンポーネント構成自体の再設計は別途のリファクタリング判断とすべきであるため不採用とした（Out of Scope参照）。

#### Reconsideration Conditions

- 責任境界の明文化のみでは重複生成の再発を防げないと運用実績から判明した場合

## Consequences

### Positive Consequences

- 各コンポーネントの責任範囲が明文化され、新規実装時に層をまたいだ判断の重複や代行を避けやすくなる
- 本ADR起草時に発見された`Orchestrator`の未使用`LLMTurnRunner`重複が、修正対象としてissue化される（Known Deviations参照）
- ADR-001が定めるWorkflow Engineの必須性・唯一性を、それ以外の層についても一貫した形で補完する

### Negative Consequences

- 既存実装がすべて本ADRの境界に厳密に従っているわけではなく（Known Deviations参照）、追加の修正作業が発生する
- コンポーネント境界の文書化により、将来のリファクタリング時に境界変更の妥当性を都度検証する必要が生じる

## Invariants

- INV-023: Workflow Engine以外のコンポーネント（`Orchestrator`、`LLMTurnRunner`、`ToolExecutor`）は、永続的なTask/Attempt状態、stage遷移、再試行、承認可否を自ら決定しない。これらはWorkflow Engineの管理下でのみ決定される。
- INV-024: `LLMTurnRunner`のインスタンス生成は、実際にLLM/Tool Call往復ループを駆動するコンポーネント1箇所に一元化される。他のコンポーネントが未使用または重複した`LLMTurnRunner`インスタンスを保持しない。
- INV-025: MCP Serverが担う外部操作の技術的安全性判断（allowlist検証、path検証、サンドボックス実行、リソース制限、引数バリデーション）は、Orchestrator層またはToolExecutor層で代行・重複実装されない。

## Verification

### Automated Tests

- **Test**: `Orchestrator`が`LLMTurnRunner`の未使用インスタンスを保持しないことの回帰テスト（新規作成が必要）
  - **Verifies**: INV-024
  - **Type**: Unit
  - **Blocking**: No（現時点で未実装、Known Deviationsのissue解決後に追加）

### Startup Validation

該当なし（本ADRはコンポーネント間の責任配分に関する静的な設計規律であり、起動時検証の対象ではない）。

### Deployment Validation

該当なし。

### Runtime Monitoring

- Health Check: 該当なし
- Metrics: 既存のワークフローイベント・Tool実行監査ログ（ADR-001、既存実装のaudit機構）で代替
- Logs: 既存の`agent.tool_audit`等の監査ログ機構を継続利用
- Alert条件: 該当なし

### Manual Review

- 新規コンポーネント追加時、またはOrchestrator/LLMTurnRunner/ToolExecutor/MCP Serverいずれかの責任範囲を変更する変更のコードレビュー時に、本ADRの責任境界との整合性を確認する

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。INV-023、INV-025は現時点で自動テストがなく、コードレビュー（Manual Review）にのみ依存している。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

See Related Documents > Implementation References for the current file/symbol list.

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

- `Orchestrator.__init__`（`scripts/agent/orchestrator.py`）が使用されない`LLMTurnRunner`インスタンスを`self._llm_runner`として生成しており、実際のLLM/Tool Call往復ループは`LlmTurnExecutor`（`scripts/agent/llm_turn_executor.py`）が内部で独自に生成する別インスタンスによって処理されている。これはINV-024（`LLMTurnRunner`生成の一元化）に対する現状の逸脱であり、修正issue（`issues/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md`）で追跡する。
- 「Workflow Engineが再試行を担う」という本ADRの定義自体はINV-023に反しないが、`ToolLoopGuard.check_retry()`（`scripts/agent/tool_loop_guard.py`）とLLM transport層（`llm_max_retries`等、`config/agent.toml`）にも別個の"retry"概念が存在し、WorkflowEngineの`retry_policy`との関係が未文書化。粒度が異なるため直ちにINV-023違反とは判定しないが、整理不足はドキュメント化issue（`issues/20260914-123659_arch03_retry_ownership_documentation_and_layering.md`）で追跡する。→ **RESOLVED**: 三層のリトライ範囲の説明は `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` に追加済み（REQ-002）。

ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。

## Review Triggers

次の条件が発生した場合、このADRを再評価する。

- Orchestrator/LLMTurnRunner/ToolExecutor/MCP Serverいずれかのコンポーネント構成が統合または分割により大きく変更された場合
- Workflow Engineの必須性・唯一性（ADR-001）自体が再評価された場合
- 複数Hostまたは分散実行構成へ変更する場合
- 本ADRの責任境界と矛盾する実装が新たに発見され、Known Deviationsとして追跡しきれない規模になった場合

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner

### Approval Record

- **Approved By**: タスクレベル承認判断(リポジトリ管理者。個別レビュアー名は記録しない)
- **Approval Date**: 記録なし(タスクレベル承認判断のため個別の承認日は記録しない)
- **Approval Reference**: `docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

本ADRの`Accepted`ステータスは、上記ガバナンス文書が定めるタスクレベル承認判断を受理証跡とする。個別レビュアー名・承認日による正式なApproval Recordは作成していない。

## Related Documents

### Specifications

- [ADR-001: Workflow Engine必須化](ADR-001-workflow-engine-mandatory.md) — Workflow Engineの必須性・唯一性を定める前提ADR
- [Turn Processing Flow](../05_agent_03_03_turn-processing-flow-workflow-engine.md) — ワークフロー実行の詳細

### Operations

- なし

### Known Issues

- `issues/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md` — INV-024違反の修正issue

### Implementation References

- `scripts/agent/orchestrator.py` — `Orchestrator.handle_turn()`
- `scripts/agent/workflow/workflow_engine.py` — `WorkflowEngine.run()`
- `scripts/agent/workflow_engine_adapter.py` — `WorkflowEngineAdapter.execute_turn()`
- `scripts/agent/llm_turn_executor.py` — `LlmTurnExecutor.handle_llm_turn()`
- `scripts/agent/llm_turn_runner.py` — `LLMTurnRunner.run()`
- `scripts/shared/tool_executor.py` — `ToolExecutor._raw_execute()`
- `scripts/mcp_servers/tool_validators.py` — `validate_tool_args()`
- `scripts/mcp_servers/shell/shell_service.py`
- テスト — `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `tests/agent/test_orchestrator_bg_failure_threshold.py`, `tests/agent/test_llm_turn_runner.py`

## Completion Checklist

ADRをAcceptedへ変更する前に確認する。

- [x] 解決する問題が明確である
- [x] Decisionが1つの主要な設計判断に絞られている
- [x] Decisionが必須、禁止、正本、Fallback条件などの明確な表現で記載されている
- [x] 採用理由が現在の実装以外の観点で説明されている
- [x] 実質的な代替案と不採用理由が記載されている
- [x] Positive Consequencesが記載されている
- [x] Negative Consequencesが記載されている
- [x] 検証可能なInvariantsが定義されている
- [x] 各InvariantにVerificationが対応している
- [x] 自動化可能な検証がManual Reviewだけになっていない（一部INVは現時点でManual Reviewのみ。今後の自動テスト追加はINV-024の修正issue解決後に検討）
- [x] 関係するSpecificationと矛盾していない
- [x] 現行実装との差異がKnown Issueへ登録されている
- [x] Ownerと必要なReviewerが定義されている（`docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standardが定めるタスクレベル承認判断を受理証跡とする。個別のApproval Record［承認者・承認日・承認参照］は作成していない）
- [x] Review Triggersが記載されている
- [ ] ADR索引と関係領域のDocument Guideへ登録されている（別途確認が必要）
