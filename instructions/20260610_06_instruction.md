# RAG パイプライン改修計画書

## 全体方針

- 本改修では **後方互換性を維持しない**。旧 API、旧戻り値、fail-soft なフォールバック、曖昧な入力許容、warning のみで継続する設計は削除する。
- すべてのレイヤで **fail-fast** を徹底する。設定不備、トークナイザ初期化失敗、DB アクセス失敗、LLM 応答不正、RAG 検索失敗、リランキング失敗、refiner 失敗は即座に検知し、明示的な例外または結果型として扱う。
- 変換・型付けは厳密に行う。`Any`、曖昧な `dict`、暗黙の list/tuple 契約、空配列・空文字による失敗表現は廃止し、専用モデル・Protocol・結果型へ置き換える。
- `except Exception` は原則使用しない。想定される例外型のみを個別に捕捉し、それ以外はそのまま送出する。
- `repository.py` / `llm.py` / `pipeline.py` は責務分離を徹底する。SQL、スコアリング、キャッシュ、LLM 呼び出し、段階実行、HTTP 向け整形を明確に分割する。
- 日本語 FTS、RRF、semantic cache、MQE、cross-encoder rerank、context refiner といった各段階は、暗黙に連結された実装ではなく、型で接続されたパイプラインへ再構成する。

## 実装ルール

- 失敗を `[]`、`""`、`None`、warning ログに変換して継続しない。正常系と異常系は結果型または例外で明確に表現する。
- `SQLiteHelper(...)` の直接生成を各所に散らさず、Repository 層に限定する。上位層は repository interface を通じてのみ DB にアクセスする。
- `Any` を減らし、少なくとも `RagQuery`, `RagSearchResult`, `RerankResult`, `RefineResult`, `PipelineStageResult` 相当の型を導入する。
- 日本語トークナイズ、FTS query 構築、URL 検証、埋め込み BLOB 変換、LLM 応答パースは専用ユーティリティに集約し、呼び出し側で再実装しない。
- `SemanticCache` は単なる in-memory dict/配列で曖昧に保持せず、キー型・距離計算・上限・失効規則を明示する。
- MQE / rerank / summarize / refine の各 LLM 呼び出しは、リクエスト構築・レスポンスパース・失敗マッピングを分離する。
- パイプライン段階は stage model を通じて接続し、各段階の入力・出力・失敗理由を記録可能にする。

## ファイルごとの修正内容

### 1. `repository.py`

#### High
- `_build_fts_tokens_ja()` の `except Exception` を廃止し、Sudachi 初期化失敗と tokenization failure を個別に扱う。現在の「非 ASCII 抽出へフォールバック」は互換目的の救済なので削除する。
- `RagRepository` の SQL 実行結果を `dict/tuple` ではなく厳密な row model に変換する。Repository から上位へ raw row を漏らさない。
- `vector_search()` / `fts_search()` / `fetch_full_document()` の DB 失敗を空結果へ丸めない。検索失敗とヒットなしを区別する。
- `RagScorer.rrf_merge()` の入力/出力を `RagHit` 専用に固定し、RRF 用スコアと最終表示用スコアを分離する。
- `SemanticCache` の lookup/put/prune を fail-fast 化し、埋め込み次元不一致やキャッシュ破損を無視しない。

#### Medium
- Sudachi tokenizer の lazy global 初期化を廃止し、明示的 provider/adapter を注入する。
- Japanese FTS token builder と generic `_build_fts_query()` を strategy 化し、日本語/英語/将来の他言語で差し替え可能にする。
- SQL 文字列・row mapping・dedup・full document fetch を別コンポーネントへ分割する。
- `deduplicate_chunks()` と `_dedup_hits()` の責務を統一し、重複除去ルールを一箇所で定義する。

#### Low
- `cosine_sim()`、`floats_to_blob()` 周辺のユーティリティ重複を整理する。
- logging の粒度とメッセージ形式を統一する。

---

### 2. `stage.py`

#### High
- `PipelineContext` と `PipelineStage` の抽象が薄すぎるため、入力・出力・失敗理由・観測情報を持つ stage result model を追加する。
- `PipelineStage.run()` の契約を厳密化し、`Any` と未型付け observer を廃止する。

#### Medium
- observer 登録 API を typed callback / protocol に変更する。
- stage ごとの実行結果を蓄積できる pipeline trace model を導入する。

#### Low
- dataclass のフィールド責務と docstring を整理する。

---

### 3. `types.py`

#### High
- `RagHit` の責務を明確化し、検索段階・RRF 段階・rerank 段階で使う score を分離する。単一スコアに複数意味を混在させない。
- `RagHit` に生テキスト・表示用要約・内部順位メタデータを混ぜないよう、必要なら複数モデルへ分割する。

#### Medium
- query/result/stage result 用の型を追加し、repository/llm/pipeline 間の loosely typed 契約を減らす。
- 不変性を高め、stage をまたいだ accidental mutation を防ぐ。

#### Low
- フィールド名と docstring をスコアリング段階に合わせて整理する。

---

### 4. `utils.py`

#### High
- `validate_url()` の `except Exception` を廃止し、URL parse failure を個別に扱う。warning だけで `False` を返す fail-soft は削除する。
- `floats_to_blob()` / `_validate_float_list()` の入力検証を強化し、NaN / inf / 次元不一致 / 非数値混入を明示的に拒否する。
- `normalize_unicode()` の前提と適用対象を厳密化し、検索前処理と表示前処理を混在させない。

