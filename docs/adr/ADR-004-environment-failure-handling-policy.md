---
title: "ADR-004: 環境における障害処理方針"
area: adr
decision_scope:
  - system
related:
  - ADR-001
  - ADR-002
  - ADR-003
  - ADR-010
---

# ADR-004: 環境における障害処理方針

## Status

Accepted

## Summary

本ADRは、システムが稼働するすべての環境に対して単一の共通障害処理方針を定義する。環境名（Local、Development、Test、Productionなど、環境を区別するために用いられるいかなる名称も含む）は、起動検証、認証、認可、Allowlist強制、承認制御、Tool所有権要件、Routing要件、リソーススコープ検証、DB整合性要件、Workflow要件を変更しない。障害を「安全性・整合性障害」と「可用性障害」に分類し、安全性・整合性障害は常に起動時Fail-Fastまたは実行時Fail-Closedとする。必須コンポーネントの利用不能は起動を中止させるが、非必須コンポーネントの可用性障害に限り、そのコンポーネントを無効化したうえで部分的可用性の状態として起動継続を許可する。Fallbackは、他のAccepted ADRが発生条件・移行先・適格性・制限・結果の意味・観測可能性を明示的に定義する場合に限り許可される。ADR-010が定義するRAGフォールバックはこの唯一の例外である。

## Context

### Problem

環境名によって起動検証やFail-Fast／Fail-Closedの境界が変わってはならない。一方で、すべての依存コンポーネントを一律に起動必須として扱うと、コア処理に影響しない周辺コンポーネントの一時的な利用不能が全体の起動を妨げる。安全性・整合性に関わる障害は常に確実にFail-Fast／Fail-Closedとしつつ、コアの安全性・整合性を損なわないコンポーネントの可用性障害については、明示的な基準に基づいて起動継続を許可する必要がある。

### Constraints

- 単一ホスト、単一プロセスでの実行を前提とする
- デプロイ環境では起動前にワークフロー定義ファイルが存在することを確認する必要がある
- 外部Protocol、Library、Serviceによる制約はない
- セキュリティ要件：すべての副作用のある操作は追跡可能でなければならない
- データ整合性：承認状態はプロセス境界を超えて永続化する必要がある
- 環境名の選択や構成変更によって、安全性、検証、認証、認可、承認、Routing、データ整合性の要件が緩和されてはならない

### Assumptions

- 対象環境：単一Host、単一Agentプロセス
- 想定規模：同時実行数は限定的
- 信頼境界：Agentプロセス内でのみ権限を付与する
- 外部依存先：なし（ワークフロー定義はローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部ワークフローエンジン統合

## Decision

### Group 1: 環境共通ポリシー

1. システムは、稼働するすべての環境に対して単一の共通障害処理方針を用いる。環境ごとに異なる障害処理方針を定義しない。
2. 対象環境: システムが稼働するすべての環境。環境ごとの障害処理方針の差異は設けない。
3. 環境名は、起動検証、認証、認可、Allowlist強制、承認制御、Tool所有権要件、Routing要件、リソーススコープ検証、DB整合性要件、Workflow要件、Fail-Fast条件、Fail-Closed条件のいずれも変更しない。

### Group 2: 障害分類

4. 障害を「安全性・整合性障害」と「可用性障害」の2種類に分類する。この分類は、障害が起動全体に及ぶか特定コンポーネントに限定されるかという影響境界を判断するために用いるものであり、安全性または整合性要件を緩和する目的には用いない。
5. 安全性・整合性障害には、少なくとも次を含む: Tool所有権の重複、Workflow定義の欠落、Workflow定義の不正、必須DB Schemaの不整合、Config Isolation違反、認証設定の不正、認可設定の不正、Allowlist設定の不正、Safety Tier設定の不正、必須Secretの欠落、Tool引数Schemaの不正、リソーススコープ定義の不正、承認制御を確立できない状態、RuntimeToolRegistryの初期化失敗、Tool所有権の一意性を決定できない状態、安全なRouting先を決定できない状態、実行前提条件を検証できない状態、データ整合性障害。
6. 安全性・整合性障害は、次のいずれにも変換してはならない: 部分的可用性、警告のみでの継続、コンポーネント無効化後の実行継続、Fallback、成功扱いのNo-op。
7. 可用性障害には、MCPサーバーの利用不能、Embeddingサービスの利用不能、外部検索の利用不能、外部RAGサービスの利用不能、Observability出力先の利用不能、その他の依存先到達性の障害を含み得る。
8. 可用性障害は、それだけでは起動継続を許可しない。起動継続が許可されるのは、次のすべてを満たす場合に限る: 対象コンポーネントが非必須として明示的に分類されている、障害が当該コンポーネントに局所化されている、影響を受けるすべての機能を安全に無効化できる、いかなる安全性・整合性制御も緩和されない、結果として生じる部分的可用性の状態が観測可能である。

