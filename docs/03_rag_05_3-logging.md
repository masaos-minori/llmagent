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

### 実装上の補足

- 上記3スクリプトはいずれも `shared/logger.py` の `Logger` クラスを
  `Logger(__name__, "<path>.log")` の形で使用する。ログレベルはコンストラクタでは
  変更不可であり、常に `logging.INFO` に固定される（ロガー初期化処理内で
   `setLevel(logging.INFO)` が実行される）。
  [Explicit in code]
- 出力先はファイルハンドラ (`FileHandler`) と `stderr` への `StreamHandler` の両方。
  ログファイルのオープンに失敗した場合 (`OSError`) は、フォールバックの
  `shared.logger.fallback` ロガーへ警告を出し、`stderr`ハンドラのみで継続する。
  [Explicit in code]
- `propagate=False`が設定されており、ルートロガーへの二重出力は発生しない。
  [Explicit in code]
- `Logger`は`structured_log=True`指定でJSON-lines形式 (`_JsonFormatter`) に切り替え可能だが、
  crawler.py / chunk_splitter.py / ingester.pyはいずれも`structured_log`を指定していないため、
  本ドキュメント記載の共通フォーマットのままとなる。
  [Explicit in code]
- `extra={...}`で付与される`turn_id` / `session_id` / `rag_query_id` / `workflow_id` / `task_id`
  等のコンテキストフィールドは、テキストフォーマット (`_FORMAT`) には出力されない。
  これらは構造化ログ (`structured_log=True`) 使用時のみJSON出力に反映される。
  [Strongly implied by code] — `_FORMAT`文字列がこれらのフィールドを参照していないため。

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
