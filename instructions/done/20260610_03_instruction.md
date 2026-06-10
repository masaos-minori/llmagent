# メモリ層 改修指示書

## 全体方針

- 後方互換性は維持しない。壊れた JSONL 行の読み飛ばし、`except Exception` による握りつぶし、`memories_vec` 同期失敗の warning 継続、検索失敗時の空配列返却、曖昧な入力補正はすべて削除する。
- メモリ層は 抽出 (`extract`) / 埋め込み (`embedding_client`) / 永続化 (`jsonl_store`, `store`) / 検索 (`retriever`) / 注入 (`injection`) / 組み立て (`services`) の責務を明確に分離し、`ingestion` はそのオーケストレーションだけを担う構成へ整理する。
- JSONL と SQLite の二重永続化は、役割を曖昧にしたまま併用しない。どちらを正本にするか、どの時点で整合を保証するかを設計で明示し、永続化失敗時の振る舞いを統一する。
- API 契約と実装の不一致を残さない。特に `MemoryQuery.session_id`、hybrid 検索スコア、注入ポリシー、埋め込み失敗時の動作は、実装と仕様を一致させる。

## 実装ルール

- すべてのレイヤで fail-fast を徹底する。入力不正、永続化失敗、検索失敗、埋め込み失敗を warning で流さず、明示的な例外または構造化された失敗結果として返す。
- `except Exception` は使用しない。例外は 型ごとに分類 し、呼び出し元が判断可能な契約に変える。
- SQLite の upsert は `INSERT OR REPLACE` を使わず、`ON CONFLICT DO UPDATE` を使用する。FTS / vec 同期も「失敗しても継続」ではなく、成功を保証するか全体を失敗にする。
- 変換・型付けは厳密に行う。`MemoryEntry`, `MemoryQuery`, `EmbeddingResult` の入力検証を強化し、mapper でも曖昧な coercion をしない。
- 固定しきい値・固定キーワード・固定 prefix のような埋め込みルールは policy/config に切り出し、多言語や運用条件に応じて差し替え可能にする。

## ファイルごとの修正内容

### `jsonl_store.py`

- High: malformed JSONL 行や不正 entry をスキップせず、即例外または隔離処理に変更する。`_entry_from_dict()` の broad exception を削除する。
- High: append-only ログとして durability を強化し、部分書き込み・クラッシュ時の扱いを明示する。
- Medium: `malformed_count` のような読み取り副作用状態をやめ、読み取り結果・監査結果を分離する。JSONL レコード形式は schema で厳密検証する。

### `mapper.py`

- High: `tags` を含む入力形式を厳密化し、許可しない形式は即失敗にする。mapper を唯一の正規変換経路に統一する。
- Medium: sqlite row/dict を雑に同列で扱わず、専用 row protocol または typed row を導入する。

### `retriever.py`

- High: `MemoryQuery.session_id` を未使用のまま残さない。使うなら SQL に反映し、使わないなら型から削除する。
- High: RRF merge 後に `_score(0.0, ...)` で再スコアして hybrid 意味を失わせている実装を修正し、FTS/KNN の合成スコア方式を再設計する。
- High: `search()` / `knn_search()` / `top_semantic()` の broad exception fallback を削除し、検索障害を「ヒットなし」に見せない。
- Medium: `_build_fts_query()` を日本語・記号・複数語検索に対応できる構成へ変更し、ranking policy（importance / pin / recency / context）を設定可能にする。

### `services.py`

- High: 単純な dataclass container をやめ、依存関係を明示する builder/factory に置き換える。
- Medium: service container は具象依存を減らし、必要に応じて interface / protocol を介した構成にする。

### `store.py`

- High: `INSERT OR REPLACE` を廃止し、`ON CONFLICT DO UPDATE` に変更する。FTS/vec の同期は warning でスキップせず、失敗時は全体失敗にする。
- High: `_write_vec()`、`delete()`、`clear_by_session()`、整合性確認系にある broad exception と warning 継続を削除する。
- High: FTS 同期の手動 delete→insert をやめ、DB 主導同期（trigger も含む）または一元同期機構に切り替える。
- Medium: `SQLiteHelper("session")` の直接生成をやめ、接続生成責務を注入可能にする。読み取り API と書き込み API は責務ごとに分割する。

