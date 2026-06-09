# TODO

## 0. 実装方針

- 最優先方針は、後方互換性維持のためだけに残っている facade / 二重 API / private 依存を削除し、責務ごとのサービス境界を明確化すること である。特に `layer.py` は旧 `MemoryLayer` 互換を明示しており、今回の改修方針では削除対象とする。
- 実装順は、アーキテクチャ破綻の修正 → API 境界の正常化 → データ整合性と失敗表現の厳格化 の順とする。private API 依存や無言フォールバックは、以降の改修を難しくするため先に除去する。



## TODO 1. `MemoryLayer` 互換 facade を廃止する

### 目的

- 旧 monolithic `MemoryLayer` との互換維持のために残された構成を廃止し、呼出側を `MemoryInjectionService` / `MemoryIngestionService` / `MemoryRetriever` の明示利用へ移行する。`layer.py` の docstring 自体が「旧構成互換」「callers need no changes」を目的としている。

### 実施内容

- `layer.py` の `MemoryLayer` を削除対象にする。
- `factory.py` や呼出元を修正し、`MemoryLayer` 経由ではなく必要なサービスを直接 DI する構成へ変更する。`MemoryLayer` の肥大化した引数群はサービス別設定に分解する。
- `list_entries()`, `get_entry()`, `pin_entry()`, `unpin_entry()`, `delete_entry()`, `prune()`, `count_prunable()`, `search()`, `clear()`, `stat_*` の facade メソッドを廃止し、対応する責務のサービス / ストア側 API に移す。

### 完了条件

- アプリケーション層から `MemoryLayer` の参照が消える。
- 旧互換目的の constructor signature が削除される。



## TODO 2. private API / private 属性への依存を全廃する

### 目的

- 現状のサービス間依存は public 契約ではなく private 実装に食い込んでおり、責務分割と交換可能性を壊している。`MemoryIngestionService` は `retriever._vec_search()` を直接呼び、`MemoryLayer.search()` は `self._ingestion._retriever` に依存している。

### 実施内容

- `ingestion.py` の `_has_near_duplicate()` と `_link_duplicates()` から `retriever._vec_search()` 直接呼出を削除する。
- `retriever.py` に、重複判定用の public API を追加する。例: `find_near_duplicates()` または `knn_search()`。
- `layer.py` の `search()` にある `self._ingestion._retriever.search(...)` を廃止し、検索責務を `MemoryRetriever` 側へ直接移す。
- `self._project`, `self._repo`, `self._retriever` などの private 属性の外部流用を禁止し、必要な値は public な引数または明示的な設定オブジェクトで渡す。

### 完了条件

- 他モジュールから `_vec_search`, `_retriever`, `_project`, `_repo` などの private 名参照がなくなる。
- dedup と検索が public API 経由でのみ実行される。



## TODO 3. `JsonlMemoryStore` の二重書込 API を解消する

### 目的

- `jsonl_store.py` には `async write()` と `sync append()` の二重 API が存在し、保存経路と排他制御のルールが不統一である。これは互換維持または移行途中の残骸と見なせるため削除対象である。

### 実施内容

- `JsonlMemoryStore.append()` を削除する。
- JSONL への保存経路を `write()` の 1 本に統一する。
- 全呼出元を確認し、同期 append 経路が残っていれば非同期 write へ移行する。
- JSONL が source of truth である前提に合わせて、以後の再構築や監査もこの単一路経路を起点に設計する。

### 完了条件

- `jsonl_store.py` に JSONL 追記 API が 1 つしか残らない。
- JSONL 保存の排他制御ルールが一意に決まる。



## TODO 4. データ変換の無言フォールバックをやめ、型検証を `types.py` に集約する

### 目的

- `mapper.py` と `jsonl_store.py` の両方で、不正 `source_type` を `SourceType.CONVERSATION` へフォールバックしている。また `tags` 変換失敗時に空配列へ落とすなど、データ異常を隠蔽している。これを止め、`types.py` を唯一のバリデーション起点にする。

### 実施内容

- `types.py` に `MemoryEntry` / `MemoryQuery` 作成時の検証ロジックを集約する。少なくとも `memory_type`, `source_type`, `importance`, `created_at`, `updated_at` を検証対象にする。
- `mapper.py` の unknown `source_type -> CONVERSATION` フォールバックを削除する。厳格に失敗させるか、呼出側へエラーを返す。
- `mapper.py` の `tags` 変換失敗時 `[]` フォールバックを削除する。
- `jsonl_store.py` の `_entry_from_dict()` にある同様の `source_type` フォールバックを削除し、`types.py` の検証へ委譲する。
- 行変換 / dict 変換が必要なら、`row_to_entry()` と `dict_to_entry()` を分けた上で、最終的な検証は共通の生成関数で行う。

