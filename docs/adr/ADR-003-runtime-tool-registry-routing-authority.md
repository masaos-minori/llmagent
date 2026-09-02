---
title: "ADR-003: RuntimeToolRegistryを唯一のルーティング権威とする"
area: adr
decision_scope:
  - system
related:
  - ADR-001
  - ADR-002
---

# ADR-003: RuntimeToolRegistryを唯一のルーティング権威とする

## Status

Accepted

使用可能なStatusは次のとおりとする。

- `Proposed`: 提案中、レビューまたは承認前
- `Accepted`: 採用済みであり、現行設計として有効

Accepted後に現在の判断を変更する場合は、本ADR本文を直接更新する。同じ変更の中で、影響を受けるSpecification、Reference、Operations文書および検証要件を更新する。

## Summary

Tool名から実行先MCPサーバーを決定する権威を`RuntimeToolRegistry`へ一本化し、静的定義、設定、Discovery結果によるルーティングの二重化を防止する。起動時に各MCPサーバーから取得したTool定義を正規化し`RuntimeTool`として登録し、`ToolRouteResolver`は`RuntimeToolRegistry`だけを参照する。静的`ToolRegistry`、設定上のTool名一覧、LLM Prompt内のTool定義を実行時Routingに使用しない。

`RuntimeToolRegistry`はさらに、Tool所有権とRoutingだけでなく、LLM可視性、静的可用性、Dynamic Health、承認状態、実行適格性という関連する概念群についても唯一の権威である。これらは互いに異なる概念であり、単一の「有効/無効」フラグへ統合しない。

## Context

### Problem

複数の経路でTool名からMCPサーバーへのルーティングが行われると、所有権の競合や予期せぬToolのルーティングが発生する。具体的には以下の問題がある。

- `ToolRegistry`（静的定義）と`RuntimeToolRegistry`（ライブDiscovery）の両方がルーティング権限を持つ場合、同一Tool名の所有権が衝突する可能性がある
- 設定ファイル上の`tool_names`リストがルーティング入力として機能すると、設定とDiscovery結果の不一致が予期せぬルーティングを引き起こす
- 未登録Toolを名前規則から推測してRoutingすると、Security Controlを迂回できる
- 複数MCPサーバーが同じTool名を公開した場合、Profileにかかわらずどちらへルーティングするか不明確になる
- Tool定義の存在、Discovery、LLM可視性、Routing所有権、静的な設定由来の可用性、動的なサーバー健全性、承認状態、実行適格性は別個の概念であるにもかかわらず、単一の「有効/無効」フラグへ暗黙に統合されると、コードが誤った概念を参照したり、実際にはフィルタしていない処理段階が存在するかのように文書化されたりする

### Constraints

- 単一ホスト、複数プロセスでの実行を前提とする
- デプロイ環境では起動前に各MCPサーバーからTool定義を取得する必要がある
- セキュリティ要件：未登録Toolの実行を拒否しなければならない
- データ整合性：Safety TierとWrite属性はRouting、承認、監査で同じ値を参照しなければならない
- 運用要件：Discovery結果は起動時に一度取得され、Agentプロセスの再起動まで再取得されない
- 外部依存先：各MCPサーバーの`/v1/tools`エンドポイント

### Assumptions

- 対象環境：単一Host、複数プロセス（Agentプロセス1、各MCPサーバープロセス）
- 想定規模：同時実行数は限定的
- 信頼境界：各MCPサーバー内でのみ権限を付与する
- 外部依存先：MCPサーバーの`/v1/tools`エンドポイント
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部ツール定義ストア統合、Agent再起動なしのMCPサーバー追加・削除（Hot Reload）

## Decision

### Decision Details

