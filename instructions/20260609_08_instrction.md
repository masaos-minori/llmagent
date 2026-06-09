# agent/memory 改修計画書 実行計画版

## 1. 目的

本計画書は、添付された `agent/memory` 配下の Python 実装を対象として、責務の整理、重複実装の削減、永続化経路の一貫化、検索・注入品質の改善、および後方互換性維持のために残置された旧機能の削除方針と実施手順を定義するものである。対象には `services.py`、`types.py`、`store.py`、`embedding_client.py`、`mapper.py`、`jsonl_store.py`、`injection.py`、`retriever.py`、`extract.py`、`ingestion.py` を含む。

## 2. 対象範囲

本計画書の対象範囲は以下とする。

- メモリの型定義、抽出、保存、検索、注入に関する実装全体。`types.py` はデータ型、`extract.py` は抽出、`jsonl_store.py` と `store.py` は保存、`retriever.py` は検索、`injection.py` は注入、`ingestion.py` は抽出から保存までの統合経路を担う。
- `services.py` に定義された `MemoryServices` コンテナを含む依存注入境界。`services.py` には `MemoryServices` が `MemoryLayer` を置き換える旨が記載されている。

## 3. 前提と確認範囲

- `mapper.py`、`jsonl_store.py`、`injection.py`、`embedding_client.py`、`extract.py`、`ingestion.py`、`services.py` は取得できた内容から具体的な改善点を確認できた。
- `types.py`、`store.py`、`retriever.py` は取得結果が先頭中心であり、責務説明や一部定義は確認できたが、内部実装の全量までは確認できていない。そのため、これら 3 ファイルについては、見えている責務記述と公開定義に基づく計画として記述する。

## 4. 全体方針

### 4.1 基本方針

1. 書き込み経路を単一化する。現在は `ingestion.py` が JSONL と SQLite の両方へ保存し、`jsonl_store.py` は JSONL を source of truth と明記している。保存責務が分散しているため、永続化入口を 1 系統に統一する。
2. `MemoryEntry` の生成・復元・既定値注入を 1 箇所に集約する。現在は `mapper.py` の `row_to_entry()` と `jsonl_store.py` の `_entry_from_dict()` が類似責務を持つ。
3. 検索スコアと近傍距離の契約を明示化する。`ingestion.py` は `retriever.py` の KNN 検索結果を「負距離」として扱っているため、暗黙契約を排除する。
4. 抽出・注入・埋め込み生成のポリシーを設定化し、コード埋め込みされた閾値・接頭辞・キーワードを外出しする。`extract.py` と `injection.py` には閾値・接頭辞・正規表現・文字数制限が定数で埋め込まれている。
5. 後方互換性維持のために残された旧機能は削除する。特に `services.py` には `MemoryLayer` を置き換える旨が明記されており、旧互換層が周辺コードに残っている場合は削除対象とする。

### 4.2 設計方針

- 型定義を中心に据え、復元、検証、既定値補完の責務を `types.py` 側へ寄せる。`MemoryEntry` が中心データ型であり、`mapper.py` と `jsonl_store.py` がそれぞれ独自に復元を行っている状態は整理対象である。
- 検索は FTS・KNN・RRF を組み合わせる構成であるため、検索器とスコアリングを分離し、呼び出し側が内部スコア表現に依存しない構造へ改める。`retriever.py` には FTS5、KNN、RRF merge、各種 boost 定数が同居している。
- サービスコンテナは依存集約に限定し、永続化内部や検索内部を利用側へ露出しすぎない。`services.py` では `store` と `retriever` も保持している。

## 5. 実施フェーズ

### 5.1 フェーズ構成

- フェーズ1: 即時不整合の修正
- フェーズ2: 永続化と型復元の統一
- フェーズ3: 検索と注入の構造整理
- フェーズ4: 抽出ポリシーと設定化
- フェーズ5: 旧互換コードの削除と仕上げ

## 6. Implementation steps

### 6.1 フェーズ1: 即時不整合の修正

#### Step 1-1. `embedding_client.py` の埋め込み要求不整合を修正

##### 目的
`_fetch_embedding()` が受け取った `text` を埋め込み API に渡していない状態を解消する。取得できた範囲では POST 本文が `json={"content": f"query: "}` となっている。

