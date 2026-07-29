# MCP領域 設計文書レビュー報告書

対象: `docs/04_mcp_*.md` 全45ファイル。9チャンクに分けて実施したレビュー結果を統合する。

---

## 1. 全体評価

MCP領域は、これまでレビューした4ドメイン(Governance/Overview/Deployment/RAG)の中で**確認済みの事実誤りが最も多い**。単発の誤記ではなく、複数ファイルに伝播した構造的な問題が中心であり、これが本ドメインの最大の特徴である。横断的に確認された13件の問題は以下の通り(詳細はNeeds confirmation参照)。

1. ポート番号の壊滅的な不一致(`04_mcp_02_service_boundaries.md`と`04_mcp_01_tool_ownership_matrix.md`の両方で、git-mcp以外の7サーバー全てが`config/agent.toml`実値と不一致。file-mcp単一サーバー扱いも実装の3分割と乖離)
2. ツール数の誤り(`04_mcp_01_system_overview.md`のServer Catalog表: mdq-mcp「9」→実際7、web-search-mcp「1」→実際2)
3. ファイル命名規則の誤りが`04_mcp_06_14`/`04_mcp_06_15`/`04_mcp_07`の3ファイルに伝播(ベア名`server.py`/`tools.py` vs 実際の`<name>_server.py`/`<name>_tools.py`)
4. RAGツール名の完全な陳腐化(`04_mcp_05_04`が`ingest`/`search`等の廃止済みツール名を記載)
5. 監査ログ記述の矛盾(`04_mcp_02_03`と`04_mcp_06_07`が同一事実について食い違う)
6. agent.tomlフィールド数の誤り(`04_mcp_06_03`「4フィールドのみ」→実際10)
7. 存在しない関数名`check_routing_drift_vs_live()`が`04_mcp_03_02`と`04_mcp_03_05`の両方に登場
8. `_SIDE_EFFECT_TOOLS`の記載漏れ(`04_mcp_03_02`)
9. watchdog `degraded_reason`機構の自己矛盾(`04_mcp_06_13-part1` vs `04_mcp_06_12`)
10. 存在しない設定項目・ログ文字列(`repeated_tool_error_threshold`等)
11. ファイル名・パスの個別誤り(`models.py`、`mdq/server.py:308`、importパス複数)
12. RAGとAgentの責務境界がどこにも文書化されていない
13. Known Issuesファイル(`04_mcp_90`)のMCP-002エントリの陳腐化

**連結文書としての問題**: 「新しいツール追加手順」が`04_mcp_03_02`/`04_mcp_03_05`で二重(実質三重)に重複し、Fail-Open/Closed要約表が`04_mcp_05_03`/`04_mcp_05_05`で三重に重複するなど、同一情報が正本を定めないまま複数ファイルに複製されている。ポート番号やツール一覧のように「一次情報はconfig/実装であるべき情報」を文書側に転記した箇所ほど陳腐化が進んでいる。

**コード説明に寄りすぎている領域**: Pydanticモデルの全フィールド転記(`04_mcp_02_01`)、dispatch_toolのコード例(`04_mcp_02_03`)、curlコマンド例の反復(`04_mcp_06_06`)、firejailインストール手順(`04_mcp_06_16`)。これらは「コードを読めば分かる」または「READMEレベルの手順書」であり、設計判断を伝える文書としての価値が低い。

**残すべき領域**: RuntimeToolRegistry/ToolRegistry/ToolRouteResolverの責務区別、circuit breaker状態遷移(HEALTHY→DEGRADED→UNAVAILABLE→HALF_OPEN)、config_dependent/enabled/disabled_reasonの4状態不変条件、fail-open/fail-closedのリスクティア設計、Local Git vs Remote Git・File Operations vs RAG・MDQ vs RAGの境界規則。これらは実装を読むだけでは読み取れない「なぜこの設計になっているか」を説明しており、本レビュー方針でいうC(残す記述)およびD(強化候補)の中核をなす。

**再構成の基本方針**:
- ポート番号・ツール数・ツール名など「configや実装が正本であるべき数値・固有名詞」は本文に埋め込まず、生成物または参照先(config/agent.toml、`_TOOL_MODULES`等)へのポインタに置き換える。
- 「新しいツール追加手順」「Fail-Open/Closed表」は正本を1ファイルに定め、他は要約+参照リンクに縮小する。
- RAGとAgentの責務境界(観点12)は独立したセクションとして`04_mcp_05_04`または新設ファイルに明記する。
- Needs confirmationとして扱うべき箇所(オーバーライド失敗時挙動、role フィールドの用途等)を断定表現から明示的な保留表現に修正する。

---

## 2. 削除候補