1. 起動時に各MCPサーバーから取得したTool定義を正規化し、`RuntimeTool`として登録する。
2. `RuntimeTool`にはTool名、所有MCPサーバー、説明、Input Schema、Read/Write分類、Safety Tier、実行制約、LLM可視性を保持させる。
3. `ToolRouteResolver`は`RuntimeToolRegistry`だけを参照する。
4. 静的`ToolRegistry`、設定上のTool名一覧、LLM Prompt内のTool定義を実行時Routingに使用しない。
5. 静的定義を残す場合は、テスト、期待値、文書生成に限定する。
6. 未登録Toolを名前規則から推測してRoutingしない。静的RegistryへのFallbackを設けない。
7. 複数MCPサーバーが同じTool名を公開した場合は、Profileにかかわらず起動を失敗させる。
8. Safety TierとWrite属性はRouting、承認、監査で同じ`RuntimeTool`を参照する。
9. Registry更新を許可する場合、実行中Toolとの整合性を保証する。
10. Defined（定義済み）、Discoverable（Discovery可能）、Owned（所有Tool）、LLM-visible（LLMへ公開）、Statically available（静的に利用可能）、Dynamically available（動的に利用可能）、Routable（Routing可能）、Approved（承認済み）、Executable（実行可能）は別個の概念であり、これらを区別せず単一の「有効/無効」フラグへ統合しない。
11. 静的可用性（設定に基づき、各MCPサーバーがDiscovery時に算出し、`McpToolDiscoveryService`が起動時に一度取り込む値）とDynamic Health（サーバー到達性およびCircuit Breaker状態であり、`McpServerHealthRegistry`/`ToolExecutor`が実行中継続的に追跡する値）は別個のサブシステムである。静的可用性はLLMへの公開可否とRouting適格性を制御し、Dynamic Healthはすでに Routable な呼び出しが実行時に成功するかどうかを制御する。静的に有効だが動的にDownなToolは、LLMに可視かつRoutableのままとし、実行時にのみ失敗させる。
12. Dynamic Healthの状態は、LLM可視性（`enabled_for_llm`等）を自動的に変更してはならない。
13. Approval要件は無効化されたTool状態の一種ではない。Approvalは`agent/tool_policy.py`/`tool_approval.py`が所有し、Routing解決後に適用される呼び出し単位（引数によって危険度が変わり得る）のポリシー判断であり、無効化されたToolとして表現または混同してはならない。
14. Discovery由来のTool定義（`raw_definition`、静的な`status`等）を反映するには、Agentプロセスの完全な再起動が必要である。現在の承認済み仕様がRediscoveryを明示的に定義しない限り、Reload操作は Safety Tier や許可リスト由来のLLM可視性などPolicy由来フィールドのみを更新し、Discovery由来のTool定義を再取得しない。Reload挙動は、現在サポートされている範囲としてのみ記述する。
15. 静的`ToolRegistry`は、起動時Drift検証（`shared/tool_routing_validation.py`による設定`tool_names`および実行時`/v1/tools`応答との比較、`agent/services/routing_drift.py`経由で呼び出される）の入力データとしてのみ使用してよい。この用途はRouting判断そのものではなく、既に確定した`RuntimeToolRegistry`ベースのRouting結果の妥当性を事後的に警告する診断的検証であり、`ToolRouteResolver.resolve()`が`RuntimeToolRegistry`のみを参照するという原則（Decision Detail #3、INV-02）を変更しない。（2026-09-02追加、`issues/20260831-181721_adr003_01_tool_routing_validation_status_decision.md`参照）

### Responsibility Boundaries

- **RuntimeToolRegistry**: Tool所有権、Routing、LLM可視性メタデータ、および実行関連メタデータ（Safety Tier、Write属性等）に関する現行の実行時権威。
- **MCP Live Discovery**（`McpToolDiscoveryService`）: 現行の実行時Tool定義の取得元。起動時に一度、各MCPサーバーの`/v1/tools`を呼び出す。
- **Dynamic Health Subsystem**（`McpServerHealthRegistry`、`ToolExecutor`）: 到達性およびCircuit Breaker状態を担当する現行のサブシステム。LLM可視性を変更する権限を持たない。
- **Approval Subsystem**（`agent/tool_policy.py`、`agent/tool_approval.py`）: Tool解決後の呼び出し単位の承認・リスク判定を担当する現行のサブシステム。

Discovery可能、または所有されているというだけでは、そのToolが常にExecutableであることを意味しない。Dynamic HealthまたはApproval判定により、実行時に失敗または拒否され得る。

### Scope

- **対象コンポーネント**: `RuntimeToolRegistry`, `ToolRegistry`, `ToolRouteResolver`, `McpToolDiscoveryService`, `McpServerHealthRegistry`, `ToolExecutor`
- **対象プロセス**: Agentプロセス、各MCPサーバープロセス
- **対象データ**: Tool定義、Discovery結果、設定ファイル
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `RuntimeToolRegistry.resolve()`, `RuntimeToolRegistry.llm_tool_definitions()`, `RuntimeToolRegistry.apply_policy()`, `ToolRouteResolver.resolve()`, `McpToolDiscoveryService.discover_all()`

