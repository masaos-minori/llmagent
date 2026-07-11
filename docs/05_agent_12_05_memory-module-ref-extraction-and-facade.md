---
title: "Memory Layer - Module Reference: Extraction and Facade"
category: agent
tags:
  - agent
  - memory
  - module-reference
  - extract
  - jsonl-store
  - embedding-client
  - services
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_01_memory-overview-and-modes.md
  - 05_agent_12_02_memory-gate-data-model-search.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_memory.md
---

# Memory Layer — Module Reference

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

### 10. `extract.py` — ルールベースの抽出

| Function / Class | Returns | Description |
|---|---|---|
| `extract_memories(history, session_id=None, turn_id=None, project="", repo="", branch="")` | `list[MemoryEntry]` | 主要なエントリポイント |
| `ExtractionPolicy(...)` | Config | min_content_chars=80, min_turns=2, max_entries=20, min_user_content_chars=60 |

**モジュールレベルの定数:** `MIN_CONTENT_CHARS = 80`, `MIN_USER_CONTENT_CHARS = 60`, `MIN_TURNS = 2`, `MAX_ENTRIES = 20`, `SEMANTIC_HITS_REQUIRED_STRONG = 2`, `SEMANTIC_CONTENT_THRESHOLD = 200`, `IMPORTANCE_LENGTH_DIVISOR = 2000.0`


分類ロジック:
- セマンティック（ルール/決定）: ルール／ポリシーのキーワードを含む、または長文の assistant メッセージ
- エピソディック（失敗/Q&A）: 失敗を示すキーワード、または実質的な回答

importance のヒューリスティック: 基準値 0.4 ＋ length_bonus ＋ keyword_bonus。

### 11. `jsonl_store.py` — 追記専用の JSONL アーカイブ

クラス `JsonlMemoryStore(path)`:

| Method | Returns | Description |
|---|---|---|
| `write(entry)` | `None` | 非同期での追記（asyncio.Lock により直列化） |
| `read_all()` | `list[MemoryEntry]` | すべてのエントリの同期読み込み |
| `read_active()` | `list[MemoryEntry]` | ソースタイプごとの保持ポリシーに基づき、期限切れでないエントリを読み込む |
| `count_all()` | `int` | 有効なレコードの件数（`read_all()` に委譲する） |

**失敗モード:** 形式が不正な行に対する `JsonlFormatError`。

**注記:** SQLite のメモリテーブルが現在のメモリ状態の正本である。JSONL はインポート／エクスポートおよび災害復旧のための追記専用アーカイブとして保持される。削除および pin/unpin の状態変更は JSONL からは再生されない。

### 12. `embedding_client.py` — HTTP 埋め込みクライアント

クラス `EmbeddingClient(config, http=None, *, enabled=False)`:

| Method | Returns | Description |
|---|---|---|
| `fetch(text)` | `EmbeddingResult` | リトライとサーキットブレーカーを伴う非同期の埋め込み |
| `get_status()` | `EmbeddingClientStatus` | enabled、circuit_open、fail_count、resets_in_sec のスナップショット |

`EmbeddingClientConfig`: embed_url, timeout=5.0, max_retries=2, circuit_open_after=3, circuit_reset_sec=60.0, query_prefix="query: ", embed_dim=384, local_only=False。

**無効時の動作:** `enabled=False` の場合、`fetch()` は HTTP 呼び出しを行わずに即座に `EmbeddingResult(success=False, error_kind=DISABLED)` を返す。

`EmbeddingClientStatus` のフィールド: `enabled: bool`、`circuit_open: bool`、`fail_count: int`、`resets_in_sec: float | None`（circuit が closed の場合は None、それ以外は circuit がリセットされるまでの秒数）、`local_only: bool`。

`EmbeddingErrorKind` の値: `DISABLED`, `CIRCUIT_OPEN`, `TIMEOUT`, `HTTP_ERROR`, `INVALID_RESPONSE`, `UNKNOWN_ERROR`, `DIMENSION_MISMATCH`。

### 13. `services.py` — MemoryServices ファサード

クラス `MemoryServices(injection, ingestion, store, retriever, embedding_client=None, *, use_memory_layer=False)`:

| Attribute / Method | Description |
|---|---|
| `injection` | MemoryInjectionService インスタンス |
| `ingestion` | MemoryIngestionService インスタンス |
| `store` | MemoryStore インスタンス |
| `retriever` | HybridRetriever インスタンス |
| `embedding_client` | EmbeddingClient（提供されない場合は retriever から取得） |
| `get_activation_mode()` | 戻り値: "disabled" / "fts-only" / "degraded" / "hybrid" |
| `get_stats()` | 以下のキーを持つ `dict` を返す: total (int)、semantic (int)、episodic (int)、by_source (dict[str, int])、embed_skip (int)、last_retrieval_mode (str)、fts_fallback_count (int) |
| `on_session_start(session_id)` | `injection.on_session_start()` に委譲する |
| `on_session_stop(session_id, history, turn_id)` | `ingestion.on_session_stop()` に委譲する |
| `on_user_prompt(query, session_id)` | `injection.on_user_prompt()` に委譲する |

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`

## Keywords

extract.py
jsonl_store.py
embedding_client.py
services.py
