---
title: "RAG Inconsistencies and Known Issues (Part 2)"
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
source:
  - 03_rag_90_inconsistencies_and_known_issues-part1.md
---

# RAGの不整合と既知の問題

このファイルは、RAGドキュメントの再構成中に発見された既知のバグ、仕様の矛盾、
ドキュメント間の不整合、および未解決の疑問点をまとめたものである。

各エントリは以下の形式を使用する: Type / Impact / Description / Safe interpretation / Recommended action / Source。

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
- `03_rag_90_inconsistencies_and_known_issues-part1.md`

## Keywords

rag
inconsistencies
known-issues
bugs
open-questions
