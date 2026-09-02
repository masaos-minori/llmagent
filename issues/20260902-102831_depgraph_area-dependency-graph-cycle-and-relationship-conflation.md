# 依存関係グラフを関係種別ごとに分離し、循環禁止規則との矛盾を解消する

## Priority
High

**Mediumからの引き上げを提案する。** ユーザー提示の引き上げ条件のうち、以下2点が実装/文書の直接確認により該当することを確認したため：
- **正本競合の誤解決につながる**: Conflict Resolution Ruleが依存方向を正本(優先)判定に直接使用していることを確認済み（下記「確認済みの矛盾」参照）。
- **CIの循環検出が実質的に無効である**: 「実質的に無効」ではなく、循環検出ロジック自体が`tools/`配下・CI workflow・testsのいずれにも一切存在しないことを確認済み。

## 背景
`docs/00_governance_01_documentation-policy.md`「Area Dependency Graph」節と、`docs/00_governance_04_documentation-checks.md`「12. Area Dependency Graph Validation」節（Manual Checksの一部）に、内容が完全一致する依存関係グラフが重複定義されている（前者はリスト形式、後者はmermaid形式）。このグラフはOverview、Deployment、RAG、MCP、Agent、EventBus、Shared/DB、Governanceの8ノードを含み、直後に「Cycles prohibited: No circular dependencies allowed.」「Direction constraint: Dependencies only flow downward (Overview → Governance).」という制約が明記されている。

同じ`00_governance_01_documentation-policy.md`内には、別の節「Software Dependency Graph vs Documentation Reference Graph Separation」があり、「Governance文書はruntime componentを表さないためsoftware component dependency graphから除外され、software dependency graphはAgent、MCP Server、RAG、EventBus、Shared/DBのみを対象とする」と明記している。しかしこの「Software Dependency Graph」と、循環を含む「Area Dependency Graph」との関係（同一グラフの言い換えか、別グラフか）は文書のどこにも定義されていない。

## 問題
「Area Dependency Graph」は、少なくとも次の関係種別を区別なく同一の矢印表記で混在させている。
- Governanceから各領域への関係（ガバナンスポリシーの適用と推測されるが明示なし）
- Overviewから各領域への関係（文書参照または概観と推測されるが明示なし）
- RAG→Agent、MCP→Agent、Agent→EventBus等（実行時呼び出しを示唆するが明示なし）
- Deploymentから各領域への関係（配置・起動管理と推測されるが明示なし）

`A → B`が何を意味するかは、`00_governance_01_documentation-policy.md`にも`00_governance_04_documentation-checks.md`にも一度も明文化されていない。この結果、`Overview → Governance`（Overviewの一辺として記載）と`Governance → Overview`（Governanceの一辺として明記）が同一グラフに両方存在し、直接2ノード循環となっている。これは同じ節内の「Cycles prohibited」「Direction constraint: ... (Overview → Governance)」という記述と直接矛盾する。

さらに、このグラフは以下の用途に使われていることを文書上で確認した。
- Change Impact Rule（`00_governance_01_documentation-policy.md` 198-206行）／Change Impact Assessment（`00_governance_04_documentation-checks.md` 310-317行、ほぼ同一内容の重複記述）: 「area dependency graphを使って変更の影響領域をマッピングする」と明記。
- Conflict Resolution Rule（`00_governance_01_documentation-policy.md` 141-148行）: ルール3で「文書がエリアをまたぐ場合、dependency directionに基づいてどちらのエリアの仕様が優先するか確認する」と明記——依存方向を正本(優先)判定に直接使用している。

循環を含み、かつ複数の関係種別が混在したグラフを、正本競合の解決や変更影響分析にそのまま使うと、誤った優先順位判定や影響漏れを招きうる。

## 確認済みの矛盾

