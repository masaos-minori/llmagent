---
title: "ADR-004: Production Failure-Handling Policy"
area: adr
decision_scope:
  - system
related:
  - ADR-001
  - ADR-002
  - ADR-003
  - ADR-010
---

# ADR-004: Production Failure-Handling Policy

## Status

Accepted

使用可能なStatusは次のとおりとする。

- `Proposed`: 提案中、レビューまたは承認前
- `Accepted`: 採用済みであり、現行設計として有効

Accepted後に現在の判断を変更する場合は、本ADR本文を直接更新する。同じ変更の中で、影響を受けるSpecification、Reference、Operations文書および検証要件を更新する。

## Summary

本ADRは、Production modeを唯一サポートされる実行モードと定義する。障害を「可用性障害」と「安全性・整合性障害」に分類するが、これは障害が及ぶ境界（起動全体を止めるか、特定のToolまたは機能に限定されるか）を特定するために用いるものであり、安全性または整合性要件を緩和する目的には用いない。安全性・整合性障害は、起動時にはFail-Fast、実行時にはFail-Closedとする。Fallbackは、その発生条件・移行先・制限が他のAccepted ADRによって明示的に定義されている場合に限り許可される（例：ADR-010が定義するRAGのインプロセスFallback）。

## Context

### Problem

startupパイプラインおよび実行時処理におけるFail-Fast／Fail-Closedの境界が明確に定義されていない。Production modeのみをサポートする前提のもとで、どの障害が起動を中止させ、どの障害が実行時の処理を拒否させるかを明確化する必要がある。Tool所有権重複や権限不正など、安全性に関わる問題は常にFail-Fast／Fail-Closedとする必要がある。

### Constraints

- 単一ホスト、単一プロセスでの実行を前提とする
- デプロイ環境では起動前にワークフロー定義ファイルが存在することを確認する必要がある
- 外部Protocol、Library、Serviceによる制約はない
- セキュリティ要件：すべての副作用のある操作は追跡可能でなければならない
- データ整合性：承認状態はプロセス境界を超えて永続化する必要がある
- 実行モードの選択や構成変更によって、安全性または検証要件が緩和されてはならない

### Assumptions

- 対象環境：単一Host、単一Agentプロセス
- 想定規模：同時実行数は限定的
- 信頼境界：Agentプロセス内でのみ権限を付与する
- 外部依存先：なし（ワークフロー定義はローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部ワークフローエンジン統合

## Decision

### Decision Details

1. **障害の分類**: 障害を「可用性障害」と「安全性・整合性障害」に分類する。可用性障害はMCPサーバーの停止、Embedding停止、外部検索停止など、システムの可用性に影響する障害。安全性・整合性障害はTool所有権重複、権限不正、Workflow定義欠落、DB Schema不整合、Config Isolation違反など、セキュリティまたはデータ整合性に影響する障害。この分類は障害の影響境界を判断するために用いるものであり、安全性または整合性要件を緩和する目的には用いない。

2. **起動時のFail-Fast**: 次の条件は起動時にFail-Fastとする（起動を中止する）。
   - Workflow定義の欠落または不正
   - 必須DB接続の失敗
   - DB Schemaの不整合
   - RuntimeToolRegistryの初期化失敗
   - Tool所有権の重複（Live Toolの重複所有）
   - 必須MCPサーバーの失敗
   - 認証、Allowlist、Safety Tier、または必須Secretの不正もしくは欠落
   - Config Isolation違反
   - 承認制御を確立できない状態
   - Production設定検証の失敗

3. **実行時のFail-Closed**: 次の条件は実行時にFail-Closedとする（当該処理を拒否する）。
   - 不明または利用不能なTool
   - Tool所有権の曖昧性
   - Tool引数の不正
   - 必須承認の欠落
   - リソーススコープまたはAllowlist検証の失敗
   - 実行前提条件の検証失敗

