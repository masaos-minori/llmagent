---
title: "ADR-003: RuntimeToolRegistryを唯一のルーティング権威とする"
category: adr
status: accepted
date: "2026-08-20"
last_updated: "2026-08-20"
owners:
  - mcp-team
reviewers:
  - architecture-reviewer
decision_scope:
  - system
related:
  - ADR-001
  - ADR-002
supersedes: []
superseded_by: null
---

# ADR-003: RuntimeToolRegistryを唯一のルーティング権威とする

## Status

Accepted

使用可能なStatusは次のとおりとする。

- `Proposed`: 提案中、レビューまたは承認前
- `Accepted`: 採用済みであり、現行設計として有効
- `Rejected`: 検討したが不採用
- `Deprecated`: 現在は推奨しないが、一部に残存
- `Superseded`: 後継ADRによって置換済み

Accepted後に判断内容を変更する場合は本文を直接変更せず、新しいADRを作成して本ADRをSupersededへ変更する。

## Summary

Tool名から実行先MCPサーバーを決定する権威を`RuntimeToolRegistry`へ一本化し、静的定義、設定、Discovery結果によるルーティングの二重化を防止する。起動時に各MCPサーバーから取得したTool定義を正規化し`RuntimeTool`として登録し、`ToolRouteResolver`は`RuntimeToolRegistry`だけを参照する。静的`ToolRegistry`、設定上のTool名一覧、LLM Prompt内のTool定義を実行時Routingに使用しない。

## Context

### Problem

複数の経路でTool名からMCPサーバーへのルーティングが行われると、所有権の競合や予期せぬToolのルーティングが発生する。具体的には以下の問題がある。

- `ToolRegistry`（静的定義）と`RuntimeToolRegistry`（ライブDiscovery）の両方がルーティング権限を持つ場合、同一Tool名の所有権が衝突する可能性がある
- 設定ファイル上の`tool_names`リストがルーティング入力として機能すると、設定とDiscovery結果の不一致が予期せぬルーティングを引き起こす
- 未登録Toolを名前規則から推測してRoutingすると、Security Controlを迂回できる
- 複数MCPサーバーが同じTool名を公開した場合、Profileにかかわらずどちらへルーティングするか不明確になる

### Constraints

- 単一ホスト、複数プロセスでの実行を前提とする
- デプロイ環境では起動前に各MCPサーバーからTool定義を取得する必要がある
- セキュリティ要件：未登録Toolの実行を拒否しなければならない
- データ整合性：Safety TierとWrite属性はRouting、承認、監査で同じ値を参照しなければならない
- 運用要件：Discovery結果と設定上の期待値との差を検出できること
- 外部依存先：各MCPサーバーの`/v1/tools`エンドポイント

### Assumptions

- 対象環境：単一Host、複数プロセス
- 想定規模：同時実行数は限定的
- 信頼境界：各MCPサーバー内でのみ権限を付与する
- 外部依存先：MCPサーバーの`/v1/tools`エンドポイント
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部ツール定義ストア統合

## Decision

### Decision Details

1. 起動時に各MCPサーバーから取得したTool定義を正規化し、`RuntimeTool`として登録する。
2. `RuntimeTool`にはTool名、所有MCPサーバー、説明、Input Schema、Read/Write分類、Safety Tier、実行制約、利用可能状態を保持させる。
3. `ToolRouteResolver`は`RuntimeToolRegistry`だけを参照する。
4. 静的`ToolRegistry`、設定上のTool名一覧、LLM Prompt内のTool定義を実行時Routingに使用しない。
5. 静的定義を残す場合は、テスト、期待値、文書生成、Drift検証に限定する。
6. 未登録Toolを名前規則から推測してRoutingしない。静的RegistryへのFallbackを設けない。
7. 複数MCPサーバーが同じTool名を公開した場合は、Profileにかかわらず起動を失敗させる。
8. Safety TierとWrite属性はRouting、承認、監査で同じ`RuntimeTool`を参照する。
9. Discovery結果と設定上の期待値との差をRouting Driftとして検出する。
10. Registry更新を許可する場合、実行中Toolとの整合性を保証する。

