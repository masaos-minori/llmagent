---
title: "ADR-001: Workflow Engine必須化"
area: adr
decision_scope:
  - system
related: []
supersedes: []
superseded_by: null
---

# ADR-001: Workflow Engine必須化

## Status

Proposed

使用可能なStatusは次のとおりとする。

- `Proposed`: 提案中、レビューまたは承認前
- `Accepted`: 採用済みであり、現行設計として有効
- `Rejected`: 検討したが不採用
- `Deprecated`: 現在は推奨しないが、一部に残存
- `Superseded`: 後継ADRによって置換済み

Accepted後に判断内容を変更する場合は本文を直接変更せず、新しいADRを作成して本ADRをSupersededへ変更する。

## Summary

Agentの実行状態、承認、再試行、検証、永続化、再起動後の復元を共通の状態モデルで管理するため、Workflow EngineをAgent実行の必須基盤とする。Agentによる外部状態変更、Tool実行、複数ステップ処理、承認を必要とする操作はすべてWorkflow Engineの管理下で実行することを決定する。Workflow無効化モードおよびWorkflowを迂回する直接実行経路は設けない。

## Context

### Problem

このシステムはLLMが計画したタスクを実行する。一部のツールには副作用があり、一部の操作には承認が必要であり、ツール実行は観測可能かつ回復可能でなければならない。LLMからツールへの直接パスは監査と回復を困難にする。

### Constraints

- 単一ホスト、単一プロセスでの実行を前提とする
- デプロイ環境では起動前にワークフロー定義ファイルが存在することを確認する必要がある
- 外部Protocol、Library、Serviceによる制約はない
- セキュリティ要件：すべての副作用のある操作は追跡可能でなければならない
- データ整合性：承認状態はプロセス境界を超えて永続化する必要がある

### Assumptions

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
5. 単純な質問応答はWorkflowを無効化せず、軽量な単一ステージWorkflowとして表現可能であることを明記する。
6. 基本状態を`plan -> execute -> approval -> verify -> complete/failed`として定義する。承認不要時はapprovalを省略できるが、Workflow管理自体は省略しない。
7. 実行成功と検証成功を区別する。
8. Health Checkや起動前検証など、Workflow Engine自身の前提確認は適用対象外とする。

### Scope

- **対象コンポーネント**: `Orchestrator`, `WorkflowEngine`, `WorkflowLoader`, `StateStore`
- **対象プロセス**: Agentプロセス全体
- **対象データ**: タスク状態、承認状態、イベント処理記録、アティファクト
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `handle_turn()`, `WorkflowEngine.run()`, `request_approval()`

### Out of Scope

- 個別のワークフローステージ定義の詳細
- 承認ポリシーのリデザイン
- EventBus統合の導入
- ランタイム動作の変更
- ワークフロー定義ファイルのスキーマ設計（別ADRで扱う）
- 監視・メトリクス設計（別ADRで扱う）

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

- ローカル開発の簡素化
- 柔軟なデプロイメントオプション

#### Disadvantages

- ワークフロー有効/無効間で振る舞いの不一致
- オペレーターが実行パターンを予測できない
- 監査トレイルと承認追跡がローカルモードでも必要

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

### Negative Consequences

- デプロイメントにワークフロー定義ファイルが必要
- 起動時にワークフローアーティファクトが不足すると失敗
- ワークフロースキーマがサービス起動前に初期化される必要がある
- シンプルなチャットとツールベースのタスクが同じ実行制御プレーンを共有

### Operational Consequences

- 起動時にワークフロー定義ファイルが存在することを確認する必要がある
- ワークフロー失敗はプラットフォーム失敗として扱われる
- 障害対応時にワークフロー状態の調査が必要

### Security Consequences

- 信頼境界：ワークフロー管理により権限付与の一貫性が確保される
- 認証、認可：ワークフロー状態に基づく承認判定
- Secretの取扱い：ワークフロー状態は暗号化されて永続化される
- Fail-Closed：ワークフロー定義欠落時は起動中止
- Audit Log：すべてのワークフローイベントが監査ログに記録される

## Invariants

- INV-01: ワークフロー定義ファイルが欠落している場合、Agentの起動を中止する。
- INV-02: Workflow Engineを迂回する外部状態変更経路は存在しない。
- INV-03: 実行成功と検証成功は区別され、それぞれ独立して検証される。
- INV-04: 承認待ち状態は再起動後に復元される。
- INV-05: ワークフロー定義ファイルの欠落または検証失敗時は起動を中止する。
- INV-06: 必須DB Schema不整合時は起動を中止する。

## Exceptions

なし

## Failure Policy

### Fail-Fast Conditions

- ワークフロー定義ファイルが欠落している場合
- ワークフロー定義が不正である場合
- 必須DB Schemaが不整合である場合