4. **利用不能Toolの除外**: 利用不能ToolはLLMへ提示せず、実行可能にもしない。無効化または拒否された場合は、観測可能な理由を提供しなければならない。RuntimeToolRegistryそのものの挙動（所有権、Routing、LLM可視性、静的可用性とDynamic Healthの分離）はADR-003が定義し、本ADRはここで再定義しない。

5. **実行モードによる安全性要件緩和の禁止**: 実行モードの選択や構成変更によって、安全性・整合性要件が自動的に緩和されることがあってはならない。障害の分類（可用性障害／安全性・整合性障害）は、この要件を変更する根拠にはならない。

6. **Fallback方針**: Fallbackは、その発生条件・移行先・制限が他のAccepted ADRによって明示的に定義されている場合に限り許可される。現時点でこの条件を満たすFallbackは、ADR-010が定義するRAGのインプロセスFallbackのみである。それ以外の場面でFallbackを行ってはならない。

7. **コンポーネント利用不能時の起動中止**: 設定されたコンポーネント（MCPサーバーを含む）が利用不能な場合、起動を中止する。必須／非必須という区分は設けない — 設定によって有効化されたコンポーネントはすべて起動時点で利用可能でなければならず、利用不能であればFail-Fastとする。これにより、コンポーネントを無効化した状態での起動継続（Degraded起動）は発生しない。

### Scope

- **対象コンポーネント**: `StartupOrchestrator`, `McpToolDiscoveryService`, `ProductionConfigValidator`, `HealthRegistry`
- **対象プロセス**: Agentプロセス全体
- **対象データ**: 起動チェック結果、MCPサーバー状態、Tool所有権情報、承認状態
- **対象実行モード**: production（唯一サポートされる実行モード）
- **対象APIまたは処理経路**: `StartupOrchestrator.run()`, `McpToolDiscoveryService.discover_all()`, `ProductionConfigValidator.validate()`

### Out of Scope

- 個別のMCPサーバーの障害検知詳細
- OTel出力先の障害検知詳細
- Health Checkや起動前検証など、Startup Orchestrator自身の前提確認
- 既存のStartupCheckStatus（OK/WARNING/FATAL/SKIPPED）の削除
- 既存のpipeline.add_fatal()/add_warning()の削除

## Rationale

### 1. 最重要の採用理由 — Security

安全性・整合性障害は常にFail-Fast（起動時）またはFail-Closed（実行時）とする。これは、実行モードの選択によってSecurity Controlが迂回されないようにするため。

### 2. 第2の採用理由 — Operability

可用性障害と安全性・整合性障害を区別することで、障害の影響範囲を必要以上に拡大させず、問題の切り分けを容易にする。設定されたコンポーネントの利用可能性そのものは、この分類によらず起動時にFail-Fastとする（Decision Details #7）。

### 3. 第3の採用理由 — Recoverability

安全性・整合性障害でFail-Fast／Fail-Closedとすることで、部分タスク完了の検査と復旧を確実にする。起動時のFail-Fastにより、問題の早期発見と修正を促進する。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Uniform Fail-Closed for all failure types

#### Description

可用性障害と安全性・整合性障害を区別せず、すべての障害を一律Fail-Fast／Fail-Closedとする。

#### Advantages

- 単純なルール
- 安全側のデフォルト

#### Disadvantages

- 可用性障害と安全性・整合性障害の区別自体をなくすことで、障害の影響範囲に応じた説明ができなくなる
- 障害対応の優先順位付けが困難になる

#### Reason for Rejection

障害の影響範囲に応じた対応を可能にするため、可用性障害と安全性・整合性障害を区別する方式を採用した。ただし、この区別は安全性要件の緩和には用いない。コンポーネントの利用可能性そのものは、この区別によらずFail-Fastとする。

#### Reconsideration Conditions

- 運用実績により、区別を維持する複雑性が安全性上の利点を上回ると判明した場合