### Group 3: コンポーネント必須性分類

9. **必須コンポーネントの分類基準**: 次のいずれかに該当する場合、そのコンポーネントを必須として分類する。
   - システムのコア処理の開始または完了に必要である。
   - 認証、認可、承認、Routing、監査可能性、Config Isolation、永続化、データ整合性を確立する。
   - その欠落が操作の安全な拒否を妨げる。
   - その欠落が誤った成功結果を引き起こし得る。
   - コア処理に必要な正本状態を所有する。
   - あるAccepted ADRがそれを明示的に必須と定めている。
   - その障害を他の必須コンポーネントから安全に分離できない。
10. **非必須コンポーネントの分類基準**: 次のすべてが真である場合に限り、そのコンポーネントを非必須として分類できる。
    - その欠落が安全なコア処理を妨げない。
    - その欠落が認証、認可、承認、Routing、監査、Config Isolation、データ整合性のいずれの制御も迂回しない。
    - その障害を既知の機能集合へ局所化できる。
    - 関連する機能とToolを確実に無効化できる。
    - 当該機能を対象とする呼び出しをFail-Closedで拒否できる。
    - 無効化状態と影響を観測できる。
    - 他の必須コンポーネントが安全かつ内部的に整合した状態を維持する。
    - いかなるFallbackも、あるAccepted ADRによって明示的に定義されている。
11. 起動が技術的に可能であるという理由だけで、あるコンポーネントを非必須として扱ってはならない。
12. コンポーネントの必須性が未定義または判定不能な場合: 当該コンポーネントを非必須であると仮定しない。未定義の分類を起動継続の根拠として用いない。これを未解決の設計上または設定上の誤りとして扱う。該当する場合は、現行のKnown Issueを記録または参照する。
13. **分類の責任分担**: 本ADRは分類基準と障害処理契約を定義する。各コンポーネントの承認済み分類は、該当するStartup、Agent、またはMCPのSpecificationが記録する。設定は、承認済みSpecificationが許容する範囲内でのみ実効値を提供する。起動検証は、実効分類を起動継続の判断に用いる前に、それを検証する。設定だけで、承認済みのアーキテクチャまたはSpecification変更なしに、必須コンポーネントを非必須へ弱めることはできない。

### Group 4: 起動時Fail-Fast境界

14. 次の条件は起動時にFail-Fastとする（起動を中止する）。
    - Workflow定義の欠落
    - Workflow定義の不正
    - 必須DB接続の失敗
    - 必須DB Schemaの不整合
    - RuntimeToolRegistryの初期化失敗
    - Tool所有権の重複（Live Toolの重複所有）
    - 必須MCPサーバーの利用不能
    - 認証設定の不正
    - 認可設定の不正
    - Allowlist設定の不正
    - Safety Tier設定の不正
    - 必須Secretの欠落
    - Config Isolation違反
    - 承認制御を確立できない状態
    - 環境設定検証の失敗
    - 起動継続の判断が依存するコンポーネント必須性を決定できない状態

    すべての依存先障害が起動を停止させるわけではない。可用性障害であり、かつ対象コンポーネントが非必須として明示的に分類されている場合は、Decision #7に従い起動継続を許可し得る。現行の承認済みSpecificationで確認されない限り、すべてのMCPサーバーが必須であるとはみなさない。

