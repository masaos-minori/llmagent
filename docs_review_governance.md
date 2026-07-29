# Governance領域 設計文書レビュー報告書

対象: `docs/00_governance_01` 〜 `docs/00_governance_08`、`docs/00_index.md`(全9ファイル)

---

## 1. 全体評価

### 連結文書としての問題

- 9ファイル全体を通して「一元管理」を掲げる仕組み自体が内部で機能不全を起こしている。具体的には、Needs Confirmationの必須フィールド定義(`docs/00_governance_03_evidence-labels.md`)と集中インベントリの実フィールド構成(`docs/00_governance_07_needs-confirmation-inventory.md`)が一致せず、さらに`docs/00_governance_05_deprecated-items.md`が抱える4件のNeeds confirmation項目が07のインベントリに1件も収載されていない。「一元管理する」という文書の主張と実態が矛盾している。
- `docs/00_governance_08_known-issues-migration-plan.md`は移行計画書の体裁のまま、実際には2026-07-23付けで対象5ファイル全ての移行が完了済み(各ファイルの「移行ノート」で確認)。実装完了後に文書が更新されず取り残される、という運用上の見落としパターンが起きている。

### 重複している情報の傾向

- テンプレート的重複: 「Related Governance Documents」リンク一覧が`docs/00_governance_01`〜`07`の7ファイルほぼ完全に重複。
- 一覧の重複: 対象領域8種の列挙が`docs/00_governance_01`(In scope)と`docs/00_governance_04`(Area Values)で重複。
- ファイルパス列挙の重複: `docs/00_governance_08`のTarget Filesと`docs/00_index.md`の「既知の問題」セクションが同一5ファイルを列挙。
- frontmatter重複: `docs/00_index.md`の本文中「Related Documents」「Keywords」がfrontmatterの`related`/`tags`と完全一致。

### コード説明に寄りすぎている領域

- Governance領域全体としてコードの転記に類する記述は少ないが、`docs/00_governance_06_ai-reading-metadata.md`のRecommended Additional Fieldsにある8個の個別YAMLスニペットは、直後のUsage Examplesと重複した機械的な列挙であり、コード的な冗長性に相当する。

### 意図・境界・運用注意として残すべき領域

- `docs/00_governance_01`のDocument Classes/Update Rule/Change Impact Rule
- `docs/00_governance_02`のGeneral Rule(正本判断の3階層)/Code vs Document Conflict Rule
- `docs/00_governance_03`のEvidence Labels 1〜7とHandling Ambiguous Cases
- `docs/00_governance_04`のKnown Issue Entry Template/Lifecycle
- `docs/00_governance_05`のDeprecated管理方針(削除ではなく参照維持)
- `docs/00_governance_07`のNC-001〜017個別項目とExtraction Process
- `docs/00_index.md`の推奨読書順序

### 再構成の基本方針

1. リンク一覧・Area一覧は`docs/00_governance_01`を正本とし、他ファイルは参照一行に置き換える。
2. Needs Confirmationの必須フィールド定義(03)と集中インベントリの実フィールド(07)を一本化し、05の未収載項目を07へ統合する。
3. `docs/00_governance_08`は移行完了の事実を反映し、完了報告への書き換えまたは廃止扱いを明示する。
4. `docs/00_governance_06`はAI reading metadataという主題にスコープを絞り、Markdown記法ルールと「実装参照で確認できる情報の記載方針」は`docs/00_governance_01`側に移設または参照させる。
5. `docs/00_index.md`のfrontmatter重複本文を削除し、128行目のファイル名誤記(`-part1`)を修正する(これは推測ではなく`ls`で存在確認済みの確定誤り)。

---

## 2. 削除候補

### 削除候補: docs/00_governance_06_ai-reading-metadata.md / Recommended Additional Fields内の個別YAMLスニペット8件

- 現在の記述の問題: 各1行のYAMLスニペット(例: `scope: agent`)が8個個別に列挙されている。
- 削除理由: 直後の「Usage Examples」に統合済みのFront Matter例が既に存在し、機械的で冗長。grep一つで確認できる内容。
- 削除しても失われない情報: フィールド名・許容値・目的は表形式に圧縮すれば維持できる。
- 移動先: フィールド名・許容値・目的の3列表に圧縮し、完全な例は「Usage Examples」のみに残す。

