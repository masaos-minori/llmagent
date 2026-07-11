---
title: "RAG Inconsistencies and Known Issues"
category: rag
tags:
  - rag
  - inconsistencies
  - known-issues
  - bugs
  - open-questions
related:
  - 03_rag_00_document-guide.md
  - 03_rag_91_design_notes-part1.md
  - 03_rag_91_design_notes-part2.md
---

# RAGの不整合と既知の問題

このファイルは、RAGドキュメントの再構成中に発見された既知のバグ、仕様の矛盾、
ドキュメント間の不整合、および未解決の疑問点をまとめたものである。

各エントリは以下の形式を使用する: Type / Impact / Description / Safe interpretation / Recommended action / Source。

---

## 確定済みの設計判断

### DESIGN-2: FTS5は`normalized_content`を使用し、LLMは`content`を受け取る

- **Type:** 確定済みの設計判断
- **Impact scope:** `chunks`テーブル、`chunks_fts`仮想テーブル、`scripts/rag/repository.py`、`scripts/rag/stages/augment.py`
- **Invariants (non-negotiable):**
  - `chunks.content`は元のチャンクテキストであり、LLMコンテキストに使用される**唯一**のテキストである。
  - `chunks.normalized_content`はSudachiで正規化された日本語テキストであり、FTS5検索インデックス**専用**に使用される。LLMコンテキストに含まれてはならない。
  - FTS5は`chunks_ai`トリガー経由で`COALESCE(normalized_content, content)`をインデックス化する。
  - 日本語チャンクはSudachiで正規化された空白区切りのテキストを`normalized_content`に格納する。英語/コードチャンクは`normalized_content = NULL`を保持し、FTS5は`content`にフォールバックする。
  - `AugmentStage`は常に`content`を出力し、`normalized_content`を出力してはならない。
- **Description:** 日本語チャンクは2種類のテキスト表現を保持する。`chunks.content` (元のテキスト) は`AugmentStage`によってLLMコンテキストに注入される。`chunks.normalized_content` (Sudachi正規化済み) は`chunks_ai`トリガーによって`chunks_fts`にインデックス化される。FTS5のクエリ側でも、Sudachiの品詞フィルタリングを用いて日本語の語を正規化する。この分離により、LLMは読みやすい元のテキストを受け取りつつ、BM25検索では形態素的に正規化された形式が使用される。
- **Notes for AI reference:** Augmentステージの出力において、`content`を`normalized_content`に置き換えてはならない。この分離は意図的なものであり、確定済みである。Source: `03_rag_02_01_ingestion_pipeline-overview.md §FTS5/LLM content separation`、`03_rag_03_01_query_pipeline-overview.md §5.5 AugmentStage`。

---

### DESIGN-3: `documents`、`chunks`、`chunks_fts`、`chunks_vec`間の責務分離

- **Type:** 確定済みの設計判断
- **Impact scope:** DBスキーマ、すべての取り込みおよびクエリ処理コード
- **Invariants (non-negotiable):**
  - `documents`と`chunks`は**正規のデータストア**であり、すべての変更操作はこれらを経由する。
  - `chunks_fts`と`chunks_vec`は**派生インデックス**であり、アプリケーションコードはこれらを読み取り専用として扱う必要がある。
  - `chunks_fts`の同期: トリガーベース (`chunks_ai`/`chunks_au`/`chunks_ad`) で行われ、直接のINSERT/UPDATEは行わない。`chunks_fts`への手動編集は禁止されており、代わりに`/db rag rebuild-fts`を使用する。
  - `chunks_vec`の同期: 取り込み時のINSERTと明示的なDELETEによって行われる。外部キー制約はない (sqlite-vecの制約による)。
  - 強制再挿入時の削除順序: `chunks_vec`が最初 → `chunks` → `documents` (孤立したベクトルレコードを避けるために必須)。
  - RAG整合性チェック (`/db consistency`) は、正規の`chunks`と派生インデックスである`chunks_fts`および`chunks_vec`との同期を検証する。
- **Description:**
  - `documents`: 正規のURL/ドキュメントメタデータ (url、title、lang、fetched_at、etag、last_modified、chunking_strategy)。URLごとに1行。
  - `chunks`: 正規のチャンクテキストと位置情報 (content、normalized_content、chunk_index、chunk_type)。`doc_id`を介して`documents`への外部キー (ON DELETE CASCADE)。
  - `chunks_fts`: 派生FTS5/BM25全文検索インデックス。`COALESCE(normalized_content, content)`を使用してトリガーにより自動同期される。BM25検索専用。手動で編集してはならず、修復には`/db rag rebuild-fts`を使用する。
  - `chunks_vec`: 派生sqlite-vec KNNベクトルインデックス。float32埋め込みBLOB。KNN検索専用。