| # | 内容 | 根拠ファイル・箇所 | 確度 |
|---|---|---|---|
| 1 | `Overview → Governance`と`Governance → Overview`が同一グラフに併記され、直後の「Cycles prohibited」「Direction constraint」と矛盾する | `00_governance_01_documentation-policy.md` 286行目・292行目（Area Dependency Graph節）、`00_governance_04_documentation-checks.md` 194行目・213行目（同一内容のmermaid版） | 確定（文書に明示、両辺が同一箇所に併記） |
| 2 | 上記と完全一致するグラフが2文書に重複定義されている（内容は同一、表記形式のみ異なる） | 上記2ファイル | 確定 |
| 3 | Conflict Resolution Ruleが依存方向を正本(優先)判定に使用している | `00_governance_01_documentation-policy.md` 147行目 | 確定 |
| 4 | Change Impact Rule/Assessmentが、循環を含む方のarea dependency graphを変更影響分析に使うと明記している | `00_governance_01_documentation-policy.md` 203行目、`00_governance_04_documentation-checks.md` 312行目 | 確定 |
| 5 | 「Software Dependency Graph vs Documentation Reference Graph Separation」節がGovernance・Overview・Deploymentを除外した別のノード集合（Agent/MCP/RAG/EventBus/Shared-DBのみ）を定義しているが、「Area Dependency Graph」との関係が一度も明示されていない | `00_governance_01_documentation-policy.md` 234-238行目 | 確定（分離の実効性はNeeds Confirmation） |
| 6 | `00_governance_04_documentation-checks.md`のGovernance Verification Matrix自身が、GV-015「Software vs Documentation dependency graph separation」をMethod=Manual, Status=**Missing**, Follow-up=「Register Known Issue」と自己申告しているが、対応するKnown Issueは登録されていない（`issues/`・`issues/done/`検索で該当なし） | `00_governance_04_documentation-checks.md` 287行目 | 確定 |
| 7 | GV-016「未実装の自動検査を実装済みと記載しない」という規則自体もStatus=Missingであり、この種の矛盾を検出する仕組み自体が機能していない | `00_governance_04_documentation-checks.md` 288行目 | 確定 |
| 8 | `tools/`配下の全24ファイル（`check_docs_quality.py`, `check_docs_consistency.py`, `check_docs_structure.py`を含む）のいずれにも、依存グラフの読込・循環検出ロジックは存在しない | 各ツールのソース確認（fork調査） | 確定 |
| 9 | `.github/workflows/`配下のいずれのworkflowにも依存グラフ循環検出のstepがなく、`tests/`配下にも該当テストが存在しない | `.github/workflows/governance-docs-consistency.yml`, `ci.yml`ほか、tests/全体grep | 確定（ただし`*-docs-consistency.yml`のうちgovernance/ci以外は中身を精査していないものが一部残る） |
| 10 | 実際に`uv run python tools/check_docs_structure.py`を対象文書に対して実行しても、循環とは無関係な既存の別issue（`01_overview.md`のKeywords節欠落）のみが検出され、循環自体は検出されない | 実行結果（fork調査） | 確定 |
| 11 | 文書が主張する`RAG → EventBus`、`MCP → EventBus`、`Agent → EventBus`という3辺について、Agent/MCP/RAGのいずれのコードにもEventBusパッケージへの直接import、HTTP publish呼び出しは存在しない（grep 0件） | `scripts/agent/`, `scripts/mcp_servers/`, `scripts/rag/`全体grep（fork調査＋筆者による追加確認） | 確定（実装側の欠落。文書側の意図がruntime依存以外である可能性も残るためNeeds Confirmation） |
| 12 | `docs/adr-index.md`に別の「ADR Dependency Graph」（ADR間の参照関係）が存在し、そこでも自己申告済みの循環（CDR-1: ADR-005↔ADR-009、CDR-2: ADR-003↔ADR-007）が「governance frameworkの循環禁止規則に違反する」と明記されたまま未解決で残っている | `docs/adr-index.md` 40-58行目 | 確定（Area Dependency Graphとは別グラフ。循環禁止規則の実効性が別の場所でも既に破られている根拠として言及） |

## 根本原因
「依存」という一つの矢印表記に、実行時呼び出し・デプロイ管理・文書参照・ガバナンス適用・変更影響伝播・正本優先という異なる意味論を区別せず重ねてしまったことが根本原因である。特に「Governanceは全領域に適用される」という事実（ガバナンス適用関係）と「Overviewは概観として各領域を参照する」という事実（文書参照関係）を、実行時依存と同じ「循環禁止・一方向」という制約が課された単一グラフに押し込んだ結果、Overview⇄Governanceという構造的に不可避な相互参照（概観文書はガバナンス方針の存在を前提とし、ガバナンス文書は全体像としてOverviewを参照する）が「循環」として現れてしまっている。加えて、この重複定義・自己矛盾を検出する自動検査が一切実装されておらず、文書自身がその欠落（GV-015, GV-016）を認識しながら追跡していない。