### 削除候補: docs/04_mcp_01_tool_ownership_matrix.md / Mermaid図
- 現在の記述の問題: サーバー一覧・ポート・ツール対応が表とMermaid図の両方に存在し、完全重複している。
- 削除理由: 表が正本になり得るため、図は同じ情報の別表現に過ぎず保守コストのみ増える(実際、表・図とも実装と食い違っており二重の保守漏れが発生している)。
- 削除しても失われない情報: なし。図固有の情報はない。
- 必要な場合の移動先: どうしても視覚表現を残すなら、表を正本と明記した上で図に「生成物、手動更新禁止」等の注記を付けるか、いっそ削除する。

### 削除候補: docs/04_mcp_02_service_boundaries.md / Allowed/Forbidden operation types
- 現在の記述の問題: `04_mcp_01_tool_ownership_matrix.md`の内容とほぼ重複。
- 削除理由: 正本はOwnership Matrixとすべきであり、本ファイルに複製する必要がない。
- 削除しても失われない情報: なし(Key Boundary Rulesという別節に設計意図は残っている)。
- 必要な場合の移動先: Ownership Matrixへのリンクに置き換える。

### 削除候補: docs/04_mcp_02_01_endpoints-and-transport.md / Pydanticモデル・データクラス全フィールド転記
- 現在の記述の問題: モデル定義をそのままMarkdownに転記しており、コードを読めば分かる内容。
- 削除理由: 型定義はソースコードが正本であり、文書側で同期を維持するコストに見合わない。
- 削除しても失われない情報: なし。相関キー表やhealth()の実装詳細(deps={}固定)など設計上の注意点は別途残す。
- 必要な場合の移動先: ファイルパス・クラス名の参照のみ残す。

### 削除候補: docs/04_mcp_02_03_audit-logging-and-errors.md / dispatch_toolのコード例
- 現在の記述の問題: 関数本体をほぼそのまま転記。
- 削除理由: 実装詳細であり、コードを読めば分かる。しかもこのコード例の周辺記述(監査ログ対応サーバーの列挙)自体が誤りを含んでいる(観点5)。
- 削除しても失われない情報: なし。
- 必要な場合の移動先: 「共有`_audit_log()`を使用するサーバー」という事実のみ表形式で残し、コードへの参照はファイルパスのみとする。

### 削除候補: docs/04_mcp_06_06 (該当セクション) / 各サーバーのcurlコマンド例・JSON応答例
- 現在の記述の問題: 5例中5例で同じ注記が繰り返されており冗長。
- 削除理由: 実行手順のリファレンスであり設計判断を含まない。同一注記の反復は保守コストのみ増やす。
- 削除しても失われない情報: なし。
- 必要な場合の移動先: 共通注記は1箇所にまとめ、各サーバー固有のエンドポイント名のみ表形式で列挙する。

### 削除候補: docs/04_mcp_06_16 / firejailインストール手順
- 現在の記述の問題: OSパッケージのインストールコマンドという運用手順書レベルの内容。
- 削除理由: 設計文書の範囲外。fail-open/closedチェック項目(コード一致確認済みで重要)とは性質が異なる。
- 削除しても失われない情報: なし。
- 必要な場合の移動先: 別途セットアップ手順書(運用Runbook)があればそちらへ移動。

### 削除候補: docs/04_mcp_00_document-guide.md / File IndexとRelated Documentsの重複部分
- 現在の記述の問題: 同じファイル一覧が2箇所に存在する。
- 削除理由: エントリポイント文書内での自己重複。
- 削除しても失われない情報: なし。
- 必要な場合の移動先: File Indexを正本とし、Related Documentsは「本文中で言及した文書へのリンク」に限定して重複を避ける。

---

## 3. 要約候補

### 要約候補: docs/04_mcp_03_02_tool-registry.md, docs/04_mcp_03_05_lifecycle-and-new-server.md / 「新しいツール追加」手順
- 現在の問題: 同一の7ステップ手順が2ファイル(実質三重)に重複し、しかもいずれも存在しない関数名`check_routing_drift_vs_live()`を含んでいる。
- 要約方針: 正本を`04_mcp_03_05`(lifecycle文書)に一本化し、`04_mcp_03_02`側は「手順の要点3行+リンク」に圧縮する。関数名は`tool_routing_validation.py`の`validate_routing_against_live()`に修正する。
- 要約後のサンプル:
  > 新規ツール追加の詳細手順は`docs/04_mcp_03_05_lifecycle-and-new-server.md`を参照。要点: (1) `<name>_tools.py`にツール関数を実装、(2) RuntimeToolRegistryへの登録、(3) `validate_routing_against_live()`でドリフト検査。