### Out of Scope

- 個別のTool定義スキーマの詳細
- MCPサーバーごとの必須性と失敗方針（別ADRで扱う）
- 各MCPサーバーにおける静的可用性の算出方法の実装詳細（各MCPサーバー自身の責務であり、本ADRでは参照のみ）
- Approval Policyそのものの再設計（`tool_policy.py`/`tool_approval.py`が所有し、本ADRでは参照のみ）
- EventBus統合の設定読み込み方法の詳細
- ランタイム動作の変更
- Hot ReloadによるRediscovery（Policy B）の採用（将来のADRで扱う可能性がある選択肢であり、本ADRでは現在の方針（完全再起動によるDiscovery更新）のみを定める）
- 監視・メトリクス設計（別ADRで扱う）

## Rationale

### 1. 最重要の採用理由 — Security

未登録Toolの実行をFail-Closedで拒否するため。静的定義とDiscovery結果の両方を参照すると、設定ファイルにのみ存在するToolが予期せぬMCPサーバーへルーティングされる可能性がある。RuntimeToolRegistryだけが権威であれば、Discoveryに失敗したToolは実行されない。

### 2. 第2の採用理由 — Data Integrity

Safety TierとWrite属性がRouting、承認、監査で同じ値を参照するため、承認判定と実際の権限操作が一致する。複数経路で異なる値が参照されると、承認されたToolが実際にはWrite権限を持つという矛盾が生じる。

### 3. 第3の採用理由 — Operability

Routing権威が一つに限定されるため、どの経路の値が実際に適用されたかが常に明確である。静的定義とDiscovery結果の両方を参照すると、どの経路の値が実際に適用されたか不明確になる。

### 4. 第4の採用理由 — Correctness / Maintainability

実際には複数の異なる意味を持つ単一の「有効/無効」概念は、コードが誤った概念を参照する原因になり、実際にはフィルタしていない処理段階が存在するかのような文書化を招く。「静的可用性 対 Dynamic Health」および「Approval 対 無効化状態」を明示的に区別することで、Dynamic Health駆動の機能をLLM可視性と同じフィールドへ書き込んでしまうという低コストで起こりやすい誤りを防止する。

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

Operabilityを優先し、テストのための期待値が必要であるため不採用とした。

#### Reconsideration Conditions

- Discovery結果のみで十分な検証ができる場合
- テストの自動化が十分に進んだ場合

### Alternative D: Unify static availability and dynamic health into one `enabled` signal

#### Description

静的可用性とDynamic Healthを単一の`enabled`シグナルへ統合する。

#### Advantages

- シンプルな心的モデル
- 確認すべきフラグが一つになる

#### Disadvantages

- Circuit Breakerが作動するたびにLLM可視Tool一覧が変化し、一時的なネットワーク不調によってLLMから見たTool可用性が不安定化する
- 実行時エラーに比べて影響範囲がはるかに大きい

#### Reason for Rejection

現行の分離（静的が可視性を、Dynamicが実行時の成否を制御する）の方が既に安全な設計であるため、分離を維持し明文化する。

#### Reconsideration Conditions

- Dynamic Healthの変化がLLM可視性に反映されるべき新たな要件が生じた場合

### Alternative E: Represent approval-required as a disabled state

#### Description

Approval要求状態を無効化Tool機構の一部として表現する。

#### Advantages

- 既存の無効化Tool機構を再利用できる

#### Disadvantages

- Approvalは引数（例：パスやBranch）に基づくRisk Escalationを伴う呼び出し単位の判断であり、Tool単位の静的な無効化フラグでは表現できない
- 両者を統合すると、Approval対象Toolが本来LLMに可視であるべき場面でも不可視になり、実行時にGateされるという設計を実現できなくなる

#### Reason for Rejection

呼び出し時のPolicy判断とTool単位の可用性フラグを混同するため不採用とした。両者を分離することは、既に実装されている現実であり、正しいモデルでもある。

## Consequences

### Positive Consequences

