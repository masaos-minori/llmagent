---
title: "ADR-XXX: 設計判断のタイトル"
category: adr
status: proposed
date: "YYYY-MM-DD"
last_updated: "YYYY-MM-DD"
owners:
  - team-name
reviewers:
  - architecture-reviewer
decision_scope:
  - system
related:
  - ADR-YYY
supersedes: []
superseded_by: null
---

# ADR-XXX: 設計判断のタイトル

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

このADRで決定する内容を2から4文で簡潔に記載する。

- 何を決定するか
- どの領域へ適用するか
- 最も重要な制約または効果は何か

## Context

この判断が必要になった背景、解決すべき問題、制約を記載する。

### Problem

解決すべき問題を具体的に記載する。

- 現行構成で発生している問題
- 判断しない場合に発生する影響
- 複数の実装方式から選択する必要がある理由

### Constraints

判断時に考慮した制約を記載する。

- 技術的制約
- セキュリティ制約
- データ整合性の制約
- 運用、監視、復旧上の制約
- 性能、CPU、メモリ、ディスクの制約
- デプロイ環境、単一ホスト、複数ホストなどの制約
- 外部Protocol、Library、Serviceによる制約

### Assumptions

判断の前提を記載する。

- 対象環境
- 想定規模
- 信頼境界
- 外部依存先
- 前提が崩れた場合に再評価が必要な事項

## Decision

採用する設計を明確に記載する。

曖昧な推奨表現を避け、次のような判断表現を使用する。

- 使用する
- 使用しない
- 必須とする
- 禁止する
- 正本とする
- 派生データとする
- 指定条件では起動を中止する
- 指定条件に限りFallbackを許可する

### Decision Details

決定内容を実装方式へ依存しすぎない粒度で具体化する。

1. 決定事項1
2. 決定事項2
3. 決定事項3

### Scope

このADRを適用する範囲を記載する。

- 対象コンポーネント
- 対象プロセス
- 対象データ
- 対象Environment Profile
- 対象APIまたは処理経路

### Out of Scope

このADRでは決定しない事項を記載する。

- 対象外のコンポーネント
- 別ADRで扱う判断
- 実装タスクで決定する詳細
- 将来構想であり、現時点では採用しない事項

## Rationale

この設計を採用した理由を、優先順位の高い順に記載する。

### 1. 最重要の採用理由

採用理由と、改善される品質特性を記載する。

### 2. 第2の採用理由

採用理由と、改善される品質特性を記載する。

### 3. 第3の採用理由

採用理由と、改善される品質特性を記載する。

評価軸の例:

- Correctness
- Security
- Data Integrity
- Recoverability
- Operability
- Observability
- Maintainability
- Performance
- Resource Consumption
- Extensibility
- Implementation Cost

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

検討した代替案と不採用理由を記載する。

### Alternative A: 代替案の名称

#### Description

代替案の概要を記載する。

#### Advantages

- 利点1
- 利点2

#### Disadvantages

- 欠点1
- 欠点2

#### Reason for Rejection

どの評価軸を優先し、なぜ不採用としたかを記載する。

#### Reconsideration Conditions

どの条件が成立した場合に、この代替案を再検討するかを記載する。

### Alternative B: 代替案の名称

#### Description

代替案の概要を記載する。

#### Advantages

- 利点1
- 利点2

#### Disadvantages

- 欠点1
- 欠点2

#### Reason for Rejection

不採用理由を記載する。

#### Reconsideration Conditions

再検討条件を記載する。

## Consequences

採用によって発生する正と負の影響を記載する。

### Positive Consequences

- 得られる利点
- 単純化される処理
- 改善される安全性、整合性、復旧性
- 明確になる責務や所有権

### Negative Consequences

- 追加される複雑性
- 性能またはResource上のCost
- 運用負荷
- 移行作業
- 失われる柔軟性
- 実装上の制約

### Operational Consequences

- 起動、停止への影響
- Health Checkへの影響
- 監視項目
- Backup、Recoveryへの影響
- 障害対応への影響
- 必要になるRunbook

### Security Consequences

- 信頼境界への影響
- 認証、認可への影響
- Secretの取扱い
- Fail-Open、Fail-Closedへの影響
- Audit Logへの影響

## Invariants

内部実装を変更しても維持しなければならない条件を記載する。

各Invariantは、適合しているかを判定でき、可能な限り自動テストへ変換できる表現とする。