### 削除候補: docs/00_governance_08_known-issues-migration-plan.md / Current Format Summary(23-61行)

- 現在の記述の問題: RAG/MCP/Agent/EventBus/Sharedの移行前フォーマット詳細だが、移行は2026-07-23に完了済みで「もう存在しない過去の状態」の記述になっている。
- 削除理由: 現在の正本は移行後の実ファイル自体であり、旧フォーマットの詳細は運用上の価値を持たない。
- 削除しても失われない情報: 必要な履歴は各Known Issuesファイルの「移行ノート」セクションに既にある。
- 移動先: なし(削除のみ)。

### 削除候補: docs/00_governance_08_known-issues-migration-plan.md / Suggested Migration Order(85-93行)

- 現在の記述の問題: 未実施を前提とした優先順位付けだが、全エリア完了済みの現在は意味を持たない。
- 削除理由: 実施順を示す価値は完了後には消滅している。
- 削除しても失われない情報: 実施順の記録が必要ならgit historyで足りる。
- 移動先: なし(削除のみ)。

### 削除候補: docs/00_index.md / Related Documents(151-159行)

- 現在の記述の問題: frontmatterの`related`フィールド(10-17行)と完全に重複するファイルリスト。
- 削除理由: 二重管理により将来の更新漏れリスクが生じる。
- 削除しても失われない情報: frontmatterの`related`に情報は残る。
- 移動先: なし(frontmatterへの一本化)。

### 削除候補: docs/00_index.md / Keywords(161-168行)

- 現在の記述の問題: frontmatterの`tags`(4-9行)と完全一致。
- 削除理由: Related Documentsと同様の二重管理。
- 削除しても失われない情報: frontmatterの`tags`に情報は残る。
- 移動先: なし(frontmatterへの一本化)。

---

## 3. 要約候補

### 要約候補: docs/00_governance_01_documentation-governance.md 他6ファイル / 「Related Governance Documents」リンク一覧の7ファイル完全重複

- 現在の問題: 同一のリンク一覧(6項目)が`docs/00_governance_01`〜`07`の全7ファイルに完全重複している。
- 要約方針: `docs/00_governance_01`を正本とし、他ファイルは一行の参照に置き換える。
- 要約後のサンプル: 「関連文書一覧は `docs/00_governance_01_documentation-governance.md` を参照。」

### 要約候補: docs/00_governance_02_canonical-source-rule.md / Resolution Workflow(5ステップ)

- 現在の問題: Conflict Resolution Rule(4ステップ)と内容が大きく重なり、両者の関係(個別ルールか全体ワークフローか)が明示されていない。
- 要約方針: Resolution Workflow冒頭に「Conflict Resolution Rule / Code vs Document Conflict Rule / Known Issues Registration Ruleを包含する全体プロセスである」旨を一文追記する。
- 要約後のサンプル: 「本ワークフローは、以下の個別ルール(Conflict Resolution Rule等)を実行順に統合した全体プロセスである。」

### 要約候補: docs/00_governance_04_known-issues-template.md / Area Values(8領域列挙)

- 現在の問題: `docs/00_governance_01`の「In scope」セクションと完全に同一のリストが重複している。
- 要約方針: 「対象領域は `docs/00_governance_01` のScopeを参照」に置き換える。
- 要約後のサンプル: 「Area値は `docs/00_governance_01_documentation-governance.md` のIn scopeで定義される8領域と同一。」

### 要約候補: docs/00_governance_06_ai-reading-metadata.md / 末尾「Markdown記法ルール」

- 現在の問題: 本文書の主題(AIによる文書選択メタデータ)と無関係な一般Markdown整形規約であり、スコープ不一致。
- 要約方針: `docs/00_governance_01`側に「文書フォーマット規約」として移設するか独立スタイルガイドを作り、本ファイルからはリンクのみとする。
- 要約後のサンプル: 「Markdown記法の統一ルールは `docs/00_governance_01` (または別途スタイルガイド)を参照。」

### 要約候補: docs/00_governance_07_needs-confirmation-inventory.md / 「プライオリティ値(日本語)」セクション

- 現在の問題: Inventory Entry Fields項目12「Priority」の英語説明と全く同じ内容が日本語で重複記載。
- 要約方針: 英語定義+日本語補足を1箇所にまとめる。
- 要約後のサンプル: 「Priority: High / Medium / Low(高: ブロッキング, 中: 要対応, 低: 参考情報)」