### 要約候補: docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md, docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md / Fail-Open/Closed要約表
- 現在の問題: 同一の要約表が2ファイル(実質3箇所)に重複している。
- 要約方針: 正本を`04_mcp_05_03`(リスクティア分類を扱う本流文書)に置き、`04_mcp_05_05`側はmdq固有の追加ルール(deny-allロックダウン等)のみ残して共通部分は参照に置き換える。
- 要約後のサンプル:
  > Fail-open/fail-closedの基本方針は`docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`を参照。mdq-mcp固有のロックダウン規則(deny-all時の挙動)は本ファイル末尾に別途記載。

### 要約候補: docs/04_mcp_04_04_mdq.md, docs/04_mcp_05_04_mdq-rag-boundary.md / MDQ FTS5対RAGの判断基準
- 現在の問題: 同じ判断基準が2ファイルに分散し、かつ`05_04`側のツール名が陳腐化しているため整合性が取れているか確認できない。
- 要約方針: 判断基準の正本を`05_04`(境界文書)に集約し、`04_04`側は「使い分けの一文+参照リンク」に縮小する。ツール名修正(観点4)と同時に実施する。
- 要約後のサンプル:
  > MDQ(FTS5)とRAGの使い分け基準は`docs/04_mcp_05_04_mdq-rag-boundary.md`のデータ所有権表を参照。

### 要約候補: docs/04_mcp_06_04 / Major Default Values表
- 現在の問題: `half_open_cooldown_sec`(30秒)が表から漏れており、他の性能閾値についても実測値か見積もりかの区別がない。
- 要約方針: 表自体は残すが、各値に「実測(commit XXX時点)」「見積もり(未計測、Needs confirmation)」の出典列を追加し、漏れていた`half_open_cooldown_sec`を追記する。
- 要約後のサンプル:
  > | 設定項目 | 値 | 出典 |
  > | --- | --- | --- |
  > | failure_threshold | 3 | 実測(コード確認済み) |
  > | half_open_cooldown_sec | 30 | 実測(コード確認済み) |
  > | (性能閾値X) | Yms | 見積もり、Needs confirmation |

---

## 4. 残す・強化する記述

### 強化候補: docs/04_mcp_05_04_mdq-rag-boundary.md および全体構成 / RAGとAgentの責務境界(観点12)
- 残す理由: 本ドメイン最重要観点として明示的に指定されている。データ所有権表・Agent access patternsは既に良い骨格を持つ。
- 強化すべき観点: rag-pipeline-mcpと`RagPipeline`コア実装の関係、Agent層が本番経路では必ずMCP経由でのみRAGにアクセスすること、直接importする経路がテスト専用か否か。
- 追記例:
  > **RAGとAgentの責務境界**: `RagPipeline`はコアロジックを実装するが、本番経路のAgentは`rag-pipeline-mcp`(HTTP境界)を経由してのみ呼び出す。Agentコードから`RagPipeline`を直接importする経路はテスト/開発用途に限定され、本番運用では使用しない(Needs confirmation: importの直接呼び出しが完全に禁止されているか、それとも慣習に留まるか)。

### 強化候補: docs/04_mcp_01_system_overview.md / RuntimeToolRegistry/ToolRegistry/ToolRouteResolverの区別
- 残す理由: MCP領域で最も紛らわしい3概念の区別であり、正本性(観点: ToolExecutor/RuntimeToolRegistryの正本性)を理解する上で必須。
- 強化すべき観点: 「configのtool_namesはルーティングの入力ではない」という重要事実(`04_mcp_03_01`にはあるが`04_mcp_06_03`に欠落)をここでも明記し、どのファイルが実行時の正本かを一箇所で断定する。
- 追記例:
  > 実行時のツールルーティングの正本は`RuntimeToolRegistry`であり、`config/agent.toml`の`tool_names`フィールドはルーティングの入力として使用されない(観測用途のみ)。詳細は`docs/04_mcp_06_03`参照。

### 強化候補: docs/04_mcp_03_06_tool-runtime-availability-metadata.md / config_dependent/enabled/disabled_reasonの4状態モデル
- 残す理由: MCP全体の可用性表現の核であり、ToolExecutor/RuntimeToolRegistryの正本性観点でも中心的記述。
- 強化すべき観点: 「/v1/tools as RuntimeToolRegistry Source」というホットリロード経路の有無が未確認のまま残っている。設定変更後にRuntimeToolRegistryが自動的に再構築されるのか、プロセス再起動が必要なのかを明記する。
- 追記例:
  > `/v1/tools`エンドポイントはRuntimeToolRegistryの現在状態を返すが、`config/agent.toml`変更後にこの状態がホットリロードされるかは未確認(Needs confirmation)。`/reload`の対象範囲は`docs/04_mcp_06_17`の制約(`[mcp_servers.*]`は対象外)と合わせて確認すること。