### Scope

- **対象コンポーネント**: `RuntimeToolRegistry`, `ToolRegistry`, `ToolRouteResolver`
- **対象プロセス**: Agentプロセス、各MCPサーバープロセス
- **対象データ**: Tool定義、Discovery結果、設定ファイル
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `RuntimeToolRegistry.resolve()`, `ToolRouteResolver.resolve()`, `McpToolDiscoveryService.discover_all()`

### Out of Scope

- 個別のTool定義スキーマの詳細
- MCPサーバーごとの必須性と失敗方針（別ADRで扱う）
- EventBus統合の設定読み込み方法の詳細
- ランタイム動作の変更
- 監視・メトリクス設計（別ADRで扱う）

## Rationale

### 1. 最重要の採用理由 — Security

未登録Toolの実行をFail-Closedで拒否するため。静的定義とDiscovery結果の両方を参照すると、設定ファイルにのみ存在するToolが予期せぬMCPサーバーへルーティングされる可能性がある。RuntimeToolRegistryだけが権威であれば、Discoveryに失敗したToolは実行されない。

### 2. 第2の採用理由 — Data Integrity

Safety TierとWrite属性がRouting、承認、監査で同じ値を参照するため、承認判定と実際の権限操作が一致する。複数経路で異なる値が参照されると、承認されたToolが実際にはWrite権限を持つという矛盾が生じる。

### 3. 第3の採用理由 — Operability

Discovery結果と設定上の期待値との差をRouting Driftとして明確に検出できる。静的定義とDiscovery結果の両方を参照すると、どの経路の値が実際に適用されたか不明確になる。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Dual routing authority (ToolRegistry + RuntimeToolRegistry)

#### Description

静的`ToolRegistry`と`RuntimeToolRegistry`の両方を参照し、Discovery結果がない場合に静的定義へフォールバックする。

#### Advantages

- Discovery失敗時の冗長性
- 旧仕様の継続的なサポート

#### Disadvantages

- 所有権の競合の可能性
- 設定とDiscovery結果の不一致による予期せぬルーティング
- 未登録Toolの安全性低下
- Safety TierとWrite属性の不一致

#### Reason for Rejection

Securityを優先し、未登録Toolの実行をFail-Closedで拒否するため不採用とした。

#### Reconsideration Conditions

- Discovery機構の信頼性が大幅に向上した場合
- 静的定義とDiscovery結果の整合性が保証される場合

### Alternative B: Dynamic tool registration at runtime

#### Description

RuntimeToolRegistryを更新しつつ、動的にToolを追加・削除する。

#### Advantages

- フレキシブルなTool管理
- RuntimeでのTool追加が可能

#### Disadvantages

- 実行中のToolとの整合性の困難さ
- Security Controlの複雑化
- 承認状態の失効リスク

#### Reason for Rejection

Data Integrityを優先し、実行中のToolとの整合性を保証するため不採用とした。

#### Reconsideration Conditions

- RuntimeでのTool追加が必要となる場合
- 承認状態の動的更新が必要となる場合

### Alternative C: No static definition at all

#### Description

静的定義を完全に廃止し、Discovery結果のみを使用する。

#### Advantages

- シンプルな構造
- 低複雑性

#### Disadvantages

- テスト、Drift検証のための期待値がない
- 文書生成のためのSeedデータがない
- 新Toolの事前登録ができない

#### Reason for Rejection

Operabilityを優先し、Drift検証とテストのための期待値が必要であるため不採用とした。

#### Reconsideration Conditions

- Discovery結果のみで十分な検証ができる場合
- テストの自動化が十分に進んだ場合

## Consequences

### Positive Consequences

