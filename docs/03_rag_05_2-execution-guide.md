---
title: "2. Execution Guide"
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

# 2. 実行ガイド

## 2. 実行ガイド

### 2.1 前提条件

```bash
# embed-llmが起動していることを確認
curl -s http://127.0.0.1:8003/health

# 設定ファイルが存在することを確認 (rag_src_dirを定義、デフォルトは/opt/llm/rag-src)
ls -la config/rag_pipeline.toml
```

### 2.2 ステップ1: クロール

```bash
# config/rag_pipeline.tomlのtarget_urls全件
nohup uv run python scripts/rag/ingestion/crawler.py > logs/crawl.log 2>&1 &
tail -f logs/crawl.log

# 単一URL
uv run python scripts/rag/ingestion/crawler.py --url "https://ziglang.org/documentation/master/" --lang en

# 複数URL (同じ--langが全てに適用される)
uv run python scripts/rag/ingestion/crawler.py \
    --url "https://ziglang.org/documentation/master/" \
          "https://zig.guide/" \
    --lang en
```

### 2.3 ステップ2: チャンク分割

```bash
# {rag_src_dir}/内の未処理.jsonファイル全件
uv run python scripts/rag/ingestion/chunk_splitter.py

# 単一ファイル (設定にある絶対パスを使用)
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-ziglang.json

# 既存チャンクの再生成 (--force)
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

### 2.4 ステップ3: 埋め込みと保存

```bash
# 実行前にembed-llmを確認
curl -s http://127.0.0.1:8003/health

uv run python scripts/rag/ingestion/ingester.py

# 既存URLの強制再登録 (削除して再挿入)
uv run python scripts/rag/ingestion/ingester.py --force
```

### 2.5 スクリプトごとの`--force`の動作

| Script | `--force` effect |
|---|---|
| `crawler.py` | 適用対象外 (クローラーは常に上書きし、実行ごとの`visited`集合により冪等性を確保) |
| `chunk_splitter.py` | 既存の`{stem}-*.json`チャンクを削除して再生成 |
| `ingester.py` | 対象URLの`chunks_vec` → `chunks` → `documents`レコードを削除後、再挿入 |

### 2.6 RAG整合性チェック (`db/maintenance.py`)

`check_rag_consistency(db)`を使用して、トリガーベースの同期失敗や孤立レコードを検出する。
大量取り込みの後、強制再登録の後、または診断時に実行する。

```python
from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues
from db.helper import SQLiteHelper

with SQLiteHelper("rag").open() as db:
    report: RagConsistencyReport = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```

**`RagConsistencyReport`のフィールド:**

| Field | Description |
|---|---|
| `chunks` | `chunks`テーブルの行数 |
| `fts` | `chunks_fts_docsize`シャドウテーブルにインデックスされたドキュメント数 |
| `vec` | `chunks_vec`テーブルの行数 |
| `orphan_vec_count` | `chunk_id`が`chunks`に対応する行を持たない`chunks_vec`の行数 |
| `fts_gap` | `chunks - fts`。0であればFTSインデックスは同期済み |
| `fts_orphan_count` | `fts - chunks`。正の値は余分なFTSエントリ (データ損失のリスク) を示す |
| `affected_chunk_ids` | FTSに存在しないchunk_id (最大10件) |
| `affected_doc_ids` | FTSに存在しないチャンクのdoc_id (最大10件) |
| `affected_orphan_chunk_ids` | `chunks`に対応する行がない`chunks_vec`のchunk_id (最大10件) |
| `affected_orphan_urls` | 孤立したvec行を持つドキュメントのURL (最大10件。親ドキュメントが解決できない場合は`None`) |

**CLI:** `/db consistency`はREPLから同じチェックを実行し、問題点を表示する。

**取り込み後の警告:** `ingester.py`は各`ingest_all()`実行後に非ブロッキングの整合性チェックを実行する。警告はログに記録されるが、取り込み処理自体は中断しない。

**注記:**
- `fts`は`chunks_fts`ではなく`chunks_fts_docsize` (FTS5シャドウテーブル) から読み取られる。
  これにより、バッキングテーブルのjoinに依存しない、正確なFTS5インデックス済みドキュメント数が得られる。
- `orphan_vec_count > 0`はvecトリガーの失敗を示す。該当URLに対して`ingester.py --force`を再実行することで修復できる。
- この関数は読み取り専用であり、不整合を修復するものではない。
- パフォーマンス: 孤立検出における`NOT IN`サブクエリはO(vec × chunks)である。大規模データセットではメンテナンスウィンドウ中に実行すること。

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