### `types.py`

- High: `MemoryQuery` に `limit`・`memory_type`・`query` のバリデーションを追加する。`EmbeddingResult.error_kind` は自由文字列ではなく enum 化する。
- Medium: `MemoryEntry` の mutable な永続化前提を見直し、生成入力と永続化済み entity を分ける。

### `embedding_client.py`

- High: `_fetch_embedding()` の broad exception を廃止し、HTTP エラー、接続エラー、デコード失敗、レスポンス不正を明確に分類する。
- High: `disabled` を通常失敗結果として返すだけの設計を見直し、設定不備は fail-fast にする。`\"query: {text}\"` のハードコードは policy 化する。
- Medium: response schema を厳密検証し、埋め込み次元・要素型・空配列の扱いを明文化する。circuit breaker の観測性も強化する。

### `extract.py`

- High: 英語固定キーワードと固定文字数に依存した抽出ルールを廃止し、policy/config で差し替え可能な抽出器へ変更する。
- High: candidate 抽出と summary 生成を分離し、抽出器は判定責務だけを持つ構造にする。
- Medium: assistant/user で異なる判定を strategy 化し、importance 計算を retriever の ranking policy と整合させる。

### `ingestion.py`

- High: JSONL と SQLite の分断書き込みを解消し、永続化の一貫性を保証する。イベントログ→再投影か、単一正本＋再構築戦略へ切り替える。
- High: `on_session_stop()` と内部永続化処理の broad exception を削除し、entry 単位・全体単位の失敗を明示する。
- High: dedup を embedding 成功にのみ依存させず、埋め込み失敗時でも最低限の重複抑止方針を持たせる。manual write と自動 ingestion の経路は統一する。
- Medium: dedup policy を拡張可能にし、dedup 判定そのものを retriever 依存から分離する。

### `injection.py`

- High: `on_session_start()` / `on_user_prompt()` の broad exception fallback を削除し、検索障害・埋め込み障害・注入結果なしを区別する。
- High: session start と prompt 時の prefix 仕様を統一し、重複 snippet を排除する。semantic / episodic の注入は dedup 済みで返す。
- Medium: 件数ベースではなく token/char budget ベースで注入量を制御し、embedding 失敗時の FTS-only fallback も policy として明示する。

## 作業ステップ

1. 型と契約を先に固定する
   `types.py`・`mapper.py`・`services.py` を先に整理し、`MemoryEntry / MemoryQuery / EmbeddingResult`・service 組み立て・mapper 契約を確定する。
2. 永続化を fail-fast に置き換える
   `store.py` の upsert/sync 戦略を全面改修し、`jsonl_store.py` の malformed スキップを廃止する。JSONL と SQLite の整合方針をこの段階で決める。
3. 埋め込みと検索の契約を修正する
   `embedding_client.py` の失敗分類を厳密化し、`retriever.py` の session\_id / hybrid score / fallback を修正する。
4. 抽出と注入の policy を外出しする
   `extract.py` の英語固定ルールを置き換え、`injection.py` の注入件数・prefix・fallback を policy 駆動にする。
5. ingestion を再オーケストレーションする
   `ingestion.py` を、抽出・埋め込み・dedup・永続化・監査を明示的な結果として返す orchestrator に書き換える。manual write 系も同じ経路に統合する。
6. 最後に一貫性テストを追加する
   malformed JSONL、SQLite 失敗、vec 障害、埋め込み失敗、retriever 障害、注入重複などの異常系テストを追加する。

## 完了条件

- malformed JSONL、DB 書き込み失敗、vec 同期失敗、検索失敗が warning だけで握りつぶされず、呼び出し元が識別可能な失敗として扱える。
- `INSERT OR REPLACE`、broad exception、silent fallback、曖昧 coercion がコードベースから除去されている。
- JSONL と SQLite の関係が明文化され、分断書き込みが設計上解消されている。
- `MemoryQuery`、hybrid retrieval、top semantic、injection の API 契約が実装と一致している。
- 抽出・検索・注入のルールが policy/config 化され、英語固定・件数固定・prefix 固定の実装に依存していない。
