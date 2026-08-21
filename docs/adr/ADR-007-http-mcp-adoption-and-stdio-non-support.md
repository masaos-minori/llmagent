---
title: "ADR-007: HTTP MCP採用とstdio非サポート"
category: adr
status: accepted
date: "2026-08-21"
last_updated: "2026-08-21"
owners:
  - mcp-team
reviewers:
  - architecture-reviewer
decision_scope:
  - mcp
related:
  - ADR-002
supersedes: []
superseded_by: null
---

# ADR-007: HTTP MCP採用とstdio非サポート

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

AgentとMCPサーバー間の正式なTransportをHTTPへ統一し、stdioを使用しない判断とその運用、安全上の条件を正典化する。subprocess起動とTool Transportを区別し、Timeout、Retry、Health Checkの責務を定義する。Remote公開時の認証、TLS要件を記載する。stdioの残存参照を除去またはDeprecated化する。

## Context

### Problem

MCP（Model Context Protocol）では標準的にstdio Transportが使用されるが、本プロジェクトではAgentとMCPサーバー間の通信にHTTP Transportを採用する。stdioを使用しない判断とその運用、安全上の条件を明確にする必要がある。また、subprocess起動の場合でも、起動後のTool通信はHTTPで行うことを区別する必要がある。

### Constraints

- 単一ホスト、複数プロセスでの実行を前提とする
- デプロイ環境では起動前に各MCPサーバーの設定ファイルが存在することを確認する必要がある
- セキュリティ要件：Secretは必要なプロセスだけへ公開しなければならない
- データ整合性：各MCPサーバーの設定は独立して管理されなければならない
- 運用要件：設定変更時の影響範囲と再起動対象を所有プロセス単位で判断できること

### Assumptions

- 対象環境：単一Host、複数プロセス
- 想定規模：同時実行数は限定的
- 信頼境界：各プロセス内でのみ権限を付与する
- 外部依存先：なし（設定ファイルはローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部設定ストア統合

## Decision

### Decision Details

1. MCPサーバーは独立プロセスとしてHTTP Endpointを公開することをDecisionとする。
2. Agentは共通HTTP TransportでTool Discovery、Health Check、Tool Callを実行する。
3. subprocess起動の場合でも、起動後のTool通信はHTTPとする。
4. AgentはMCP Tool通信にstdin/stdoutを使用しない。
5. stdio TransportへのFallbackを設けない。
6. 設定Schemaや文書にstdioが残る場合は削除またはDeprecated化をする。
7. 接続Timeout、応答Timeout、Retry、Semaphore、Circuit Breaker、構造化エラー、ログを共通Transport層で扱う。
8. MCPサーバーをAgentと独立して起動、停止、Health Check、監視できる。
9. localhost以外へ公開する場合は認証とTLSを必須とする。
10. HTTPのSerialization、Socket通信コストより、障害分離、運用監視、独立配備、別ホスト配置を優先する理由を記載する。

### Scope

- **対象コンポーネント**: `HttpTransport`, `MCPServer`, `ToolTransportInvoker`, `McpServerHealthRegistry`
- **対象プロセス**: Agentプロセス、各MCPサーバープロセス
- **対象データ**: MCP設定ファイル、認証トークン
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `POST /v1/call_tool`, `GET /v1/tools`, `GET /health`

### Out of Scope

- セキュリティ認証の詳細な実装（別ADRで扱う）
- メトリクス収集の詳細な設定
- ロギングの詳細なフォーマット
- パフォーマンスベンチマークの閾値

## Rationale

### 1. 最重要の採用理由 — Operability

HTTPにより、MCPサーバーをAgentと独立して起動、停止、Health Check、監視できる。障害分離が可能になり、運用監視が容易になる。

### 2. 第2の採用理由 — Security

HTTPにより、認証（Bearer Token）とTLSによるセキュリティ制御が可能になる。stdioではこれらの制御が困難である。