### Alternative B: No distinction between availability and safety failures

#### Description

可用性障害と安全性・整合性障害を区別しない単一の障害モデルを採用する。

#### Advantages

- シンプルな構造
- 一貫した障害扱い

#### Disadvantages

- 可用性障害を安全性障害と同様に扱うことになり、影響範囲の説明が失われる
- 障害対応の優先順位付けが困難になる

#### Reason for Rejection

SecurityとOperabilityの両立のため、障害の種類に応じて異なる対応を可能にする区別を維持することとした。

#### Reconsideration Conditions

- 障害分類の運用コストが実際の効果を上回ると判明した場合

### Alternative C: Dynamic failure policy based on real-time risk assessment

#### Description

リアルタイムのリスク評価に基づいて障害方針を動的に変更する。

#### Advantages

- より柔軟な障害対応
- リスクに応じた最適化

#### Disadvantages

- 複雑な実装が必要
- リアルタイム評価の誤判定リスク
- 予測不可能な振る舞い

#### Reason for Rejection

CorrectnessとMaintainabilityを優先し、静的な障害分類で十分であると判断したため不採用とした。

#### Reconsideration Conditions

- リアルタイムリスク評価の精度が実証され、運用コストが許容範囲を超える場合

## Consequences

### Positive Consequences

- 安全性・整合性障害は常にFail-Fast（起動時）またはFail-Closed（実行時）
- 障害の分類により、影響範囲（起動全体か特定機能か）を特定できる
- 実行モードの選択や構成変更だけで危険なToolが自動許可されない
- Fallbackが許可される条件が、他のAccepted ADRによる明示的な定義に限定される
- コンポーネント利用可能性の判定基準が単一（Fail-Fast）になり、起動判断が単純化される

### Negative Consequences

- 設定されたコンポーネントが一時的に利用不能なだけで起動全体が中止されるため、運用上の柔軟性は失われる
- 設定の不整合による混乱の可能性

### Operational Consequences

- 起動時に障害分類に基づく検証が必要
- 障害対応時の判断基準が明確になる
- コンポーネントを無効化した状態での起動継続（Degraded起動）を運用手段として使えない

### Security Consequences

- 信頼境界：安全性・整合性障害は常にFail-Fast／Fail-Closed
- 認証、認可：実行モードの選択や構成変更だけで危険なToolが自動許可されない
- Secretの取扱い：必須Secretの欠落はFail-Fast
- Fail-Closed：安全性・整合性障害は常にFail-Fast（起動時）またはFail-Closed（実行時）
- Audit Log：すべての障害が監査ログに記録される

## Invariants

- INV-01: Production modeが唯一サポートされる実行モードである。
- INV-02: 実行モードの選択や構成変更によって、安全性または検証要件が緩和されない。
- INV-03: Workflow定義が欠落または不正な場合、起動を中止する。
- INV-04: Tool所有権の重複が発生した場合、起動を中止する。
- INV-05: 必須DBの接続失敗またはDB Schema不整合が発生した場合、起動を中止する。
- INV-06: 認証、Allowlist、Safety Tier、必須Secretの不正もしくは欠落、Config Isolation違反、承認制御を確立できない状態は、いずれも起動時にFail-Fastとする。
- INV-07: 必須コンポーネントが利用不能な場合、起動を中止する。
- INV-08: 利用不能ToolはLLMへ提示されず、実行もされない。
- INV-09: 安全性・整合性障害がDegraded状態に変換されることはない。
- INV-10: Fallbackは、他のAccepted ADRが明示的に定義する場合に限り許可される。
- INV-11: 無効化または拒否されたToolは、観測可能な理由を提供する。

## Exceptions

なし

例外がない場合は「なし」と明記する。

## Failure Policy

### Fail-Fast Conditions (Startup)

