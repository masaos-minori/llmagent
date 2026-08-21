---
title: "ADR-004: Environment Profile別障害方針 — Fail-Fast/Fail-Open"
category: adr
status: proposed
date: "2026-08-21"
last_updated: "2026-08-21"
owners:
  - agent-team
reviewers:
  - architecture-reviewer
decision_scope:
  - system
related:
  - ADR-001
  - ADR-002
  - ADR-003
supersedes: []
superseded_by: null
---

# ADR-004: Environment Profile別障害方針 — Fail-Fast/Fail-Open

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

障害を「可用性障害」と「安全性・整合性障害」に分類し、productionでは安全性・整合性の失敗で起動中止または処理拒否を行い、localでは非必須機能の可用性障害に限りDegraded状態で継続可能とする。Profile変更だけで危険なToolが自動許可されないことを明記する。MCPサーバーごとの必須性と失敗方針を表す設定モデルを導入する。

## Context

### Problem

現行の実装では、startupパイプラインのFATAL/WARNING区別がEnvironment Profile（production/local）間で明確に定義されていない。local環境でのFail-OpenがSecurity Controlの迂回にならないよう、どの障害で起動中止するか、どの障害でDegraded継続するかを明確化する必要がある。また、Tool所有権重複や権限不正など、安全性に関わる問題はlocalでもFail-Closedとする必要がある。

### Constraints

- 単一ホスト、単一プロセスでの実行を前提とする
- デプロイ環境では起動前にワークフロー定義ファイルが存在することを確認する必要がある
- 外部Protocol、Library、Serviceによる制約はない
- セキュリティ要件：すべての副作用のある操作は追跡可能でなければならない
- データ整合性：承認状態はプロセス境界を超えて永続化する必要がある
- Fail-Closed条件はproduction/local両方で適用される

### Assumptions

- 対象環境：単一Host、単一Agentプロセス
- 想定規模：同時実行数は限定的
- 信頼境界：Agentプロセス内でのみ権限を付与する
- 外部依存先：なし（ワークフロー定義はローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部ワークフローエンジン統合

## Decision

### Decision Details

1. **障害の分類**: 障害を「可用性障害」と「安全性・整合性障害」に分類する。可用性障害はMCPサーバーの停止、Embedding停止、外部検索停止など、システムの可用性に影響する障害。安全性・整合性障害はTool所有権重複、権限不正、Workflow定義欠落、DB Schema不整合、Config Isolation違反など、セキュリティまたはデータ整合性に影響する障害。

2. **productionのFail-Fast**: productionでは次を起動中止または処理拒否とする。
   - 必須MCPサーバーの起動失敗
   - Tool所有権の重複
   - Workflow定義またはSchemaの不正
   - 必須DBの接続失敗
   - 認証、Allowlist、Safety Tierの不正
   - 必須Secretの欠落
   - Tool Routing権威を確立できない状態
   - production用設定検証の失敗

3. **localのFail-Open（可用性障害のみ）**: localでは次の非必須機能障害に限り、警告とDegraded状態で継続可能とする。
   - 非必須MCPサーバー停止
   - Embedding停止によるFTS-only動作
   - 任意の外部検索停止
   - 任意のOTel出力先停止

4. **localのFail-Closed（安全性・整合性障害）**: localでも次はFail-Closedとする。
   - Tool所有権重複
   - Write/Delete/Shellの権限設定不正
   - Workflow定義の欠落または不正
   - DB Schema不整合
   - Config Isolation違反
   - Tool引数Schemaの重大な不整合
   - 承認制御を確立できない状態

5. **Degraded状態の可観測性**: Degraded状態、無効化されたTool、起動継続理由をCLI、Diagnostics、ログから確認できるようにする。

6. **利用不能Toolの除外**: 利用不能ToolをLLMへ提示しない。

7. **Profile変更による危険Toolの自動許可禁止**: Profile変更だけで危険なToolが自動許可されないことを明記する。local環境でのFail-Openは、可用性障害に限られる。安全性・整合性障害はproduction/local問わずFail-Closedである。

8. **MCPサーバーごとの必須性と失敗方針の設定モデル**: 次の設定モデルを検討する。