#### Medium
- URL 検証、埋め込み変換、Unicode 正規化をそれぞれ独立した utility module へ再配置する。
- 数値配列 validation の戻り値を明示的な正規化済み配列型にする。

#### Low
- ログと例外文言の統一。

---

### 5. `llm.py`

#### High
- `_get_cfg()` の module-level cache + `except Exception` + `{}` fallback を廃止する。設定ロード失敗は即例外とし、設定未読込のまま継続しない。
- `_parse_mqe_response()` の malformed JSON fallback を廃止し、MQE 応答不正は明示的失敗として扱う。元クエリ返却による救済は削除する。
- `RagLLM.expand_queries()` / `cross_encoder_rerank()` / `refine_context()` / `summarize_tool_result()` の broad exception を削除し、HTTP failure / parse failure / schema failure / LLM semantic failure を分類する。
- `_extract_chat_content()` に依存する OpenAI 互換応答パースを strict model 化する。`dict[str, Any]` と ad-hoc field access を廃止する。
- `get_embedding()` の戻り値・エラー契約を厳密化し、埋め込み取得失敗を上位が `[]` や fallback に変換しないようにする。

#### Medium
- MQE / rerank / summarize / refine のリクエスト生成とレスポンスパースを個別コンポーネントへ分離する。
- temperature / max_tokens / prompt 生成を policy/config 主導へ整理する。
- RRF 後 rerank・context refiner・tool result summarize の役割を型で分ける。
- `orjson` と raw dict を跨ぐ処理を typed response adapter に置き換える。

#### Low
- prompt builder 関数の命名と責務を整理する。
- logging の指標（件数、長さ、経過時間）を標準化する。

---

### 6. `pipeline.py`

#### High
- `RagPipeline` の `except Exception` ベースの fallback を全面的に廃止する。段階失敗を hidden fallback ではなく、明示的な stage failure として上位へ返す。
- `expand_queries_safe()` のような safe wrapper を削除し、失敗を握りつぶさない構造へ変更する。
- `run()` / `augment()` / `_augment_http()` / `_augment_refiner()` の責務を再分割し、query expansion、retrieval、rerank、document assembly、refine、HTTP 向け整形を独立 phase にする。
- `SQLiteHelper` 直接利用を pipeline 層から排除し、document fetch は repository interface 経由に統一する。
- `SemanticCache` を pipeline 内で直接扱いすぎないようにし、lookup/put と cache invalidation を専用 service に分離する。

#### Medium
- `sanitize_document()` を document assembly/formatter 層へ移し、pipeline 本体から文字列整形責務を外す。
- `search_queries()` / `rerank_candidates()` / `_format_chunks()` の入出力を typed stage result に置き換える。
- `last_timings` 等の観測情報を trace model に集約し、段階別性能計測を構造化する。
- HTTP 向け augment と refiner 向け augment を一つの pipeline result から派生させる形に整理する。

#### Low
- helper 関数名と logging メッセージを整理する。

## 作業ステップ

1. **型と失敗契約の固定**
   - `types.py`, `stage.py` を先に見直し、RAG 全体で使う query/result/stage result/error 型を定義する。
   - `RagHit` の score 責務を分割し、RRF・rerank・表示で使う値を明確にする。

2. **ユーティリティと repository の fail-fast 化**
   - `utils.py` の URL/embedding validation を厳密化する。
   - `repository.py` の tokenization fallback、DB failure fallback、raw row 契約を廃止する。
   - Sudachi tokenizer を provider/adapter 化する。

3. **LLM レイヤの再構成**
   - `llm.py` の config cache/fallback を除去する。
   - MQE / rerank / summarize / refine / embedding それぞれの request/response adapter を分離し、broad exception を除去する。

4. **Pipeline の段階分離**
   - `pipeline.py` を expand → retrieve → merge/dedup → rerank → fetch/assemble → refine → format の明示的 phase に分割する。
   - `expand_queries_safe()` など safe wrapper を削除し、stage failure を trace/result に反映する。

5. **Cache と observability の整理**
   - `SemanticCache` の責務を repository から分離し、専用 cache service に整理する。
   - stage ごとの timings / warnings / failure reasons を trace model に記録する。

6. **異常系テスト追加**
   - Sudachi unavailable
   - invalid URL
   - invalid embedding floats
   - malformed MQE response
   - malformed rerank response
   - DB fetch failure
   - cache dimension mismatch
   - refiner failure
   - empty-hit と failure の区別

## 完了条件

- `except Exception` が原則として除去され、未知例外を暗黙吸収しない。
- `repository.py`, `llm.py`, `pipeline.py` から fail-soft な fallback が除去されている。
- `RagHit` および pipeline 入出力が厳密な型で接続され、`Any` や raw dict 契約が大幅に減っている。
- Japanese FTS tokenization failure、DB failure、LLM parse failure が warning や空結果に丸められず、明示的な failure として扱われている。
- pipeline は明示的な stage モデルで実行され、各段階の失敗理由・観測情報が追跡できる。
- Semantic cache、RRF merge、rerank、refine、document formatting の責務境界が明確になっている。
- utility レイヤの URL/embedding validation が厳密化され、不正入力を即拒否する。
- repository と pipeline が `SQLiteHelper` や raw SQL 結果の扱いを必要最小限に限定している。