- INV-01: 不変条件1
- INV-02: 不変条件2
- INV-03: 不変条件3

悪い例:

- 適切にRoutingする。
- 可能な限り安全に処理する。

良い例:

- 複数のMCPサーバーが同じTool名を公開した場合、Agentの起動を中止する。
- `normalized_content`をLLM向けRAG Contextへ出力してはならない。
- ACK済みOffsetを現在値より小さい値へ更新してはならない。

## Exceptions

通常方針を適用しない範囲を記載する。

例外ごとに次を明示する。

- 何が例外か
- なぜ例外か
- どの条件まで許可するか
- 誰が例外を判断するか
- 恒久的な例外とする場合に新ADRが必要か

### Exception 1: 例外の名称

- **対象**: 例外対象
- **理由**: 例外とする理由
- **許容条件**: 例外を許容する条件
- **禁止事項**: 例外でも許可しない事項
- **終了条件**: 例外を終了する条件

例外がない場合は「なし」と明記する。

## Failure Policy

障害時の動作に影響するADRの場合に記載する。

### Fail-Fast Conditions

- 起動または処理を中止する条件

### Fail-Open or Degraded Conditions

- 警告またはDegraded状態で継続できる条件

### Retry Policy

- Retry対象
- Retry回数
- Backoff
- RetryしないError

### Fallback Policy

- Fallback対象
- Fallback先
- Fallbackを禁止する条件
- Fallback理由の記録先

該当しない場合は「対象外」と記載する。

## Data Ownership and Persistence

データの正本、派生データ、永続化に影響するADRの場合に記載する。

- **System of Record**: 正本となるデータ
- **Derived Data**: 再生成可能な派生データ
- **Ownership**: データを所有するComponentまたはProcess
- **Persistence**: 永続化先
- **Transaction Boundary**: Transaction境界
- **Recovery Source**: 復旧時の再構築元
- **Deletion Rule**: 削除順序とCascade規則

該当しない場合は「対象外」と記載する。

## Verification

ADRのDecisionとInvariantsへの適合を検証する方法を記載する。

### Automated Tests

- **Test**: テスト名またはテスト対象
  - **Verifies**: 対応するInvariant
  - **Type**: Unit / Integration / Regression
  - **Blocking**: Yes / No

### Startup Validation

- 起動時に検証する条件
- 失敗時に起動を中止するか

### Deployment Validation

- デプロイ前後に検証する条件
- Schema、設定、Artifact、Checksumなどの確認

### Runtime Monitoring

- Health Check
- Metrics
- Logs
- Alert条件
- Degraded条件

### Manual Review

自動検証できない項目だけを記載する。

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Migration and Rollout

既存実装、設定、データ、文書の移行が必要な場合に記載する。

### Migration Steps

1. 移行作業1
2. 移行作業2
3. 移行作業3

### Compatibility

- 後方互換性の有無
- 旧設定、旧Data、旧APIの扱い
- 移行期間中の二重経路の有無

### Rollback

- Rollback可能な条件
- Rollback手順
- Rollbackできない変更
- Data復旧方法

### Completion Criteria

- 移行完了と判断する条件
- 旧経路を削除する条件

移行が不要な場合は「既存実装はDecisionに適合しており、移行作業は不要」と記載する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル
- 主要ClassまたはFunction
- 設定ファイル、設定Key
- 対応するテスト

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

- **Known Issue**: ISSUE-ID
- **Type**: Implementation Bug / Design Deviation / Missing Documentation / Missing Test / Unconfirmed Behavior
- **Summary**: 差異の概要
- **Impact**: 影響
- **Resolution Target**: 解決目標

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

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: セキュリティ影響がある場合
- Operations Reviewer: 運用、監視、復旧へ影響する場合
- Data Owner: データ所有権、Schema、保持へ影響する場合

### Approval Record

- **Approved By**: reviewer-name
- **Approval Date**: YYYY-MM-DD
- **Approval Reference**: Pull Request、Issue、Review記録

## Related Documents

### Related ADRs

- ADR-YYY: 関連する設計判断

### Specifications

- 関係するArchitectureまたはSpecification

### Operations

- 関係するRunbookまたはTroubleshooting Guide

### Known Issues

- 関係するKnown Issue

### Implementation References

- 実装File PathとSymbol名

## Change History

Accepted後は、Decisionの意味を変更しない軽微な修正だけを記録する。

- YYYY-MM-DD: Proposedとして作成
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
