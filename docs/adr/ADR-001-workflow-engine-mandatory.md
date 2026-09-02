---
title: "ADR-001: Workflow Engine必須化"
area: adr
decision_scope:
  - system
related: []
---

# ADR-001: Workflow Engine必須化

## Status

Accepted

## Summary

Agentの実行状態、承認、再試行、検証、永続化、再起動後の復元を共通の状態モデルで管理するため、Workflow EngineをAgent実行の必須基盤とする。Agentによる外部状態変更、Tool実行、複数ステップ処理、承認を必要とする操作はすべてWorkflow Engineの管理下で実行する。Workflow無効化モードおよびWorkflowを迂回する直接実行経路は設けない。

## Context

### Problem

このシステムはLLMが計画したタスクを実行する。一部のツールには副作用があり、一部の操作には承認が必要であり、ツール実行は観測可能かつ回復可能でなければならない。LLMからツールへの直接パスは監査と回復を困難にする。

### Constraints

- 単一ホスト、単一プロセスでの実行を前提とする
- デプロイ環境では起動前にワークフロー定義ファイルが存在することを確認する必要がある
- 外部Protocol、Library、Serviceによる制約はない
- セキュリティ要件：すべての副作用のある操作は追跡可能でなければならない
- データ整合性：承認状態はプロセス境界を超えて永続化する必要がある

## Assumptions

- 対象環境：単一Host、単一Agentプロセス
- 想定規模：同時実行数は限定的
- 信頼境界：Agentプロセス内でのみ権限を付与する
- 外部依存先：なし（ワークフロー定義はローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部ワークフローエンジン統合

## Decision

### Decision Details

1. WorkflowEngineは必須である。ワークフロー定義ファイルはデプロイ必須成果物である。欠落または検証失敗時はAgent起動を中止する。
2. Agentによる外部状態変更、Tool実行、複数ステップ処理、承認を必要とする操作はすべてWorkflow Engineの管理下で実行する。
3. Workflow無効化モードを設けない。
4. Workflowを迂回する直接実行経路を設けない。
5. すべてのAgent処理は、単純な質問応答を含め、Workflow Engineの管理下に置かれる。処理が単純であることは、Workflow Engineを迂回する理由にはならない。
6. 基本状態を`plan -> execute -> approval -> verify -> complete/failed`として定義する。承認不要時はapprovalを省略できるが、Workflow管理自体は省略しない。
7. 実行成功と検証成功を区別する。
8. Health Checkや起動前検証など、Workflow Engine自身の前提確認は適用対象外とする。
9. Workflow状態（Task、Attempt、承認、処理済みEvent、Artifact）は`workflow.sqlite`に永続化される。Taskを削除する場合は、関連するAttempt、処理済みEvent、Artifact、承認をCascade削除する。

### Scope

- **対象コンポーネント**: `Orchestrator`, `WorkflowEngine`, `WorkflowLoader`, `StateStore`
- **対象プロセス**: Agentプロセス全体
- **対象データ**: タスク状態、承認状態、イベント処理記録、アティファクト
- **対象Environment Profile**: production（唯一サポートされる実行モード）
- **対象APIまたは処理経路**: `handle_turn()`, `WorkflowEngine.run()`, `request_approval()`

### Out of Scope

- 個別のワークフローステージ定義の詳細
- 承認ポリシーのリデザイン
- EventBus統合の導入
- ランタイム動作の変更
- ワークフロー定義ファイルのスキーマ設計
- 監視・メトリクス設計
- Production全体の障害方針（ADR-004が扱う）

## Rationale

### 1. 最重要の採用理由 — Correctness

すべての副作用のある操作を追跡可能にし、承認状態をプロセス境界を超えて永続化する必要がある。直接実行経路は監査と回復を困難にする。

### 2. 第2の採用理由 — Recoverability

部分タスク完了の検査と復旧には、永続化されたタスクおよび試行状態が必要である。ワークフロー管理がない場合、中断後の再開が不可能になる。

### 3. 第3の採用理由 — Operability

ツール実行はLLM会話状態にのみ依存すべきではない。ワークフロー管理により、実行パターンを一貫して予測可能にし、障害対応を簡素化する。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Direct tool execution without workflow

#### Description

LLMからツールへの直接パスを許可し、ワークフロー管理を省略する。

#### Advantages

