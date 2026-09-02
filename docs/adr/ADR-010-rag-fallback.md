---
title: "ADR-010: RAGの外部実行失敗時のインプロセスフォールバック"
area: adr
decision_scope:
  - rag
related:
  - ADR-002
supersedes: []
superseded_by: null
---

# ADR-010: RAGの外部実行失敗時のインプロセスフォールバック

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

RAGパイプラインの外部サービス実行失敗時に、インプロセスローカルRAGへ自動フォールバックする判断を正典化する。`rag_service_url`の有無で実行モードを切り替え、HTTPエラーと空結果を区別し、冪等な再実行を可能にする。DESIGN-1をADRへ移管する。

## Context

### Problem

RAGパイプラインは外部RAGサービスへの依存が高く、ネットワーク障害やサービス停止時に検索機能全体が停止する。また、空結果と技術的失敗の区別が明確でないため、適切なリカバリーが困難である。

### Constraints

- 単一Host、複数プロセスでの実行を前提とする
- デプロイ環境では起動前に各DBファイルが存在することを確認する必要がある
- sqlite-vec拡張を使用するため、標準的なFK制約の一部が制限される
- 日本語と英語/コードで異なるトークナイザ方式を使用する

### Assumptions

- 対象環境：単一Host、複数プロセス
- 想定規模：同時実行数は限定的
- 信頼境界：各DB内でのみ権限を付与する
- 外部依存先：なし（SQLiteはローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部イベントストア統合

## Decision

### Decision Details

1. `rag_service_url`が設定されている場合、外部RAGサービスへHTTP POSTする。
2. `rag_service_url`が未設定の場合、インプロセスローカルRAGを実行する。
3. HTTP呼び出しは`call_rag_service()`で実行し、`timeout=10.0`で各試行を制御する。
4. HTTPエラー（401, 403, 4xx, 5xx）と空結果（`""`）を区別する。
5. 空結果は有効な結果として扱い、フォールバックをトリガーしない。
6. 技術的失敗（タイムアウト、接続エラー、HTTPエラー）のみをフォールバック条件とする。
7. フォールバック時はMQE → KNN/BM25 → RRF → Rerank → Augmentの全パイプラインを再実行する。
8. 結果ソース（Remote/Local/Fallback）を追跡し、メトリクス・ログに記録する。
9. 解析エラーはログに記録し、空結果として扱う。
10. ローカルDBアクセスは`rag.sqlite`のみを使用する。
11. 外部RAGとローカルRAGのコーパス差異を明記し、結果の一貫性を保証しないことを記載する。
12. `remote_nonempty`, `remote_empty`, `in_process_fallback`, `ResultSource`, `HttpResultKind`の用語を定義する。

### Scope

- **対象コンポーネント**: `RagPipeline`, `call_rag_service()`, `AugmentStage`
- **対象プロセス**: Agentプロセス、ingesterプロセス
- **対象データ**: `rag.sqlite`, `session.sqlite`
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `RagPipeline.augment()`, `call_rag_service()`, `AugmentStage.run()`

### Out of Scope

- 個別のHTTPステータスコードの詳細なハンドリング
- リトライポリシーの詳細なパラメータ
- メトリクスの収集方法
- ログの出力形式
- コーパス同期のプロトコル

## Rationale

### 1. 最重要の採用理由 — Availability

外部RAGサービスの障害時に検索機能が停止すると、ユーザー体験が大きく損なわれる。インプロセスフォールバックにより、可用性を維持できる。

### 2. 第2の採用理由 — Error Classification

空結果と技術的失敗を区別することで、不要なフォールバックを防ぐ。空結果は「検索したが該当なし」であり、技術的失敗は「検索できなかった」という意味が異なる。

### 3. 第3の採用理由 — Observability

結果ソースを追跡することで、どの経路で結果が取得されたかを把握でき、デバッグと運用に役立つ。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: No Fallback

#### Description

外部RAGサービスが失敗した場合、エラーを返す。

#### Advantages

- シンプルな実装
- 結果の一貫性が確保される

#### Disadvantages

- 可用性が低下する
- ユーザー体験が悪化する

#### Reason for Rejection

Availabilityを優先し、外部サービスの障害時も検索機能を維持するため不採用とした。

#### Reconsideration Conditions

- 結果の一貫性が必須となる場合
- フォールバックによる混乱が生じる場合

### Alternative B: Fallback Only on Specific Errors

#### Description