### Group 5: 実行時Fail-Closed境界

15. 次の条件は実行時にFail-Closedとする（当該処理を拒否する）。
    - 不明なTool
    - 無効化されたTool
    - 利用不能なTool
    - Tool所有権の曖昧性
    - Tool引数の不正
    - 必須承認の欠落
    - 認証または認可の失敗
    - リソーススコープ検証の失敗
    - Allowlist検証の失敗
    - 実行前提条件を検証できない状態
    - 安全な実行先を決定できない状態
    - 無効化された非必須コンポーネントを対象とする要求
16. 拒否された操作は、失敗または拒否の結果を返さなければならない。成功扱いのNo-opへ変換してはならない。名前推測によるRoutingを行ってはならない。静的Registryへフォールバックしてはならない。あるAccepted ADRが明示的に許可しない限り、別のToolへリダイレクトしてはならない。観測可能な理由を記録しなければならない。

### Group 6: 必須コンポーネントの挙動

17. 必須コンポーネントが利用不能な場合: 起動を中止する。障害と理由を観測可能にする。当該コンポーネントを静かに無効化しない。あるAccepted ADRが明示的に許可しない限りFallbackを行わない。

### Group 7: 非必須コンポーネントの挙動

18. 非必須コンポーネントに可用性障害が生じた場合: 当該コンポーネントを無効化する。部分的可用性の状態でシステムの起動継続を許可する。当該コンポーネントのToolおよび機能を実行可能な公開対象から除外する。当該Toolまたは機能を対象とする新規呼び出しを拒否する。無効化状態を報告する。障害理由を報告する。影響を受ける機能を報告する。起動継続を許可した理由を報告する。現行の承認済みDiagnosticsおよび運用Observability機構を通じて状態を公開する。システムを完全に利用可能であるとは報告しない。
19. 同一コンポーネントに安全性・整合性障害が生じている場合、起動継続は禁止される。非必須として分類されていることは、安全性・整合性障害に対する免除にはならない。

### Group 8: 部分的可用性の観測可能性

20. 無効化状態、障害理由、影響を受ける機能、および起動継続の判断は、現行の承認済みDiagnostics、Health Check、およびログを通じて観測可能でなければならない。部分的可用性の状態にあるシステムを、完全に利用可能であると報告してはならない。

### Group 9: Tool可視性と実行境界

21. 無効化されたコンポーネントに関連付けられたToolは: LLMへ実行可能として提示してはならない。新規呼び出しに対してRouting可能であってはならない。実行可能であってはならない。観測可能な無効化理由を持たなければならない。
22. `RuntimeToolRegistry`、Tool所有権、Routing、静的可用性、Dynamic Health、LLM可視性、承認状態の分離、実行適格性、ReloadおよびRediscovery挙動については、引き続きADR-003が権威である。本ADRは、これらの概念がコンポーネントの必須性分類とどう関わるかという障害処理上の帰結のみを定義し、ADR-003の決定を再定義しない。
23. 静的`ToolRegistry`または`tool_names`によるDrift検証、静的RegistryへのRoutingフォールバック、名前推測によるRoutingを再導入しない。
24. コンポーネントが起動時の分類（非必須・可用性障害により無効化）によって利用不能である場合と、起動後にDynamic Healthにより動的に利用不能となった場合を区別する。前者はADR-003の「静的可用性」に関わる状態であり、LLM可視性とRouting適格性に影響する。後者はADR-003の「Dynamic Health」に関わる状態であり、実行時の成否にのみ影響し、LLM可視性を自動的に変更しない。ADR-003が定めるこの区別を本ADRにおいて統合・崩壊させない。

### Group 10: Fallback境界

25. Fallbackはデフォルトで禁止される。
26. Fallbackは、あるAccepted ADRが次のすべてを明示的に定義する場合に限り許可される: 発生条件（Failure Trigger）、Fallback先（Destination）、適格条件（Eligibility Conditions）、制限（Restrictions）、結果の意味（Result Semantics）、観測可能性要件（Observability Requirements）。
27. ADR-010は、承認済みの外部RAG→インプロセスRAGフォールバックの唯一の権威である。ADR-010は、そのRAG関連条件についてのみFallbackを許可し、一般的なFail-Open挙動を許可するものではない。通常の空RAG結果は、自動的にFallbackの契機とはならない。安全性・整合性障害は、可用性Fallbackの契機としてはならない。Fallbackは、認証、認可、承認、Allowlist、Routing、データ整合性のいずれの制御も迂回してはならない。

