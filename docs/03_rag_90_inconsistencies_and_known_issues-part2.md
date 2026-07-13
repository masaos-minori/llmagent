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

**Status:** 未解決の設計上の疑問点 (実装に対して2026-07-12に再検証済み。事象は引き続き現行コードで再現する)
**Affected code:** `scripts/rag/ingestion/ingester.py` — `main()`が619行目で
`ingester.ingest_all(args.force)`を呼び出す
**Impact:** CLIの`rag-ingest`実行後、稼働中の`RagPipeline`インスタンス (例: MCPサーバー内) は
古いセマンティックキャッシュエントリを保持し続ける。以降のクエリは、更新されたドキュメント群を
反映していないキャッシュ結果を返す可能性がある。
**Root cause:** `main()`は`on_ingest_complete`コールバックを渡さずに
`ingester.ingest_all(args.force)`を呼び出している。`RagIngester.ingest_all()`は
`on_ingest_complete: Callable[[], None] | None = None` (93行目) を受け付け、それを転送する (130行目)。
このコールバックが取り込み後のキャッシュ無効化を行う唯一の仕組みである。
**Recommended action:** 取り込み直後に最新の結果を必要とする呼び出し元では、
`on_ingest_complete`に`pipeline.semantic_cache.invalidate`を渡すこと。

**根拠分類:** Explicit in code (`scripts/rag/ingestion/ingester.py` 90-130行目の`ingest_all()`定義、604-619行目の`main()`実装を確認。`on_ingest_complete`を渡す呼び出しは存在しない)。

---

*（OPEN-02「delete_document()はセマンティックキャッシュを無効化しない」は解決済み。
scripts/mcp_servers/rag_pipeline/service.py の fmt_delete_document()(210〜213行)が
削除成功時に self._pipeline_or_raise().invalidate_cache() を呼び出しており、
このエントリが指摘していたギャップはもはや存在しない。
2026-07-12再確認: fmt_delete_document()は212行目で invalidate_cache() を呼び出しており、
RagPipeline.invalidate_cache()(scripts/rag/pipeline.py 606行目)が semantic_cache.invalidate() を
呼ぶ実装のまま維持されている。解決済みの状態に変化なし。
根拠分類: Explicit in code。）*

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
