---
title: "ADR-002: プロセス単位の設定所有権とConfig Isolation"
category: adr
status: accepted
date: "2026-08-20"
last_updated: "2026-08-20"
owners:
  - agent-team
reviewers:
  - architecture-reviewer
decision_scope:
  - system
related:
  - ADR-001
supersedes: []
superseded_by: null
---

# ADR-002: プロセス単位の設定所有権とConfig Isolation

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

Agent、各MCPサーバー、RAGインジェクションプロセス、EventBusが自身の設定ファイルを所有し、許可された設定ファイルだけを読む設計を正典化する。共通設定ファイルの新設を禁止し、値の重複を独立プロセスの明示的な依存先指定として許容する。Secretの最小公開と環境変数のPrefix/Allowlist適用により、プロセス境界を超えた設定漏洩を防ぐ。

## Context

### Problem

複数のプロセス（Agent、MCPサーバー、crawler、ingester、chunk_splitter、eventbus）が同じ設定ファイルを読み込むと、設定の所有権が不明確になり、Secretの過剰な公開や設定の相互依存が発生する。また、共通設定ファイルの新設により、設定の分散管理が複雑化し、設定変更時の影響範囲が把握できなくなる。

### Constraints

- 単一ホスト、複数プロセスでの実行を前提とする
- デプロイ環境では起動前に各プロセスの設定ファイルが存在することを確認する必要がある
- セキュリティ要件：Secretは必要なプロセスだけへ公開しなければならない
- データ整合性：各プロセスの設定は独立して管理されなければならない
- 運用要件：設定変更時の影響範囲と再起動対象を所有プロセス単位で判断できること

### Assumptions

- 対象環境：単一Host、複数プロセス
- 想定規模：同時実行数は限定的
- 信頼境界：各プロセス内でのみ権限を付与する
- 外部依存先：なし（設定ファイルはローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部設定ストア統合

## Decision

### Decision Details

1. Agentは`config/agent.toml`のみを読み込む。
2. 各MCPサーバーは`config/<key>_mcp_server.toml`のみを読み込む。
3. crawlerは`config/crawler.toml`のみを読み込む。
4. chunk_splitterは`config/chunk_splitter.toml`のみを読み込む。
5. ingesterは`config/ingester.toml`のみを読み込む。
6. EventBusは`config/eventbus.toml`のみを読み込む。
7. AgentはMCPサーバー内部設定を解釈しない。
8. MCPサーバーは`agent.toml`を参照しない。
9. 共通Config Loaderの利用は許可するが、プロセスごとに許可ファイルを限定し、許可外ファイルの読込をRuntime Errorとする。
10. 共通設定ファイルを新設しない。
11. DBパス、URL、Timeoutなどの値が複数設定に重複することを、独立プロセスの明示的な依存先指定として許容する。
12. 同名キーが複数ファイルにあっても、別の設定契約として扱う。
13. Secretは必要なプロセスだけへ公開する。環境変数にもPrefixまたはAllowlistを設ける。
14. 設定変更時の影響範囲と再起動対象を所有プロセス単位で判断する。
15. Module Import時に設定を暗黙読込しない。

### Scope

- **対象コンポーネント**: `ConfigLoader`, `MCPServer`, `Orchestrator`
- **対象プロセス**: Agentプロセス、各MCPサーバープロセス、crawlerプロセス、ingesterプロセス、chunk_splitterプロセス、eventbusプロセス
- **対象データ**: 設定ファイル、環境変数、Secret
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `ConfigLoader.restrict_to()`, `ConfigLoader.load()`, `MCPServer.run_http()`

### Out of Scope

- 個別の設定ファイルスキーマの詳細
- 環境変数の詳細なPrefix/Allowlist設計
- EventBus統合の設定読み込み方法の詳細
- ランタイム動作の変更
- 監視・メトリクス設計（別ADRで扱う）

## Rationale

### 1. 最重要の採用理由 — Security

Secretの最小公開により、プロセス境界を超えた設定漏洩を防ぐ。各プロセスが自身の設定ファイルだけを読み込むことで、他プロセスのSecretへのアクセスを物理的に遮断する。

### 2. 第2の採用理由 — Operability

設定変更時の影響範囲と再起動対象を所有プロセス単位で明確にできる。共通設定ファイルがないため、設定変更が他のプロセスに予期せぬ影響を与えることはない。

### 3. 第3の採用理由 — Data Integrity

各プロセスの設定は独立して管理されるため、設定の競合や上書きによるデータ破損を防ぐ。同名キーが異なる意味を持つことを明確にすることで、意図しない設定の共有を防ぐ。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Shared common config file