### Scope

- **対象コンポーネント**: `StartupOrchestrator`, `McpToolDiscoveryService`, `ProductionConfigValidator`, `McpServerHealthRegistry`
- **対象プロセス**: Agentプロセス全体
- **対象データ**: 起動チェック結果、MCPサーバー状態、Tool所有権情報、承認状態
- **対象環境**: システムが稼働するすべての環境。環境ごとの障害処理方針の差異は設けない。
- **対象APIまたは処理経路**: `StartupOrchestrator.run()`, `McpToolDiscoveryService.discover_all()`, `ProductionConfigValidator.validate()`

### Out of Scope

- 個別のMCPサーバーの障害検知詳細
- OTel出力先の障害検知詳細
- Health Checkや起動前検証など、Startup Orchestrator自身の前提確認
- 既存のStartupCheckStatus（OK/WARNING/FATAL/SKIPPED）の削除
- 既存のpipeline.add_fatal()/add_warning()の削除
- 個別コンポーネントの必須／非必須の具体的な割り当て（該当するSpecificationが定義する）
- 新しい設定キーまたは設定モデルの導入
- ADR-003が定義するRuntimeToolRegistry、Routing、可用性概念の再設計
- ADR-010が定義するRAG Fallbackの変更

## Rationale

### 1. 最重要の採用理由 — Security

安全性・整合性障害は常にFail-Fast（起動時）またはFail-Closed（実行時）とする。環境名の選択によってSecurity Controlが迂回されないようにするため。

### 2. 第2の採用理由 — Data Integrity

必須コンポーネントの利用不能を無条件に起動中止とすることで、正本状態の所有者やConfig Isolation・承認制御の確立者が欠けたまま処理が進行することを防ぐ。

### 3. 第3の採用理由 — Predictability

環境ごとに異なる障害処理方針を持たないことで、どの環境でも同じ条件が同じ結果（Fail-Fast/Fail-Closed/継続）を生むことを保証し、運用者の予測可能性を高める。

### 4. 第4の採用理由 — Availability

非必須コンポーネントの可用性障害まで一律に起動全体を中止すると、コアの安全性・整合性に影響しない機能まで不必要に停止する。明示的な基準の下でのみ部分的可用性を認めることで、必要な可用性を確保する。

### 5. 第5の採用理由 — Operability

コンポーネントの無効化・部分的可用性の理由を明示的に観測可能とすることで、利用不能な機能があたかも利用可能であるかのように見える状態を防ぎ、障害対応を容易にする。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Separate failure-handling policies per Environment Profile

#### Description

Local、Development、Productionなど、環境ごとに異なる障害処理方針（Fail-Fast条件やFail-Open許容範囲）を定義する。

#### Advantages

- 開発時の摩擦を減らせる

#### Disadvantages

- 環境ごとの挙動差異が、意図しない安全性の緩和を生み得る
- どの環境でどの保証が成立するかの予測が困難になる

#### Reason for Rejection

SecurityとPredictabilityを優先し、環境名によって保証が変わらない単一の共通方針を採用した。

#### Reconsideration Conditions

- 開発時の摩擦がAvailability上の重大な障害となる場合

### Alternative B: Treat every dependency as required

#### Description

すべての依存コンポーネントを一律必須として扱い、いずれかが利用不能な場合は常に起動を中止する。

#### Advantages

- 単純なルール
- 分類ミスのリスクがない

#### Disadvantages

- コア処理に影響しない周辺コンポーネントの一時的な障害でも起動全体が止まる
- 運用上の柔軟性が失われる

#### Reason for Rejection

Availabilityを優先し、コアの安全性・整合性に影響しないコンポーネントについては明示的な基準の下で部分的可用性を認めることとした。