### Fail-Open or Degraded Conditions

- Health Checkや起動前検証など、Workflow Engine自身の前提確認は適用対象外
- ローカル開発環境では、ワークフロー定義の軽微な検証エラーは警告として記録される

### Retry Policy

- Retry対象：ワークフローステージ実行失敗
- Retry回数：`retry_policy.max_attempts`（デフォルト3回）
- Backoff：固定間隔（デフォルト1秒）
- RetryしないError：承認拒否、システムエラー

### Fallback Policy

- Fallback対象：なし
- Fallback先：なし
- Fallbackを禁止する条件：ワークフロー定義欠落時
- Fallback理由の記録先：監査ログ

該当しない場合は「対象外」と記載する。

## Data Ownership and Persistence

- **System of Record**: `workflow.sqlite`（tasks, attempts, processed_events, artifacts, approvalsテーブル）
- **Derived Data**: 再生成可能な派生データ（ワークフロー定義ファイルのSHA256チェックサム）
- **Ownership**: `StateStore`（ワークフロー状態の所有）、`WorkflowEngine`（ワークフロー実行の所有）
- **Persistence**: SQLite（`workflow.sqlite`）、ワークフロー定義ファイル（JSON）
- **Transaction Boundary**: ワークフローステージ実行単位
- **Recovery Source**: `StateStore.recover_stale_attempts()`（プロセス起動時の stale attempt 復旧）
- **Deletion Rule**: タスク削除時は関連する試行、イベント、アティファクト、承認をCascade削除

該当しない場合は「対象外」と記載する。

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
  **Blocking**: Yes

- **Test**: 承認待ち状態の再起動後復元テスト
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Workflow Engine迂回の外部状態変更経路不存在テスト
  - **Verifies**: INV-02
  - **Type**: Regression
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
- Degraded条件：ワークフロー定義の軽微な検証エラー（ローカル開発環境）

### Manual Review

- ワークフロー定義の変更レビュー
- 承認ポリシーの変更レビュー
- デプロイメント前のワークフロー定義検証

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Migration and Rollout

既存実装はDecisionに適合しており、移行作業は不要。

### Compatibility

- 後方互換性：既存のワークフロー定義ファイルはそのまま使用可能
- 旧設定、旧Data、旧APIの扱い：なし

### Rollback

- Rollback可能な条件：ワークフロー定義の変更が問題を引き起こした場合
- Rollback手順：旧ワークフロー定義ファイルを復元
- Rollbackできない変更：ワークフロー状態の永続化（ロールバック不可）
- Data復旧方法：`StateStore.recover_stale_attempts()`

### Completion Criteria

- 移行完了と判断する条件：既存実装がDecisionに適合していることを確認
- 旧経路を削除する条件：既存実装がDecisionに適合していることを確認

移行が不要な場合は「既存実装はDecisionに適合しており、移行作業は不要」と記載する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/agent/orchestrator.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/loader.py`, `scripts/db/store.py`
- 主要ClassまたはFunction: `Orchestrator.handle_turn()`, `WorkflowEngine.run()`, `WorkflowLoader.load()`, `StateStore.request_approval()`
- 設定ファイル、設定Key: `config/workflows/default.json`
- 対応するテスト: `tests/integration/test_workflow_engine.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

### WF-001: INV-01とINV-05の重複

- **Known Issue**: WF-001
- **Type**: Missing Documentation
- **Summary**: INV-01とINV-05は同一の不変条件を記述している
- **Conflicting Source**: docs/adr/ADR-001-workflow-engine-mandatory.md:243, docs/adr/ADR-001-workflow-engine-mandatory.md:247 (deprecated: use section-based references)
- **Expected Design**: INV-01: 「ワークフロー定義ファイルが欠落している場合、Agentの起動を中止する。」INV-05: 「ワークフロー定義ファイルの欠落または検証失敗時は起動を中止する。」
- **Observed Implementation**: 両方とも`StartupOrchestrator._check_workflow_definition()`（`scripts/agent/startup.py`）および`Orchestrator.__init__()`のワークフロー読み込み処理（`scripts/agent/orchestrator.py`）の同一の起動前検証を参照している
- **Impact**: ドキュメントの曖昧さ；開発者がINV-01とINV-05が異なる障害モードをカバーしていると誤解する可能性がある
- **Recommended Action**: INV-01とINV-05を1つに統合するか、区別を明確にする（例：INV-01はファイル欠落、INV-05は検証失敗）
- **Owner**: TBD
- **Resolution Target**: Next ADR review cycle

### WF-002: INV-03の明示的テスト不足