#### Description

全プロセスが共通の設定ファイルを読み込み、必要な値だけを参照する。

#### Advantages

- 設定の一元管理
- 同じ値の重複を回避できる

#### Disadvantages

- Secretの過剰な公開
- 設定の相互依存
- 設定変更時の影響範囲の不明確さ
- 設定ファイルの肥大化

#### Reason for Rejection

SecurityとOperabilityを優先し、共通設定ファイルによるSecretの過剰な公開と設定の相互依存を防ぐため不採用とした。

#### Reconsideration Conditions

- 運用規模が拡大し、設定の一元管理が必要となる場合
- 外部設定ストアの導入により、Secretの分離が可能となる場合

### Alternative B: Dynamic config resolution at runtime

#### Description

プロセス起動時に動的に設定ファイルを検索し、存在する設定ファイルを自動的に読み込む。

#### Advantages

- フレキシブルな設定管理
- 設定ファイルの追加が容易

#### Disadvantages

- 設定の所有権が不明確
- 意図しない設定の読み込み
- 設定変更時の影響範囲の不明確さ

#### Reason for Rejection

Data Integrityを優先し、設定の所有権を明確にするため不採用とした。

#### Reconsideration Conditions

- 設定ファイルの動的生成が必要となる場合
- クラウド環境での設定管理が必要となる場合

### Alternative C: No config isolation enforcement

#### Description

プロセス間の設定分離を強制せず、各プロセスが自由に設定ファイルを読み込む。

#### Advantages

- シンプルな構造
- 低複雑性

#### Disadvantages

- Secretの過剰な公開
- 設定の相互依存
- 設定変更時の影響範囲の不明確さ
- セキュリティリスク

#### Reason for Rejection

Securityを優先し、プロセス境界を超えた設定漏洩を防ぐため不採用とした。

#### Reconsideration Conditions

- 信頼境界が大幅に変更される場合
- 単一プロセス構成へ移行する場合

## Consequences

### Positive Consequences

- Secretの最小公開が確保される
- 設定変更時の影響範囲が明確になる
- 各プロセスの設定が独立して管理される
- MCPサーバーがAgentの設定に依存しない
- 設定ファイルの所有権が明確になる

### Negative Consequences

- 同じ値の重複記述が必要になる
- 設定ファイルの数が増加する
- 移行期間中の二重経路の必要性
- 設定ファイルの一貫性管理の負荷

### Operational Consequences

- 起動時に各プロセスの設定ファイルが存在することを確認する必要がある
- 設定変更時は所有プロセスの再起動が必要
- 障害対応時に設定ファイルの調査が必要

### Security Consequences

- 信頼境界：各プロセス内でのみ権限を付与する
- 認証、認可：設定ファイルに基づく権限判定
- Secretの取扱い：最小公開原則に従う
- Fail-Closed：設定ファイル欠落時は起動中止
- Audit Log：設定読み込みイベントの記録

## Invariants

- INV-01: 各プロセスは許可された設定ファイルだけを読み込む。
- INV-02: 許可外設定ファイルへのアクセスは拒否される。
- INV-03: MCPサーバーはagent.tomlなしで単体起動できる。
- INV-04: AgentへMCP固有Secretを渡さずに起動できる。

## Exceptions

なし

## Failure Policy

### Fail-Fast Conditions

- 各プロセスの設定ファイルが欠落している場合
- 設定ファイルが不正である場合

### Fail-Open or Degraded Conditions

- ローカル開発環境では、設定ファイルの軽微な検証エラーは警告として記録される

### Retry Policy

- Retry対象：設定ファイル読み込み失敗
- Retry回数：`retry_policy.max_attempts`（デフォルト3回）
- Backoff：固定間隔（デフォルト1秒）
- RetryしないError：設定ファイルの構文エラー

### Fallback Policy

- Fallback対象：なし
- Fallback先：なし
- Fallbackを禁止する条件：設定ファイル欠落時
- Fallback理由の記録先：監査ログ

該当しない場合は「対象外」と記載する。

## Data Ownership and Persistence

- **System of Record**: 各プロセスの設定ファイル（TOML形式）
- **Derived Data**: 再生成可能な派生データ（設定ファイルのSHA256チェックサム）
- **Ownership**: 各プロセス（設定ファイルの所有）
- **Persistence**: ファイルシステム（`config/`ディレクトリ）
- **Transaction Boundary**: 設定ファイル読み込み単位
- **Recovery Source**: 設定ファイル（手動復旧）
- **Deletion Rule**: 設定ファイル削除時は関連するプロセスの再起動が必要