```text
required_in_production = true | false
required_in_local = true | false
failure_policy = fail-fast | disable-tool | degraded
```

### Scope

- **対象コンポーネント**: `StartupOrchestrator`, `McpToolDiscoveryService`, `ProductionConfigValidator`, `HealthRegistry`
- **対象プロセス**: Agentプロセス全体
- **対象データ**: 起動チェック結果、MCPサーバー状態、Tool所有権情報、承認状態
- **対象Environment Profile**: production、local
- **対象APIまたは処理経路**: `StartupOrchestrator.run()`, `McpToolDiscoveryService.discover_all()`, `ProductionConfigValidator.validate()`

### Out of Scope

- 個別のMCPサーバーの障害検知詳細
- OTel出力先の障害検知詳細
- Health Checkや起動前検証など、Startup Orchestrator自身の前提確認
- 既存のStartupCheckStatus（OK/WARNING/FATAL/SKIPPED）の削除
- 既存のpipeline.add_fatal()/add_warning()の削除

## Rationale

### 1. 最重要の採用理由 — Security

安全性・整合性障害はproduction/local問わずFail-Closedとする。これは、local環境でのFail-OpenがSecurity Controlの迂回にならないようにするため。Profile変更だけで危険なToolが自動許可されないことを明記する。

### 2. 第2の採用理由 — Operability

可用性障害はlocalではDegraded継続可能とし、開発者の生産性を確保する。ただし、Degraded状態はCLI、Diagnostics、ログから確認可能にする。

### 3. 第3の採用理由 — Recoverability

安全性・整合性障害でFail-Closedとすることで、部分タスク完了の検査と復旧を確実にする。起動時のFail-Fastにより、問題の早期発見と修正を促進する。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Uniform Fail-Closed for all environments

#### Description

すべての環境で同じFail-Closed方針を適用する。

#### Advantages

- 単純なルール
- 安全側のデフォルト

#### Disadvantages

- local開発の生産性が低下する
- 非必須機能の障害で開発者がブロックされる

#### Reason for Rejection

Operabilityを優先し、local環境では非必須機能の可用性障害に限りDegraded継続を許可するため不採用とした。

#### Reconsideration Conditions

- 運用規模が拡大し、local環境での障害が本番環境に影響を与える場合

### Alternative B: No distinction between availability and safety failures

#### Description

可用性障害と安全性・整合性障害を区別しない。

#### Advantages

- シンプルな構造
- 一貫した障害扱い

#### Disadvantages

- local開発の生産性が低下する
- 安全性・整合性障害を軽視する

#### Reason for Rejection

SecurityとOperabilityを優先し、障害の種類に応じて異なる障害方針を適用するため不採用とした。

#### Reconsideration Conditions

- 運用規模が縮小し、local開発の生産性が重要でなくなる場合

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

CorrectnessとMaintainabilityを優先し、静的な設定モデルで十分であると判断したため不採用とした。

#### Reconsideration Conditions

- リアルタイムリスク評価の精度が実証され、運用コストが許容範囲を超える場合

## Consequences

### Positive Consequences

- 安全性・整合性障害はproduction/local問わずFail-Closed
- 可用性障害はlocalではDegraded継続可能
- Profile変更だけで危険なToolが自動許可されない
- MCPサーバーごとの必須性と失敗方針を設定可能
- Degraded状態の可観測性が向上

### Negative Consequences

- 追加される設定項目（required_in_production, required_in_local, failure_policy）
- 移行作業のコスト
- 設定の不整合による混乱

### Operational Consequences

- 起動時に障害方針に基づく検証が必要
- Degraded状態の監視が必要
- 障害対応時の判断基準が明確になる

### Security Consequences

- 信頼境界：安全性・整合性障害はproduction/local問わずFail-Closed
- 認証、認可：Profile変更だけで危険なToolが自動許可されない
- Secretの取扱い：必須Secretの欠落はFail-Closed
- Fail-Closed：安全性・整合性障害は常にFail-Closed
- Audit Log：すべての障害が監査ログに記録される

## Invariants