- **RAG consistency checks:** 正規データと派生インデックス間の同期を検証する:
  - `fts_gap`: `chunks_fts`に欠落しているチャンク数 (修復: `/db rag rebuild-fts`)
  - `fts_orphan_count`: 対応するチャンクを持たないFTSエントリ (データ損失のリスク; 修復: `/db rag rebuild-fts`)
  - `orphan_vec_count`: 対応するチャンクを持たないベクトル行 (修復: `ingester.py --force`)
- **Notes for AI reference:** sqlite-vecの仮想テーブルは標準的な外部キー制約をサポートしない。RAG整合性チェック (`/db consistency`) は、正規の`chunks`と派生インデックスである`chunks_fts`および`chunks_vec`との同期を検証する。Source: `03_rag_04_05_dto-types.md §DB Schema`、`03_rag_05_1-configuration-reference.md §RAG index consistency checks`。

---

---

## キャッシュ無効化

### OPEN-01: CLIによる取り込みはセマンティックキャッシュを無効化しない

**Status:** 未解決の設計上の疑問点 (実装に対して2026-07-09に検証済み)
**Affected code:** `scripts/rag/ingestion/ingester.py` — `main()`が620行目で
`ingester.ingest_all(args.force)`を呼び出す
**Impact:** CLIの`rag-ingest`実行後、稼働中の`RagPipeline`インスタンス (例: MCPサーバー内) は
古いセマンティックキャッシュエントリを保持し続ける。以降のクエリは、更新されたドキュメント群を
反映していないキャッシュ結果を返す可能性がある。
**Root cause:** `main()`は`on_ingest_complete`コールバックを渡さずに
`ingester.ingest_all(args.force)`を呼び出している。`RagIngester.ingest_all()`は
`on_ingest_complete: Callable[[], None] | None = None` (95行目) を受け付け、それを転送する (132行目)。
このコールバックが取り込み後のキャッシュ無効化を行う唯一の仕組みである。
**Recommended action:** 取り込み直後に最新の結果を必要とする呼び出し元では、
`on_ingest_complete`に`pipeline.semantic_cache.invalidate`を渡すこと。

---

### OPEN-02: `delete_document()`はセマンティックキャッシュを無効化しない

**Status:** 未解決の設計上の疑問点 (実装に対して2026-07-09に検証済み — 対象のコードパスは
更新されているが、根本原因は変わらない)
**Affected code:** 削除ロジックは本エントリ記載時点から`service.py`外に移動している。
現在の実際の呼び出し連鎖: `scripts/mcp_servers/rag_pipeline/service.py::RagPipelineMCPService.fmt_delete_document()`
(`rag_delete_document` MCPツールハンドラ、197行目) が
`scripts/mcp_servers/rag_pipeline/document_manager.py::DocumentManager.delete_document()` (72行目) を呼び出し、
これが`chunks_vec`と`documents`の行をSQLで直接削除する。
**Impact:** `rag_delete_document` MCPツールでドキュメントが削除された後も、削除された
ドキュメントを参照していたキャッシュ済みのセマンティック検索結果は、次の`invalidate()`呼び出し
またはプロセス再起動まで`SemanticCache`に残り続ける。
**Root cause:** `fmt_delete_document()`も`DocumentManager.delete_document()`も
`semantic_cache.invalidate()`を呼び出していない。`DocumentManager`はパイプラインやそのキャッシュへの
参照を保持していないため、直接無効化することができない。無効化できるのは
`self._pipeline: RagPipelineLike`および`RagPipeline.semantic_cache` (`scripts/rag/pipeline.py:125`参照) を
保持する`RagPipelineMCPService`のみである。MCPサービス内に他の無効化経路は存在しない。
**Recommended action:** `fmt_delete_document()`内で、`self._doc_mgr.delete_document(url)`が
`True`を返した後に`self._pipeline.semantic_cache.invalidate()`を呼び出す
(`_pipeline_or_raise()`の既存パターンに合わせて`self._pipeline is None`のガードを入れる)。
あるいは、呼び出し元が別途キャッシュ無効化を行う必要がある旨をドキュメント化する。

---

## 未解決の課題

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_91_design_notes-part1.md`
- `03_rag_91_design_notes-part2.md`

## Keywords

rag
inconsistencies
known-issues
bugs
open-questions