- Workflow定義の欠落または不正
- 必須DB接続の失敗
- DB Schemaの不整合
- RuntimeToolRegistryの初期化失敗
- Tool所有権の重複（Live Toolの重複所有）
- 必須MCPサーバーの失敗
- 認証、Allowlist、Safety Tier、または必須Secretの不正もしくは欠落
- Config Isolation違反
- 承認制御を確立できない状態
- Production設定検証の失敗

### Fail-Closed Conditions (Execution)

- 不明または利用不能なTool
- Tool所有権の曖昧性
- Tool引数の不正
- 必須承認の欠落
- リソーススコープまたはAllowlist検証の失敗
- 実行前提条件の検証失敗

### Retry Policy

- Retry対象：MCPサーバーの一時的な障害
- Retry回数：`startup_retry.max_attempts`（デフォルト3回）
- Backoff：固定間隔（デフォルト1秒）
- RetryしないError：承認拒否、システムエラー

### Fallback Policy

- Fallback対象：ADR-010が定義するRAGのインプロセスFallback
- Fallback先：ADR-010参照
- Fallbackを禁止する条件：安全性・整合性障害、および他のAccepted ADRで明示的に許可されていないすべての場面
- Fallback理由の記録先：監査ログ

該当しない場合は「対象外」と記載する。

## Data Ownership and Persistence

- **System of Record**: `StartupValidationResult`（起動チェック結果）、`HealthRegistry`（MCPサーバー状態）
- **Derived Data**: 再生成可能な派生データ（障害分類の結果）
- **Ownership**: `StartupOrchestrator`（起動チェックの所有）、`McpToolDiscoveryService`（MCPサーバー状態の所有）
- **Persistence**: SQLite（`workflow.sqlite`）、ログファイル
- **Transaction Boundary**: 起動チェック単位
- **Recovery Source**: `StartupValidationResult`（起動チェック結果の復旧）
- **Deletion Rule**: 起動チェック結果は再起動後に再生成

該当しない場合は「対象外」と記載する。

## Verification

### Automated Tests

- **Test**: 必須MCPサーバー停止時に起動が失敗すること
  - **Verifies**: INV-07
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Tool所有権重複、権限不正、Workflow不正で起動が失敗すること
  - **Verifies**: INV-04, INV-03, INV-06
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 利用不能ToolがLLMのTool一覧から除外され、かつ実行要求も拒否されること
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 実行モードの選択や構成変更だけで危険なToolが自動許可されないこと
  - **Verifies**: INV-02
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: ADR-010で定義される場面以外でFallbackが発生しないこと
  - **Verifies**: INV-10
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 無効化されたToolの呼び出しが理由文字列付きで拒否されること（`tests/mcp_servers/file/test_call_tool_validation.py`、file-mcpのみを対象とした限定的な検証）
  - **Verifies**: INV-11
  - **Type**: Unit
  - **Blocking**: No

### Startup Validation

- 障害方針に基づく起動検証
- 起動検証結果の表示

### Deployment Validation

- デプロイ前後に障害方針の設定を確認
- Fail-Fastが有効になっていることを確認

### Runtime Monitoring

- Health Check：MCPサーバーのヘルスチェック
- Metrics：無効化されたToolの数
- Logs：障害分類の結果、起動継続理由
- Alert条件：安全性・整合性障害

### Manual Review

- 障害方針の変更レビュー
- 設定されたMCPサーバー一覧の見直し
- INV-01（Production modeが唯一サポートされる実行モードであること）を直接検証する自動テストは存在しない
- INV-09（安全性・整合性障害がDegraded状態に変換されないこと）を横断的に検証する自動テストは存在しない
- INV-11（無効化・拒否されたToolが観測可能な理由を提供すること）は file-mcp でのみテストされており、他のMCPサーバーへの網羅的なテストは存在しない

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/agent/startup.py`, `scripts/shared/mcp_config.py`, `scripts/shared/production_config_validator.py`, `scripts/agent/services/mcp_tool_discovery.py`
- 主要ClassまたはFunction: `StartupOrchestrator.run()`, `McpToolDiscoveryService.discover_all()`, `ProductionConfigValidator.validate()`
- 設定ファイル、設定Key: `config/agent.toml`
- 対応するテスト: `tests/agent/shared/test_startup_validation_pipeline.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