### 要約候補: docs/00_governance_08_known-issues-migration-plan.md / Priority Criteria(74-83行)

- 現在の問題: 6基準自体は汎用的だが、現状はエリア固有の記述に埋もれている。
- 要約方針: エリア名・件数への言及を外し、「複数ドキュメントの移行作業を優先順位付けする際の一般原則」として抽出する。
- 要約後のサンプル: 「移行優先度は、影響範囲・参照頻度・既存の矛盾件数など6基準で判断する(エリア非依存の一般原則)。」

### 要約候補: docs/00_governance_08_known-issues-migration-plan.md / Target Files(11-19行)と Related Governance Documents(120-130行)

- 現在の問題: ファイルパスの列挙が`docs/00_index.md`の「既知の問題」セクションと重複。
- 要約方針: 個別列挙をやめ「`docs/00_index.md`の既知の問題セクション参照」に置き換える。
- 要約後のサンプル: 「対象ファイル一覧は `docs/00_index.md` の既知の問題セクションを参照。」

### 要約候補: docs/00_index.md / 「タスク別ドキュメント参照」配下の各表(73-149行)

- 現在の問題: タスク→ファイルのルーティングという設計判断そのものだが、ファイル名の羅列はコード構造変更のたびに陳腐化しやすい(実際に128行目でリンク切れが発生済み)。
- 要約方針: 表自体・粒度は残しつつ、冒頭に「本表はソースコード構造の変更に追従して更新が必要な一覧であり、正本はモジュール構造との整合を保つこと」という運用注意を一文加える。
- 要約後のサンプル: 「※本表は該当ドキュメントのリネーム・分割に追従して更新する運用注意事項であり、定期的な実在確認が必要。」

---

## 4. 残す・強化する記述

### 強化候補: docs/00_governance_01_documentation-governance.md / Change Impact Rule

- 残す理由: 文書変更時の影響波及範囲を判断する設計ロジックそのものであり、コードから読み取れない。
- 強化すべき観点: Change Impact Ruleが参照する「area dependency graph」の所在が本文に示されていない。実装者が参照先を誤解する恐れがある。
- 追記例: 「area dependency graphは `<所在ファイルパス>` を参照する(未整備の場合はNeeds confirmation登録)。」

### 強化候補: docs/00_governance_01_documentation-governance.md / Review Rule

- 残す理由: レビュープロセスという運用ルールであり残すべき。
- 強化すべき観点: レビューの承認者・実施主体が定義されておらず、責務境界が曖昧。
- 追記例: 「レビューは各領域のドキュメントオーナー(領域ガイド冒頭に明記)が実施する。」

### 強化候補: docs/00_governance_02_canonical-source-rule.md / General Rule(コード>最新レビュー文書>領域ガイドの3階層)

- 残す理由: 正本判断の根幹ロジックであり中核記述。
- 強化すべき観点: 番号順(1→2→3)が優先順位を意味するのか単なる列挙なのか読み取れない。「最新レビュー文書」と「領域ガイドが示す正本」が矛盾した場合の適用順序を明記すべき。
- 追記例: 「本リストは優先順位順であり、1が最優先。矛盾時は上位を採用する。」

### 強化候補: docs/00_governance_02_canonical-source-rule.md / Code vs Document Conflict Rule(5分類)

- 残す理由: コードと文書の矛盾を扱う中核的分類体系(Outdated code/Design deviation/Provisional implementation/Bug/Missing documentation)であり価値が高い。強化不要、そのまま残すべき。

### 強化候補: docs/00_governance_03_evidence-labels.md / Evidence Labels 1〜7、Handling Ambiguous Cases

- 残す理由: 確信度のスペクトラム定義であり中核概念。「迷ったら低信頼度側に倒す」という運用判断基準は実装者・レビュアーの判断のブレを防ぐ。強化不要、そのまま残す。

### 強化候補: docs/00_governance_04_known-issues-template.md / Lifecycle

- 残す理由: open→investigating→fixed/deferred/wontfix、deprecatedへの遷移条件という設計判断を示す。
- 強化すべき観点: 状態遷移が文章のみで記述されており誤解が生じやすい。
- 追記例: 状態遷移図または表(現在状態/遷移条件/遷移先)を追加する。