特定のHTTPステータスコード（例：5xx）のみをフォールバック条件とする。

#### Advantages

- 意図せぬフォールバックを防ぐ
- 結果の一貫性が向上する

#### Disadvantages

- ネットワーク障害などの他のエラーに対応できない
- 複雑なルールが必要になる

#### Reason for Rejection

Availabilityを優先し、すべての技術的失敗に対応するため不採用とした。

#### Reconsideration Conditions

- 特定のエラーのみをフォールバック条件とする必要がある場合
- 結果の一貫性が重要となる場合

### Alternative C: Separate Corpus for Local

#### Description

ローカルRAGと外部RAGで異なるコーパスを使用する。

#### Advantages

- 結果の一貫性が確保される
- コーパスの独立性が向上する

#### Disadvantages

- コーパスの同期が複雑になる
- データの冗長性が増加する

#### Reason for Rejection

Availabilityを優先し、コーパスの同期コストを回避するため不採用とした。

#### Reconsideration Conditions

- 結果の一貫性が必須となる場合
- コーパスの同期コストが許容範囲内となる場合

## Consequences

### Positive Consequences

- 外部RAGサービスの障害時も検索機能が継続する
- 空結果と技術的失敗の区別が可能になる
- 結果ソースを追跡できる
- デバッグと運用が容易になる

### Negative Consequences

- フォールバック時のパフォーマンスが低下する可能性がある
- 結果の一貫性が保証されない
- コーパスの同期コストが発生する
- 複雑なエラー分類が必要になる

### Operational Consequences

- 起動時にフォールバック状態が確認される
- 障害発生時に手動コマンドが必要
- メトリクスとログの確認が必要

該当しない場合は「対象外」と記載する。

### Security Consequences

- 信頼境界：各DB内でのみ権限を付与する
- 認証、認可：設定ファイルに基づく権限判定
- Secretの取扱い：最小公開原則に従う
- Fail-Closed：設定ファイル欠落時は起動中止
- Audit Log：設定読み込みイベントの記録

該当しない場合は「対象外」と記載する。

## Invariants

- INV-01: `rag_service_url`の有無で実行モードを切り替える。
- INV-02: HTTP呼び出しは`timeout=10.0`で各試行を制御する。
- INV-03: 空結果は有効な結果として扱い、フォールバックをトリガーしない。
- INV-04: 技術的失敗（タイムアウト、接続エラー、HTTPエラー）のみをフォールバック条件とする。
- INV-05: フォールバック時はMQE → KNN/BM25 → RRF → Rerank → Augmentの全パイプラインを再実行する。
- INV-06: 結果ソース（Remote/Local/Fallback）を追跡し、メトリクス・ログに記録する。
- INV-07: 解析エラーはログに記録し、空結果として扱う。
- INV-08: ローカルDBアクセスは`rag.sqlite`のみを使用する。
- INV-09: 外部RAGとローカルRAGのコーパス差異を明記し、結果の一貫性を保証しないことを記載する。
- INV-10: `remote_nonempty`, `remote_empty`, `in_process_fallback`, `ResultSource`, `HttpResultKind`の用語を定義する。

## Exceptions

なし

## Failure Policy

### Fail-Fast Conditions

- `rag.sqlite`の接続失敗時（RAG機能停止）
- `session.sqlite`の接続失敗時（セッション機能停止）
- ローカルRAGのパイプライン実行失敗時

### Fail-Open or Degraded Conditions

- ローカル開発環境では、軽微な整合性不一致は警告として記録される
- localプロファイルでは、Health Check失敗はwarningとして記録され、特定サーバーが無効化される

### Retry Policy

- Retry対象：インジェクション失敗
- Retry回数：`retry_policy.max_attempts`（デフォルト3回）
- Backoff：固定間隔（デフォルト1秒）
- RetryしないError：整合性チェックの不一致

該当しない場合は「対象外」と記載する。

### Fallback Policy

- Fallback対象：技術的失敗
- Fallback先：インプロセスローカルRAG
- Fallbackを禁止する条件：整合性チェックの不一致
- Fallback理由の記録先：監査ログ

該当しない場合は「対象外」と記載する。

## Data Ownership and Persistence