- Routing権威が明確になり、所有権の競合が防止される
- 未登録Toolの実行がFail-Closedで拒否される
- Safety TierとWrite属性がRouting、承認、監査で一致する
- Discovery結果と設定の差がRouting Driftとして検出される
- 複数MCPサーバーのTool名重複が起動時に検出される

### Negative Consequences

- Discovery失敗時にToolが実行されない
- 新Toolの追加にはDiscovery結果の更新が必要
- RuntimeToolRegistryの構築コスト
- 既存の静的定義依存のコードの修正

### Operational Consequences

- 起動時にDiscovery結果に基づいてRoutingが確定する
- RuntimeでのTool追加・削除は禁止
- Health Checkへの影響：Discovery失敗時は起動中止
- 障害対応：Discovery失敗時は再起動が必要

### Security Consequences

- 信頼境界：Discovery結果のみがRouting権威
- 認証、認可：RuntimeToolRegistryがSafety Tierを一元管理
- Secretの取扱い：Discovery結果に基づく
- Fail-Open、Fail-Closed：未登録ToolはFail-Closed
- Audit Log：Routing、承認、監査で同一Safety Tierを参照

## Invariants

- INV-01: 複数のMCPサーバーが同じTool名を公開した場合、Agentの起動を中止する。
- INV-02: `ToolRouteResolver.resolve()`は`RuntimeToolRegistry`のみを参照し、未知のTool名に対しては`ValueError`を即時発生させる。
- INV-03: Safety TierとWrite属性はRouting、承認、監査で同一の`RuntimeTool`を参照する。
- INV-04: 静的`ToolRegistry`は実行時Routingに使用せず、Drift検証・テスト・文書生成に限定する。
- INV-05: Discovery結果と設定上の期待値の差をRouting Driftとして検出し、報告する。

## Exceptions

なし

通常方針を適用しない例外はない。例外を許容する条件は定義しない。

## Failure Policy

### Fail-Fast Conditions

- 複数MCPサーバーが同じTool名を公開した場合
- `RuntimeToolRegistry`の初期化に失敗した場合
- 未登録ToolがRouting要求した場合

### Fail-Open or Degraded Conditions

該当なし

### Retry Policy

該当なし

### Fallback Policy

該当なし

## Data Ownership and Persistence

- **System of Record**: `RuntimeToolRegistry`（起動時に`McpToolDiscoveryService`から取得したDiscovery結果）
- **Derived Data**: `ToolRegistry`（Drift検証用）、設定ファイル上の`tool_names`（Drift検証用）
- **Ownership**: `RuntimeToolRegistry`
- **Persistence**: メモリ上
- **Transaction Boundary**: 起動時
- **Recovery Source**: 再起動後のDiscovery
- **Deletion Rule**: 該当なし

## Verification

### Automated Tests

- **Test**: Tool名の所有権重複で起動が失敗すること
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 未登録Toolが実行されないこと
  - **Verifies**: INV-02
  - **Type**: Unit
  - **Blocking**: Yes

- **Test**: 静的ToolRegistryへFallbackしないこと
  - **Verifies**: INV-04
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Discovery結果と期待値のDriftを検出すること
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Routing、承認、監査が同一Safety Tierを参照すること
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes

### Startup Validation

- 起動時にDiscovery結果に基づいてRoutingが確定する
- Discovery失敗時は起動を中止する

### Deployment Validation

- デプロイ前後にDiscovery結果を確認する
- Schema、設定、Artifact、Checksumなどの確認

### Runtime Monitoring

- Health Check
- Metrics
- Logs
- Alert条件：Discovery失敗時
- Degraded条件：該当なし

### Manual Review

自動検証できない項目はない。

## Migration and Rollout

### Migration Steps

1. RuntimeToolRegistryのRouting権威を明文化
2. ToolRouteResolverの参照先をRuntimeToolRegistryへ統一
3. 静的ToolRegistryの用途をDrift検証・テスト・文書生成へ限定
4. 既存文書のRegistry説明をADRと整合させる