### 強化候補: docs/04_mcp_04_02_file-write-file-delete-shell.md / shell-mcpサンドボックス強制の責務所在
- 残す理由: 「サンドボックスはデフォルト無効」というコード一致確認済みの重要な安全性記述。
- 強化すべき観点: 本番強制ロジックの主体がshell-mcp自身ではなくAgent側の`repl_health.py`であることが本文から読み取れず、責務境界を誤解させる。
- 追記例:
  > shell-mcp自身はサンドボックスをデフォルトで強制しない。本番環境での強制はAgent側`repl_health.py`が担っており、shell-mcpは自身の設定に従うのみである(責務: 強制ロジックはAgent層、実行はMCPサーバー層)。

### 強化候補: docs/04_mcp_06_09 / circuit breaker状態遷移
- 残す理由: HEALTHY→DEGRADED→UNAVAILABLE→HALF_OPENの遷移はコード一致確認済みで、運用上最も重要な障害対応知識。
- 強化すべき観点: `06_03`側に欠落している「configのtool_namesはルーティングに使われない」という事実をここにも相互参照として明記し、読者がどちらのファイルを読んでも正しい理解に到達できるようにする。
- 追記例:
  > 注: `[mcp_servers.*].tool_names`はcircuit breakerの状態やルーティングには影響しない。ルーティングの入力ではなく、あくまで参照情報である(`docs/04_mcp_06_03`と矛盾しないこと)。

### 強化候補: docs/04_mcp_02_02_startup-modes-and-health.md / restart_recommended常にFalse固定
- 残す理由: 「ヘルス表示は自動復旧しない」という運用者向けの重要な誤解防止記述。
- 強化すべき観点: なぜ常にFalseに固定されているのか(未実装なのか、意図的な設計なのか)の理由が本文にない。
- 追記例:
  > `restart_recommended`は現状常に`False`を返す(Needs confirmation: 将来実装予定の未実装フラグか、それとも自動再起動を意図的に提供しない設計判断か)。運用者は本フィールドを信用して自動復旧を期待してはならない。

---

## 5. Before / After 書き換え例

### 例1: ポート番号(最重要・確認済み事実誤り)
- 対象: docs/04_mcp_01_tool_ownership_matrix.md, docs/04_mcp_02_service_boundaries.md
- Before:
  > | サーバー | ポート |
  > | --- | --- |
  > | web-search-mcp | 8009 |
  > | rag-pipeline-mcp | 8005 |
  > | cicd-mcp | 8006 |
  > | mdq-mcp | 8007 |
  > | shell-mcp | 8008 |
  > | github-mcp | 8012 |
  > | git-mcp | 8014 |
  > | file-mcp | (単一サーバーとして記載) |
- After:
  > ポート番号は`config/agent.toml`の`[mcp_servers.*]`セクションを正本とする。本文には固定値を転記せず、以下のように参照のみ記載する。
  >
  > 各サーバーの実ポートは`config/agent.toml`を参照(2026-07時点でgit-mcpの8014以外、本表と実装値に食い違いがあることを確認済みのため、本文中の固定値記載は廃止する)。file-mcpはfile-read-mcp/file-write-mcp/file-delete-mcpの3サーバーに分割済み(単一サーバーとして扱う記述は削除)。
- 書き換え理由: 転記された数値は7/8サーバーで実装と不一致であることが確認済み。数値を文書に固定すると再度陳腐化するため、正本(config)への参照に置き換える。file-mcpの単一サーバー扱いは古いアーキテクチャ世代の記述であり、3分割の実態に合わせる。

### 例2: Server Catalogのツール数(確認済み事実誤り)
- 対象: docs/04_mcp_01_system_overview.md
- Before:
  > | サーバー | ツール数 |
  > | --- | --- |
  > | mdq-mcp | 9 |
  > | web-search-mcp | 1 |
- After:
  > | サーバー | ツール数 | 備考 |
  > | --- | --- | --- |
  > | mdq-mcp | 7 | 2026-07時点、実装確認済み |
  > | web-search-mcp | 2 | browser_fetch統合により1→2(要更新履歴に追記) |
- 書き換え理由: 実装確認の結果、mdq-mcpは7、web-search-mcpは2であることが確定した。browser_fetch統合という更新イベントが起きていたにもかかわらず数値が追随していなかったため、更新履歴の記載も合わせて行う。

### 例3: ファイル命名規則(3ファイルに伝播した誤り)
- 対象: docs/04_mcp_06_14, docs/04_mcp_06_15, docs/04_mcp_07_tool_schema_export_policy.md
- Before:
  > `mcp_servers/<name>/server.py`にdispatch()を実装する。
  > (07番) 過去は`tools.py`という命名だったが、現在も`tools.py`を用いる…(41-43行で「ベア名は過去のもの」としながら本文はベア名のまま)