該当しない場合は「対象外」と記載する。

## Verification

### Automated Tests

- **Test**: 各プロセスが許可された設定ファイルだけを読み込めること
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 許可外設定ファイルへのアクセスが拒否されること
  - **Verifies**: INV-02
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: MCPサーバーがagent.tomlなしで単体起動できること
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: AgentへMCP固有Secretを渡さずに起動できること
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes

### Startup Validation

- 各プロセスの設定ファイルが存在するか
- 設定ファイルが有効か（parseable TOML、必須フィールド）

### Deployment Validation

- デプロイ前後に各プロセスの設定ファイルのSHA256チェックサムを確認
- デプロイ後の設定ファイルがソースと一致するか

### Runtime Monitoring

- Health Check：設定ファイルの読み込み成功確認
- Metrics：設定ファイル読み込みイベント
- Logs：設定読み込みイベント、エラーイベント
- Alert条件：設定ファイル読み込み失敗、設定ファイルの構文エラー
- Degraded条件：設定ファイルの軽微な検証エラー（ローカル開発環境）

### Manual Review

- 設定ファイルの変更レビュー
- デプロイメント前の設定ファイル検証

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Migration and Rollout

既存実装はDecisionに適合しており、移行作業は不要。

### Compatibility

- 後方互換性：既存の設定ファイルはそのまま使用可能
- 旧設定、旧Data、旧APIの扱い：なし

### Rollback

- Rollback可能な条件：設定ファイルの変更が問題を引き起こした場合
- Rollback手順：旧設定ファイルを復元
- Rollbackできない変更：設定ファイルの削除（ロールバック不可）
- Data復旧方法：設定ファイルの手動復旧

### Completion Criteria

- 移行完了と判断する条件：既存実装がDecisionに適合していることを確認
- 旧経路を削除する条件：既存実装がDecisionに適合していることを確認

移行が不要な場合は「既存実装はDecisionに適合しており、移行作業は不要」と記載する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/shared/config_loader.py`, `scripts/mcp_servers/server.py`, `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/ingester.py`
- 主要ClassまたはFunction: `ConfigLoader.restrict_to()`, `ConfigLoader.load()`, `MCPServer.run_http()`, `Orchestrator.handle_turn()`
- 設定ファイル、設定Key: `config/agent.toml`, `config/*_mcp_server.toml`, `config/crawler.toml`, `config/chunk_splitter.toml`, `config/ingester.toml`, `config/eventbus.toml`
- 対応するテスト: `tests/shared/test_config_loader.py`, `tests/agent/test_config_permission_cross_server.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

- **Known Issue**: なし
- **Type**: N/A
- **Summary**: 確認済みの差異なし
- **Impact**: なし
- **Resolution Target**: なし

差異がない場合は「確認済みの差異なし」と記載する。

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

- 設定ファイルの形式が大幅に変更された場合
- 共通設定ファイルの新設が必要となった場合
- 永続化ストレージがファイル以外へ移行された場合

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

- ADR-001: Workflow Engine必須化

### Specifications

- [Configuration Loading](05_agent_08_01_configuration-loading-agent-config.md) — Agent設定読み込みの詳細
- [MCP Configuration File Inventory](04_mcp_06_02_configuration-file-inventory.md) — MCP設定ファイル一覧

### Operations

- [Runtime and Execution - Config and Logging](90_shared_03_01_runtime_and_execution-config-and-logging.md) — ランタイム設定とロギング

### Known Issues

- なし

### Implementation References

- `scripts/shared/config_loader.py` — `ConfigLoader.restrict_to()`, `ConfigLoader.load()`
- `scripts/mcp_servers/server.py` — `MCPServer.run_http()`
- `scripts/rag/ingestion/crawler.py` — `crawler`プロセスの設定読み込み
- `scripts/rag/ingestion/chunk_splitter.py` — `chunk_splitter`プロセスの設定読み込み
- `scripts/rag/ingestion/ingester.py` — `ingester`プロセスの設定読み込み
- `config/agent.toml` — Agent設定ファイル
- `config/*_mcp_server.toml` — MCPサーバー設定ファイル
- `config/crawler.toml` — crawler設定ファイル
- `config/chunk_splitter.toml` — chunk_splitter設定ファイル
- `config/ingester.toml` — ingester設定ファイル
- `config/eventbus.toml` — EventBus設定ファイル

## Change History

- 2026-08-20: Acceptedとして作成

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
