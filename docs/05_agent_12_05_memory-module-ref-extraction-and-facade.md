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
  - 05_agent_12_01_memory-overview-and-modes-part1.md
  - 05_agent_12_02_memory-gate-data-model-search-part1.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
---

# Memory Layer — Module Reference

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

### 10. `extract.py` — ルールベースの抽出

| Function / Class | Returns | Description |
|---|---|---|
| `extract_memories(history, session_id=None, turn_id=None, project="", repo="", branch="", max_content_chars=500, policy=None)` | `list[MemoryEntry]` | 主要なエントリポイント。`max_content_chars` は assistant メッセージの切り詰め長。`policy` で `ExtractionPolicy` を上書き可能 |
| `ExtractionPolicy(...)` | Config | min_content_chars=80, min_user_content_chars=60, min_turns=2, max_entries=20 |

**モジュールレベルの定数:** `MIN_CONTENT_CHARS = 80`, `MIN_USER_CONTENT_CHARS = 60`, `MIN_TURNS = 2`, `MAX_ENTRIES = 20`, `SEMANTIC_HITS_REQUIRED_STRONG = 2`, `SEMANTIC_CONTENT_THRESHOLD = 200`, `IMPORTANCE_LENGTH_DIVISOR = 2000.0`


分類ロジック:
- セマンティック（ルール/決定）: assistant メッセージが `SEMANTIC_HITS_REQUIRED_STRONG` 件以上のキーワードを含むか、1件以上かつ長さが `SEMANTIC_CONTENT_THRESHOLD` 文字以上。さらに decision キーワードと semantic キーワードの両方が一致すれば `SourceType.DECISION`、それ以外は `SourceType.RULE`
- エピソディック（失敗/Q&A）: 失敗を示すキーワードがあれば `SourceType.FAILURE`、それ以外で `MIN_CONTENT_CHARS * 2` 文字以上あれば `SourceType.CONVERSATION`
- user メッセージからも抽出する: `MIN_USER_CONTENT_CHARS` 以上かつセマンティックキーワードを含む場合のみ、`SourceType.RULE`（tag: `user-rule`）として抽出（Explicit in code: `_try_extract_from_user`）

importance のヒューリスティック: `_importance_from_content()` により、種別・source_type ごとの基準値（semantic: DECISION=0.55 / それ以外0.4、episodic: FAILURE=0.45 / それ以外0.4）＋ length_bonus（最大0.3）＋（semanticのみ）keyword_bonus（最大0.2）＋（semanticのみ）固定0.1。episodic は上限0.8、semantic は上限1.0でクリップされる。

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

クラス `MemoryServices(injection, ingestion, store, retriever, embedding_client=None, use_memory_layer=True)`:

`AppServices.memory` の実体（型）となるファサードクラス（Explicit in code: モジュール docstring "Replaces MemoryLayer as the AppServices.memory type."）。

| Attribute / Method | Description |
|---|---|
| `injection` | MemoryInjectionService インスタンス |
| `ingestion` | MemoryIngestionService インスタンス |
| `store` | MemoryStore インスタンス |
| `retriever` | HybridRetriever インスタンス |
| `embedding_client` | EmbeddingClient。コンストラクタ引数が `None` の場合、`retriever.embed_client` から取得（それも無ければ `None`） |
| `get_activation_mode()` | 戻り値: "disabled"（`use_memory_layer=False`）/ "fts-only"（embedding_client なし、または無効）/ "degraded"（サーキットブレーカー作動中）/ "hybrid"（有効かつサーキット閉） |
| `get_stats()` | 以下のキーを持つ `dict` を返す: total (int)、semantic (int)、episodic (int)、by_source (dict[str, int])、embed_skip (int)、last_retrieval_mode (str)、fts_fallback_count (int) |
| `on_session_start(session_id)` | `injection.on_session_start()` に委譲する。`session_id` は現状 injection 側では未使用（コード注記: "session_id not used by injection layer"） |
| `on_session_stop(session_id, history, turn_id=None)` | `ingestion.on_session_stop()` に委譲する（非同期） |
| `on_user_prompt(query, session_id)` | `injection.on_user_prompt()` に委譲する（非同期） |

**実装上の補足 (Current behavior):** コンストラクタのデフォルトは `use_memory_layer=True` である（ドキュメント旧記述の `False` は誤り。Explicit in code）。

### 13.1 `ingestion.py` — MemoryIngestionService（詳細）

クラス `MemoryIngestionService(store, jsonl, retriever, embed_client, dedup_policy=None, project="", repo="", branch="", max_content_chars=500)`。

`services.py` の `ingestion` 属性の実体であり、抽出・重複排除・永続化を担う（重点調査対象、直近更新あり）。

| Method | Returns | Description |
|---|---|---|
| `on_session_stop(session_id, history, turn_id=None)` | `None` | `extract_memories()` で候補を抽出し、各エントリを埋め込み＋重複排除つきで永続化する |
| `write_semantic(session_id, content)` | `None` | importance=0.7, source_type=RULE の手動セマンティックエントリを重複排除なしで永続化 |
| `write_episodic(session_id, content)` | `None` | importance=0.5, source_type=CONVERSATION の手動エピソディックエントリを重複排除なしで永続化 |
| `stat_embed_skip` (attribute) | `int` | 埋め込み取得に失敗し埋め込みなしで保存された件数の累計 |

**実装意図 (Implementation note):** `on_session_stop()` による自動抽出は埋め込みベースの重複排除（`DedupAction.SKIP_NEW`）を適用するが、`write_semantic`/`write_episodic` による手動書き込みは意図的に重複排除をバイパスする（コード注記: "Manual writes via write_semantic/write_episodic bypass dedup intentionally."）。（Explicit in code）

**重複排除ロジック:**
- 埋め込み取得後、`HybridRetriever.knn_search()` で近傍5件を検索し、source_type ごとの閾値（`enums.DEDUP_THRESHOLDS`、未定義時は `DedupPolicy.threshold`）より距離が近い既存エントリがあれば新規エントリを破棄する（SKIP_NEW）
- 破棄されない場合も、閾値内の近傍が見つかれば `memory_links` テーブルに `(src_id, dst_id)` の関連リンクを記録する（`INSERT OR IGNORE`）

**失敗時の意図 (Failure behavior):**
- 埋め込み取得が失敗した場合（例外発生時含む）、`stat_embed_skip` をインクリメントしログ出力のうえ、埋め込みなしで SQLite/JSONL への保存を継続する（フェイルオープン。Explicit in code）
- JSONL への書き込みが `OSError` で失敗した場合、警告ログを出し「SQLite のみに保存された」ことを明示して処理を継続する（SQLite が正本であるため致命的エラーとしない。Explicit in code）
- `memory_links` への挿入が `sqlite3.OperationalError`/`IntegrityError` で失敗した場合も警告ログのみで処理を継続する

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes-part1.md`
- `05_agent_12_02_memory-gate-data-model-search-part1.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`

## Keywords

extract.py
jsonl_store.py
embedding_client.py
services.py
ingestion.py
dedup
memory_links