- After:
  > `mcp_servers/<name>_server.py`にdispatch()を実装する。ツール定義は`mcp_servers/<name>_tools.py`に置く。
  > (07番) 命名規則はかつて`server.py`/`tools.py`という共有ディレクトリ配下のベア名だったが、現在は`<name>_server.py`/`<name>_tools.py`というフラット命名に変更されている(移行済み、ベア名は廃止)。
- 書き換え理由: 実装は全サーバーで`<name>_server.py`/`<name>_tools.py`形式であることを確認済み。07番ファイルは本文41-43行で「ベア名は過去のもの」と認識しながら他の箇所ではベア名を使い続けており自己矛盾しているため、全文をフラット命名に統一する。

### 例4: RAGツール名の陳腐化
- 対象: docs/04_mcp_05_04_mdq-rag-boundary.md
- Before:
  > RAGを使用する場面: `ingest`でドキュメント登録、`search`で検索、`get_document`/`delete_document`/`list_documents`で管理操作を行う。
- After:
  > RAGを使用する場面: `rag_run_pipeline`でドキュメント登録・パイプライン実行、`rag_debug_pipeline`でデバッグ実行、`rag_list_documents`で一覧取得、`rag_delete_document`で削除を行う(検索単体の独立ツールは現状存在しない。検索は`rag_run_pipeline`のモードとして提供される。Needs confirmation: 検索専用の呼び出し方法)。
- 書き換え理由: 実装確認済みの実ツール名は`rag_run_pipeline`/`rag_debug_pipeline`/`rag_list_documents`/`rag_delete_document`の4つであり、旧ツール名は存在しない。同一ドメイン内の`05_03`は既に新名称を使っており、本ファイルのみ取り残されていたため統一する。

### 例5: 存在しない関数名の修正
- 対象: docs/04_mcp_03_02_tool-registry.md, docs/04_mcp_03_05_lifecycle-and-new-server.md
- Before:
  > ルーティングのドリフトは`check_routing_drift_vs_live()`で検出できる。
- After:
  > ルーティングのドリフトは`tool_routing_validation.py`の`validate_routing_against_live()`で検出できる。
- 書き換え理由: `check_routing_drift_vs_live()`という関数はコード上に存在しない。実装確認の結果、該当機能は`tool_routing_validation.py`の`validate_routing_against_live()`であることが判明したため、両ファイルとも修正する。

---

## 6. Needs confirmation 一覧

### A. 確認済みの事実誤り(優先度高)

#### Needs confirmation: ポート番号(01_tool_ownership_matrix, 02_service_boundaries)
- 確認したいこと: なぜ7/8サーバーでポート番号が食い違ったのか(単なる転記ミスか、旧アーキテクチャ世代の文書が更新されずに残ったものか)。
- 現在の根拠: `config/agent.toml`との突き合わせにより、git-mcp(8014)以外の全サーバーで値が不一致であることを確認済み。
- 不確実な理由: 誤りの発生時期・原因が特定できていない。
- 誤っていた場合の影響: 運用者がこの文書を見て誤ったポートに接続を試みる、あるいはfile-mcpを単一サーバーとして扱う誤解が新規参画者に伝播する。
- 推奨対応: 本文からポート固定値を削除し、config参照に置き換える(例1参照)。あわせてfile-mcp分割の経緯を`04_mcp_04_02`等に一言残す。

#### Needs confirmation: mdq-mcp/web-search-mcpのツール数(01_system_overview)
- 確認したいこと: 誤記載がいつから続いているか、Server Catalog表の更新プロセスが存在するか。
- 現在の根拠: 実装確認によりmdq-mcp=7、web-search-mcp=2(browser_fetch統合後)であることを確認済み。
- 不確実な理由: 更新漏れの原因(手動更新プロセスの欠如か)が不明。
- 誤っていた場合の影響: ツール一覧を信頼した設計変更や監査で数が合わず混乱を招く。
- 推奨対応: 数値を修正した上で、更新履歴セクションに「browser_fetch統合(web_fetch廃止)によりツール数変更」の記録を追加する。

#### Needs confirmation: ファイル命名規則(06_14, 06_15, 07_tool_schema_export_policy)
- 確認したいこと: 07番ファイル自身が41-43行で認識している「ベア名は過去のもの」という事実がなぜ本文の他の箇所には反映されなかったか。
- 現在の根拠: 実装は全て`<name>_server.py`/`<name>_tools.py`形式であることを確認済み。
- 不確実な理由: 07番ファイル内の自己矛盾の発生経緯(部分的な修正漏れか)が不明。
- 誤っていた場合の影響: 新規MCPサーバー追加時に誤ったファイル名で実装してしまう。
- 推奨対応: 3ファイルとも全文をフラット命名に統一し、07番の自己矛盾箇所を解消する(例3参照)。