- シンプルな構造
- 低リスク操作のオーバーヘッド削減

#### Disadvantages

- 監査と回復が困難になる
- 承認/再試行ロジックに対する永続状態がない
- 部分タスク完了の検査が不可能

#### Reason for Rejection

CorrectnessとRecoverabilityを優先し、監査可能性と回復性を確保するため。

#### Reconsideration Conditions

- 監査要件が大幅に緩和される場合
- 回復性が不要となる場合

### Alternative B: Optional workflow mode

#### Description

ワークフローモードをオプションとし、環境ごとに有効/無効を切り替え可能にする。

#### Advantages

- 開発の簡素化
- 柔軟なデプロイメントオプション

#### Disadvantages

- ワークフロー有効/無効間で振る舞いの不一致
- オペレーターが実行パターンを予測できない
- 監査トレイルと承認追跡が無効化時も必要

#### Reason for Rejection

OperabilityとData Integrityを優先し、環境固有のルールが混乱を引き起こすため不採用とした。

#### Reconsideration Conditions

- 運用規模が拡大し、ワークフロー管理のオーバーヘッドが許容範囲を超える場合

### Alternative C: Fallback execution when workflow definition is missing

#### Description

ワークフロー定義が欠落している場合、直接実行へフォールバックする。

#### Advantages

- 設定エラーの静かな軽減
- 移行期間の柔軟性

#### Disadvantages

- 設定エラーを隠蔽する
- 起動失敗により即時フィードバックを提供しない

#### Reason for Rejection

Fail-Fast原則を優先し、構成エラーを即時検出するため不採用とした。

#### Reconsideration Conditions

- 大規模な移行期間が必要で、段階的展開が必須となる場合

### Alternative D: Ad-hoc per-tool approval without workflow state

#### Description

ワークフロー状態を使用せず、ツールレベルのアドホック承認のみで管理する。

#### Advantages

- 単純な承認フロー
- 低複雑性

#### Disadvantages

- 承認状態がプロセス再起動後も持続しない
- どの承認がどの試行に適用されるかを追跡できない
- バッチ結果検証ができない

#### Reason for Rejection

RecoverabilityとData Integrityを優先し、プロセス境界を超えた状態永続化が必要であるため不採用とした。

#### Reconsideration Conditions

- 承認要件が大幅に簡素化され、バッチ検証が不要となる場合

## Consequences

### Positive Consequences

- すべての副作用のある操作を追跡可能
- 承認状態がプロセス境界を超えて永続化
- 再試行と冪等性挙動が中央で管理
- 部分タスク完了が検査可能
- 復旧に必要な永続タスクおよび試行状態がある
- ワークフロー失敗がプラットフォーム失敗として扱われる
- ワークフローイベント、承認イベント、エラーイベントがログに記録される

### Negative Consequences

- デプロイメントにワークフロー定義ファイルが必要
- 起動時にワークフローアーティファクトが不足すると失敗
- ワークフロースキーマがサービス起動前に初期化される必要がある
- シンプルなチャットとツールベースのタスクが同じ実行制御プレーンを共有
- 起動時にワークフロー定義ファイルとDB Schemaの整合性確認が必要になり、障害対応時にはワークフロー状態の調査が必要になる

## Invariants

- INV-01: ワークフロー定義ファイルが欠落している場合、Agentの起動を中止する。
- INV-02: Workflow Engineを迂回する外部状態変更経路は存在しない。
- INV-03: 実行成功と検証成功は区別され、それぞれ独立して検証される。
- INV-04: 承認待ち状態は再起動後に復元される。
- INV-05: ワークフロー定義ファイルの検証失敗時は起動を中止する。
- INV-06: 必須DB Schema不整合時は起動を中止する。
- INV-07: プロセス起動時、中断されたAttemptは`recover_stale_attempts()`により`failed`として復旧される。

## Verification

### Automated Tests

- **Test**: ワークフロー定義欠落時の起動失敗テスト
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: ワークフロー定義不正時の起動失敗テスト
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 必須DB Schema不整合時の起動失敗テスト
  - **Verifies**: INV-06
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 承認待ち状態の再起動後復元テスト（`test_startup_recovered_approval_can_resume`）
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Workflow Engine迂回の外部状態変更経路不存在テスト
  - **Verifies**: INV-02
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: `test_execute_success_verify_failure_marks_task_failed`（execute成功後にverifyが失敗した場合、タスク状態が`completed`ではなく`failed`になることを確認）
  - **Verifies**: INV-03
  - **Type**: Unit
  - **Blocking**: Yes

