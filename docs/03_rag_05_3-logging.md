---
title: "3. Logging"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_05_1-configuration-reference.md
---

# 3. ロギング

## 3. ロギング

| Script | Log file | Log levels |
|---|---|---|
| `crawler.py` | `/opt/llm/logs/crawl.log` + stderr | INFO: 開始/保存/スキップ; WARNING: HTTPエラー/リトライ |
| `chunk_splitter.py` | `/opt/llm/logs/chunk.log` + stderr | INFO: ファイル数/チャンク数; WARNING: Sudachiエラー; ERROR: ファイル失敗 (トレースバック付き) |
| `ingester.py` | `/opt/llm/logs/ingest.log` + stderr | INFO: チャンク数/挿入数/移動数; WARNING: 埋め込みエラー/リトライ/スキップ; ERROR: 読み取り/移動/グループ化の失敗 (トレースバック付き) |

**共通フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