#### Needs confirmation: RAGツール名の陳腐化(05_04_mdq-rag-boundary)
- 確認したいこと: 検索単体の独立ツールが本当に存在しないのか、`rag_run_pipeline`のモード引数で検索のみを行えるのか。
- 現在の根拠: `ingest`/`search`/`get_document`/`delete_document`/`list_documents`はコード上に存在せず、実際は`rag_run_pipeline`/`rag_debug_pipeline`/`rag_list_documents`/`rag_delete_document`の4ツールであることを確認済み。
- 不確実な理由: 検索専用の呼び出し方法(パイプラインのモード指定か別APIか)が未確認。
- 誤っていた場合の影響: Agent実装者が存在しないツール名を呼び出しコードに書いてしまう。
- 推奨対応: ツール名を修正した上で、検索専用の呼び出し方法を実装者に確認し追記する。

#### Needs confirmation: 監査ログ記述の矛盾(02_03_audit-logging-and-errors vs 06_07_reading-audit-logs)
- 確認したいこと: cicd-mcp/git-mcpが共有`_audit_log()`を呼んでいるかどうかの最終事実、および両ファイルのどちらを正本とするか。
- 現在の根拠: `06_07`内の別表および実コードでは、cicd-mcp/git-mcpは共有`_audit_log()`を使用していることを確認済み。`02_03`は「logging.getLoggerのみ」と矛盾する記述をしている。
- 不確実な理由: `02_03`がいつの実装状態を基に書かれたか(過去の実装が変わった可能性)が不明。
- 誤っていた場合の影響: 監査ログの網羅性を誤認し、コンプライアンス確認で見落としが発生する。
- 推奨対応: `02_03`を修正し、`06_07`の表を正本として一本化する。rag-pipeline-mcpの監査ログ有無は別途B群で確認する。

#### Needs confirmation: agent.tomlフィールド数(06_03)
- 確認したいこと: 「4フィールドのみ」という記述がいつの仕様を指しているか。
- 現在の根拠: 現行configには`tool_names`/`auth_token`/`role`/`call_timeout_sec`/`startup_timeout_sec`を含む10フィールドが実在することを確認済み。
- 不確実な理由: 4フィールド時代の仕様からの更新漏れか、意図的な簡略化(主要フィールドのみ紹介する意図)かが不明。
- 誤っていた場合の影響: 設定可能な項目を過小に認識し、`role`等のフィールドを見落とす。
- 推奨対応: 10フィールド全てを列挙する表に差し替える。「主要フィールドのみ」とする場合はその旨を明記する。

#### Needs confirmation: 存在しない関数名check_routing_drift_vs_live()(03_02, 03_05)
- 確認したいこと: この関数名がどの時点の設計案・別ブランチの名称に由来するか。
- 現在の根拠: 実装確認により、該当機能は`tool_routing_validation.py`の`validate_routing_against_live()`であることを確認済み。
- 不確実な理由: 命名変更の経緯が不明。
- 誤っていた場合の影響: 開発者が存在しない関数を呼び出そうとしてエラーになる。
- 推奨対応: 両ファイルとも正しい関数名・ファイルパスに修正する(例5参照)。

#### Needs confirmation: `_SIDE_EFFECT_TOOLS`の記載漏れ(03_02_tool-registry)
- 確認したいこと: `CICD_WRITE_TOOLS`/`RAG_WRITE_TOOLS`/`MDQ_WRITE_TOOLS`が意図的に除外されたのか単純な記載漏れか。
- 現在の根拠: 実装上これら3つの定数が存在することを確認済み。
- 不確実な理由: 除外の意図が不明。
- 誤っていた場合の影響: 副作用のあるツールの網羅性チェックで見落としが発生する。
- 推奨対応: 3つの定数を追記し一覧を完全にする。

#### Needs confirmation: watchdog degraded_reasonの自己矛盾(06_13-part1 vs 06_12)
- 確認したいこと: `record_failure(reason=...)`という記載が正しいシグネチャなのか、それとも`06_12`の「record_degradedは呼び出し元ゼロのdead code」が正しいのか。
- 現在の根拠: `06_12`はコード確認済みの正確な記述として「dead code」を記載しているが、`06_13-part1`は存在しないシグネチャを前提に説明しており、両者が矛盾している。
- 不確実な理由: `06_13-part1`がどの設計段階を前提に書かれたか不明。
- 誤っていた場合の影響: degraded reasonの記録機構が実際に動作していると誤認し、監視設計を誤る。
- 推奨対応: `06_13-part1`を`06_12`の記述に合わせて修正し、degraded_reasonがdead codeであることを明記する。