### Compatibility

- 後方互換性：あり（既存の静的定義はDrift検証用として残る）
- 旧設定、旧Data、旧APIの扱い：Drift検証用として維持
- 移行期間中の二重経路の有無：なし

### Rollback

- Rollback可能な条件：ADRの判断内容を変更する場合
- Rollback手順：新しいADRを作成して本ADRをSupersededへ変更
- Rollbackできない変更：該当なし
- Data復旧方法：再起動後のDiscovery

### Completion Criteria

- RuntimeToolRegistryを唯一の権威とするADRが作成されている
- ToolRouteResolverの参照先が一意に定義されている
- 静的ToolRegistryの用途が限定されている
- Tool所有権重複時のFail-Fastが定義されている
- Routing DriftとSafety属性の扱いが記載されている
- 既存文書のRegistry説明がADRと整合している

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- **実装ファイル**:
  - `scripts/shared/runtime_tool_registry.py`: `RuntimeToolRegistry`
  - `scripts/shared/route_resolver.py`: `ToolRouteResolver`
  - `scripts/shared/tool_registry.py`: `ToolRegistry`
  - `scripts/shared/runtime_tool.py`: `RuntimeTool`
  - `scripts/shared/tool_routing_validation.py`: Drift検証
- **主要ClassまたはFunction**:
  - `RuntimeToolRegistry.resolve()`: Routing権威
  - `ToolRouteResolver.resolve()`: RuntimeToolRegistryのみを参照
  - `ToolRegistry.get_all_tool_names()`: Drift検証用
- **設定ファイル、設定Key**:
  - `config/agent.toml`の`[mcp_servers.*]`
  - `tool_constants.py`のfrozenset（Drift検証用）
- **対応するテスト**:
  - `tests/unit/test_runtime_tool_registry.py`
  - `tests/unit/test_route_resolver.py`
  - `tests/unit/test_tool_routing_validation.py`

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
- 障害実績により前提またはFailure Policyが妥当でないと判明した場合
- 代替案の不採用理由が成立しなくなった場合

このADR固有の見直し条件を追加すること。

- MCPサーバーごとの必須性と失敗方針の変更（ADR-004と連動）
- RuntimeToolのフィールド定義の変更
- Routing Driftの閾値変更

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: セキュリティ影響がある場合
- Operations Reviewer: 運用、監視、復旧へ影響する場合
- Data Owner: データ所有権、Schema、保持へ影響する場合

### Approval Record

- **Approved By**: architecture-reviewer
- **Approval Date**: 2026-08-20
- **Approval Reference**: ADR-003作成

## Related Documents

### Related ADRs

- ADR-001: Workflow Engineの必須化
- ADR-002: Config Isolation

### Specifications

- [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) — MCP Discovery and Routing
- [04_mcp_03_02_tool-registry.md](04_mcp_03_02_tool-registry.md) — Tool Registry Reference
- [05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md) — Agent Tool Execution
- [90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md](90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md) — Shared Runtime

### Operations

- 関係するRunbookまたはTroubleshooting Guide

### Known Issues

- 関係するKnown Issue

### Implementation References

- `scripts/shared/runtime_tool_registry.py::RuntimeToolRegistry`
- `scripts/shared/route_resolver.py::ToolRouteResolver`
- `scripts/shared/tool_registry.py::ToolRegistry`
- `scripts/shared/runtime_tool.py::RuntimeTool`
- `scripts/shared/tool_routing_validation.py`

## Change History

Accepted後は、Decisionの意味を変更しない軽微な修正だけを記録する。

- 2026-08-20: Proposedとして作成
- 2026-08-20: Acceptedへ変更

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
- [x] 現行実装との差異がKnown Issueへ登録されている
- [x] Ownerと必要なReviewerが定義されている
- [x] Review Triggersが記載されている
- [x] ADR索引と関係領域のDocument Guideへ登録されている