- **Test**: `recover_stale_attempts()`の楽観的ロック・復旧挙動テスト（`tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`）
  - **Verifies**: INV-07
  - **Type**: Unit
  - **Blocking**: Yes

### Startup Validation

- ワークフロー定義ファイルが存在するか
- ワークフロー定義が有効か（parseable JSON、必須フィールド、ステージ、リトライポリシー）
- 必須DBテーブルが存在するか
- DBスキーマバージョンが一致するか

### Deployment Validation

- デプロイ前後にワークフロー定義ファイルのSHA256チェックサムを確認
- デプロイ後のワークフロー定義がソースと一致するか

### Runtime Monitoring

- Health Check：ワークフローエンジン自体のヘルスチェックは適用対象外
- Metrics：ワークフローステータス、承認状態、試行状態
- Logs：ワークフローイベント、承認イベント、エラーイベント
- Alert条件：ワークフロー失敗、承認タイムアウト、Schema不整合

### Manual Review

- ワークフロー定義の変更レビュー
- 承認ポリシーの変更レビュー
- デプロイメント前のワークフロー定義検証

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/agent/orchestrator.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/workflow_loader.py`, `scripts/agent/workflow/state_store.py`
- 主要ClassまたはFunction: `Orchestrator.handle_turn()`, `WorkflowEngine.run()`, `WorkflowLoader.load()`, `StateStore.request_approval()`, `StateStore.recover_stale_attempts()`
- 設定ファイル、設定Key: `config/workflows/default.json`
- 対応するテスト: `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

確認済みの差異なし

ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。

## Review Triggers

次の条件が発生した場合、このADRを再評価する。

- 運用規模または同時実行数が大きく変化した場合
- 単一Hostから複数Hostまたは分散構成へ変更する場合
- Security要件、監査要件が変更された場合
- 性能目標またはResource制約が変更された場合
- 外部Protocolまたは採用Libraryが変更、廃止された場合
- 障害実績により前提が妥当でないと判明した場合
- 代替案の不採用理由が成立しなくなった場合
- ワークフロー定義ファイルの形式が大幅に変更された場合
- 承認モデルが根本的に変更された場合
- 永続化ストレージがSQLite以外へ移行された場合

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: セキュリティ影響がある場合
- Operations Reviewer: 運用、監視、復旧へ影響する場合
- Data Owner: データ所有権、Schema、保持へ影響する場合

### Approval Record

- **Approved By**: タスクレベル承認判断(リポジトリ管理者。個別レビュアー名は記録しない)
- **Approval Date**: 記録なし(タスクレベル承認判断のため個別の承認日は記録しない)
- **Approval Reference**: `docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

本ADRの`Accepted`ステータスは、上記ガバナンス文書が定めるタスクレベル承認判断を受理証跡とする。個別レビュアー名・承認日による正式なApproval Recordは作成していない。

## Related Documents

### Specifications

- [Turn Processing Flow](05_agent_03_03_turn-processing-flow-workflow-engine.md) — ワークフロー実行の詳細
- [Deployment Guide](02_deployment.md) — デプロイメント時のワークフロー検証

### Operations

- [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook) — 障害対応手順

### Known Issues

- なし

### Implementation References

- `scripts/agent/orchestrator.py` — `Orchestrator.handle_turn()`
- `scripts/agent/workflow/workflow_engine.py` — `WorkflowEngine.run()`
- `scripts/agent/workflow/workflow_loader.py` — `WorkflowLoader.load()`
- `scripts/agent/workflow/state_store.py` — `StateStore.request_approval()`, `StateStore.recover_stale_attempts()`
- `config/workflows/default.json` — ワークフロー定義ファイル

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
- [x] 自動化可能な検証がManual Reviewだけになっていない
- [x] 関係するSpecificationと矛盾していない
- [x] 現行実装との差異がKnown Issueへ登録されている
- [ ] Ownerと必要なReviewerが定義されている（Approval Recordはpendingのまま — 承認者・承認日・承認参照が未確定）
- [x] Review Triggersが記載されている
- [ ] ADR索引と関係領域のDocument Guideへ登録されている（別途確認が必要）