## 影響
- **循環検出**: 現在の定義のまま循環検出を実装した場合、Overview⇄Governanceで必ず失敗する。逆に言えば、現在この検査が存在しないため、この矛盾は放置され続けている。
- **変更影響分析**: Change Impact Rule/Assessmentが循環・関係種別混在のグラフをそのまま使う設計になっており、Governance関連の変更やOverview関連の変更で誤った影響範囲が算出されるおそれがある。
- **正本競合の解決**: Conflict Resolution Ruleが依存方向を正本判定に使うと明記しているため、実行時依存ではない辺（Governance→各領域等）を根拠に、誤って「どちらの仕様が優先するか」を判定してしまう可能性がある。
- **文書更新対象の決定**: 混在したグラフに基づく限り、実際には関係のない領域の文書まで更新対象として誤って含める、または逆に本来更新すべき領域を見落とす可能性がある。
- **レビューゲート**: Review Gate Conditions（`00_governance_04_documentation-checks.md`）は「3領域以上に影響する変更」等をトリガーとしており、影響領域の算出元が同じarea dependency graphである以上、同様の誤判定リスクを引き継ぐ。
- **AIエージェントによる文書選択**: 本プロジェクトのAI運用ルール（`AGENTS.md`/`routing.md`）はタスクに応じたdocs参照を前提としており、Change Impact Ruleに基づく参照文書選択が同じグラフに依存する場合、誤った文書を正本として選択するリスクがある。
- **CIの信頼性**: 循環禁止・分離要件を謳いながら検証手段が皆無であるため、「ドキュメントが定めるルール」と「実際に強制されているルール」の乖離が固定化されている。

## 対象範囲
- `docs/00_governance_01_documentation-policy.md`の「Area Dependency Graph」節、「Software Dependency Graph vs Documentation Reference Graph Separation」節、「Conflict Resolution Rule」節、「Change Impact Rule」節
- `docs/00_governance_04_documentation-checks.md`の「12. Area Dependency Graph Validation」節、「Governance Verification Matrix」（GV-015, GV-016）、「Change Impact Assessment」節
- 上記2文書間の重複定義の統合（`00_governance_03_issue-and-uncertainty-management.md`の先例パターンに倣い、正本を一つに定める）
- Software Runtime Dependency Graph、Deployment Management Graph、Documentation Reference Graph、Governance Applicability Matrix、Change Impact Rule/Matrixの再定義（下記「解決方針」参照）
- 依存関係循環検出の自動化（対象範囲：Software Runtime Dependency Graphのみ。Documentation Reference Graphの循環検出は別ロジックとして分離実装する）

## 対象外
- `docs/adr-index.md`の「ADR Dependency Graph」自体の循環（CDR-1: ADR-005↔ADR-009、CDR-2: ADR-003↔ADR-007）の解消——これはArea Dependency Graphとは別グラフ・別問題であり、本Issueでは扱わない。ただし関連する既知の未解決事項として「関連文書」に記録する。
- `scripts/rag/`と`scripts/mcp_servers/rag_pipeline/`の関係の詳細調査（両者が同一RAG機能の異なる実装なのか、意図的に分離された別モジュールなのかは本調査で確定できなかった）——別途調査が必要な独立した論点であり、依存グラフの構造修正そのものには必須ではないため対象外とする。
- EventBusへの実際のpublish経路の特定——Agent/MCP/RAGのいずれからも呼び出しが確認できなかったため、これが「未実装機能」なのか「文書の誤り」なのかの判断はNeeds Confirmationとし、本Issueの解決方針（関係種別の分離）はこの判断結果を待たずに進められる。
- 個別MCPサーバー間の呼び出し関係の網羅的な再調査（本Issueは Area/領域単位のグラフを対象とし、領域内部の詳細設計には立ち入らない）。

## 調査結果

### 1. 現在定義されている依存関係グラフの正確なノードと辺
「Area Dependency Graph」（`00_governance_01_documentation-policy.md`・`00_governance_04_documentation-checks.md`に同一内容で重複定義）:

| 始点 | 終点 |
|---|---|
| Overview | Deployment, RAG, MCP, Agent, EventBus, Shared/DB, Governance |
| Deployment | RAG, MCP, Agent, EventBus, Shared/DB |
| RAG | Agent, EventBus |
| MCP | Agent, EventBus |
| Agent | EventBus, Shared/DB |
| EventBus | Shared/DB |
| Governance | Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB |

別に、「Software Dependency Graph vs Documentation Reference Graph Separation」節はGovernanceを除外し、ノード集合をAgent/MCP Server/RAG/EventBus/Shared-DBのみとする方針を文章で述べているが、辺の一覧は定義されていない。

さらに別に、`docs/adr-index.md`の「ADR Dependency Graph」はADR単位の参照関係（例: `ADR-002 → ADR-001, ADR-003, ...`）を定義しており、Area Dependency Graphとは対象・粒度が異なる。

### 2. 各グラフで`A → B`が何を意味しているか
**いずれの文書にも明文化されていない。** Needs Confirmationとして扱う（後述）。

### 3. 明示的または推移的な循環が存在するか
- 直接循環: `Overview ⇄ Governance`（確定）。
- 3ノード以上の推移的循環: 今回確認した範囲（Deployment/RAG/MCP/Agent/EventBus/Shared-DBの辺）では検出されなかった。これらのノードはGovernanceを経由しない限り循環しない一方向の構造になっている。
- 別グラフ（ADR Dependency Graph）に既知の循環2件（CDR-1, CDR-2）が既に自己申告されている（対象外だが関連事実として記録）。

### 4. Overview、Deployment、Governance、Securityがruntime componentとして扱われているか
実装コード（`scripts/`配下）を確認した結果、Overview・Governanceに対応するモジュール・パッケージ・プロセスは一切存在しない（`find`で0件）。Deploymentは`deploy/deploy.sh`によるファイル配置・起動スクリプト設置のみで、Python importや実行時呼び出しを含まない——runtime dependencyではなく管理関係である。Security（文書としての領域）については本調査で個別のruntime実体確認は行っていない（Needs Confirmation）。

### 5. Software Dependency GraphとDocumentation Reference Graphが実際に分離されているか
文書上は分離を謳っているが（`00_governance_01_documentation-policy.md`234-238行）、以下の理由で実効性がない、またはNeeds Confirmationである。
- 「Software Dependency Graph」という名称の辺一覧がどこにも定義されていない（ノード集合の記述のみ）。
- Change Impact Rule/Conflict Resolution Ruleが参照するのは「area dependency graph」であり、これが「Software Dependency Graph」と同一なのか、循環を含む方の「Area Dependency Graph」なのかが不明——後者を指している可能性が高い（名称が完全一致するため）。
- GV-015自身が「Software vs Documentation dependency graph separation」をStatus=Missingと自己申告している。

### 6. Area Dependency Graphが各処理にどう使われているか
| 処理 | 使用が文書上明記されているか | 根拠 |
|---|---|---|
| 変更影響分析 | 明記あり | Change Impact Rule/Assessment |
| 文書更新対象の特定 | 明記あり（Change Impact Ruleの一部として） | 同上 |
| 正本競合の解決 | 明記あり | Conflict Resolution Rule |
| レビュー対象の決定 | 間接的に関連 | Review Gate Conditions（影響領域数を判定基準に使用） |
| CIによる循環検出 | **実装なし** | 確認済み（tools/, CI workflow, tests全て0件） |
| AIエージェントによる参照文書選択 | 直接の明記はないが、`routing.md`/`AGENTS.md`のタスク別docs参照方針と同種の仕組みに波及しうる | Needs Confirmation |