### 3. 第3の採用理由 — Portability

HTTPにより、別ホスト配置が可能になる。MCPサーバーを別Hostにデプロイしても、同じプロトコルで通信できる。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Stdio Transport support

#### Description

stdio Transportを公式にサポートし、AgentとMCPサーバー間の通信にstdin/stdoutを使用する。

#### Advantages

- MCP標準のプロトコル
- シンプルな実装
- ローカルプロセス間通信に適す

#### Disadvantages

- 障害分離ができない
- 運用監視が困難
- 認証とTLSが困難
- 別ホスト配置ができない
- 独立配備ができない

#### Reason for Rejection

OperabilityとSecurityを優先し、障害分離と運用監視の可能性を防ぐため不採用とした。

#### Reconsideration Conditions

- ローカル開発環境のみで使用する場合
- 障害分離が必要ない場合

### Alternative B: No subprocess startup mode

#### Description

subprocess起動モードを廃止し、すべてをexternal persistent modeとする。

#### Advantages

- シンプルな構造
- 依存関係が少ない

#### Disadvantages

- 自動起動ができなくなる
- 手動管理が必要
- 障害復旧が遅れる

#### Reason for Rejection

Operabilityを優先し、自動起動と自動再起動の可能性を防ぐため不採用とした。

#### Reconsideration Conditions

- 手動管理が許容される場合
- 自動起動が必要ない場合

### Alternative C: No authentication for remote exposure

#### Description

認証を実装せず、Firewall制限のみで外部公開を防止する。

#### Advantages

- シンプルな実装
- 低オーバーヘッド

#### Disadvantages

- セキュリティリスク
- 認証なしでアクセス可能
- 監査が困難

#### Reason for Rejection

Securityを優先し、認証なしのアクセスを防ぐため不採用とした。

#### Reconsideration Conditions

- Firewall制限が十分に堅牢である場合
- 認証なしのアクセスが許容される場合

## Consequences

### Positive Consequences

- MCPサーバーの独立したライフサイクル管理が可能になる
- 障害分離が確保される
- 運用監視が容易になる
- 認証とTLSによるセキュリティ制御が可能になる
- 別ホスト配置が可能になる
- 独立配備が可能になる

### Negative Consequences

- HTTPのSerializationオーバーヘッド
- Socket通信コスト
- 認証の実装が必要になる
- TLSの設定が必要になる

### Operational Consequences

- 起動時に各MCPサーバーの設定ファイルが存在することを確認する必要がある
- 設定変更時は所有プロセスの再起動が必要
- 障害対応時に設定ファイルの調査が必要

該当しない場合は「対象外」と記載する。

### Security Consequences

- 信頼境界：各プロセス内でのみ権限を付与する
- 認証、認可：設定ファイルに基づく権限判定
- Secretの取扱い：最小公開原則に従う
- Fail-Closed：設定ファイル欠落時は起動中止
- Audit Log：設定読み込みイベントの記録

該当しない場合は「対象外」と記載する。

## Invariants

- INV-01: MCPサーバーは独立プロセスとしてHTTP Endpointを公開する。
- INV-02: Agentは共通HTTP TransportでTool Discovery、Health Check、Tool Callを実行する。
- INV-03: subprocess起動の場合でも、起動後のTool通信はHTTPとする。
- INV-04: AgentはMCP Tool通信にstdin/stdoutを使用しない。
- INV-05: stdio TransportへのFallbackを設けない。
- INV-06: 設定Schemaや文書にstdioが残る場合は削除またはDeprecated化をする。
- INV-07: 接続Timeout、応答Timeout、Retry、Semaphore、Circuit Breaker、構造化エラー、ログを共通Transport層で扱う。
- INV-08: MCPサーバーをAgentと独立して起動、停止、Health Check、監視できる。
- INV-09: localhost以外へ公開する場合は認証とTLSを必須とする。
- INV-10: HTTPのSerialization、Socket通信コストより、障害分離、運用監視、独立配備、別ホスト配置を優先する。