- **System of Record**: `rag.sqlite`（ローカルRAG用）、外部RAGサービス（リモートRAG用）
- **Derived Data**: 再生成可能な派生データ（FTS5、Vector Index）
- **Ownership**: RAGチーム（正本の所有）
- **Persistence**: ファイルシステム（`/opt/llm/db/`ディレクトリ）
- **Transaction Boundary**: DB単位
- **Recovery Source**: 各DBの手動復旧
- **Deletion Rule**: 各DBの削除は独立して実行する

該当しない場合は「対象外」と記載する。

## Verification

### Automated Tests

- **Test**: 外部RAGサービスが失敗したときにインプロセスローカルRAGへフォールバックすること
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 空結果が有効な結果として扱われること
  - **Verifies**: INV-03
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: 結果ソースが正しく追跡されること
  - **Verifies**: INV-06
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: フォールバック時のパイプラインが冪等に再実行されること
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes

### Startup Validation

- 起動時にフォールバック状態が確認される
- 設定ファイルが有効か（parseable TOML、必須フィールド）

### Deployment Validation

- デプロイ前後にフォールバック状態の確認
- デプロイ後の整合性チェックがPASSすること

### Runtime Monitoring

- Health Check：フォールバック状態
- Metrics：フォールバック回数、結果ソース分布
- Logs：フォールバックイベント、エラーイベント
- Alert条件：`fallback_count > threshold`
- Degraded条件：依存関係の障害

### Manual Review

- デプロイメント前のフォールバック状態検証

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/rag/pipeline.py`, `scripts/rag/pipeline_service.py`, `scripts/shared/config_loader.py`
- 主要ClassまたはFunction: `RagPipeline.augment()`, `call_rag_service()`, `AugmentStage.run()`
- データベーススキーマ: `rag.sqlite`（`documents`, `chunks`, `chunks_fts`, `chunks_vec`）
- トリガー: `chunks_ai`, `chunks_au`, `chunks_ad`
- 対応するテスト: `tests/test_rag_pipeline.py`, `tests/test_rag_pipeline_stage.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

- **Known Issue**: DESIGN-1 — 外部RAGとローカルRAGのコーパス差異が明記されていない。結果の一貫性が保証されないため、ユーザーが予期せぬ結果を得る可能性がある。
- **Type**: Architectural Limitation
- **Summary**: 外部RAGとローカルRAGのコーパス差異が明記されていない
- **Impact**: ユーザーが予期せぬ結果を得る可能性がある
- **Resolution Target**: ドキュメントでコーパス差異を明記する

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

- sqlite-vecがFK制約をサポートする場合
- FTS5が標準的なDELETEをサポートする場合
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

- **Approved By**: タスクレベル承認判断(リポジトリ管理者。個別レビュアー名は記録しない)
- **Approval Date**: 記録なし(タスクレベル承認判断のため個別の承認日は記録しない)
- **Approval Reference**: `docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

本ADRの`Accepted`ステータスは、上記ガバナンス文書が定めるタスクレベル承認判断を受理証跡とする。個別レビュアー名・承認日による正式なApproval Recordは作成していない。

## Related Documents

### Related ADRs

- ADR-002: プロセス単位の設定所有権とConfig Isolation
- ADR-005: RAGの正本と派生インデックスの関係

### Specifications

- [RAG Query Pipeline](03_rag_05_9-rag-query-pipeline.md) — クエリパイプライン
- [RAG Augment Stage](03_rag_05_10_augment-stage.md) — Augmentステージ
- [RAG Error Handling Reference](03_rag_05_4-error-handling-reference.md) — エラーハンドリング
- [Configuration Reference](03_rag_05_1-configuration-reference.md) — 設定参照
- [RAG Design Notes](03_rag_91_design_notes.md) — DESIGN-1ノート
- [DB Schema Reference](90_shared_04_02_db_architecture_and_schema-schema-reference.md) — DBスキーマ参照

### Operations

- [RAG Operations](03_rag_05_6-rag-operations.md) — RAG運用手順

### Known Issues

- なし

### Implementation References

- `scripts/rag/pipeline.py` — `RagPipeline.augment()`, `RagPipeline._format_chunks()`
- `scripts/rag/pipeline_service.py` — `call_rag_service()`
- `scripts/shared/config_loader.py` — `ConfigLoader.restrict_to()`, `ConfigLoader.load()`
- `rag.sqlite` — `documents`, `chunks`, `chunks_fts`, `chunks_vec`
- トリガー — `chunks_ai`, `chunks_au`, `chunks_ad`
- テスト — `tests/test_rag_pipeline.py`, `tests/test_rag_pipeline_stage.py`

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