- Routing権威が明確になり、所有権の競合が防止される
- 未登録Toolの実行がFail-Closedで拒否される
- Safety TierとWrite属性がRouting、承認、監査で一致する
- 複数MCPサーバーのTool名重複が起動時に検出される
- 共有語彙（Defined/Discoverable/Owned/LLM-visible/Statically available/Dynamically available/Routable/Approved/Executable）により、将来のMCPサーバー実装およびAgent側Routing実装での誤用を防止しやすくなる
- Reload/再起動境界の明文化により、Config変更が既にLive Registryへ反映されたという誤った運用判断を防止する

### Negative Consequences

- Discovery失敗時にToolが実行されない
- 新Toolの追加にはDiscovery結果の更新が必要
- RuntimeToolRegistryの構築コスト
- 既存の静的定義依存のコードの修正

### Operational Consequences

- 起動時にDiscovery結果に基づいてRoutingが確定する
- RuntimeでのTool追加・削除は禁止
- Discovery由来の状態に影響する設定変更は、Agentプロセスの完全な再起動が必要であり、Reloadでは反映されない
- Health Checkへの影響：Discovery失敗時は起動中止
- 障害対応：Discovery失敗時は再起動が必要

### Security Consequences

- 信頼境界：Discovery結果のみがRouting権威
- 認証、認可：RuntimeToolRegistryがSafety Tierを一元管理
- Secretの取扱い：Discovery結果に基づく
- Fail-Open、Fail-Closed：未登録ToolはFail-Closed
- 静的可用性がLLM可視性を継続してGateすることで、Config駆動のSecurity Control（例：`read_only=true`）がDynamic Health信号によって弱められることを防止する
- Audit Log：Routing、承認、監査で同一Safety Tierを参照

## Invariants

- INV-01: 複数のMCPサーバーが同じTool名を公開した場合、Agentの起動を中止する。
- INV-02: `ToolRouteResolver.resolve()`は`RuntimeToolRegistry`のみを参照し、未知のTool名に対しては`ValueError`を即時発生させる。
- INV-03: Safety TierとWrite属性はRouting、承認、監査で同一の`RuntimeTool`を参照する。
- INV-04: 静的`ToolRegistry`は実行時Routingに使用せず、テスト・文書生成、および起動時Drift検証(`shared/tool_routing_validation.py`)の入力データに限定する（Decision Detail #15、2026-09-02追加）。
- INV-05: Defined、Discoverable、Owned、LLM-visible、Statically available、Dynamically available、Routable、Approved、Executableは別個の概念として扱い、単一の「有効/無効」へ統合しない。
- INV-06: 静的に無効化されたToolは、LLMへ実行可能として公開してはならない。
- INV-07: Dynamic Healthの状態は、`enabled_for_llm`等のLLM可視性を変更してはならない。
- INV-08: 承認要求状態は、無効化されたTool状態として表現してはならない。
- INV-09: Discoverable、Owned、Statically Available、またはRoutableであることは、そのToolが常にExecutableであることを意味しない。実行時にDynamic HealthまたはApprovalにより拒否され得る。

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

Dynamic HealthはCircuit Breakerによる CLOSED/OPEN/HALF_OPEN のTrial-Recovery Semanticsを実行層で用いる。本ADRはこの挙動を変更しない。

### Fallback Policy

該当なし

## Data Ownership and Persistence

- **System of Record**: `RuntimeToolRegistry`（起動時に`McpToolDiscoveryService`から取得したDiscovery結果）
- **Derived Data**: `ToolRegistry`（テスト・文書生成用）
- **Ownership**: `RuntimeToolRegistry`
- **Persistence**: メモリ上（プロセス単位、再起動で再構築）
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