### 強化候補: docs/00_governance_05_deprecated-items.md / Deprecated Document References(diagnostics.jsonl等)

- 残す理由: 「削除ではなく後継を明記した上での参照」という運用方針そのものであり、方針書の削除提案原則と合致する重要ルール。How to Refer to Deprecated Items、Maintenance Ruleも同様に残すべき。
- 強化すべき観点: 各エントリにEvidence Label(Deprecated)が明示されておらず、`docs/00_governance_03`のラベル運用と整合していない。
- 追記例: 「Evidence: Deprecated(廃止確認済み、後継: <ファイル名>)」

### 強化候補: docs/00_governance_06_ai-reading-metadata.md / 「実装参照で確認できる情報の記載方針」

- 残す理由: 本レビューの分類基準(削除/圧縮/参照置換/保持/既知の問題へ/Needs Confirmationへ)とほぼ同一の運用ルールであり極めて重要。
- 強化すべき観点: 「AI Reading Metadata」という本ファイルの主題と直接関係がなく、`docs/00_governance_01`の中核ルールとして参照されるべきだが埋もれている。
- 追記例: `docs/00_governance_01`から「文書記載方針(削除/要約/保持判断基準)は `docs/00_governance_06` の当該セクションを参照」とリンクを張る。

### 強化候補: docs/00_governance_07_needs-confirmation-inventory.md / NC-001〜NC-017個別項目、Extraction Process

- 残す理由: いずれも「実装が不明」等の設計リスクを含む未解決論点であり、方針書が定める「残す記述」(既知の不整合・未解決論点)そのもの。「ソース文書を抽出時に変更しない」という運用ルールも重要。強化は下記Needs confirmation側で扱う。

### 強化候補: docs/00_governance_08_known-issues-migration-plan.md / Migration Policy(63-72行)

- 残す理由: ID保持・内容改変禁止・メタデータ追加方針という判断理由・運用ルールであり、将来同種の移行作業に再利用できる不変条件。
- 強化すべき観点: 「本ポリシーは2026-07-23の全エリア移行で採用された」旨が明記されておらず、既に実施済みであることが反映されていない。
- 追記例: 「本ポリシーは2026-07-23実施のRAG/MCP/Agent/EventBus/Shared全5エリア移行で適用済み。」

### 強化候補: docs/00_governance_08_known-issues-migration-plan.md / Risks(95-99行)、Acceptance Criteria for Future Migration(110-118行)

- 残す理由: トレードオフとリスク軽減策、判断基準として価値がある。
- 強化すべき観点: 「Lost historical context」の軽減策(移行ノートに残す)が実際に各ファイルで満たされているかの検証結果が未記載。Acceptance Criteriaも「Future」ではなく完了済み5エリアの充足チェックに更新すべき。
- 追記例: 「検証結果: 5エリア全ファイルで移行ノートに移行元フォーマット・移行日を記載済み(2026-07-27確認)。」

### 強化候補: docs/00_index.md / 推奨読書順序(35-45行)

- 残す理由: 新規参加者向けの読む順序という設計意図(全体像→環境構築→関心領域→既知の問題)であり残すべき。強化不要。

### 強化候補: docs/00_index.md / 「タスク別ドキュメント参照」導入文(57-59行)

- 残す理由: 「`docs/*.md`を全件読み込まないこと」というコンテキスト消費抑制の重要な運用制約。
- 強化すべき観点: なぜ全件読み込みを禁止するのか理由が一切書かれていない。「してはいけない」ルールのみで将来の実装者・エージェントが意図を誤解しうる。
- 追記例: 「理由: 全件読み込みはコンテキスト消費が過大になり、タスクに無関係な情報がノイズとして混入するため。」

---

## 5. Before / After 書き換え例

### 例1: Related Governance Documentsリンク一覧の重複解消

- Before(`docs/00_governance_02`他6ファイルの末尾に共通で存在):
  ```
  ## Related Governance Documents
  - 00_governance_01_documentation-governance.md
  - 00_governance_02_canonical-source-rule.md
  - 00_governance_03_evidence-labels.md
  - 00_governance_04_known-issues-template.md
  - 00_governance_05_deprecated-items.md
  - 00_governance_06_ai-reading-metadata.md
  ```
- After:
  ```
  ## Related Governance Documents
  関連文書一覧は `docs/00_governance_01_documentation-governance.md` を参照。
  ```