### 7. 依存方向が実装上の呼び出し方向と一致しているか
| 文書上の辺 | 実装確認結果 | 一致/不一致 |
|---|---|---|
| Agent（の一部としてのMCP呼び出し方向、文書には明示辺なし） | Agent→MCP（HTTPで確認） | 文書に対応する辺自体が存在しないため評価不能 |
| RAG → Agent | Agent↔RAG間の直接import関係は0件。AgentはRAG機能を`mcp_servers/rag_pipeline`（別MCPサーバー）経由で利用 | **文書の辺と実装が一致しない可能性が高い**（Needs Confirmation） |
| MCP → Agent | 実装はAgent→MCPの一方向のみ確認（Agent→MCPのHTTP呼び出し、逆方向のimportは0件） | **文書の辺（MCP→Agent）と実装（Agent→MCP）が逆転している可能性** |
| Agent → EventBus, RAG → EventBus, MCP → EventBus | 実装上、EventBusパッケージへのimport/HTTP呼び出しはAgent/MCP/RAGのいずれにも0件 | **実装での裏付けなし**（Needs Confirmation: 未実装機能か文書の誤りか） |
| Agent → Shared/DB | 一致（Agent, RAG, MCPいずれも`scripts/db`を直接import） | 一致 |
| Deployment → 各領域 | Deploymentは実行時呼び出しを行わない配置関係 | 文書の矢印がruntime dependencyを意味するなら不一致（関係種別の相違） |

### 8. 既存の自動検査が矛盾を検出または見逃しているか
`tools/check_docs_structure.py`、`check_docs_consistency.py`、`check_docs_quality.py`を含む`tools/`配下の全ツール、CI workflow、testsのいずれにも依存グラフの読込・循環検出ロジックが存在せず、この矛盾は構造的に見逃され続けている。「Area Dependency Graph Validation」は文書内で正しく「Manual Checks」に分類されており（Automated Checksには含まれない）、「自動検査済みと文書に書いてあるのに実装がない」という虚偽表示ではないが、Manual Checkとして実施された形跡（Known Issue登録等）もない。

## 解決方針
ユーザー提示のA〜E案を評価した結果、**すべてを採用する（単一案の選択ではなく、関係種別ごとの分離そのものが解決策）**。

- **A. Software Runtime Dependency Graph**: 対象はAgent, MCP, RAG, EventBus, Shared/DB。矢印`A→B`は「Aが実行時にBを呼び出す、またはBの機能・データを必要とする」と明文化する。Overview, Deployment, Governanceは除外する。循環禁止をこのグラフにのみ適用する。ノード・辺は本Issueの「調査結果 7」で確認した実装上の呼び出し方向（Agent→MCP、Agent→Shared/DB等）に基づいて再構成し、EventBus関連の辺は実装確認ができるまでNeeds Confirmationとして保留する。
- **B. Deployment Management Graph**: Deploymentが各コンポーネントを配置・設定・起動・停止・検証する関係として分離する。循環検出の対象にしない。
- **C. Documentation Reference Graph**: 文書間リンクを表す。通常の相互参照（Overview⇄Governance等の文書参照）は許容し、リンク切れ・自己参照・重複参照・正本参照循環・AI文書選択を不定にする循環のみ個別に検査する。
- **D. Governance Applicability Matrix**: Governanceから各領域への関係を依存辺ではなくマトリクスで表現する。
- **E. Change Impact Rule/Matrix**: 変更種別ごとに使用する関係を定義する（runtime behavior変更→Runtime Dependency Graph、config変更→Configuration Ownership Map、API変更→API Consumer Map、governance変更→Governance Applicability Matrix、document-only変更→Documentation Reference Graph）。Configuration Ownership MapとAPI Consumer Mapは本Issューの調査範囲外で新規に必要となる可能性があり、その要否はNeeds Confirmationとする。

Conflict Resolution Ruleからは、依存方向による正本判定（現行ルール3）を削除し、正本は判断対象ごとに個別の正本源（Accepted ADR／API Schema／Schema Generator or DDL／実装コード／Specification and Tests／配備済み設定／Operations or Runbook）で決定する方式に置き換える。

## 実装タスク
- [ ] Software Runtime Dependency Graphを定義する（対象: Agent, MCP, RAG, EventBus, Shared/DB）
- [ ] Runtime GraphからOverview、Deployment、Governanceを除外する
- [ ] `A → B`の意味を明文化する（Runtime Graph、Deployment Management Graph、Documentation Reference Graphそれぞれについて個別に定義する）
- [ ] Deployment Management Graphを分離する
- [ ] Documentation Reference Graphを分離する
- [ ] Governance Applicability Matrixを作成する
- [ ] Change Impact Ruleが使用するグラフを変更種別ごとに定義する
- [ ] Conflict Resolution Ruleから依存方向による正本判定を除外し、判断対象ごとの正本源を明記する
- [ ] `Documentation Policy`と`Documentation Checks`の重複するグラフ定義（Area Dependency Graph / Area Dependency Graph Validation）を一つの正本へ集約する
- [ ] runtime dependencyの循環検出を実装する（対象: Software Runtime Dependency Graphのみ）
- [ ] 文書参照検査をruntime循環検査から分離して実装する
- [ ] 既存の矛盾する記述（Overview⇄Governance循環を含む現行のArea Dependency Graph定義）を削除または修正する
- [ ] GV-015・GV-016のStatusをMissingのまま放置せず、本Issueの対応状況に応じて更新する

