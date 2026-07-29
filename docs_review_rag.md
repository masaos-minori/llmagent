# RAG領域 設計文書レビュー報告書

## 1. 全体評価

### 連結文書としての問題
`docs/03_rag_*.md` 全40ファイルは、概要文書(00, 01, 02_01, 03_01)→詳細文書(02_02〜02_09, 03_02〜03_07)→リファレンス文書(04_*, 05_*)→設計ノート(90, 91)という階層構造を持つが、各階層で同一情報が繰り返し記述されており、かつ改稿のたびに一部だけが更新されるため階層間で内容が食い違う状態になっている。特に「クラスの公開メソッド一覧」「設定パラメータ表」「DTOフィールド表」「CLI引数表」は、概要・詳細・リファレンスの3層すべてに形を変えて存在し、更新責任の所在が不明確である。

### 重複している情報の傾向
- メソッドシグネチャ・定数一覧・DTOフィールド一覧が、詳細文書とリファレンス文書(05_1, 04_01〜04_05)の双方に重複。
- CLIオプション説明が02_01と各詳細文書(02_02, 02_03, 02_04)で重複。
- 出力JSON形式のサンプルが詳細文書とDTO文書(04_01)で重複。
- 削除順序・鮮度判定・ETag更新といった「設計判断」レベルの記述までもが、複数箇所に微妙に異なる表現で複製されており、これが後述の確定済み誤りの温床になっている。

### コード説明に寄りすぎている領域
クラスのコンストラクタ引数表、モジュールレベル定数表、ログフィールド表、テストのアサーション逐語列挙など、コードそのものを読めば得られる情報がそのまま転記されている箇所が全編にわたり多数存在する。これらは「なぜそうしたか」を伴わない限りReference API・コードコメント・テスト仕様への移動対象である。

### 意図・境界・運用注意として残すべき領域
- RAGとAgentの責務境界(03_01の「対象に含まれないもの」、02_05/02_08の`RagRepository`境界、03_05のcontent/normalized_content不変条件)。
- MCPサーバが担う範囲(05_8冒頭の責務境界宣言、rag_pipeline_mcp_server.tomlがagent.tomlと完全独立という05_1の指摘)。
- DESIGN-2(FTS5コンテンツ分離)・DESIGN-3(documents/chunks/chunks_fts/chunks_vecの責務分離)という91_design_notesの確定済み設計判断。
- プロセス境界をまたぐキャッシュ鮮度問題(03_06)、use_rrf=False時の品質トレードオフ(03_04, 05_1)など、運用上の落とし穴。
- 既知の不具合(ETag doc_id=0、result_source二重定義、reconcile_url()バグ修正記録)。