### ADR-004-D1-profile-config-model-still-present: `required_in_local`/`failure_policy` remain in implementation after profile-specific model removal

- **Known Issue**: ADR-004-D1-profile-config-model-still-present
- **Type**: Design Deviation
- **Summary**: 本改訂により、production/local別の必須性フラグと`failure_policy`の3値モデルはADRの決定から削除され、コンポーネント利用不能は区分によらずFail-Fastとする単一モデルに置き換わったが、実装（`McpServerConfig`）にはproduction/local別フラグと3値の`failure_policy`が現存する
- **Conflicting Source**: `scripts/shared/mcp_config.py`の`McpServerConfig`（`required_in_production`、`required_in_local`、`failure_policy`フィールド）
- **Expected Design**: 本ADRはProduction modeのみをサポートし、設定されたコンポーネントが利用不能な場合は区分なく起動を中止する（Decision Details #7）
- **Observed Implementation**: 実装は依然としてproduction/local別の必須性フラグと`failure_policy`の3値モデル（`FailurePolicy.FAIL_FAST`等）を保持している
- **Impact**: ADRと実装の間に、環境別設定モデルの扱いについて明確な乖離がある。実装側の`required_in_local`／`failure_policy`は現行ADRのモデルと整合しない
- **Recommended Action**: `McpServerConfig`から`required_in_local`と`failure_policy`を削除し、`required_in_production`相当の単一フラグ（またはコンポーネント有効化フラグ）のみでコンポーネント利用不能時のFail-Fastを表現するよう実装を整合させる
- **Owner**: TBD
- **Resolution Target**: 次回の`scripts/shared/mcp_config.py`変更時

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

- コンポーネント利用不能時にFail-Fast以外の挙動（無効化しての起動継続等）を認める必要が生じた場合
- Fallbackを許可する新しいAccepted ADRが追加された場合

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

- ADR-001: ワークフロー Engine必須化 — ワークフロー定義の欠落はFail-Fast
- ADR-002: プロセス単位の設定所有権とConfig Isolation — Config Isolation違反はFail-Fast
- ADR-003: RuntimeToolRegistryを唯一のルーティング権威とする — RuntimeToolRegistry初期化失敗はFail-Fast
- ADR-010: RAGの外部実行失敗時のインプロセスフォールバック — 本ADRが許可する唯一のFallback

### Specifications

- [Turn Processing Flow](05_agent_03_03_turn-processing-flow-workflow-engine.md) — ワークフロー実行の詳細
- [Deployment Guide](02_deployment.md) — デプロイメント時のワークフロー検証

### Operations

- [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook) — 障害対応手順

### Known Issues

- なし

### Implementation References

- `scripts/agent/startup.py` — `StartupOrchestrator.run()`
- `scripts/shared/mcp_config.py` — `McpServerConfig`
- `scripts/shared/production_config_validator.py` — `ProductionConfigValidator.validate()`
- `scripts/agent/services/mcp_tool_discovery.py` — `McpToolDiscoveryService.discover_all()`
- `config/agent.toml` — 設定ファイル

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
- [x] 既存ADRとの関係が記載されている
- [ ] 関係するSpecificationと矛盾していない（要再確認 — production/local別の必須性・failure_policyに言及する他文書がないか未確認。Known Deviations ADR-004-D1参照）
- [x] 現行実装との差異がKnown Issueへ登録されている
- [ ] Ownerと必要なReviewerが定義されている（Approval Recordは pending のまま）
- [x] Review Triggersが記載されている
- [ ] ADR索引と関係領域のDocument Guideへ登録されている（別途確認が必要）