## Exceptions

なし

## Failure Policy

### Fail-Fast Conditions

- MCPサーバーのHealth Check失敗時
- 認証トークンの検証失敗時
- TLS証明書の検証失敗時

### Fail-Open or Degraded Conditions

- ローカル開発環境では、軽微な整合性不一致は警告として記録される
- localプロファイルでは、Health Check失敗はwarningとして記録され、特定サーバーが無効化される

### Retry Policy

- Retry対象：HTTP 429/502/503/504
- Retry回数：最大3回
- Backoff：減少型遅延（4s, 2s, 1s）※指数関数的バックオフではない
- RetryしないError：タイムアウト、他のHTTPステータスコード

該当しない場合は「対象外」と記載する。

### Fallback Policy

- Fallback対象：なし
- Fallback先：なし
- Fallbackを禁止する条件：stdioへのフォールバック
- Fallback理由の記録先：監査ログ

該当しない場合は「対象外」と記載する。

## Data Ownership and Persistence

- **System of Record**: MCP設定ファイル（TOML形式）
- **Derived Data**: 再生成可能な派生データ（設定ファイルのSHA256チェックサム）
- **Ownership**: MCPチーム（設定ファイルの所有）
- **Persistence**: ファイルシステム（`config/`ディレクトリ）
- **Transaction Boundary**: 設定ファイル読み込み単位
- **Recovery Source**: 設定ファイル（手動復旧）
- **Deletion Rule**: 設定ファイル削除時は関連するプロセスの再起動が必要

該当しない場合は「対象外」と記載する。

## Verification

### Automated Tests

- **Test**: subprocess起動後の通信がHTTPで行われること
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Tool Call TimeoutとTransport Errorが共通エラーへ変換されること
  - **Verifies**: INV-07
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Health CheckがAgent外からも利用できること
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: stdioを実行時Transportとして参照する経路がないこと
  - **Verifies**: INV-04
  - **Type**: Regression
  - **Blocking**: Yes

### Startup Validation

- 起動時にDB接続が確認される
- 設定ファイルが有効か（parseable TOML、必須フィールド）

### Deployment Validation

- デプロイ前後にDB Schemaの確認
- デプロイ後の整合性チェックがPASSすること

### Runtime Monitoring

- Health Check：DB接続状態、DLQタスク状態、Brokerキューバックログ、Slow Consumer検出
- Metrics：Event publish count, ACK count, NACK count, DLQ promotion count
- Logs：Event publishイベント、ACKイベント、NACKイベント、DLQイベント
- Alert条件：`db_unavailable`, `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`
- Degraded条件：依存関係の障害

該当しない場合は「対象外」と記載する。

### Manual Review

- DLQ昇格の調査
- デプロイメント前のDB Schema検証

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Migration and Rollout

既存実装はDecisionに適合しているが、以下のKnown IssueをADRで判断を確定する必要がある。

### Compatibility

- 後方互換性：既存の設定ファイルはそのまま使用可能
- 旧設定、旧Data、旧APIの扱い：`healthcheck_mode`フィールドは削除済み（HTTP唯一のTransportのため冗長）

### Rollback

- Rollback可能な条件：ADRの判断が誤りであった場合
- Rollback手順：新しいADRを作成して本ADRをSupersededへ変更
- Rollbackできない変更：Eventの削除（ロールバック不可）
- Data復旧方法：SQLiteの手動復旧

該当しない場合は「対象外」と記載する。

### Completion Criteria

- 移行完了と判断する条件：既存実装がDecisionに適合していることを確認
- 旧経路を削除する条件：既存実装がDecisionに適合していることを確認