### 再構成の基本方針
1. Reference API層(シグネチャ・フィールド表・定数表)は本文から切り離し、コード自動生成またはコードコメントへ委譲する。
2. 「コードデフォルト値」と「運用設定値(config/*.toml実測値)」を全ファイルで明示的に区別する書式に統一する(現状は05_5・05_1の一部でしか徹底されていない)。
3. 行番号による参照(例: `repository.py:232`)は変更に弱く複数箇所でズレが確認されたため、関数名・変数名・セクション名ベースの参照に統一する(05_5の方針を全体に横展開)。
4. `03_rag_90_inconsistencies_and_known_issues.md`を実体化し、既知の不具合・未確認事項の単一の集約先として機能させる(現状エントリ0件)。
5. 性能閾値・数値制約について「見積もりか実測か」を明記する運用ルールを設ける。

### 横断的な確定済み誤り(最優先で修正すべき7件)
今回のレビューでは、Needs confirmationとは区別すべき**確認済みの事実誤り**が複数ファイルにまたがって発見された。いずれもコードとの突合により誤りと断定できるため、他の指摘に優先して修正すべきである。

1. **廃止済みコマンドへの言及**: `docs/03_rag_05_2-execution-guide.md`、`docs/03_rag_05_7-rag-index-consistency-checks.md`、`docs/03_rag_91_design_notes-part1.md`の3ファイルが`/db consistency`・`/db rag rebuild-fts`という廃止済みコマンド名を記載している。現行の正しいコマンドは`/session rag-consistency`・`/session rag-rebuild-fts`(`cmd_session.py`)。05_2は廃止に気づいているが後継名を書いておらず、05_7・91は廃止に気づかず現行手順として案内してしまっている。
2. **delete_document()の削除順序不一致**: `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md`は「chunks_vec→chunks→documents」の3段階と記載するが、実装(`document_manager.py`両方)は「chunks_vec→documents(CASCADEでchunks削除)」の2段階であり、`chunks`テーブルへの明示DELETEはコード上存在しない。`docs/03_rag_91_design_notes-part1.md`のDESIGN-3の記述の方が実装と一致する。
3. **ETagManager doc_id=0固定値問題**: `scripts/rag/ingestion/document_manager.py`の`_update_etag()`が`ETagManager(self._db, 0)`とdoc_idを固定値0で渡しており、SQLiteのdoc_idは1始まりのため`UPDATE ... WHERE doc_id = 0`は実質何も更新しない。`docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md`(誤: 更新されると記載)、`docs/03_rag_02_05_ingestion_pipeline-document-manager.md`(参照先とされるが実体記述なし)、`docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`(Needs confirmation扱いだが実際は確定した事実誤り)にまたがって不整合。
4. **crawl_fileの鮮度判定責務の誤帰属**: `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`の「鮮度判定(自動)」節はWebCrawlerの責務として記載しているが、実際にスキップ/再インジェクション判定を行うのは`scripts/rag/ingestion/document_manager.py`の`DocumentManager`(ingesterステージ)である。`crawl_file()`はmtime/SHA-256を計算しペイロードに格納するのみで無条件にJSON出力する。
5. **クロール深度・ページ数上限の食い違い**: `docs/03_rag_01_system_overview-part2.md`は「最大6ホップ」「最大500ページ」と記載するが、実際の`config/crawler.toml`は`max_depth = 3`・`max_pages = 200`。同一文書群内の`docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md`(3ホップ、config一致)とも矛盾している。
6. **`[debug]`出力例の非実在**: `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`と`docs/03_rag_03_04_query_pipeline-search-stages.md`の両方に`/rag search --debug`の出力例として`[debug] http mode: ...`・`[debug] fusion: ...`が掲載されているが、コード全体を検索しても`[debug]`という文字列は1件も存在しない。
7. **chunk_utils.py共有関数の実質的な未共有**: `docs/03_rag_02_07_ingestion_pipeline-utils.md`の「ミックスインでの使用箇所」テーブルは、`ChunkEnglishMixin`・`ChunkJapaneseMixin`が実際には`chunk_utils.py`の関数をほとんど使わず独自実装していることを反映しておらず、設計意図(共有ヘルパー抽出)と実装が乖離している。

---

## 2. 削除候補

### 削除候補: docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md / 「公開メソッド」表・「モジュールレベルのユーティリティ」表
- 現在の記述の問題: メソッドシグネチャの逐語列挙で、設計判断を伴わない。
- 削除理由: コードを読めば即座に分かる内容。
- 削除しても失われない情報: BFS戦略・並行数制御方式についての一行説明は別途本文に残せば設計意図は失われない。
- 移動先: Reference API(自動生成)。

### 削除候補: docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md / 「モジュールレベルの定数」表・「公開メソッド」表
- 現在の記述の問題: 閾値の値だけが列挙され選定理由がない。
- 削除理由: 定数値そのものはコードコメントで十分。
- 削除しても失われない情報: `MIN_HEADING_LINES_FOR_MARKDOWN`等、設計判断に関わる閾値のみ本文に個別記載すれば十分。
- 移動先: コードコメント、Reference API。

### 削除候補: docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md / 出力JSON形式の例・「ロギング」節
- 現在の記述の問題: `docs/03_rag_04_01_dto-models_data.md`(DTO)、`docs/03_rag_05_3-logging.md`(ロギングリファレンス)とそれぞれ内容が重複。
- 削除理由: 正本が別に存在する。
- 削除しても失われない情報: なし(正本側に同等以上の情報あり)。
- 移動先: JSON形式は04_01へ一本化、ロギングは05_3へ統合。

### 削除候補: docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md / 「Dataclass」表・「公開メソッド」表、docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md / 「更新されるDBテーブル」表・「ロギング」構造化フィールド列
- 現在の記述の問題: シグネチャ・フィールドの機械的列挙。
- 削除理由: Reference API/運用Runbookで代替可能。
- 削除しても失われない情報: 削除順序の不変条件・embedding_dims検証など設計判断部分は本文に残すため失われない。
- 移動先: Reference API、運用Runbook。

### 削除候補: docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md / 「関数/シグネチャ/戻り値/説明」表・「定数」表(LOG_KEY_*)・「利用元」表
- 現在の記述の問題: 純粋なAPI一覧。
- 削除理由: コードを読めば分かる。
- 削除しても失われない情報: `MIN_TEXT_LENGTH_FOR_DETECTION=100`のような設計判断値は個別に残す。
- 移動先: Reference API/コードコメント。

### 削除候補: docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md / 「コンストラクタ」表・「公開属性」表・「公開メソッド」表、-part2.md / 「HTTP RAGリクエストの詳細」表
- 現在の記述の問題: シグネチャ列挙とコード例の重複。
- 削除理由: Reference API化が適切。
- 削除しても失われない情報: `module_cfg`のバイパス挙動、`http_result_kind`の意味論は本文に残すため失われない。
- 移動先: Reference API。

### 削除候補: docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md / 「PipelineContext」「SearchDiagnostics」「get_diagnostics()戻り値」の各フィールド表
- 現在の記述の問題: フィールド一覧の逐語転記。
- 削除理由: DTO文書(04_02)と重複。
- 削除しても失われない情報: http_result_kindの二重定義(enum4値 vs 文字列3値)という境界条件は最重要のため残す。
- 移動先: 04_02への統合、Reference API。

### 削除候補: docs/03_rag_03_07_query_pipeline-tests.md / 8.1/8.2表のテスト名・アサーション逐語列挙(18件)
- 現在の記述の問題: テストコードの転記。
- 削除理由: テストファイル自体が正本になり得る。
- 削除しても失われない情報: 「保証されている性質」という要約カテゴリを残せば設計意図は失われない。
- 移動先: テスト仕様/テストファイルへのポインタ。

### 削除候補: docs/03_rag_05_7-rag-index-consistency-checks.md / AUTO-GENERATEDブロック
- 現在の記述の問題: `docs/03_rag_05_1-configuration-reference.md`と内容が重複し、かつ`tools/gen_rag_reference.py`のOPS_DOC定数がファイル分割前の構成を指しているため自動更新が効いていない。
- 削除理由: 二重管理の解消、生成元の不整合解消。
- 削除しても失われない情報: 05_1に同等の情報がある。
- 移動先: docs/03_rag_05_1-configuration-reference.mdへ一本化(OPS_DOC定数の修正も併せて必要)。

### 削除候補: docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md / crawler・chunk_splitter・ingesterのusageブロック(--help出力)、list_documents()シグネチャ
- 現在の記述の問題: CLIヘルプの転記。
- 削除理由: 自動生成可能。
- 削除しても失われない情報: 冒頭の責務境界宣言(RAG MCP内部処理とAgent層DB直接アクセスの区別)は最重要のため残す。
- 移動先: 自動生成Reference API。

---

## 3. 要約候補

### 要約候補: docs/03_rag_01_system_overview-part2.md / 「クエリパイプライン」ステージ表・「MCPサーバーの責務分担」表
- 現在の問題: クラス名や`rrf_k`デフォルト値まで記載し、正典ソースである`docs/03_rag_03_01_query_pipeline-overview.md`と重複。加えて数値部分に確定済み誤り(深度・ページ数)を含む。
- 要約方針: まず数値を実配置設定値(config/crawler.toml)に修正した上で、ステージ名+一行説明のみに圧縮し、詳細は各detail文書への参照に置き換える。
- 要約後のサンプル: 「MQE→検索→融合→リランク→補強の5ステージ。各ステージの詳細はdocs/03_rag_03_02〜03_05を参照。」

### 要約候補: docs/03_rag_02_01_ingestion_pipeline-overview.md / 「ファイルのライフサイクル」表
- 現在の問題: 各段階の出力ファイルパスが02_02/02_03/02_04それぞれのdetail文書と重複。
- 要約方針: 概要レベル(crawl→split→ingestという3段階と出力ディレクトリの位置づけ)のみ残し、ファイル名詳細は各detail文書に委譲。
- 要約後のサンプル: 「crawl結果はrag-src配下のJSONとして出力され、split・ingestが順に消費する。各ファイル形式の詳細は02_02〜02_04を参照。」

### 要約候補: docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md / 「設定パラメータ」表(9項目)
- 現在の問題: `docs/03_rag_05_1-configuration-reference.md`(正典ソース)と重複し、かつコードフォールバック値と運用設定値が区別されていない。
- 要約方針: 責務理解に直結する項目(max_depth, max_pages, skip_nofollow)のみ残し、コードフォールバック値/運用値を明示区別する形に修正。他は05_1参照に統一。
- 要約後のサンプル: 「max_depth(コードフォールバック: 未指定時3 / 運用値: config/crawler.tomlで3)。全パラメータの一覧はdocs/03_rag_05_1参照。」

### 要約候補: docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md / 「CLI引数」テーブル
- 現在の問題: --forceオプションの説明が冗長。
- 要約方針: 「既存チャンクの再生成(センチネルチェック無視)」という1文に圧縮。
- 要約後のサンプル: 「--force: センチネルチェックを無視し既存チャンクを再生成する。」

### 要約候補: docs/03_rag_02_08_ingestion_pipeline-shared.md / 「利用元」テーブル
- 現在の問題: `chunk_splitter.py`が`normalize_unicode`を使うと記載されているが実際は`chunk_japanese.py`のみが使用、`pipeline.py`が`sanitize_document`/`floats_to_blob`を使うと記載されているが実際に直接importするのは`stages/augment.py`と`repository.py`という誤りを含む。
- 要約方針: 誤りを訂正した上で、関数単位の利用元テーブルは項目数を絞り「主要な利用元1〜2箇所」のみ記載する形に圧縮。
- 要約後のサンプル: 「normalize_unicode: chunk_japanese.pyが使用。sanitize_document/floats_to_blob: stages/augment.py, repository.pyが使用(pipeline.pyからの直接呼び出しはない)。」

### 要約候補: docs/03_rag_04_02_dto-models_result.md / SearchDiagnosticsのフィールド表(8個)
- 現在の問題: フィールドが並列に列挙され、追加時期による性質差が読み取れない。
- 要約方針: 「ローカル実行由来のカウンタ」と「HTTP RAGサービス導入後に追加されたremote系フィールド」の2グループに分けて説明する形に圧縮。
- 要約後のサンプル: 「ローカル系: fallback_count等。HTTP導入後追加: http_result_kind, remote_*系(サービス委譲時のみ意味を持つ)。」

### 要約候補: docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md, -part2.md / SemanticCache・RagRepository等のメソッド/SQLクエリ表
- 現在の問題: SQL文とメソッド一覧の詳細転記。
- 要約方針: 各クラスの責務1文+最重要な設計判断(キャッシュ鮮度問題、result_source混同注意)のみ残し、SQL・メソッド表はReference APIへ。
- 要約後のサンプル: 「RagRepository: DBアクセスを集約するヘルパー層。日本語FTS5のトークン化差異はコードコメント参照。」

### 要約候補: docs/03_rag_05_4-error-handling-reference.md / Crawler/ChunkSplitter/RagIngesterのエラーケース表
- 現在の問題: リトライ回数等の細部が個別に記載され設定リファレンスと重複。
- 要約方針: リトライ回数等の数値はdocs/03_rag_05_1参照に統一し、本文には「リトライの有無」「失敗時の挙動(継続/中断)」という設計判断のみ残す。
- 要約後のサンプル: 「HTTPエラーはリトライ対象(回数は05_1参照)。リトライ上限到達後は当該ページをスキップし処理継続。」

---

## 4. 残す・強化する記述

### 強化候補: docs/03_rag_00_document-guide.md / 「コンフリクト解決」節
- 残す理由: 矛盾検出時の運用フローを定めた唯一の記述であり、今回発見された確定済み誤り群の是正プロセスの拠り所となる。
- 強化すべき観点: 「責任を持つドキュメント側で根本原因を修正する」とあるが、誰が・どのタイミングで実施するかのトリガ条件が欠落している。
- 追記例: 「レビューや実装変更で矛盾を検出した場合、Canonical Source Ruleで定めた正本側のファイルを修正し、`docs/03_rag_90_inconsistencies_and_known_issues.md`に検出日・内容を追記する。」

### 強化候補: docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md / 「鮮度判定(自動)」節
- 残す理由: WebCrawlerとDocumentManagerの責務境界を扱う最重要記述だが、現状は責務の誤帰属を含む。
- 強化すべき観点: `crawl_file()`はハッシュ計算とペイロード格納のみ、スキップ/再インジェクション判定は`document_manager.py`の`DocumentManager`(ingesterステージ)が担うという役割分担を明記する。
- 追記例: 「WebCrawler.crawl_file()はmtime/SHA-256を計算しペイロードに格納するのみで、常に無条件でJSONを出力する。スキップ/再インジェクションの判定は`scripts/rag/ingestion/document_manager.py`の`DocumentManager._is_file_unchanged`/`_handle_existing_file`が行う。」

### 強化候補: docs/03_rag_02_06_ingestion_pipeline-supporting-components.md / 「境界条件」節(ETagManager doc_id=0問題)
- 残す理由: DB整合性に直結する既知の不具合であり、安易に削除すべきでない。
- 強化すべき観点: 現状「Needs confirmation」扱いだが、コード読解により`_update_etag()`が`ETagManager(self._db, 0)`でdoc_idを固定値0にしているため実質機能しないことが確定している。Needs confirmationから確定事実へ格上げし、docs/03_rag_02_05・02_04-part1の記述とも整合させる。
- 追記例: 「既知の不具合(確認済み): `_update_etag()`はdoc_idを渡さずETagManager(self._db, 0)を生成するため、スキップ経路でのetag/last_modified更新は事実上行われない(WHERE doc_id=0は既存文書に一致しない)。詳細はdocs/03_rag_90を参照。」

### 強化候補: docs/03_rag_03_01_query_pipeline-overview.md / 「identity vs truthiness」の注記
- 残す理由: `is not None`判定と空文字列""の扱いという、実装者が最も誤解しやすい挙動を正確に説明している。
- 強化すべき観点: なぜこの判定方式を採用したか(空の検索結果と未実行を区別する必要性)という設計理由を補足する。
- 追記例: 「""は有効な(空の)結果として扱われ、Noneは未実行を表す。これにより「検索したが0件だった」と「まだ検索していない」を区別できる。」

### 強化候補: docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md / `http_result_kind`分類表・「remote_emptyはフォールバックではなく成功」の注記
- 残す理由: HTTPモードの成否判定という設計判断の中核であり実装確認済みで正確。
- 強化すべき観点: 「無限委譲の防止」(rag_service_url=""をハードコード)の設計理由が書かれていない。
- 追記例: 「MCPアダプタ側でrag_service_url=""を固定することで、HTTP委譲先が再度HTTP委譲を試みる無限ループを構造的に防止している。」

### 強化候補: docs/03_rag_03_04_query_pipeline-search-stages.md / 「検索品質のトレードオフ」節(use_rrf=False)
- 残す理由: 代替案とその却下理由を明記した模範的な設計判断記述であり、コードとも整合確認済み。
- 強化すべき観点: 起動時警告の記述が実装(`pipeline.py:152-155`)と食い違っているため、参照先を修正する。
- 追記例: 「use_rrf=False設定時はpipeline.py内で起動時に警告ログが出力される(config_validator.py経由ではない)。」

### 強化候補: docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md / 「CLIインジェスト後のキャッシュ鮮度」節
- 残す理由: プロセス境界をまたぐ状態管理の正本問題であり運用上の最重要注意点。
- 強化すべき観点: 具体的にどのタイミングで再起動が必要か(CLIでインジェスト後、クエリプロセスを再起動しない限りキャッシュが古いままか)を明記する。
- 追記例: 「CLIでの再インジェスト後、稼働中のクエリプロセスのSemanticCacheは自動的には無効化されない。反映させるにはプロセス再起動または明示的なinvalidate()呼び出しが必要。」

### 強化候補: docs/03_rag_05_1-configuration-reference.md / 「プロセス分離ポリシー」節
- 残す理由: rag_pipeline_mcp_server.tomlとagent.tomlが完全独立で同名キーが別値を持ちうるという、実装者が誤解しやすい最重要ポイント。
- 強化すべき観点: ファイルパスの誤記(`server.py`/`service.py`/`models.py`という短縮名)を実ファイル名(`rag_pipeline_server.py`/`rag_pipeline_service.py`/`rag_pipeline_models.py`)に修正する。`refiner_max_chars_per_chunk`の乖離(コードデフォルト800、運用値300)が未記載のため追記する。
- 追記例: 「refiner_max_chars_per_chunk: コードデフォルト800 / 運用設定値300(config/rag_pipeline_mcp_server.toml)。他パラメータと同様に乖離を明記。」

### 強化候補: docs/03_rag_05_6-local-file-re-ingestion.md / ETagではなくSHA-256ハッシュで差分検知する設計判断
- 残す理由: file:// URLの整合性検知メカニズムという責務境界に関わる重要記述。
- 強化すべき観点: 本ファイルはetag_manager.py等の実コード突合が未実施のため、次回レビューでの検証を推奨する旨を明記する。
- 追記例: 「(未検証: 本節の記述はetag_manager.pyとの直接突合を実施していない。次回レビューで検証予定。)」

### 強化候補: docs/03_rag_91_design_notes-part1.md / DESIGN-3「強制再挿入時の削除順序」
- 残す理由: 実装(chunks_vec→documents、CASCADEでchunks削除)と一致確認済みの正確な記述であり、docs/03_rag_05_8の誤りを正すための正本となる。
- 強化すべき観点: `/db rab rebuild-fts`という廃止コマンドの記載を`/session rag-rebuild-fts`に修正する。
- 追記例: 「FTSインデックスの再構築は`/session rag-rebuild-fts`コマンドで行う(旧`/db rag rebuild-fts`は廃止済み)。」

---

## 5. Before / After 書き換え例

### 例1: 廃止済みコマンドの記載

**対象**: docs/03_rag_91_design_notes-part1.md(同様の誤りがdocs/03_rag_05_7-rag-index-consistency-checks.mdにも存在)

- Before: 「FTSインデックスの再構築が必要な場合は `/db rag rebuild-fts` を実行する。」
- After: 「FTSインデックスの再構築が必要な場合は `/session rag-rebuild-fts` を実行する(旧`/db rag rebuild-fts`は廃止済み、cmd_session.py参照)。」
- 書き換え理由: `/db rag rebuild-fts`はソースファイルが存在せず(`__pycache__`の.pycのみ残存)、実行不能な手順を案内していた。廃止事実だけでなく現行コマンド名を明記する必要がある。

### 例2: delete_document()の削除順序

**対象**: docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md

- Before: 「delete_document()はchunks_vec→chunks→documentsの3段階で削除を行う。」
- After: 「delete_document()はchunks_vec→documentsの2段階で削除を行う。documentsテーブルの削除はCASCADE制約によりchunksテーブルの関連行を連鎖削除する。chunksテーブルへの明示的なDELETE文はコード上存在しない(docs/03_rag_91_design_notes-part1.md DESIGN-3参照)。」
- 書き換え理由: `document_manager.py`(両実装)を確認した結果、chunksへの明示DELETEは実装されておらずCASCADEのみで削除される。91_design_notes-part1の記述の方が実装と一致するため、そちらを正本として05_8を修正する。

### 例3: ETagManagerのdoc_id=0固定値問題

**対象**: docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md

- Before: 「スキップ経路のガードによりetag/last_modifiedはUPDATEされる。」
- After: 「既知の不具合(確認済み): `_update_etag()`は`ETagManager(self._db, 0)`を生成しdoc_idを渡していないため、`UPDATE ... WHERE doc_id = 0`は既存文書(doc_idは1始まり)に一致せず、スキップ経路でのetag/last_modified更新は実質機能しない。詳細はdocs/03_rag_90_inconsistencies_and_known_issues.mdを参照。」
- 書き換え理由: コード読解で確定した不具合を「更新される」という誤った前提で記述しており、実装者が誤解する。確定事実として明記し、Known Issuesへの参照を追加する。

### 例4: crawl_fileの鮮度判定責務の誤帰属

**対象**: docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md

- Before: 「鮮度判定(自動): crawl_fileはmtime/SHA-256を用いて変更を検知し、変更がなければスキップする。」
- After: 「crawl_file()はmtime/SHA-256を計算しペイロードに格納するのみで、常に無条件でJSONファイルを出力する(スキップ判定は行わない)。実際のスキップ/再インジェクション判定は`scripts/rag/ingestion/document_manager.py`の`DocumentManager`(ingesterステージ)が`_is_file_unchanged`/`_handle_existing_file`で行う。」
- 書き換え理由: 責務がWebCrawlerにあるかのように書かれているが、実際はDocumentManagerの責務であり、RAGとAgentの責務境界と同様に本ドメインの重点観点である「モジュール間の責務境界」を誤らせる記述だったため。

### 例5: クロール深度・ページ数上限の設定値

**対象**: docs/03_rag_01_system_overview-part2.md

- Before: 「クロール深度: 開始URLから最大6ホップ。クロールページ数上限: サイトあたり最大500ページ(config/crawler.toml)。」
- After: 「クロール深度: config/crawler.tomlの運用値は3(max_depth=3)。コード側フォールバック値は別途存在するため、参照時は運用設定ファイルの値を優先する。クロールページ数上限: 運用値は200(max_pages=200、config/crawler.toml)。500はコードのフォールバック値であり運用値ではない。」
- 書き換え理由: 実際の`config/crawler.toml`はmax_depth=3・max_pages=200であり、コードのフォールバック値と混同していた。同一文書群内のdocs/03_rag_02_02_ingestion_pipeline-crawler-part1.mdの記述(3ホップ)とも矛盾しており、運用値とコードデフォルト値を区別しないまま記載したことが原因。

---

## 6. Needs confirmation 一覧

### A. 確認済みの事実誤り(優先度高)

### Needs confirmation: 廃止コマンド`/db consistency`・`/db rag rebuild-fts`(docs/03_rag_05_2, 05_7, 91_design_notes-part1)
- 確認したいこと: 表記の統一と後継コマンド名の明記。
- 現在の根拠: cmd_session.pyに`/session rag-consistency`・`/session rag-rebuild-fts`が実装されている一方、`/db consistency`・`/db rag rebuild-fts`のソースは見つからない(.pycのみ残存)。
- 不確実な理由: なし(確定済み)。
- 誤っていた場合の影響: 運用担当者が実行不能な手順で障害対応を試み、復旧が遅延する。
- 推奨対応: 3ファイルを一括修正し、docs/03_rag_90へ「旧コマンド廃止」のエントリを追記。

### Needs confirmation: delete_document()の削除順序(docs/03_rag_05_8 vs 91_design_notes-part1)
- 確認したいこと: どちらが実装と一致するかの最終確定。
- 現在の根拠: `document_manager.py`(rag/ingestionおよびmcp_servers/rag_pipeline双方)にchunksテーブルへの明示DELETEが存在せずCASCADE削除のみ確認。
- 不確実な理由: なし(コード確認済み)。
- 誤っていた場合の影響: DB削除処理のレビューア・実装者が存在しない3段階目を前提にコードを読み違え、CASCADE制約変更時の影響範囲を誤判断する。
- 推奨対応: 05_8を91_design_notes-part1の記述に合わせて修正し、docs/03_rag_90へエントリ追加。

### Needs confirmation: ETagManager doc_id=0固定値問題(docs/03_rag_02_04-part1, 02_05, 02_06)
- 確認したいこと: この不具合が既にissue化されているか、意図した仕様か。
- 現在の根拠: `_update_etag()`が`ETagManager(self._db, 0)`を生成しdoc_idを渡していないことをコードで確認。
- 不確実な理由: 意図した挙動である可能性は理論上排除できないが、doc_id=0固定は明らかにバグの特徴を持つ。
- 誤っていた場合の影響: etag/last_modifiedベースの差分検知が機能せず、不要な再インジェクションまたは更新見逃しが継続する。
- 推奨対応: issue起票のうえdocs/03_rag_90へ確定事実として登録し、02_04/02_05/02_06の記述を統一。

### Needs confirmation: crawl_fileの鮮度判定責務の誤帰属(docs/03_rag_02_02-part2)
- 確認したいこと: なし(コード確認済みで確定)。
- 現在の根拠: `crawler.py`のcrawl_file()にスキップロジックがなく、`document_manager.py`のDocumentManagerに実装されていることをコードで確認。
- 不確実な理由: なし。
- 誤っていた場合の影響: 実装者がWebCrawler側にスキップロジックを追加しようとし、DocumentManagerとの二重実装・競合を生む。
- 推奨対応: 02_02-part2を責務境界に沿って修正。

### Needs confirmation: クロール深度・ページ数上限の食い違い(docs/03_rag_01-part2 vs 02_02-part1 vs config/crawler.toml)
- 確認したいこと: なし(config/crawler.tomlの実値で確定)。
- 現在の根拠: config/crawler.tomlの`max_depth=3`, `max_pages=200`を確認。
- 不確実な理由: なし。
- 誤っていた場合の影響: 運用担当者がクロール範囲の見積もりを誤り、想定外の負荷やクロール漏れを引き起こす。
- 推奨対応: 01-part2を修正し、コードフォールバック値と運用値を明示区別する注記を追加。

### Needs confirmation: `[debug]`出力例の非実在(docs/03_rag_03_02-part2, 03_04)
- 確認したいこと: `/rag search --debug`というコマンド自体および出力フォーマットが現存するか。
- 現在の根拠: リポジトリ全体をgrepしても`[debug]`という文字列を含むコードが見つからない。
- 不確実な理由: 別名のデバッグ出力に置き換わった可能性、あるいはドキュメント作成時の想定機能で実装されなかった可能性の両方があり、どちらか判別できていない。
- 誤っていた場合の影響: 運用担当者が存在しないオプションを試して混乱する。
- 推奨対応: 実装担当者に現行のデバッグ出力手段を確認のうえ、両ファイルを同時に修正または削除。

### Needs confirmation: chunk_utils.py共有関数の実質的な未共有(docs/03_rag_02_07)
- 確認したいこと: なし(コード確認済み)。
- 現在の根拠: `ChunkEnglishMixin`は`start_next_buf`のみ使用し独自実装、`ChunkJapaneseMixin`は何もインポートせず独自実装。`merge_text_items`を実際に使うのは`ChunkSplitter._chunk_code`のみ。
- 不確実な理由: なし。
- 誤っていた場合の影響: chunk_utils.pyを修正すれば全チャンク化ロジックに反映されると誤解し、英語・日本語チャンク化に反映されないバグを埋め込むおそれがある。
- 推奨対応: 表を実態に合わせて訂正し、リファクタリング未完了である旨を明記(将来の統合予定があるかは別途確認)。

### Needs confirmation: delete_existing_document()というメソッド名の誤記(docs/03_rag_02_04-part1)
- 確認したいこと: なし(コード確認済み)。
- 現在の根拠: `scripts/mcp_servers/rag_pipeline/document_manager.py`には`delete_existing_document()`は存在せず、実際は`delete_document(url: str)`。
- 不確実な理由: なし。
- 誤っていた場合の影響: コードを検索してもメソッドが見つからず、実装者が混乱する。
- 推奨対応: メソッド名を`delete_document(url)`に修正。

### Needs confirmation: ファイル名の誤記(docs/03_rag_05_1)
- 確認したいこと: なし(コード確認済み)。
- 現在の根拠: 「server.py」「service.py」「models.py」という短縮表記は実際には`rag_pipeline_server.py`/`rag_pipeline_service.py`/`rag_pipeline_models.py`。
- 不確実な理由: なし。
- 誤っていた場合の影響: 実装者がベースクラス用ファイル(存在すれば)と混同し、誤ったファイルを編集する。
- 推奨対応: フルファイル名に修正。

### Needs confirmation: 行番号参照のズレ(複数箇所)
- 確認したいこと: なし(各箇所コード確認済み)。
- 現在の根拠: 「config/agent.toml:43」(実際17行目、docs/03_rag_01-part2)、「repository.py:232」(実際237行目、docs/03_rag_03_02-part1)、「llm_client.py:49」(実際56行目、docs/03_rag_03_06-part2)、「call_rag_service()のtimeout=10.0がリファレンス側で121行目と記載(実際123行目、docs/03_rag_05_1)」の4件で行番号ズレを確認。
- 不確実な理由: なし。
- 誤っていた場合の影響: 実装者が指定行を見ても該当コードが見つからず、誤って別の記述をコンテキストと誤認する。
- 推奨対応: 全箇所で行番号参照をキー名・関数名・変数名ベースの参照に置き換える(docs/03_rag_05_5が既に採用している方針を横展開)。

### Needs confirmation: refiner_max_chars_per_chunkの乖離未記載(docs/03_rag_05_1)
- 確認したいこと: なし(コード確認済み)。
- 現在の根拠: コードデフォルト800に対し運用設定値は300だが、他項目は乖離を注記しているのにこの項目のみ注記がない。
- 不確実な理由: なし。
- 誤っていた場合の影響: 運用値300を前提にしたチューニング判断で、実装者がコードデフォルト800を参照し誤った見積もりをする。
- 推奨対応: 他項目と同様の乖離注記を追加。

### Needs confirmation: use_rrf=False時の起動時警告の出力元不一致(docs/03_rag_03_04)
- 確認したいこと: なし(コード確認済み)。
- 現在の根拠: 文書は「config_validator.py経由」と記載するが、実際の警告は`pipeline.py:152-155`。
- 不確実な理由: なし。
- 誤っていた場合の影響: 障害調査時に誤ったファイルのログ出力箇所を探し、原因特定が遅延する。
- 推奨対応: 参照元をpipeline.pyに修正。

### Needs confirmation: 「利用元」テーブルの誤り(docs/03_rag_02_08)
- 確認したいこと: なし(コード確認済み)。
- 現在の根拠: `chunk_splitter.py`が`normalize_unicode`を使うと記載されているが実際は`chunk_japanese.py`のみ。`pipeline.py`が`sanitize_document`/`floats_to_blob`を使うと記載されているが実際の直接呼び出しは`stages/augment.py`・`repository.py`。
- 不確実な理由: なし。
- 誤っていた場合の影響: 依存関係を誤認し、リファクタリング時に影響範囲を見誤る。
- 推奨対応: テーブルを実態に合わせて修正。

### B. 執筆者の意図確認が必要な項目

### Needs confirmation: FTS5クエリのトークン数上限20の根拠(docs/03_rag_02_08)
- 確認したいこと: `_MAX_FTS_TOKENS = 20`という具体値が実測に基づくものか経験則か。
- 現在の根拠: コード上の値自体は一致確認済みだが、「クエリ爆発を防ぐため」という理由のみで具体的な根拠(実測データ、負荷試験結果等)が本文にもコードにもない。
- 不確実な理由: 見積もりか実測かの区別が本ドメインの重点観点であるにもかかわらず本文に記載がない。
- 誤っていた場合の影響: 将来の性能問題発生時に、20という値の妥当性を再検証する手がかりがない。
- 推奨対応: 執筆者または実装担当者に根拠を確認し、見積もり/実測の別を明記。

### Needs confirmation: MIN_TEXT_LENGTH_FOR_DETECTION=100の根拠(docs/03_rag_02_09)
- 確認したいこと: 言語判定の閾値100文字が実測か経験則か。
- 現在の根拠: 値自体はコードと一致するが根拠の記載がない。
- 不確実な理由: 同上。
- 誤っていた場合の影響: 短文の言語誤判定が発生した場合、閾値見直しの判断材料がない。
- 推奨対応: 根拠を確認のうえ追記。

### Needs confirmation: MIN_HEADING_LINES_FOR_MARKDOWN=2の決定根拠(docs/03_rag_02_03-part1)
- 確認したいこと: 実験的な調整結果か経験則か。
- 現在の根拠: 値の記載はあるが根拠なし。
- 不確実な理由: 同上。
- 誤っていた場合の影響: Markdown見出しチャンク化の挙動を変更する際、閾値変更の妥当性を判断できない。
- 推奨対応: 執筆者に確認。

### Needs confirmation: 未使用の疑いがあるDTO群(docs/03_rag_04_01のRegisteredDocument、04_03のAuditLogRecord/ApprovalDecision、04_04のConfig系dataclass、04_05のPipelineRunResult.result_source)
- 確認したいこと: 将来利用見込みの先行定義か、削除し忘れの残骸か。
- 現在の根拠: いずれもgrep突合の結果、自身の定義以外から参照されていないことを確認済み。
- 不確実な理由: 「未使用」であることは確認できるが、削除可否の判断(将来計画の有無)は文書からもコードからも判断できない。
- 誤っていた場合の影響: 誤って削除すると将来実装予定だった機能の設計情報が失われる。逆に残し続けると保守負荷が増え、DTOと実行時経路の乖離(04_04の設定系dataclassが実際の設定読み込み経路と未接続)がさらに拡大する。
- 推奨対応: 実装担当者に将来計画の有無を確認し、docs/03_rag_90へKnown Issues/Needs Confirmation Inventoryとして一本化。個別ファイルへの分散記載をやめる。

### Needs confirmation: PipelineRunResult.result_sourceとSearchDiagnostics.result_sourceの二重定義の解消方針(docs/03_rag_03_06-part2, 04_05)
- 確認したいこと: 他の呼び出し経路(プラグイン等)でPipelineRunResult.result_sourceが明示的に設定されるケースがあるか。
- 現在の根拠: grep突合でPipelineRunResult.result_sourceは常にNoneであることを確認。
- 不確実な理由: 全呼び出し経路を網羅的に確認したわけではない。
- 誤っていた場合の影響: 実装者がPipelineRunResult.result_sourceを参照し、常にNoneであることに気づかず不具合を見逃す。
- 推奨対応: 全呼び出し元の洗い出しを実施し、確定次第どちらか一方のフィールドを廃止するか用途を明確に分離する。

### Needs confirmation: HTTPモード成功時のlast_fetch_result更新有無(docs/03_rag_03_03)
- 確認したいこと: call_rag_service()呼び出し後、実際にHTTPモードでfetch_resultが更新されるか。
- 現在の根拠: call_rag_service()のdocstringには「set_fetch_resultは定義されているが呼ばれない」と明記されている。
- 不確実な理由: docstringの記述と実際の呼び出しグラフの網羅的突合までは実施していない。
- 誤っていた場合の影響: HTTPモードでの診断情報(fetch_result)が更新されないまま運用され、障害調査時に古い情報を参照してしまう。
- 推奨対応: 呼び出しグラフを再確認し、断定を避けたまま本文にNeeds confirmationとして明記(既にその方針で記載されている点は適切)。

### Needs confirmation: ingestion設定dataclass(models_config.py)の将来的な検証計画(docs/03_rag_04_04)
- 確認したいこと: TOMLスキーマ検証を将来これらのdataclassで行う計画があるか、別の検証手段に置き換え済みか。
- 現在の根拠: grep突合の結果インスタンス化箇所が見つからず、ConfigLoaderが返す生dictを直接参照している実態を確認。
- 不確実な理由: 将来計画の有無は文書・コードいずれからも判断できない。
- 誤っていた場合の影響: 設定値の型検証が行われないまま運用が継続し、誤設定の検知が遅れる。
- 推奨対応: 設計担当者に将来計画を確認し、計画がなければdataclass自体の削除を検討。

### Needs confirmation: etag_manager.py等ローカルファイル再取り込み機構の未検証部分(docs/03_rag_05_6)
- 確認したいこと: SHA-256ハッシュベース差分検知の記述がetag_manager.py実装と完全に一致するか。
- 現在の根拠: 本ファイルは今回のレビュー範囲でコード突合が未実施。
- 不確実な理由: 他ファイルで発見された誤り(ETag doc_id=0問題等)との関連可能性があるが、本ファイル自体は未検証。
- 誤っていた場合の影響: 05_6の記述にも同種の誤りが潜んでいる可能性を排除できない。
- 推奨対応: 次回レビューサイクルでetag_manager.pyとの突合を実施する。

### Needs confirmation: 90_inconsistencies_and_known_issues.mdの本文欠落(docs/03_rag_90)
- 確認したいこと: 本来あるべき既知の不具合・矛盾のエントリが、移行前フォーマットには存在していたのか、移行時に本文が失われたのか。
- 現在の根拠: 現状のファイルには移行ノートとキーワードのみで実体エントリが0件。
- 不確実な理由: 移行履歴(git log等)を確認しない限り判断できない。
- 誤っていた場合の影響: 既知の不具合の集約先が機能せず、今回発見した7件の確定済み誤りを含む重要情報が分散したまま放置される。
- 推奨対応: 移行履歴を確認のうえ、今回のレビューで確認した全ての確定済み誤り・Needs confirmation項目をこのファイルに一元的に追記する。
