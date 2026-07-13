---
title: "Memory Layer - Module Reference: Core and Store"
category: agent
tags:
  - agent
  - memory
  - module-reference
  - types
  - store
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_01_memory-overview-and-modes-part1.md
  - 05_agent_12_02_memory-gate-data-model-search-part1.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
---

# Memory Layer — Module Reference

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

### 1. `__init__.py` — 公開 API のバレル

サブモジュールからすべての公開シンボルを再エクスポートする。主なカテゴリ:

- **ランタイム型:** `MemoryEntry`、`MemoryQuery`、`MemoryHit`、`EmbeddingResult`、`EmbeddingErrorKind`、`SourceType`
- **Enum:** `DedupAction`、`DedupPolicy`、`MemoryType`
- **例外:** `EmbeddingProtocolError`、`EmbeddingTransportError`、`ExtractionError`、`InjectionValidationError`、`JsonlFormatError`、`MemoryConsistencyError`、`MemorySchemaError`、`UnknownMemoryTypeError`
- **モデル:** `ConsistencyReport`、`HistoryMessage`、`MemorySnippet`
- **サービス:** `MemoryIngestionService`、`MemoryInjectionService`、`MemoryServices`
- **ストア:** `MemoryStore`
- **JSONL:** `JsonlMemoryStore`
- **リトリーバー:** `FtsRetriever`、`HybridRetriever`、`VectorRetriever`
- **マッパー:** float から BLOB への変換とタイムスタンプ付与を行う内部変換関数
- **抽出:** `ExtractionPolicy`、`extract_memories`
- **埋め込み:** `EmbeddingClient`、`EmbeddingClientConfig`
- **注入:** `InjectionPolicy`

特記事項: 内部のマッパーユーティリティは、他のモジュールで使用するために `__all__` でエクスポートされている。

### 2. `types.py` — コアランタイム型

| Type | Description | Key fields |
|---|---|---|
| `MemoryEntry` | 永続化されるメモリエントリ | memory_id, memory_type (MemoryType: SEMANTIC="semantic" / EPISODIC="episodic"), source_type (SourceType: RULE="rule" / CONVERSATION="conversation" / DECISION="decision" / FAILURE="failure"), session_id (int \| None, default: None), turn_id (str \| None, default: None), content, summary, tags (list[str], default: []), importance (float, default: 0.5), pinned (bool, default: False), created_at (str, auto-filled by write_ops.add()), updated_at (str, auto-filled by write_ops.add()), project (str, default: ""), repo (str, default: ""), branch (str, default: "") |
| `MemoryQuery` | 検索入力 | query (str), memory_type (str \| None, default: None), limit (int, default: 10), session_id (int \| None, default: None)。`__post_init__` は `query` が空でないこと、`limit > 0` であることを検証する。 |
| `MemoryHit` | ランク付けされた検索結果 | entry (MemoryEntry), score (float) |
| `EmbeddingResult` | 埋め込み取得の結果 | success (bool), embedding (list[float] \| None), error_kind (EmbeddingErrorKind \| None) |
| `EmbeddingErrorKind` | エラー分類 | `DISABLED`, `TIMEOUT`, `HTTP_ERROR`, `CIRCUIT_OPEN`, `DIMENSION_MISMATCH`, `INVALID_RESPONSE`, `UNKNOWN_ERROR`（StrEnum。値は小文字: `"disabled"`、`"timeout"` など） |
| `SourceType` | エントリの発生元 | `"rule"`, `"conversation"`, `"decision"`, `"failure"`（StrEnum。メンバー名は大文字: RULE, CONVERSATION, DECISION, FAILURE） |

### 3. `enums.py` — ドメイン enum

| Enum / Dict | Values | Description |
|---|---|---|
| `MemoryType` | `"semantic"` (member: SEMANTIC), `"episodic"` (member: EPISODIC) | メモリの分類 |
| `DedupAction` | `"skip_new"` (member: SKIP_NEW) | 準重複が見つかった場合の重複排除動作 |
| `DedupPolicy` | action (DedupAction.SKIP_NEW) + threshold (0.3) | 重複排除設定用のデータクラス |
| `RetrievalMode` | `"fts"`, `"knn"`, `"hybrid"` (members: FTS, KNN, HYBRID) | 検索モードの選択 |
| `ExtractionDecision` | `"accept"`, `"reject_too_short"`, `"reject_no_keywords"`, `"reject_dedup"` (members: ACCEPT, REJECT_TOO_SHORT, REJECT_NO_KEYWORDS, REJECT_DEDUP) | 抽出結果 |
| `DEDUP_THRESHOLDS` | `RULE: 0.98`, `DECISION: 0.98`, `FAILURE: 0.90`, `CONVERSATION: 0.85` | ソースタイプごとの重複排除類似度閾値 |
| `RETENTION_DAYS` | `FAILURE: 180`, `CONVERSATION: 90`, `RULE/DECISION: None` | ソースタイプごとの保持ポリシー |

