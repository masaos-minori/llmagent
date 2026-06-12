# 取込パイプライン — 実行ガイド

API リファレンス → [`docs/03_ref-ingestion.md`](03_ref-ingestion.md)

## 1. ドキュメント収集・投入

取込は `scripts/rag/ingestion/crawler.py` → `scripts/rag/ingestion/chunk_splitter.py` → `scripts/rag/ingestion/ingester.py` の 3 ステップで実行する。

### 1.1 前提条件

- `embed-llm` サービスが起動済み (`curl -s http://127.0.0.1:8003/health` で確認)

### 1.2 実行手順

```bash
source .venv/bin/activate

# ── ステップ 1: クロール ──────────────────────────────────────────────────────
# 全 TARGET_URLS のクロール (長時間時は nohup 推奨)
nohup uv run python scripts/rag/ingestion/crawler.py > logs/crawl.log 2>&1 &

tail -f logs/crawl.log

# 単一 URL のクロール
uv run python scripts/rag/ingestion/crawler.py --url "https://ziglang.org/documentation/master/" --lang en

# 複数 URL のクロール (同一 --lang が全 URL に適用される)
uv run python scripts/rag/ingestion/crawler.py \
    --url "https://ziglang.org/documentation/master/" \
          "https://zig.guide/" \
    --lang en

# ── ステップ 2: チャンク分割 ─────────────────────────────────────────────────
uv run python scripts/rag/ingestion/chunk_splitter.py

# 特定ファイルのみ処理
uv run python scripts/rag/ingestion/chunk_splitter.py --file rag-src/20240101120000-ziglang.txt

# 既存チャンクを再生成する場合 (--force)
uv run python scripts/rag/ingestion/chunk_splitter.py --force

# ── ステップ 3: 埋込生成・DB 投入 ────────────────────────────────────────────
# embed-llm が起動していることを確認
curl -s http://127.0.0.1:8003/health

uv run python scripts/rag/ingestion/ingester.py

# 強制再登録 (既登録 URL を最新コンテンツで上書き)
uv run python scripts/rag/ingestion/ingester.py --force
```

### 1.3 ファイルライフサイクル

| パス | 生成元 | フォーマット |
|---|---|---|
| `rag-src/yyyymmddhhmmss-{slug}.txt` | `rag/ingestion/crawler.py` | JSON: `{url, title, lang, fetched_at, content, code_blocks: [...]}` |
| `rag-src/chunk/{stem}-{idx:04d}.txt` | `rag/ingestion/chunk_splitter.py` | JSON: `{url, title, lang, source_file, chunk_index, chunk_type, content, normalized_content, etag, last_modified}` |
| `rag-src/registered/{stem}-{idx:04d}.txt` | `rag/ingestion/ingester.py` が移動 | 上記と同一 (処理済みを示す) |

拡張子は `.txt` でも中身は JSON。