##### 実施内容

- `_fetch_embedding(text, http, embed_url)` の POST 本文に `text` を反映する
- 例外ログに例外オブジェクトの内容を出力する
- `EmbeddingResult.error_kind` の分類を見直す準備として、ログ出力粒度を上げる

##### 成果物

- 修正版 `embedding_client.py`
- 例外ログ確認結果

##### 完了条件

- 埋め込み API 呼び出しが入力 `text` を使用する
- HTTP エラー時および一般例外時に具体的なエラー情報がログへ残る



#### Step 1-2. `injection.py` の未使用引数と出力規則の不整合を修正

##### 目的
`on_session_start(session_id)` の `session_id` 未使用、および `format_prefix_*` と `"[Memory]"` 固定文字列の不整合を解消する。

##### 実施内容

- `session_id` を利用するか削除するか方針を決定する
- `on_session_start()` と `on_user_prompt()` のスニペット接頭辞規則を統一する
- `summary or content[:100]` の整形ロジックをポリシー化する準備を行う

##### 成果物

- 修正版 `injection.py`
- 注入フォーマット仕様メモ

##### 完了条件

- 未使用引数が残っていない
- セッション開始時と問い合わせ時でスニペット表現が一貫している



#### Step 1-3. `ingestion.py` の保存経路差分を解消

##### 目的
`on_session_stop()` と `_persist_entry()` の永続化経路差分をなくし、保存結果の意味を統一する。取得できた内容では `on_session_stop()` は dedup と duplicate link 記録まで行う一方、`_persist_entry()` は単純保存のみである。

##### 実施内容

- 保存共通関数を定義し、`on_session_stop()` と `write_*()` が同じ保存パイプラインを通るように変更する
- dedup 判定、JSONL 書き込み、SQLite upsert、duplicate link 作成の適用条件を整理する
- `write_semantic()` / `write_episodic()` が経路差分を持たないよう構造を調整する

##### 成果物

- 修正版 `ingestion.py`
- 保存フロー図

##### 完了条件

- 手動書き込みと自動抽出書き込みで保存経路が一致する
- dedup と duplicate link の適用単位がコード上で一貫している



### 6.2 フェーズ2: 永続化と型復元の統一

#### Step 2-1. `MemoryEntry` 復元処理の統合設計を定義

##### 目的
`mapper.py` の `row_to_entry()` と `jsonl_store.py` の `_entry_from_dict()` に分散している復元ロジックを統合する。

##### 実施内容

- `MemoryEntry` 復元責務を `types.py` 側または専用 factory / codec へ集約する方針を確定する
- 既定値注入、タグ JSON decode、型変換、検証失敗時の扱いを共通契約として定義する
- 呼び出し元 `mapper.py` と `jsonl_store.py` を薄い変換層へ縮退させる設計にする

##### 成果物

- 型復元仕様
- 統合先モジュール設計メモ

##### 完了条件

- `MemoryEntry` 復元ルールが 1 箇所に定義されていると明言できる状態になる



#### Step 2-2. `mapper.py` と `jsonl_store.py` を統合設計へ寄せる

##### 目的
実コード上の復元重複を削除する。

##### 実施内容

- `mapper.py` は SQLite row から統一復元関数を呼ぶだけにする
- `jsonl_store.py` は dict から統一復元関数を呼ぶだけにする
- 個別の既定値注入や型変換コードを撤去する

##### 成果物

- 修正版 `mapper.py`
- 修正版 `jsonl_store.py`

##### 完了条件

- 復元ロジックの重複が消えている
- `mapper.py` と `jsonl_store.py` が同じ復元契約に従う



#### Step 2-3. JSONL / SQLite 二重書き込みの整合性戦略を決定

##### 目的
`jsonl_store.py` が source of truth とされる一方で、`ingestion.py` が JSONL と SQLite を逐次更新している構造の整合性問題に対処する。

##### 実施内容

- JSONL 優先、SQLite 再構築可能、または同期成功を前提とするかの戦略を決める
- `store.py` の `check_consistency()` が担うべき役割を明確化する
- 再同期機能または検知ログの必要性を整理する

##### 成果物

- 永続化整合性方針
- 障害時の扱いメモ

