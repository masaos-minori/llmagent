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

**Status:** 解決済み (2026-07-14に`scripts/rag/ingestion/ingester.py`の`ingest_all()`へ
`POST /rag_invalidate_cache`呼び出しを追加して解消)
**Affected code:** `scripts/rag/ingestion/ingester.py` — `ingest_all()`完了後
**Resolution:** `ingest_all()`完了後に`rag_pipeline_service_url`を取得し、
MCPサーバーの`/rag_invalidate_cache`エンドポイントへHTTP POSTを送信。
失敗時はWARNINGをログ出力して継続。
**Root cause:** `main()`は`on_ingest_complete`コールバックを渡さずに
`ingester.ingest_all(args.force)`を呼び出している。`RagIngester.ingest_all()`は
`on_ingest_complete: Callable[[], None] | None = None` (93行目) を受け付け、それを転送する (130行目)。
このコールバックが取り込み後のキャッシュ無効化を行う唯一の仕組みである。

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