移行が不要な場合は「既存実装はDecisionに適合しており、移行作業は不要」と記載する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/mcp_servers/server.py`, `scripts/shared/http_transport.py`, `scripts/shared/tool_transport_invoker.py`, `scripts/shared/mcp_server_health_registry.py`
- 主要ClassまたはFunction: `MCPServer.run_http()`, `HttpTransport.call_tool()`, `ToolTransportInvoker.invoke()`, `McpServerHealthRegistry.record_failure()`
- データベーススキーマ: MCP設定ファイル（`config/*_mcp_server.toml`）、認証トークン（環境変数またはシークレットファイル）
- HTTPエンドポイント: `POST /v1/call_tool`, `GET /v1/tools`, `GET /health`
- Circuit Breaker: 5-state（HEALTHY → DEGRADED → UNAVAILABLE → HALF_OPEN → HEALTHY）
- 対応するテスト: `tests/test_mcp_*.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

- **Known Issue**: MCP-001 — `include_disabled` filter unimplemented on `/v1/tools`.
- **Type**: Open Issue
- **Summary**: `/v1/tools`でdisabledサーバーのフィルタリングが未実装
- **Impact**: disabledサーバーの情報も返される可能性がある
- **Resolution Target**: リファクタリング時に実装

- **Known Issue**: MCP-002 — Tool runtime availability metadata partially implemented (`enabled`/`disabled_reason` missing on some servers).
- **Type**: Documentation Gap
- **Summary**: ツールの実行時利用状況メタデータの不完全
- **Impact**: 運用担当者の混乱
- **Resolution Target**: ドキュメントの更新が必要

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

- MCP標準がstdio以外のTransportを公式サポートする場合
- TLS/mTLSの実装が必要となった場合
- 永続化ストレージがファイル以外へ移行された場合
- 障害分離が必要なくなった場合

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

- ADR-002: プロセス単位の設定所有権とConfig Isolation

### Specifications

- [MCP System Overview](04_mcp_01_system_overview.md) — MCPアーキテクチャ概要
- [Endpoints and Transport](04_mcp_02_01_endpoints-and-transport.md) — エンドポイントとTransport
- [Startup Modes and Health](04_mcp_02_02_startup-modes-and-health.md) — 起動モードとヘルス
- [Dispatch and Routing](04_mcp_03_01_dispatch-and-routing.md) — ディスパッチとルーティング
- [Transport and Health](04_mcp_03_03_transport-and-health.md) — Transportとヘルス
- [Tool Call Tracing and Watchdog](04_mcp_03_04_tool-call-tracing-and-watchdog.md) — ツール呼び出し追跡とウォッチドッグ
- [Lifecycle and New Server](04_mcp_03_05_lifecycle-and-new-server.md) — ライフサイクル
- [Configuration File Inventory](04_mcp_06_02_configuration-file-inventory.md) — 設定ファイル一覧
- [Long-running HTTP Operation Startup Mode/Subprocess](04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md) — HTTP操作起動モード
- [New MCP Server Addition Checklist](04_mcp_06_15_new-mcp-server-addition-checklist.md) — MCPサーバー追加チェックリスト

### Operations

- [MCP Operations](04_mcp_05_7-mcp-operations.md) — MCP運用手順

### Known Issues

- [MCP Known Issues](04_mcp_90_inconsistencies_and_known_issues.md) — MCP既知の問題

### Implementation References

- `scripts/mcp_servers/server.py` — `MCPServer.run_http()`
- `scripts/shared/http_transport.py` — `HttpTransport.call_tool()`
- `scripts/shared/tool_transport_invoker.py` — `ToolTransportInvoker.invoke()`
- `scripts/shared/mcp_server_health_registry.py` — `McpServerHealthRegistry.record_failure()`
- `config/*_mcp_server.toml` — MCPサーバー設定ファイル
- テスト — `tests/test_mcp_*.py`

## Change History

- 2026-08-21: Acceptedとして作成。stdio非サポートの判断を確定

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