## 文書更新タスク
- [ ] `docs/00_governance_01_documentation-policy.md`: 「Area Dependency Graph」節を新グラフ体系（A〜E）へ置き換える。「Software Dependency Graph vs Documentation Reference Graph Separation」節と統合し、矛盾のない単一の記述にする。Conflict Resolution Ruleのルール3を修正する。Change Impact Ruleを変更種別ごとのグラフ参照に更新する。
- [ ] `docs/00_governance_04_documentation-checks.md`: 「12. Area Dependency Graph Validation」節（mermaid版）を`00_governance_01_documentation-policy.md`と重複させず、どちらか一方を正本として他方から参照する形に修正する。Governance Verification MatrixのGV-015・GV-016のStatusを更新する。Change Impact Assessment節を`00_governance_01_documentation-policy.md`のChange Impact Ruleとの重複排除も含めて更新する。
- [ ] 新設するGovernance Applicability Matrix、Deployment Management Graph、Documentation Reference Graphの記述場所を決定し、追加する（既存文書内の新セクションか新規文書かはNeeds Confirmation）。
- [ ] `docs/adr-index.md`の「ADR Dependency Graph」既知の循環（CDR-1, CDR-2）について、本Issueとは別のKnown Issueとして登録することを推奨する旨を関連文書として記録する（本Issueでは解消しない）。

## テストおよび自動検査
- Software Runtime Dependency Graphの循環検出を行う新規ツール（`tools/`配下）を追加する。既存の`check_docs_quality.py`/`check_docs_consistency.py`/`check_docs_structure.py`のいずれにも依存グラフ検査ロジックが存在しないことを確認済みであるため、新規スクリプトとして追加するか、既存ツールの拡張とするかは実装時に判断する。
- 追加した循環検出ツールをCI workflow（`governance-docs-consistency.yml`または新規workflow）に組み込む。
- Documentation Reference Graphの循環検査（リンク切れ・自己参照・重複参照・正本参照循環）は、上記のruntime循環検査とは別のロジック・別のtest/CI stepとして実装し、誤って同一の循環検出として扱わないようにする。
- `docs/00_governance_03_issue-and-uncertainty-management.md`のNeeds Confirmation運用に倣い、本Issueの調査で判明したNeeds Confirmation項目（下記）を同インベントリへ登録する。
- 修正後、`uv run python tools/check_docs_quality.py`・`uv run python tools/check_docs_structure.py`・`uv run python tools/check_needs_confirmation_inventory.py`が新たな問題を報告しないことを確認する。

## Needs Confirmation
- `A → B`が実行時依存・ガバナンス適用・文書参照のいずれを意味するか、現行のArea Dependency Graphには一度も明文化されていない。新グラフ体系の設計はオーナー確認のうえで確定する。
- `RAG → EventBus`、`MCP → EventBus`、`Agent → EventBus`という3辺が、実装未着手の設計意図なのか、文書の誤りなのか。実装コード（Agent/MCP/RAG）にEventBusへの呼び出しが一切確認できなかった。
- `scripts/rag/`（crawler/chunk_splitter/ingester/pipeline.py）と`scripts/mcp_servers/rag_pipeline/`が同一RAG機能の異なる実装なのか、意図的に分離された別モジュールなのか。
- MCP→Agentという文書上の辺（明示的にはAgent→MCPのみ確認）が実装と逆方向である可能性——文書の意図（例えば「MCPの障害通知がAgentへ影響する」等の非runtime的な意味）を確認する必要がある。
- Security（文書としての領域）がruntime componentとして扱われるべきか、Governanceと同様に除外すべきか、本調査では個別確認していない。
- Configuration Ownership Map、API Consumer Mapという、Change Impact Rule再設計（E案）が前提とする新しいマップが、本Issueの範囲で新規に定義すべきものか、既存の何らかの文書に相当するものが既にあるか。
- 新設するGovernance Applicability Matrix等の記述場所（既存文書内の新セクションか新規文書か）。
- `*-docs-consistency.yml`のうち`governance`・`ci.yml`以外のworkflow（`agent-docs-consistency.yml`等）の中身は未精査であり、依存グラフ関連のstepが存在しないことは governance/ci.yml でのみ確認済みである。