- INV-01: Tool所有権の重複が発生した場合、production/local問わず起動を中止する。
- INV-02: Workflow定義が欠落している場合、production/local問わず起動を中止する。
- INV-03: DB Schema不整合が発生した場合、production/local問わず起動を中止する。
- INV-04: Config Isolation違反が発生した場合、production/local問わず起動を中止する。
- INV-05: 利用不能ToolがLLMへ提示されない。
- INV-06: local環境でのFail-Openは可用性障害に限られる。
- INV-07: Profile変更だけで危険なToolが自動許可されない。
- INV-08: production環境でのFail-Fastは安全性・整合性障害を含む。

## Exceptions

なし

例外がない場合は「なし」と明記する。

## Failure Policy

### Fail-Fast Conditions

**production:**
- 必須MCPサーバーの起動失敗
- Tool所有権の重複
- Workflow定義またはSchemaの不正
- 必須DBの接続失敗
- 認証、Allowlist、Safety Tierの不正
- 必須Secretの欠落
- Tool Routing権威を確立できない状態
- production用設定検証の失敗

**local (安全性・整合性障害):**
- Tool所有権重複
- Write/Delete/Shellの権限設定不正
- Workflow定義の欠落または不正
- DB Schema不整合
- Config Isolation違反
- Tool引数Schemaの重大な不整合
- 承認制御を確立できない状態

### Fail-Open or Degraded Conditions

**local (可用性障害のみ):**
- 非必須MCPサーバー停止
- Embedding停止によるFTS-only動作
- 任意の外部検索停止
- 任意のOTel出力先停止

**production:**
- 該当なし（すべてFail-Fast）

### Retry Policy

- Retry対象：MCPサーバーの一時的な障害
- Retry回数：`startup_retry.max_attempts`（デフォルト3回）
- Backoff：固定間隔（デフォルト1秒）
- RetryしないError：承認拒否、システムエラー

### Fallback Policy

- Fallback対象：なし
- Fallback先：なし
- Fallbackを禁止する条件：安全性・整合性障害
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

- **Test**: productionで必須MCP停止時に起動が失敗すること
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: localで非必須MCP停止時にDegraded起動すること
  - **Verifies**: INV-06
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: localでもTool所有権重複、権限不正、Workflow不正で起動が失敗すること
  - **Verifies**: INV-01, INV-02, INV-03
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 利用不能ToolがLLMのTool一覧から除外されること
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Profile変更だけで危険なToolが自動許可されないこと
  - **Verifies**: INV-07
  - **Type**: Regression
  - **Blocking**: Yes

### Startup Validation

- 障害方針に基づく起動検証
- production/localの違いに応じた検証結果の表示

### Deployment Validation

- デプロイ前後に障害方針の設定を確認
- production環境でのFail-Fastが有効になっていることを確認

### Runtime Monitoring

- Health Check：MCPサーバーのヘルスチェック
- Metrics：Degraded状態、無効化されたToolの数
- Logs：障害分類の結果、起動継続理由
- Alert条件：安全性・整合性障害、productionでのFail-Fast
- Degraded条件：localでの可用性障害

### Manual Review

- 障害方針の変更レビュー
- MCPサーバーごとの必須性の見直し

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Migration and Rollout

既存実装はDecisionに部分的に適合している。移行作業は必要だが、既存のStartupCheckStatus（OK/WARNING/FATAL/SKIPPED）とpipeline.add_fatal()/add_warning()の仕組みは維持する。

### Migration Steps

1. 障害分類の定義を文書化する
2. MCPサーバーごとの必須性と失敗方針の設定モデルを導入する
3. local環境でのFail-Open条件を明確化する
4. Degraded状態の可観測性を向上させる

### Compatibility

- 後方互換性：既存のStartupCheckStatusは維持される
- 旧設定、旧Data、旧APIの扱い：新しい設定モデルは既存設定と共存可能

### Rollback

- Rollback可能な条件：設定モデルの変更が問題を引き起こした場合
- Rollback手順：旧設定ファイルを復元
- Rollbackできない変更：障害分類の定義（文書のみ）
- Data復旧方法：既存のStartupValidationResult

### Completion Criteria