- 書き換え理由: 7ファイル完全重複はテンプレート項目の過剰な重複の典型例。正本を01に固定することで将来の追加・変更時の更新漏れを防ぐ。

### 例2: docs/00_governance_06 個別YAMLスニペットの圧縮

- Before:
  ```
  scope: agent
  audience: developer
  priority: high
  ...(計8スニペット)
  ```
- After:
  | フィールド名 | 許容値 | 目的 |
  |---|---|---|
  | scope | agent, mcp, rag, ... | 対象領域の識別 |
  | audience | developer, operator | 想定読者 |
  | priority | high, medium, low | 優先度 |

  (完全な記述例は「Usage Examples」節を参照)
- 書き換え理由: Usage Examplesと機能的に重複する個別スニペットを削除し、表形式に圧縮することでgrep一つで分かる情報の重複記載を解消する。

### 例3: docs/00_index.md 128行目のファイル名誤記修正

- Before:
  ```
  RAG known bugs / inconsistencies: 03_rag_90_inconsistencies_and_known_issues-part1.md
  ```
- After:
  ```
  RAG known bugs / inconsistencies: 03_rag_90_inconsistencies_and_known_issues.md
  ```
- 書き換え理由: `ls`で実ファイルを確認済みの確定誤り(`-part1`は存在しない)。同一ファイル内51行目、`docs/00_governance_08`15行目では正しい表記が使われており、128行目のみ食い違っている。これはNeeds confirmationではなく確認済みの修正事項。

### 例4: docs/00_governance_08 の移行完了反映

- Before(文書冒頭、計画中の体裁のまま):
  ```
  # Known Issues Migration Plan
  本文書はRAG/MCP/Agent/EventBus/Sharedの5エリアのKnown Issuesドキュメントを
  共通テンプレートへ移行するための計画である。
  ```
- After:
  ```
  # Known Issues Migration Plan (完了: 2026-07-23)
  Status: Completed
  本文書は2026-07-23に実施されたRAG/MCP/Agent/EventBus/Sharedの5エリア
  Known Issuesドキュメントの共通テンプレート移行に関する記録である。
  移行後の実ファイルは各ドキュメントの「移行ノート」セクションを正本とする。
  ```
- 書き換え理由: 実装完了後も「計画」の体裁のまま放置されており、実ファイル状態(全エリア移行済み)と矛盾している。ステータスフィールドを明示することで文書のライフサイクル(有効/完了/廃止)を読者に伝えられる。

### 例5: docs/00_index.md 全件読み込み禁止ルールへの理由追記