#### Reconsideration Conditions

- 分類基準の運用コストが実際の可用性向上を上回ると判明した場合

### Alternative C: Continue startup after any dependency failure

#### Description

依存コンポーネントの種別を問わず、いかなる障害でも起動継続を許可する。

#### Advantages

- 起動の中断が最小化される

#### Disadvantages

- 安全性・整合性障害まで継続を許すことになり、Security上のリスクが著しく高い

#### Reason for Rejection

Securityを最優先し、安全性・整合性障害は常にFail-Fast／Fail-Closedとする。

#### Reconsideration Conditions

- 該当なし（安全性・整合性障害への継続許可は再検討しない）

### Alternative D: Allow only explicitly classified non-required components to be disabled

#### Description

本ADRが採用する方式。非必須として明示的に分類されたコンポーネントのみ、可用性障害時に無効化のうえ起動継続を許可する。

#### Advantages

- 分類基準が明示的であるため、恣意的な継続判断を防げる
- 安全性・整合性障害とは独立して扱える

#### Disadvantages

- 各コンポーネントの分類を維持するコストが発生する
- 分類の誤りが、必要な起動中止を妨げるか、または利用可能な機能を不必要に無効化する可能性がある

#### Reason for Rejection

不採用ではなく、本ADRの採用方式である。比較対象として記載する。

### Alternative E: Dynamic failure policy based on real-time risk assessment

#### Description

リアルタイムのリスク評価に基づいて障害方針を動的に変更する。

#### Advantages

- より柔軟な障害対応

#### Disadvantages

- 複雑な実装が必要
- リアルタイム評価の誤判定リスク
- 予測不可能な振る舞い

#### Reason for Rejection

PredictabilityとMaintainabilityを優先し、静的な分類基準で十分であると判断したため不採用とした。

#### Reconsideration Conditions

- リアルタイムリスク評価の精度が実証され、運用コストが許容範囲を超える場合

## Consequences

### Positive Consequences

- 単一の一貫した障害処理方針が全環境に適用される
- 環境名による安全性の緩和が発生しない
- 起動および実行の境界が予測可能になる
- 非必須コンポーネントのみが利用不能な場合、起動継続が可能になる
- 利用不能な機能が実行可能な公開対象から明示的に除外される
- 部分的可用性の状態が観測可能になる
- Fallbackが許可される条件が、他のAccepted ADRによる明示的な定義に限定される

### Negative Consequences

- コンポーネントの必須性を定義し維持する必要がある
- 分類の誤りは、不要な起動中止、または必須機能の不適切な無効化のいずれかを引き起こし得る
- 部分的可用性の実現にはDiagnostics、Health Check、ログの対応が必要になる
- 起動検証がより包括的になる
- すべての環境が同じ安全性要件を満たす必要がある
- 運用者は、可用性障害と安全性・整合性障害を区別して対応する必要がある

## Invariants

- INV-01: システムは、稼働するすべての環境に対して単一の共通障害処理方針を用いる。
- INV-02: 環境名は、安全性または検証要件を緩和しない。
- INV-03: Workflow定義が欠落または不正な場合、起動を中止する。
- INV-04: Tool所有権の重複が発生した場合、起動を中止する。
- INV-05: 必須DBの接続失敗またはSchema不整合が発生した場合、起動を中止する。
- INV-06: RuntimeToolRegistryの初期化に失敗した場合、起動を中止する。
- INV-07: 認証、認可、Allowlist、Safety Tier、Config Isolation、承認制御確立の失敗は、いずれも起動時にFail-Closed（Fail-Fast）とする。
- INV-08: 必須コンポーネントが利用不能な場合、起動を中止する。
- INV-09: 非必須コンポーネントは、可用性障害の場合に限り無効化できる。
- INV-10: 安全性・整合性障害は、部分的可用性に変換されない。
- INV-11: 無効化されたコンポーネントに関連するToolは、LLMへ実行可能として提示されない。
- INV-12: 無効化されたコンポーネントに関連するToolは実行できない。
- INV-13: 部分的可用性の状態とその理由は観測可能である。
- INV-14: コンポーネントの必須性が未定義の場合、起動継続を許可しない。
- INV-15: Fallbackは、他のAccepted ADRが明示的に定義する場合に限り許可される。
- INV-16: ADR-010は、承認済みRAG Fallbackの権威であり続ける。