- 移行完了と判断する条件：障害分類の定義が文書化され、設定モデルが導入されたことを確認
- 旧経路を削除する条件：既存実装がDecisionに適合していることを確認

移行が不要な場合は「既存実装はDecisionに適合しており、移行作業は不要」と記載する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/agent/startup.py`, `scripts/shared/mcp_config.py`, `scripts/shared/production_config_validator.py`, `scripts/agent/services/mcp_tool_discovery.py`
- 主要ClassまたはFunction: `StartupOrchestrator.run()`, `McpToolDiscoveryService.discover_all()`, `ProductionConfigValidator.validate()`
- 設定ファイル、設定Key: `config/agent.toml`
- 対応するテスト: `tests/integration/test_startup_validation.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

### ADR-004-D8-failure-policy-unused: `failure_policy` defined but never enforced

- **Known Issue**: ADR-004-D8-failure-policy-unused
- **Type**: Design Deviation
- **Summary**: Decision #8 defines three failure policies per MCP server (fail-fast / disable-tool / degraded) but only the binary required/not-required model is implemented
- **Conflicting Source**: docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md:Decision #8, scripts/shared/mcp_config.py:97, scripts/agent/services/mcp_tool_discovery.py:131-134
- **Expected Design**: Each MCP server can specify its own failure policy, allowing different handling strategies (immediate abort vs. tool disable vs. degraded operation) when a server becomes unreachable
- **Observed Implementation**: Only `required_in_production` / `required_in_local` flags are used (binary FATAL/WARNING). The `failure_policy` field exists in McpServerConfig but is never consulted anywhere in the codebase
- **Impact**: MCP servers cannot express nuanced failure tolerance beyond binary required/not-required; production deployments lose flexibility for non-critical servers
- **Recommended Action**: Implement failure_policy enforcement in McpToolDiscoveryService._fetch_server_tools(); add integration test verifying each policy produces correct startup behavior
- **Owner**: TBD
- **Resolution Target**: Before ADR-004 moves from Proposed to Accepted status

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

- MCPサーバーごとの必須性の設定モデルに変更があった場合
- local環境でのFail-Open条件が変更された場合
- Profile別障害方針の変更があった場合

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

- ADR-001: ワークフロー Engine必須化 — ワークフロー定義の欠落はFail-Closed
- ADR-002: プロセス単位の設定所有権とConfig Isolation — Config Isolation違反はFail-Closed
- ADR-003: RuntimeToolRegistryを唯一のルーティング権威とする — Tool Routing権威を確立できない状態はFail-Fast

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

## Change History

- 2026-08-21: Proposedとして作成

Accepted後は、Decisionの意味を変更しない軽微な修正だけを記録する。

- YYYY-MM-DD: Acceptedへ変更
- YYYY-MM-DD: Linkまたは表現を修正。Decisionの変更なし

判断内容を変更する場合は、新しいADRを作成して本ADRをSupersededへ変更する。

## Completion Checklist

ADRをAcceptedへ変更する前に確認する。

- [ ] 解決する問題が明確である
- [ ] Decisionが1つの主要な設計判断に絞られている
- [ ] Decisionが必須、禁止、正本、Fallback条件などの明確な表現で記載されている
- [ ] 採用理由が現在の実装以外の観点で説明されている
- [ ] 実質的な代替案と不採用理由が記載されている
- [ ] Positive Consequencesが記載されている
- [ ] Negative Consequencesが記載されている
- [ ] Securityへの影響が評価されている
- [ ] Operations、Monitoring、Recoveryへの影響が評価されている
- [ ] 検証可能なInvariantsが定義されている
- [ ] Exceptionsまたは適用対象外が明確である
- [ ] 各InvariantにVerificationが対応している
- [ ] 自動化可能な検証がManual Reviewだけになっていない
- [ ] Migrationまたは移行不要の理由が記載されている
- [ ] 既存ADRとの関係が記載されている
- [ ] 関係するSpecificationと矛盾していない
- [ ] 現行実装との差異がKnown Issueへ登録されている
- [ ] Ownerと必要なReviewerが定義されている
- [ ] Review Triggersが記載されている
- [ ] ADR索引と関係領域のDocument Guideへ登録されている