### 4. `exceptions.py` — 例外階層

| Exception | Raised when |
|---|---|
| `MemorySchemaError` | 無効なデータスキーマ（例: retriever における無効な created_at） |
| `MemoryConsistencyError` | FTS の件数と memories の件数が不一致 |
| `ExtractionError` | メモリ抽出が失敗した場合 |
| `InjectionValidationError` | 空のクエリが on_user_prompt に渡された場合 |
| `EmbeddingProtocolError` | 埋め込み API が予期しない応答を返した場合 |
| `EmbeddingTransportError` | 埋め込み API への HTTP トランスポートが失敗した場合 |
| `JsonlFormatError` | 読み込み時に JSONL の行の形式が不正だった場合 |
| `UnknownMemoryTypeError` | 認識できない memory_type 文字列だった場合 |
| `MemoryStorageError` | DB 書き込み操作が失敗した場合 |

### 5. `models.py` — 不変の DTO

| Class | Fields | Purpose |
|---|---|---|
| `HistoryMessage` | role (str), content (str) | 会話履歴内の単一メッセージ |
| `JsonlRecord` | 不変の DTO。フィールド: memory_id (str), memory_type (str), source_type (str), session_id (int \| None, default: None), turn_id (str \| None, default: None), project (str, default: ""), repo (str, default: ""), branch (str, default: ""), content (str), summary (str), tags (list[str], default: []), importance (float, default: 0.5), pinned (bool, default: False), created_at (str, default: ""), updated_at (str, default: "") | JSONL メモリストアからデシリアライズされたレコード |
| `MemorySnippet` | text (str), source (str), score (float) | ソースタグと検索スコアを持つ、注入用のコンテキストスニペット |
| `ConsistencyReport` | memories (int), fts (int), vec (int) | 整合性チェック用の行数比較 |

### 6. `store.py` — 読み取り専用の CRUD レイヤー

書き込み操作（`add`、`upsert`、`delete`、`clear_by_session`）は `write_ops.py` にある。

クラス `MemoryStore(embed_dim=None)`。

| Method | Returns | Description |
|---|---|---|
| `search_by_type(memory_type, limit=10, min_importance=0.0)` | `list[MemoryEntry]` | タイプでフィルタリングし、pinned DESC、importance DESC、created_at DESC の順で並べる |
| `list_entries(source_type=None, branch=None, limit=50)` | `list[MemoryEntry]` | オプションの source_type や branch でフィルタリングしたエントリを返す |
| `count_vec()` | `int` | memories_vec の行数 |
| `check_consistency()` | `ConsistencyReport` | memories / memories_fts / memories_vec の件数を比較する |
| `get_by_id(memory_id)` | `MemoryEntry \| None` | 主キーによる検索 |

**失敗モード:**
- `sqlite3.OperationalError` — DB ロック、vec テーブルの欠落など
- `MemoryConsistencyError` — FTS の件数取得が失敗した場合

**`list_entries` の branch フィルタ挙動 (境界条件):**

`branch` を指定した場合の WHERE 条件は `branch = '' OR branch = ?` であり、branch が空文字列のエントリ（例: リポジトリ非依存の全体ルール）は指定した branch 値に関わらず常にマッチする。branch を絞り込みたい場合でも、branch 未設定のエントリは除外されない（根拠: Explicit in code — `store.py` `list_entries()`）。

**`embed_dim` の実装挙動 (Current behavior):**

`MemoryStore.__init__` は `embed_dim` を `self._embed_dim` にそのまま保持するのみで、`store.py` 内のいずれのメソッドからも参照されない。デフォルト値は `None` であり、コード上「未指定時に 384 になる」処理は `store.py` には存在しない（旧ドキュメントの記述はコードと不一致 — 修正済み）。

実際には `agent/memory/ingestion.py` の `MemoryIngestionService` が `self._store._embed_dim` を読み取り、`write_ops.write_upsert(..., embed_dim=...)` に渡す。そこで `mapper._floats_to_blob(embedding, expected_dim)` が呼ばれ、`expected_dim` が非 None かつ埋め込みベクトルの長さと不一致の場合に `ValueError` を送出する（次元検証用途）。

384 という既定値は `MemoryStore` 自体にはなく、呼び出し元 `agent/factory.py` が `MemoryStore(embed_dim=ctx.cfg.memory.memory_embed_dim)` として渡す `AgentConfig.memory.memory_embed_dim`（`agent/config_dataclasses.py` で既定値 384、`agent/config_builders.py` で `memory_embed_dim` 設定キーから読み込み）に由来する。（根拠: Explicit in code — `store.py`, `ingestion.py`, `write_ops.py`, `mapper.py`, `factory.py`, `config_dataclasses.py`, `config_builders.py` を確認）

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes-part1.md`
- `05_agent_12_02_memory-gate-data-model-search-part1.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`

## Keywords

__init__.py
types.py
enums.py
exceptions.py
models.py
store.py