## Verification

### Automated Tests

- **Test**: Workflow定義の欠落・不正で起動が失敗すること（`tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition`、`tests/agent/test_repl_health.py`の`check_workflow_definition()`関連テスト）
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed（実行してPass確認済み）

- **Test**: 必須DB Schema不整合で起動が失敗すること（`tests/agent/test_startup.py::test_aborts_on_missing_workflow_schema`）
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed（実行してPass確認済み）

- **Test**: Tool所有権重複で起動が失敗すること（ADR-003 Verification参照）
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed（ADR-003側で管理・検証）

- **Test**: RuntimeToolRegistry初期化失敗、必須DB接続失敗、認証/認可/Allowlist/Safety Tier/Config Isolation/承認制御確立の失敗が起動を中止させること
  - **Verifies**: INV-06, INV-07
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Needs confirmation — `tests/agent/shared/test_startup_validation_pipeline.py`はFATAL/WARNING集約の一般機構（`test_single_fatal_readiness_raises`等）を検証するが、各条件個別のシナリオテストは本タスクで個々に確認していない

- **Test**: 必須コンポーネント（必須MCPサーバー等）の利用不能が起動を中止させること
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: **未検証** — `scripts/agent/services/mcp_tool_discovery.py`の`is_required`分岐を直接検証する専用テストは見つからなかった。Known Deviations参照

- **Test**: 非必須コンポーネントの可用性障害が起動継続を許可し、当該コンポーネントが無効化されること
  - **Verifies**: INV-09
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: **未検証** — 同上。WARNING集約時に起動が継続する一般機構（`test_warnings_only_no_raise`）は存在するが、非必須コンポーネント分類に紐づく専用シナリオのテストは見つからなかった

- **Test**: 安全性・整合性障害が部分的可用性に変換されないこと
  - **Verifies**: INV-10
  - **Type**: Regression
  - **Blocking**: Yes
  - **Status**: Confirmed in code structure（`scripts/agent/startup.py`のWorkflow/Schema/Tool所有権チェックは`is_required`分岐を経由せず常にFATAL経路を通る）；この構造を直接横断的に検証する専用テストはない

- **Test**: 無効化されたコンポーネントに関連するToolが呼び出し拒否されること（`tests/mcp_servers/file/test_call_tool_validation.py`、file-mcpのみを対象とした限定的な検証）
  - **Verifies**: INV-11, INV-12
  - **Type**: Unit
  - **Blocking**: No
  - **Status**: Confirmed（file-mcp限定）

- **Test**: ADR-010で定義される場面以外でFallbackが発生しないこと
  - **Verifies**: INV-15, INV-16
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Needs confirmation（本タスクでは個別に再実行していない）

### Startup Validation

- 環境設定の検証（環境名によらず同一の検証項目を適用する）
- 各コンポーネントの実効必須性分類の検証
- 障害分類に基づく起動継続可否の判定

### Deployment Validation

- デプロイ前後に障害処理方針の設定を確認
- Fail-Fastが必須コンポーネントに対して有効になっていることを確認

### Runtime Monitoring

- Health Check：MCPサーバーのヘルスチェック
- Metrics：無効化されたコンポーネント・Toolの数
- Logs：障害分類の結果、起動継続理由、無効化理由
- Alert条件：安全性・整合性障害

### Manual Review