##### 完了条件

- JSONL と SQLite のどちらを基準とするかが明確
- 片系失敗時の扱いが定義されている



### 6.3 フェーズ3: 検索と注入の構造整理

#### Step 3-1. `retriever.py` のスコア契約を明文化

##### 目的
`knn_search()` の返却 `score` を `ingestion.py` が負距離として解釈している暗黙契約を解消する。

##### 実施内容

- `MemoryHit` または関連返却型に距離または類似度の意味を明示する方針を決める
- FTS と KNN のスコア表現を分離し、呼び出し側が `-score` 変換をしない形へ改める
- dedup 判定と duplicate link 判定が明示的な距離値を使うよう見直す

##### 成果物

- 検索スコア契約仕様
- `retriever.py` / `ingestion.py` 修正版

##### 完了条件

- 呼び出し側が `-hit.score` に依存しない
- score の意味がコメントではなく型・契約として表現される



#### Step 3-2. `retriever.py` の責務を分割

##### 目的
FTS、KNN、Hybrid、RRF merge が同居する構造を段階的に整理する。取得できた内容ではこれらが 1 ファイルに集約されている。

##### 実施内容

- FTS クエリ生成、FTS 検索、ベクトル検索、統合スコアリングを分ける設計を作成する
- まずモジュール内関数分離を行い、その後必要に応じてファイル分割する
- `_build_fts_query()` のトークン生成は単独責務として切り出す

##### 成果物

- 検索モジュール分割案
- 段階的移行実装

##### 完了条件

- `retriever.py` 内で責務境界が読み取れる
- FTS と KNN の評価ロジックが分離されている



#### Step 3-3. `injection.py` の注入戦略を統一

##### 目的
`on_session_start()` と `on_user_prompt()` の検索・整形経路の差を縮小し、ポリシー起点で一貫した注入設計にする。

##### 実施内容

- セッション開始時注入と問い合わせ時注入の違いをポリシーで表現する
- semantic / episodic の件数制御と重要度閾値を統一的に扱う
- 整形文字数上限、prefix、summary 優先規則を設定へ寄せる

##### 成果物

- 修正版 `injection.py`
- 注入ポリシー定義

##### 完了条件

- 注入戦略がメソッドごとの個別実装ではなく、共通ポリシーで説明できる



### 6.4 フェーズ4: 抽出ポリシーと設定化

#### Step 4-1. `extract.py` の抽出ルールを設定化

##### 目的
semantic / episodic 抽出が英語キーワードや固定閾値に結びついている状態を改善する。

##### 実施内容

- `MIN_CONTENT_CHARS`、`MIN_USER_CONTENT_CHARS`、`MIN_TURNS`、`MAX_ENTRIES` を設定化する
- `_SEMANTIC_KEYWORDS`、`_EPISODIC_FAILURE_KEYWORDS` を設定駆動へ寄せる
- 言語依存キーワードをコード埋め込みから外す

##### 成果物

- 抽出設定定義
- 修正版 `extract.py`

##### 完了条件

- 閾値とキーワード定義がハードコードから設定へ移行している



#### Step 4-2. 要約・重要度・分類規則を整理

##### 目的
`_classify_content()`、`_importance_from_content()`、`_make_summary()` に分散したヒューリスティックを整理する。

##### 実施内容

- 分類規則、重要度算出規則、summary 規則をポリシーとしてまとめる
- `ingestion.py` の `_build_manual_entry()` が使用する summary 規則と統一する
- 全文判定と保存文字数制御を分離する

##### 成果物

- 抽出・要約ポリシー
- `extract.py` / `ingestion.py` 修正版

##### 完了条件

- 手動登録と自動抽出で summary 規則が一致している
- 重要度計算と分類の責務境界が整理されている



### 6.5 フェーズ5: 旧互換コードの削除と仕上げ

#### Step 5-1. `MemoryLayer` 互換コードの削除

##### 目的
`services.py` にある「`MemoryLayer` の置換済み」という記述に沿い、旧互換コードを整理する。添付コード中では互換実装本体は確認できないが、削除対象確認は必要である。

##### 実施内容