### 完了条件

- `SourceType.CONVERSATION` への自動フォールバックコードが `mapper.py` / `jsonl_store.py` から消える。
- `MemoryEntry` の生成時検証が `types.py` 起点で一元化される。



## TODO 5. `EmbeddingClient` の失敗表現を `None` 返却から明示的な結果型へ変更する

### 目的

- `embedding_client.py` の `_fetch_embedding()` はエラー時に常に `None` を返し、warning を出すだけで失敗理由を呼出側へ伝えない。このため、通信失敗・応答不正・埋め込み空配列などの違いを扱えない。

### 実施内容

- `EmbeddingClient.fetch()` / `_fetch_embedding()` の返却を `list[float] | None` から、成功 / 失敗理由を持つ結果型 に変更する。
- `ingestion.py` と `injection.py` 側も、新しい結果型に合わせて分岐を明示化する。埋め込みなし継続、再試行、記録のみ継続などを区別する。
- `_fetch_embedding()` の request payload が実入力 `text` を正しく使っているか確認し、不正であれば即修正する。読取可能範囲では `json={"content": f"query: "}` のように見え、`text` の実使用が不明瞭である。

### 完了条件

- 埋め込み取得失敗時に、呼出側が原因別の処理を選べる。
- `None` だけを見て曖昧に継続する分岐が削減される。



## TODO 6. `MemoryRetriever` を検索方式ごとに分割する

### 目的

- `retriever.py` は FTS5、ベクトル検索、RRF merge、スコアリング定数、FTS クエリ構築を 1 モジュールに抱えている。これにより dedup 用 KNN、通常検索、スコア調整が密結合になっている。

### 実施内容

- `retriever.py` を少なくとも以下に分離する。
  * `FtsRetriever`
  * `VectorRetriever`
  * `HybridRetriever` または merge 戦略モジュール
- dedup が必要とする KNN 検索は `VectorRetriever` の public API とする。
- `FTS` の query builder は専用関数 / クラスへ分離し、単純 `" OR ".join(tokens)` から改善可能な構造にする。

### 完了条件

- dedup 用検索と通常検索の責務境界が明確になる。
- `MemoryRetriever` という単一巨大責務が解消される。



## TODO 7. `InjectionPolicy.dedup_window` の未使用設定を削除する

### 目的

- `InjectionPolicy.dedup_window` は「future impl」とコメントされている未実装項目であり、設定だけ残っている。今回方針では後方互換や将来予約のための未使用フィールドは削除対象とする。

### 実施内容

- `InjectionPolicy` から `dedup_window` を削除する。
- もし注入重複抑止が本当に必要であれば、別 TODO として実装仕様を確定後に再導入する。現段階では「未使用設定を残さない」方を優先する。

### 完了条件

- 未使用設定項目が `InjectionPolicy` から消える。
- 設定ファイル / 呼出側引数にも不要項目が残らない。



## TODO 8. `DedupAction` の多モード運用を整理し、不要モードを削除する

### 目的

- `ingestion.py` には `DedupAction.SKIP_NEW` と `LINK_ONLY` があるが、モード分岐は永続化フローを複雑化させる。要件上不要な互換モードなら削除し、単一動作に固定した方がよい。

### 実施内容

- 現行要件で `LINK_ONLY` が必要かを確認する。不要なら削除する。
- dedup の既定動作を 1 つに固定し、`on_session_stop()` / 手動登録の両方で同一ルールを適用する方向に寄せる。

### 完了条件

- `DedupAction` が単純化される、または不要なモードが削除される。
- 永続化フローの条件分岐が減る。



# 推奨実装順

1. TODO 1: `MemoryLayer` 廃止
2. TODO 2: private API / private 属性依存の全廃
3. TODO 3: `JsonlMemoryStore` 二重 API 解消
4. TODO 4: 型検証の `types.py` 集約と無言フォールバック撤廃
5. TODO 5: `EmbeddingClient` の失敗表現明確化
6. TODO 6: `MemoryRetriever` 分割
7. TODO 7: `InjectionPolicy.dedup_window` 削除
8. TODO 8: `DedupAction` 多モード整理