- **Test**: 起動時Drift検証(config/live比較)が静的`ToolRegistry`を入力として使用し、`RuntimeToolRegistry`ベースのRouting判断自体を変更しないこと
  - **Verifies**: INV-04 (Decision Detail #15)
  - **Type**: Integration
  - **Blocking**: No（警告のみ。strictモード時は起動を中止するが、Routing判断そのものには影響しない）
  - **Test files**: `tests/agent/test_startup_routing_drift.py`, `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`, `tests/shared/test_tool_registry.py`, `tests/shared/test_tool_safety_tiers.py`

- **Test**: Routing、承認、監査が同一Safety Tierを参照すること
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 静的に無効化されたToolが`llm_tool_definitions()`に含まれないこと
  - **Verifies**: INV-06
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Circuit-Openなサーバーに属するToolが`llm_tool_definitions()`に残ること
  - **Verifies**: INV-07
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

- 将来のPRがDynamic Health駆動のコードパスから`enabled_for_llm`へ書き込むことで、静的可用性とDynamic Healthの分離を再び統合してしまわないことを確認する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- **実装ファイル**:
  - `scripts/shared/runtime_tool_registry.py`: `RuntimeToolRegistry`
  - `scripts/shared/route_resolver.py`: `ToolRouteResolver`
  - `scripts/shared/tool_registry.py`: `ToolRegistry`
  - `scripts/shared/runtime_tool.py`: `RuntimeTool`
  - `scripts/agent/services/mcp_tool_discovery.py`: `McpToolDiscoveryService`
  - `scripts/shared/mcp_health.py`: `McpServerHealthRegistry`（Dynamic Health、参照のみ）
  - `scripts/shared/tool_executor.py`: `ToolExecutor`（Dynamic Health/実行、参照のみ）
- **主要ClassまたはFunction**:
  - `RuntimeToolRegistry.resolve()`: Routing権威
  - `RuntimeToolRegistry.llm_tool_definitions()`: LLM可視Tool一覧
  - `RuntimeToolRegistry.apply_policy()`: Reload時のPolicy由来フィールド更新（Discovery由来フィールドは更新しない）
  - `ToolRouteResolver.resolve()`: RuntimeToolRegistryのみを参照
  - `ToolRegistry.get_all_tool_names()`: テスト・文書生成用
- **設定ファイル、設定Key**:
  - `config/agent.toml`の`[mcp_servers.*]`
  - `tool_constants.py`のfrozenset（テスト・文書生成用）
- **対応するテスト**:
  - `tests/unit/test_runtime_tool_registry.py`
  - `tests/unit/test_route_resolver.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

確認済みの差異なし

ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。Reload実行フロー全体がPolicy由来フィールドのみを更新することの実装検証状況については、Shared/DB Known Issuesの該当項目を参照。

## Review Triggers

次の条件が発生した場合、このADRを再評価する。

- 運用規模または同時実行数が大きく変化した場合
- 単一Hostから複数Hostまたは分散構成へ変更する場合
- Security要件、監査要件が変更された場合
- 性能目標またはResource制約が変更された場合
- 外部Protocolまたは採用Libraryが変更、廃止された場合
- 障害実績により前提またはFailure Policyが妥当でないと判明した場合
- 代替案の不採用理由が成立しなくなった場合
- MCPサーバーごとの必須性と失敗方針の変更（ADR-004と連動）
- RuntimeToolのフィールド定義の変更
- Agent再起動なしでのMCPサーバー追加・削除（Hot Reload/Rediscovery、Policy B）が要件となる場合
- 可用性計算を各MCPサーバー個別ではなく中央集約する設計へ変更する場合

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
- **Approval Reference**: ADR-003作成、ADR-013統合

## Related Documents

### Related ADRs

- ADR-001: Workflow Engineの必須化
- ADR-002: Config Isolation

### Specifications

- [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) — MCP Discovery and Routing
- [04_mcp_03_02_tool-registry.md](04_mcp_03_02_tool-registry.md) — Tool Registry Reference
- [04_mcp_03_06_tool-runtime-availability-metadata.md](04_mcp_03_06_tool-runtime-availability-metadata.md) — Tool Runtime Availability Metadata
- [05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md) — Agent Tool Execution
- [90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md](90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md) — Shared Runtime

### Operations

- 関係するRunbookまたはTroubleshooting Guide

### Known Issues

- [Shared/DB Known Issues](90_shared_90_inconsistencies_and_known_issues.md) — CI-003（Reload実行フロー全体の検証未了）、CI-015（Tool所有権重複検出のテスト未整備）

### Implementation References

- `scripts/shared/runtime_tool_registry.py::RuntimeToolRegistry`
- `scripts/shared/route_resolver.py::ToolRouteResolver`
- `scripts/shared/tool_registry.py::ToolRegistry`
- `scripts/shared/runtime_tool.py::RuntimeTool`
- `scripts/agent/services/mcp_tool_discovery.py::McpToolDiscoveryService`

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
- [x] 関係するSpecificationと矛盾していない
- [x] 現行実装との差異がKnown Issueへ登録されている
- [x] Ownerと必要なReviewerが定義されている
- [x] Review Triggersが記載されている
- [x] ADR索引と関係領域のDocument Guideへ登録されている