- `AppServices.memory` に関わる周辺コードを確認する
- `MemoryLayer` 名称、旧別名、旧ラッパ、旧注入経路が残っていれば削除する
- ドキュメント・参照コードを `MemoryServices` に統一する

##### 成果物

- 互換コード削除一覧
- 参照更新結果

##### 完了条件

- 旧 `MemoryLayer` に依存するコードパスが残っていない



#### Step 5-2. 未使用引数・未使用設定・重複処理の削除

##### 目的
改修後に残る不要コードを整理し、最終状態を簡潔にする。取得できたコードには未使用または重複が疑われる箇所が複数ある。

##### 実施内容

- 未使用引数、未使用設定、未使用定数を削除する
- 重複復元処理、重複 summary 処理、差分保存経路を削除する
- コメント、docstring、責務説明を現行設計へ合わせて更新する

##### 成果物

- 最終修正版コード
- 差分一覧

##### 完了条件

- 後方互換のためだけの残置コードが除去されている
- docstring と実装責務が一致している



## 7. ファイル単位の修正・削除計画

### 7.1 `services.py`

#### 修正

- High
  旧 `MemoryLayer` 互換を前提とした名称・注入経路・ラッパが周辺コードに残存している場合は削除する。`services.py` 自体に「置換済み」であることが明記されているため、移行完了後の互換維持は不要である。
- Medium
  `store` と `retriever` を外部に直接公開する構造を見直し、利用側が内部構成へ依存しないよう責務境界を再定義する。
- Low
  dataclass コンテナとしての責務に限定し、依存ライフサイクル制御が必要な場合は別要素へ分離する。

#### 削除

- 旧 `MemoryLayer` 系 API、別名、ラッパ。存在する場合は削除する。



### 7.2 `types.py`

#### 修正

- High
  `MemoryEntry` を中心とした生成・検証・既定値付与の契約を型定義側に集約する。`mapper.py` と `jsonl_store.py` の復元責務を統合する前提となる。
- Medium
  `MEMORY_TYPES` の文字列集合運用を見直し、必要に応じて enum 化または厳格な型制約へ統一する。
- Low
  `_ISO8601_RE` の利用箇所を明確化し、未使用であれば削除する。

#### 削除

- 型外部で重複している既定値注入ロジックと検証ルール。統合後に型外の重複処理を削除する。



### 7.3 `store.py`

#### 修正

- High
  CRUD と診断系責務を分離する。`add()`、`upsert()`、`delete()` に加え `count_*()`、`check_consistency()` まで 1 クラスに集約されている。
- High
  `memories` / `memories_fts` / `memories_vec` の同期更新失敗時の扱いを明確化する。
- Medium
  `_floats_to_blob(values, expected_dim)` の次元検証責務を整理する。
- Low
  `_now_iso()` など共通ユーティリティの重複を解消する。

#### 削除

- 永続化層に不要な診断・補助責務。分離後は `store.py` から削除する。



### 7.4 `embedding_client.py`

#### 修正

- High
  `_fetch_embedding()` の POST 本文に `text` を反映する。取得できた内容では入力文字列が使われていない。
- High
  例外ログに例外内容を出力する。
- Medium
  `EmbeddingClientConfig` の各設定が実装へ反映されているか確認し、未使用設定を整理する。
- Low
  `EmbeddingResult.error_kind` の分類粒度を見直す。

#### 削除

- 実装で使用していない retry/circuit breaker 関連設定や旧 API 互換のためだけの分岐。存在する場合は削除する。



### 7.5 `mapper.py`

#### 修正

- High
  `jsonl_store.py` と重複する復元ロジックを統合し、`MemoryEntry` 復元経路を 1 箇所へ集約する。
- Medium
  既定値注入を mapper 層から型または専用 factory 側へ移す。
- Low
  入力型を必要最小限に絞り、責務境界を明確化する。

#### 削除

- `jsonl_store.py` 側と重複する `MemoryEntry` 復元ロジック。統合後に旧処理を削除する。



### 7.6 `jsonl_store.py`

#### 修正

- High
  JSONL を source of truth とする設計と、`ingestion.py` が行う逐次二重書き込みの整合性を整理する。
- Medium
  `_entry_from_dict()` を統一復元関数へ寄せる。
- Medium
  `malformed_count` の累積仕様を明確化する。