#### Needs confirmation: 存在しない設定・ログ文字列(06_13-part2)
- 確認したいこと: `repeated_tool_error_threshold`、`[debug]`ログ出力例、`error_type=tool/transport`のgrepパターンがどの実装(別レイヤーのMCPサーバー側`_record_tool_error()`)と混同されたものか。
- 現在の根拠: いずれの設定・文字列も実装コード検索で見つからないことを確認済み。実際のログ形式はJSONである。
- 不確実な理由: 混同元となった別レイヤーの機構の詳細が未整理。
- 誤っていた場合の影響: 運用者がgrepパターンを使ってログ監視を組んでも該当ログがヒットしない。
- 推奨対応: 実際のJSON構造化ログのフィールド名を確認し、正しいgrep/jqパターンに差し替える。

#### Needs confirmation: ファイル名・importパスの個別誤り(04_01, 04_04_05, 05_02)
- 確認したいこと: `models.py`(実際`github_models.py`)、`mdq/server.py:308`(実際`mdq_server.py:368`)、`mcp_servers.shell.models`等(実際`shell_models.py`等)の誤りが他にも同種のものが残っていないか。
- 現在の根拠: 個別に実装確認済み。
- 不確実な理由: 同種のファイルパス誤記が他ファイルにも潜在している可能性を排除できていない。
- 誤っていた場合の影響: 開発者がコードを探す際に誤ったパスを参照し時間を浪費する。
- 推奨対応: 各該当箇所を修正し、可能であれば全45ファイルに対しファイルパス文字列の機械的な存在チェックを行う。

#### Needs confirmation: MCP-002エントリの陳腐化(90_inconsistencies_and_known_issues)
- 確認したいこと: 「大半のサーバーで未実装」という記述の更新タイミング。
- 現在の根拠: git/file-read/file-write/file-deleteの4サーバーでenabled/disabled_reasonが実装済みであり、web_search-mcpのみ未対応であることを確認済み。
- 不確実な理由: 実装完了のタイミングと文書更新プロセスの乖離期間が不明。
- 誤っていた場合の影響: 既知の課題として扱われ続け、既に解決済みの問題に対応工数を割いてしまう。
- 推奨対応: MCP-002のステータスを「大半未実装」から「web_search-mcpのみ未対応」に更新し、First Foundフィールドも埋める。

#### Needs confirmation: cicd-mcp workflow_allowlist警告の2レイヤー混同(05_01_access-control-and-allowlists)
- 確認したいこと: Agent層(`repl_health.py`)とcicd-mcp自身(`service_guards.py`)の警告文言が本当に別物か、統合済みか。
- 現在の根拠: 2つの異なるレイヤーの警告文言が単一の警告であるかのように記述されていることを確認済み。
- 不確実な理由: 他サーバーの記述にも同様の混同がないか未確認。
- 誤っていた場合の影響: 障害対応時にどちらのレイヤーのログを見るべきか誤認し、原因特定が遅れる。
- 推奨対応: 2つの警告を別項目として明記し、それぞれの発生条件・出力先を分ける。

### B. 執筆者の意図確認が必要な項目

#### Needs confirmation: roleフィールドの用途(06_03)
- 確認したいこと: `[mcp_servers.*].role`フィールドの参照箇所がコード上ゼロであることの理由。将来実装予定か廃止予定か。
- 現在の根拠: フィールド自体はconfigに存在するが、参照箇所が見つからない。
- 不確実な理由: 設計意図(将来用の予約フィールドか)が文書化されていない。
- 誤っていた場合の影響: 運用者が意味のある値を設定しても効果がないと誤解、または逆に将来重要になる設定を放置する。
- 推奨対応: 執筆者・実装担当に用途を確認し、「未使用の予約フィールド」または「将来実装予定」と明記する。

#### Needs confirmation: 起動失敗時RuntimeErrorの影響範囲(06_05)
- 確認したいこと: MCPサーバー起動失敗時の`RuntimeError`がAgentプロセス全体をクラッシュさせるのか、当該サーバーのみ無効化されるのか。
- 現在の根拠: コード上の例外伝播経路が文書に明記されていない。
- 不確実な理由: 実装を追った限りでは責務境界が曖昧。
- 誤っていた場合の影響: 単一サーバーの設定ミスがシステム全体の障害につながるかどうかの想定が変わり、運用上の危機対応手順に差が出る。
- 推奨対応: 実装担当に例外伝播範囲を確認し、フェイルセーフの設計意図を明記する。