- Before:
  ```
  タスク別ドキュメント参照: `docs/*.md` を全件読み込まないこと。
  ```
- After:
  ```
  タスク別ドキュメント参照: `docs/*.md` を全件読み込まないこと。
  理由: 全件読み込みはコンテキスト消費が過大になり、タスクに無関係な情報が
  ノイズとして混入するため。以下のタスク別表に従い必要なファイルのみ読み込む。
  ```
- 書き換え理由: 「してはいけない」ルールのみで理由がなく、将来の実装者・エージェントが意図を誤解する恐れがある。理由を一文追記することで運用ルールとしての説得力が増す。

---

## 6. Needs confirmation 一覧

### Needs confirmation: docs/00_governance_01 / area dependency graphの所在

- 確認したいこと: Change Impact Ruleが参照する「area dependency graph」は実際にどこかに存在するのか、それとも未整備の概念か。
- 現在の根拠: 本文内で名称のみ参照され、実体・参照ファイルが示されていない。
- 不確実な理由: grep等で対応する実体を確認できていない。
- 誤っていた場合の影響: 実装者が存在しない参照先を探し続ける、または影響分析を省略してしまう。
- 推奨対応: 実体の有無を確認し、存在すれば所在を明記、存在しなければ本項目自体をNeeds confirmationとして正式登録するか記述を削除する。

### Needs confirmation: docs/00_governance_02 / General Ruleの優先順位適用順序

- 確認したいこと: コード>最新レビュー文書>領域ガイドの3階層は番号順が優先順位を意味するのか、それとも単なる列挙か。
- 現在の根拠: 番号付きリストとして記載されているのみ。
- 不確実な理由: 「最新レビュー文書」と「領域ガイドが示す正本」が矛盾した場合にどちらが優先するか本文で明言されていない。
- 誤っていた場合の影響: 正本判断を誤り、矛盾解消の作業が逆順になる恐れ。
- 推奨対応: 執筆者に意図を確認し、優先順位であることが確定次第「本リストは優先順位順」と明記する。

### Needs confirmation: docs/00_governance_02 / 「正本を固定記述しない」宣言と直後の固定表の矛盾

- 確認したいこと: 「Canonical Documents by Area」セクション(「本文書は正本を固定記述しない」と明言)と、ファイル末尾の「領域別の正典入口」表(scripts/agent/, mcp_servers/等を具体的に列挙)が矛盾していないか。
- 現在の根拠: 同一ファイル内で「ハードコードしない」と明言した直後にハードコードされた表が存在する。
- 不確実な理由: 「文書としての正本」と「コードとしての正本入口」が異なる概念という解釈も可能だが、本文でその区別が説明されておらず意図的な役割分担か記載漏れか判別できない。
- 誤っていた場合の影響: 領域が変更・追加された際にどちらの表を更新すべきか判断できず、両者が乖離するリスク。
- 推奨対応: 執筆者に意図を確認し、意図的な役割分担であれば「文書の正本とコードの正典入口は別概念である」旨を明記する一文を追加する。

### Needs confirmation: docs/00_governance_03 / 07 のNeeds Confirmationフィールド不整合

- 確認したいこと: `docs/00_governance_03`が定める必須6フィールド(Question/Evidence/Impact/Required Action/Target Document/Review Timing)と`docs/00_governance_07`の実際のフィールド構成(11〜15項目、名称も一部不一致)の対応関係。
- 現在の根拠: 03の「Target Document」「Review Timing」に相当するフィールドが07のテンプレートに明確に存在しない(07は「Source File」「Last Reviewed」等、名称・意味が微妙に異なる)。
- 不確実な理由: どちらが正本かが本文からは判断できず、テンプレート改訂の履歴も追えない。
- 誤っていた場合の影響: 今後NC項目を登録する際にどちらのフィールド定義に従うべきか運用者が混乱し、記載形式がばらつく。
- 推奨対応: どちらか一方を正本と定め、他方を追従させる整理を行う(このレビュー方針上は07を実務運用の正本とし、03側の定義を07に合わせて改訂するのが妥当と考えられる)。

### Needs confirmation: docs/00_governance_04 / "a separate migration plan"の実在確認

- 確認したいこと: Migration Notesが言及する「a separate migration plan」は実在するか、どこにあるか。
- 現在の根拠: 本文中で参照されるのみで、リンクや所在の記載がない。`docs/00_governance_08`がこれに該当する可能性がある。
- 不確実な理由: 参照先ファイル名が明示されていないため、実際に指しているものが08なのか別文書なのか特定できない。
- 誤っていた場合の影響: 読者が誤ったファイルを探す、または存在しない文書を前提に作業する。
- 推奨対応: `docs/00_governance_08`を指すのであれば明示的にファイル名でリンクする。別文書であれば作成するか記述を削除する。

### Needs confirmation: docs/00_governance_05 / 4項目のNeeds confirmationフォーマット不備と07未収載

- 確認したいこと: `config/rag_pipeline.toml`、`common.toml`、`workflow optional mode`、`shared common config`の4項目は「Status: Needs confirmation」とされているが、03が定める6必須フィールドを満たさず、かつ07の集中インベントリにも1件も収載されていない理由。
- 現在の根拠: 現状は「Current Replacement/Status/Notes/Evidence」という独自フォーマットで記載されており、03のテンプレートにも07の集中インベントリにも準拠していない。
- 不確実な理由: テンプレート不備なのか、Deprecated Items専用の簡易フォーマットとして意図的に許容されているのか本文からは判断できない。
- 誤っていた場合の影響: 07の「一元管理」が実態としては全文書を網羅しておらず、放置されたNeeds confirmation項目が見落とされ続ける。
- 推奨対応: 4項目を07の正式フォーマットに変換して収載するか、Deprecated Items専用フォーマットとして認める場合はその旨を03または07に明記する。

### Needs confirmation: docs/00_governance_06 / メタデータフィールドの実効性

- 確認したいこと: Existing/Recommended Metadata Fields(scope, audience, priority等)は実際に何らかのツール・スクリプトで解析・利用されているのか、それとも記述のみで機能していないのか。
- 現在の根拠: Non-Goalsで「AIエージェントがこれらのフィールドをどう解析・利用するかは対象外」と明言されている。
- 不確実な理由: フィールドが実効性を持つか文書上判断できず、実装(スクリプト等)の有無を確認していない。
- 誤っていた場合の影響: 実効性のないメタデータ付与に運用コストをかけ続ける、または実際には利用されているのに軽視される。
- 推奨対応: 該当ツール・スクリプトの有無をコード検索で確認し、利用実態を本文に追記する。

### Needs confirmation: docs/00_governance_07 / "eleven fields"記述と実際15項目の食い違い

- 確認したいこと: 「Inventory Entry Fields」冒頭は「the following eleven fields」(11フィールド)と明記しているが、実際には1〜15番まで15項目が列挙されている。この食い違いはどちらが正しいか。
- 現在の根拠: 本文の数字表記(11)と実際の列挙数(15)が一致しない。NC-001〜NC-017の記載でも、Priority/Related NC/Resolution Target/Blockingの4項目を埋めているのはNC-003, NC-008, NC-010, NC-014のみで、他13件は未記入。
- 不確実な理由: 本文の数字表記自体の誤り(11→15への改訂漏れ)である可能性が高いが、運用実態(4項目が任意扱いされている)と文言(must的な書き方)が一致しているかは未確認。
- 誤っていた場合の影響: 必須フィールドの範囲を誤解し、今後の登録作業でも未記入が常態化し続ける。
- 推奨対応: 実数(15)に訂正するとともに、Priority/Related NC/Resolution Target/Blockingが必須か任意かを明記し、運用実態と一致させる。

### Needs confirmation: docs/00_governance_07 / 05のNeeds confirmation項目が未収載である理由

- 確認したいこと: `docs/00_governance_05`に記載された4件の「Needs confirmation」項目が本インベントリ(NC-001〜NC-017)に一件も含まれていない理由。
- 現在の根拠: 07のPurposeは「設計文書セット全体のNeeds confirmation項目を一元管理する」ことだが、05の該当項目が未収載。
- 不確実な理由: Extraction Process(grepで抽出)が実際には全文書に対して実施されていない可能性がある。
- 誤っていた場合の影響: 「一元管理」を前提に07だけを確認する運用者が、05の未解決論点を見落とし続ける。
- 推奨対応: Extraction Processを`docs/`配下全ファイルに対して再実行し、05の4項目を07に追加登録する。

### Needs confirmation: docs/00_governance_08 / 文書ステータス(計画中/完了)の未整理

- 確認したいこと: 本文書が「計画」段階の体裁のまま放置されているのか、意図的に計画記録として保持しているのか。
- 現在の根拠: git logおよび対象5ファイルの実物確認により、`f5d3d10d`(本文書作成、2026-07-23)の直後、同日中の`7b04065c`「docs: migrate all Known Issues documents to common template」で5エリア全ての移行が完了している(各ファイルに移行ノートが実在)。
- 不確実な理由: 文書内に完了/未完了を示すステータスフィールドがなく、実ファイル状態(全エリア移行済み)と本文の体裁が矛盾している。
- 誤っていた場合の影響: 読者が「これから移行する予定がある」と誤解し、既に完了した作業を重複して検討する。
- 推奨対応: 文書冒頭に`Status: Completed(2026-07-23)`等のフィールドを追加し、完了報告として書き換える(例4参照)。

### Needs confirmation: docs/00_governance_08 / Suggested Migration Orderと実際のコミットの整合性

- 確認したいこと: Suggested Migration OrderではAgent→MCP→RAG→EventBus→Sharedの順を提案しているが、実際のコミット(`7b04065c`)は5ファイルをまとめて一括移行しているように見える。提案順序通りに段階実施されたのか、一括実施だったのか。
- 現在の根拠: git logで確認できるのはコミット`7b04065c`が5ファイルを同時に変更している事実のみ。
- 不確実な理由: 本文書からは実施プロセス(段階的か一括か)の実態を判断できない。
- 誤っていた場合の影響: 大きな実害はないが、Suggested Migration Orderが「実際には使われなかった提案」として誤解を招く。
- 推奨対応: 削除候補として扱う(既述)場合はこの論点自体が解消される。保持する場合は「提案時点のものであり実施は一括実施だった」旨を注記する。