- Low
  `asyncio.Lock` と同期ファイル I/O の組み合わせを整理する。

#### 削除

- 重複する復元処理、source of truth 設計と矛盾する暫定処理。統合後に削除する。



### 7.7 `injection.py`

#### 修正

- High
  `on_session_start(session_id)` の `session_id` を利用するか削除する。
- High
  `on_session_start()` と `on_user_prompt()` の検索・整形方針を統一する。
- Medium
  `EmbeddingClient` 依存を必要箇所に限定する。
- Medium
  スニペット生成規則をポリシーへ寄せる。
- Low
  prefix の不整合を解消する。

#### 削除

- 未使用引数、未使用依存、旧接頭辞フォーマットなど現行設計と不一致の要素を削除する。



### 7.8 `retriever.py`

#### 修正

- High
  FTS、KNN、Hybrid、RRF merge、スコアリングを分離し、責務境界を明確化する。
- High
  `score` を負距離として解釈する契約を見直し、明示的な距離または類似度の返却へ改める。
- Medium
  `_build_fts_query()` のトークン生成を改善する。
- Low
  boost 定数を設定駆動に切り替える。

#### 削除

- 旧スコア表現への依存コード、暗黙契約に基づく変換処理。特に「負距離 score」を前提とする取り扱いは削除対象とする。



### 7.9 `extract.py`

#### 修正

- High
  semantic / episodic 判定キーワードを設定化し、多言語対応可能にする。現在は英語キーワード正規表現中心である。
- High
  `_classify_content()`、`_importance_from_content()`、`_make_summary()` のヒューリスティックをポリシーオブジェクトへ寄せる。
- Medium
  `max_content_chars` による切り詰めと分類・評価を分離する。
- Medium
  assistant 抽出と user 抽出の共通処理を整理する。
- Low
  閾値定数群を設定へ移動する。

#### 削除

- 設定化後に不要となるハードコードされたキーワード群と閾値定数。



### 7.10 `ingestion.py`

#### 修正

- High
  `on_session_stop()` と `_persist_entry()` の永続化経路を統一する。
- High
  `DedupAction` と `DedupPolicy` の粒度を見直し、設計と実装の整合を取る。取得できた範囲では `SKIP_NEW` のみが存在する。
- Medium
  `knn_search()` の返却スコアに対する距離解釈を明示型へ変更する。
- Medium
  手動登録時の summary 規則を `extract.py` と統一する。
- Low
  `project` / `repo` / `branch` の保持方法を整理する。

#### 削除

- 手動書き込み専用の差分保存経路、重複する summary 生成、旧 dedup 前提の補助処理を削除する。



## 8. 削除方針

### 8.1 削除対象

- 旧 `MemoryLayer` 互換の API、型別名、注入経路、ラッパ。`services.py` に置換済みの記述があるため、移行完了後の互換維持は不要とする。
- `MemoryEntry` 復元ロジックの重複実装。`mapper.py` の `row_to_entry()` と `jsonl_store.py` の `_entry_from_dict()` は統合後に片側を削除する。
- 永続化の複数入口に残る差分実装。`ingestion.py` の `on_session_stop()` 経路と `_persist_entry()` 経路の差分ロジックは整理し、統一後の不要部分を削除する。
- 未使用引数・未使用設定・未使用フォーマット。`injection.py` の `session_id`、`embedding_client.py` における未反映設定、接頭辞の不整合などは削除または統合する。

### 8.2 削除の原則

- 互換性維持のためだけに残されているコードは残さない。明示的な移行完了条件を満たした時点で削除する。
- 機能重複は統合後に必ず片側を削除する。二重実装の併存を認めない。
- 暗黙契約に依存する補助コードは、契約の明文化または型化後に削除する。`score` を負距離とみなす処理が該当する。


## 9. 完了条件

本改修は以下を満たした時点で完了とする。

- 永続化入口が 1 系統に統一されていること。
- `MemoryEntry` 復元ロジックが 1 箇所に集約されていること。
- 検索結果のスコア／距離契約が明文化または型化されていること。
- 旧 `MemoryLayer` 互換コード、未使用引数、重複実装が削除されていること。
- 抽出・注入・埋め込みの主要設定がコード定数ではなく設定として扱えること。