- **Known Issue**: WF-002
- **Type**: Missing Test
- **Summary**: INV-03（実行成功と検証成功の区別）の明示的テストが存在しない
- **Conflicting Source**: `WorkflowEngine.run()` メソッド（`scripts/agent/workflow/workflow_engine.py`）
- **Expected Design**: INV-03: 「実行成功と検証成功は区別され、それぞれ独立して検証される」
- **Observed Implementation**: run()メソッドはplan→execute→[approval gate]→verifyを順序通り実行するが、実行成功≠検証成功を検証するテストケースが存在しない
- **Impact**: 回帰により実行と検証の結果が混同される可能性
- **Recommended Action**: （1）実行成功かつ検証失敗がタスクステータス「failed」になることを検証するテストケース、（2）修正後に再実行すると成功する実行失敗がタスクステータス「completed」になることを検証するテストケースを追加
- **Owner**: TBD
- **Resolution Target**: Next sprint

### WF-003: Decision #5 — シンプルQ&Aの単一ステージワークフロー未実装

- **Known Issue**: WF-003
- **Type**: Design Deviation
- **Summary**: シンプルQ&Aワークフローを軽量な単一ステージWorkflowで処理する設計意図が実現されていない
- **Conflicting Source**: docs/adr/ADR-001-workflow-engine-mandatory.md:155-157, config/workflows/default.json (deprecated: use section-based references)
- **Expected Design**: Decision #5: 「シンプルなQ&Aワークフローは軽量な単一ステージWorkflowで処理する」
- **Observed Implementation**: config/workflows/default.jsonのみ存在し、plan/execute/verifyの3ステージ構成。WorkflowEngine.run()は全4つのコールバック（plan_fn, execute_fn, verify_fn）を要求する
- **Impact**: シンプルQ&Aシナリオが不要なplan/verifyオーバーヘッドを経由する必要がある
- **Recommended Action**: WorkflowEngine.run()に条件付きステージ実行を追加するか、ADR-001 Decision #5を更新してこの最適化が見送りであることを反映する
- **Owner**: TBD
- **Resolution Target**: Next planning cycle

ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。

## Review Triggers

次の条件が発生した場合、このADRを再評価する。

- 運用規模または同時実行数が大きく変化した場合
- 単一Hostから複数Hostまたは分散構成へ変更する場合
- Security要件、監査要件が変更された場合
- 性能目標またはResource制約が変更された場合
- 外部Protocolまたは採用Libraryが変更、廃止された場合
- 障害実績により前提またはFailure Policyが妥当でないと判明した場合
- 代替案の不採用理由が成立しなくなった場合

このADR固有の見直し条件を追加すること。

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

- **Approved By**: pending
- **Approval Date**: pending
- **Approval Reference**: pending

## Related Documents

### Related ADRs

- ワークフロー定義ファイルのスキーマ設計、ワークフロー監視・メトリクス設計は本文書作成時点でADR番号未割当（ADR-002/ADR-003は別決定「プロセス単位の設定所有権とConfig Isolation」「RuntimeToolRegistryを唯一のルーティング権威とする」に割当済み・Accepted — `docs/adr-index.md`参照）。起票時に`docs/adr-index.md`の採番規則に従い新規採番する。

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
- `scripts/agent/workflow/loader.py` — `WorkflowLoader.load()`
- `scripts/db/store.py` — `StateStore.request_approval()`
- `config/workflows/default.json` — ワークフロー定義ファイル

## Change History

- 2026-08-20: Proposedとして作成

Accepted後は、Decisionの意味を変更しない軽微な修正だけを記録する。

- YYYY-MM-DD: Acceptedへ変更
- YYYY-MM-DD: Linkまたは表現を修正。Decisionの変更なし

判断内容を変更する場合は、新しいADRを作成して本ADRをSupersededへ変更する。

## Completion Checklist

ADRをAcceptedへ変更する前に確認する。

- [x] 解決する問題が明確である
- [x] Decisionが1つの主要な設計判断に絞られている
- [x] Decisionが必須、禁止、正本、Fallback条件などの明確な表現で記載されている
- [x] 採用理由が現在の実装以外の観点で説明されている
- [x] 実質的な代替案と不採用理由が記載されている
- [x] Positive Consequencesが記載されている
- [x] Negative Consequencesが記載されている
- [x] Securityへの影響が評価されている
- [x] Operations、Monitoring、Recoveryへの影響が評価されている
- [x] 検証可能なInvariantsが定義されている
- [x] Exceptionsまたは適用対象外が明確である
- [x] 各InvariantにVerificationが対応している
- [x] 自動化可能な検証がManual Reviewだけになっていない
- [x] Migrationまたは移行不要の理由が記載されている
- [x] 既存ADRとの関係が記載されている
- [x] 関係するSpecificationと矛盾していない
- [ ] 現行実装との差異がKnown Issueへ登録されている
- [ ] Ownerと必要なReviewerが定義されている
- [ ] Review Triggersが記載されている
- [ ] ADR索引と関係領域のDocument Guideへ登録されている