- 障害方針の変更レビュー
- コンポーネントの必須性分類の見直し
- INV-01（単一の共通障害処理方針）を直接検証する自動テストは存在しない
- INV-08・INV-09（必須／非必須コンポーネントの起動時挙動）を直接検証する自動テストは存在しない
- INV-14（未定義の必須性による起動継続禁止）は現行実装で強制されていない（Known Deviations参照）

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/agent/startup.py`, `scripts/shared/mcp_config.py`, `scripts/shared/production_config_validator.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/shared/mcp_health.py`
- 主要ClassまたはFunction: `StartupOrchestrator.run()`, `McpToolDiscoveryService.discover_all()`, `ProductionConfigValidator.validate()`, `McpServerHealthRegistry`
- 設定ファイル、設定Key: `config/agent.toml`
- 対応するテスト: `tests/agent/shared/test_startup_validation_pipeline.py`, `tests/agent/test_startup.py`
- `StartupOrchestrator`が構築する`StartupValidationResult`（`scripts/agent/shared/health_models.py`）は、プロセス起動ごとに再構築されるメモリ上の集約オブジェクトであり、`workflow.sqlite`等へ永続化されない。
- MCPサーバー到達不能時の現行の再試行は、固定遅延（`HEALTH_CHECK_RETRY_DELAY_SEC`）による単発の再試行であり、設定可能な試行回数を持つ汎用Retry Policyではない。

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

- **Known Issue [resolved]**: ADR-004-D1-profile-config-model-still-present — `scripts/shared/mcp_config.py`の`McpServerConfig`と`scripts/agent/services/mcp_tool_discovery.py`は、`security_profile`（環境）の値に基づいて`required_in_production`／`required_in_local`のいずれを参照するか分岐している。**現行の実効値**（`config/agent.toml`に上書き設定がなく、両フィールドともデフォルトの`True`）の下では、この分岐はすべての環境で同一の結果（Fail-Fast）を生むため、Decision #14（必須コンポーネント）とは矛盾しない。しかし、分類ロジック自体が環境の値を参照する構造は、「コンポーネントの必須性は環境に依存しない性質である」という本ADRの方針（Decision #1、#3）と整合しない。**影響**: INV-01, INV-02, INV-09, INV-14。— Resolved by REQ-001 through REQ-004: unified `required` field replaces `required_in_production`/`required_in_local`; `FailurePolicy` simplified to FAIL_FAST only.
- **報告のみ（Known Issue未登録）**: 非必須コンポーネントの可用性障害による起動継続（Decision #18、INV-09）、および未定義の必須性による起動継続禁止（Decision #12、INV-14）を検証する自動テストが現行では存在しない。また、コンポーネント単位の必須／非必須分類を記録する現行の承認済みSpecificationも存在しない（Decision #13が要求する分類記録の主体が未整備）。これらは新規Known Issueとして別途登録することを推奨する。

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
- コンポーネントの必須性分類ロジックが環境非依存へ改修された場合
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

承認者・承認日・承認参照は未確定である。本ADRをAcceptedとする判断は改訂作業の承認済み方針として与えられたものであり、この判断自体を承認記録の代用として扱わない。

## Related Documents

### Related ADRs

- ADR-001: Workflow Engine必須化 — Workflow定義の欠落・不正はFail-Fast
- ADR-002: プロセス単位の設定所有権とConfig Isolation — Config Isolation違反はFail-Fast
- ADR-003: RuntimeToolRegistryを唯一のルーティング権威とする — RuntimeToolRegistry初期化失敗はFail-Fast、Tool可視性・Routing・Dynamic Healthの権威
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
- `scripts/shared/mcp_health.py` — `McpServerHealthRegistry`
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
- [x] 検証可能なInvariantsが定義されている
- [x] 各InvariantにVerificationが対応している（一部はNeeds confirmation/未検証として明記）
- [ ] 自動化可能な検証がManual Reviewだけになっていない（INV-01, INV-08, INV-09, INV-14はManual Review/未検証のまま）
- [x] 既存ADRとの関係が記載されている
- [ ] 関係するSpecificationと矛盾していない（要再確認 — コンポーネント必須性分類を記録するSpecificationが現行では存在しない。Known Deviations参照）
- [x] 現行実装との差異がKnown Issueへ登録されている（一部は新規登録が必要、Known Deviations参照）
- [ ] Ownerと必要なReviewerが定義されている（Approval Recordはpendingのまま）
- [x] Review Triggersが記載されている
- [ ] ADR索引と関係領域のDocument Guideへ登録されている（別途確認が必要）