## 完了条件
- 本Issueの「実装タスク」「文書更新タスク」「テストおよび自動検査」に記載した全項目が完了していること。
- 新設した各グラフ・マトリクスについて、ノード・辺・矢印の意味・循環可否が明文化されていること。
- 既存の矛盾する記述（Overview⇄Governance循環を含む現行定義）が文書上に残っていないこと。
- 未確認事項がすべてNeeds Confirmationインベントリへ登録されていること。

## 受入条件
- [ ] `Overview → Governance → Overview`の循環がruntime dependency graphに存在しない
- [ ] GovernanceがSoftware Runtime Dependency Graphに含まれていない
- [ ] OverviewがSoftware Runtime Dependency Graphに含まれていない
- [ ] DeploymentがSoftware Runtime Dependency Graphに含まれていない
- [ ] すべてのグラフでノード、辺、矢印の意味、循環可否が定義されている
- [ ] Runtime Dependency Graphが実装上の呼び出し方向と一致している（本Issue調査結果7の不一致・Needs Confirmation事項が解消されていること）
- [ ] Runtime dependencyの循環検出がCIで実行される
- [ ] Documentation Reference Graphの循環をruntime dependencyの循環として誤検出しない
- [ ] Governanceの適用関係が依存辺ではなくApplicability Matrixで管理されている
- [ ] Change Impact Ruleが変更種別ごとに使用するグラフを定義している
- [ ] Conflict Resolution Ruleがruntime dependencyを正本優先順位として使用していない
- [ ] `Documentation Policy`と`Documentation Checks`に矛盾するグラフ定義が残っていない
- [ ] 関連する文書検査とテストが成功する
- [ ] 未確認事項はNeeds Confirmationへ登録されている

## 関連文書
- `docs/00_governance_01_documentation-policy.md` — Area Dependency Graph、Software Dependency Graph vs Documentation Reference Graph Separation、Conflict Resolution Rule、Change Impact Rule
- `docs/00_governance_04_documentation-checks.md` — Area Dependency Graph Validation、Governance Verification Matrix（GV-015, GV-016）、Change Impact Assessment
- `docs/00_governance_03_issue-and-uncertainty-management.md` — Needs Confirmationインベントリの登録先（本Issueの未確認事項を登録する際の先例）
- `docs/00_index.md` — ADR Indexへのリンク元
- `docs/adr-index.md` — 別グラフ「ADR Dependency Graph」と既知の未解決循環（CDR-1, CDR-2）。本Issueの対象外だが、循環禁止規則の実効性という観点で関連する
- `docs/01_overview.md` — Area Dependency Graphの「Overview」ノードに対応する文書（既存の別問題としてKeywords節欠落を確認済み、本Issueとは無関係）
- `.github/workflows/governance-docs-consistency.yml` — 依存グラフ検査stepが存在しないことを確認したCI workflow

## Implementation Target Files
存在を確認済みのファイルのみを記載する。

- `docs/00_governance_01_documentation-policy.md`
- `docs/00_governance_04_documentation-checks.md`
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/00_index.md`
- `docs/01_overview.md`
- `docs/adr-index.md`
- `docs/04_mcp_00_document-guide.md`
- `docs/05_agent_00_document-guide.md`
- `docs/03_rag_00_document-guide.md`
- `docs/06_eventbus_00_document-guide.md`
- `docs/90_shared_00_document-guide.md`
- `.github/workflows/governance-docs-consistency.yml`
- `tools/check_docs_structure.py`（新規循環検出ロジックの追加先候補、または新規ツール作成の判断材料として参照）
- `tools/check_docs_consistency.py`（同上）
- `tools/check_docs_quality.py`（同上）