#### Needs confirmation: restart_recommended常にFalse固定の理由(02_02)
- 確認したいこと: 未実装の暫定値か、自動再起動を提供しない意図的な設計か。
- 現在の根拠: 現状値は常にFalseであることをコードで確認済みだが理由の記述がない。
- 不確実な理由: 設計意図が文書化されていない。
- 誤っていた場合の影響: 運用者が誤って本フィールドを信頼し自動復旧を期待する。
- 推奨対応: 執筆者に確認し理由を追記する。

#### Needs confirmation: git-mcp書き込みツールに追加ガードがない理由(04_05_git)
- 確認したいこと: github-mcpとの非対称性(git-mcpには保護ブランチ等の追加ガードがない)が意図的な設計か、単なる未実装か。
- 現在の根拠: コード上、git-mcpの書き込みツールにgithub-mcp相当のガードが存在しないことを確認済み。
- 不確実な理由: 設計意図(ローカルgitはユーザー自身の責任範囲という前提か)が文書化されていない。
- 誤っていた場合の影響: 未実装の安全対策と誤認され、追加実装の優先度判断を誤る。
- 推奨対応: 執筆者・設計担当にローカルGit操作のリスク許容方針を確認し明記する。

#### Needs confirmation: fail_closedという語が設定キーか一般用語か(06_10)
- 確認したいこと: `fail_closed`が実際の設定キー名として存在するのか、それとも設計方針を表す一般用語として使われているのか。
- 現在の根拠: 文脈上どちらとも取れる記述になっている。
- 不確実な理由: 実装上の設定キー名との対応が未確認。
- 誤っていた場合の影響: 開発者が存在しない設定キーを探してしまう、または逆に実在するキーを見落とす。
- 推奨対応: 該当する実際の設定キー名(あれば)を明記し、一般用語として使う場合はその旨注記する。

#### Needs confirmation: ホットリロード経路の有無(03_06_tool-runtime-availability-metadata)
- 確認したいこと: `/v1/tools`がRuntimeToolRegistryのソースであることは分かったが、config変更後にホットリロードされる経路があるか。
- 現在の根拠: 文書上明記がなく、`06_17`の「`/reload`は`[mcp_servers.*]`を変更しない」という制約と関連する可能性がある。
- 不確実な理由: 実装のリロード経路を完全には追えていない。
- 誤っていた場合の影響: 運用者が設定変更後にリロードすれば反映されると誤解し、実際にはプロセス再起動が必要な場面で反映されないまま運用を続ける。
- 推奨対応: 実装担当に確認し、config変更の反映に必要な手順(リロードで足りるか再起動が必要か)を明記する。

#### Needs confirmation: rag-pipeline-mcpオーバーライドモード失敗時挙動(05_04_mdq-rag-boundary)
- 確認したいこと: オーバーライドモード時、失敗した場合にエラーを返すのかフォールバックするのか。
- 現在の根拠: 文書の記述と実装の挙動が食い違う可能性がチャンク5レビューで指摘されている。
- 不確実な理由: 実装の分岐条件を完全には確認できていない。
- 誤っていた場合の影響: 障害時の挙動想定を誤り、呼び出し側のエラーハンドリング設計に影響する。
- 推奨対応: 実装担当にオーバーライドモードの失敗時分岐を確認し、文書とテストケースを突き合わせる。

#### Needs confirmation: rag-pipeline-mcpの監査ログ有無(02_03_audit-logging-and-errors)
- 確認したいこと: rag-pipeline-mcpが監査ログを一切書いていない可能性がある点について、実装上の最終確認。
- 現在の根拠: `06_07`の記述で「file-read/file-write/rag-pipelineがaudit未実装」とされているが、監査ログ矛盾(A群)の修正と合わせて再確認が必要。
- 不確実な理由: `02_03`修正時に合わせて検証していないため未確定。
- 誤っていた場合の影響: 監査要件(セキュリティ・コンプライアンス)の網羅性判断を誤る。
- 推奨対応: `02_03`の修正作業と合わせて実装を再確認し、監査ログ対応サーバー一覧を確定させる。

#### Needs confirmation: browser_fetchのcapabilities=("web_fetch",)採用(08_tool_capability_naming_convention)
- 確認したいこと: この記述が本番コードの実態か、テストフィクスチャのみに存在するものか。
- 現在の根拠: 本番コード検索では確認できず、テストフィクスチャのみに存在する疑いがある。
- 不確実な理由: 検索範囲がテストコードと本番コードを完全に区別できていない可能性がある。
- 誤っていた場合の影響: 実際には別のcapability値が使われているにもかかわらず、この文書を信じて連携ツールを実装してしまう。
- 推奨対応: 実装担当に本番コードでの実際のcapabilities値を確認し、テスト専用の値であれば注記する。
