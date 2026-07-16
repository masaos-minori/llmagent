---
title: "6.5 models_config.py (`scripts/rag/models_config.py`)"
category: rag
tags:
  - rag
  - dto
  - data-model
related:
  - 03_rag_00_document-guide.md
  - 03_rag_04_05_dto-types.md
source:
  - 03_rag_04_05_dto-types.md
---

# 6.5 models_config.py (`scripts/rag/models_config.py`)

### 6.5 models_config.py (`scripts/rag/models_config.py`)

**MqeConfig** — MQEクエリ展開の設定。

| Field | Type | Default | Description |
|---|---|---|---|
| `use_mqe` | `bool` | `True` | MQEクエリ展開を有効化 |
| `mqe_url` | `str` | `""` | MQEサービスのURL |
| `mqe_timeout` | `float` | `5.0` | MQEリクエストのタイムアウト (秒) |

**FusionConfig** — RRF融合の設定。

| Field | Type | Default | Description |
|---|---|---|---|
| `rrf_k` | `int` | `60` | ランク集約用のRRF定数 |

**RerankConfig** — クロスエンコーダーリランクの設定。

| Field | Type | Default | Description |
|---|---|---|---|
| `use_rerank` | `bool` | `True` | クロスエンコーダーによるリランクを有効化 |
| `rerank_url` | `str` | `""` | リランクサービスのURL |
| `rerank_timeout` | `float` | `10.0` | リランクリクエストのタイムアウト (秒) |
| `rerank_max_tokens` | `int` | `512` | リランクLLM呼び出しの最大トークン数 |

**SearchConfig** — 検索の設定。

| Field | Type | Default | Description |
|---|---|---|---|
| `use_search` | `bool` | `True` | ベクトル/FTS検索を有効化 |
| `embed_url` | `str` | `""` | 埋め込みサービスのURL |
| `embed_timeout` | `float` | `5.0` | 埋め込みリクエストのタイムアウト (秒) |
| `top_k_search` | `int` | `10` | クエリごとの結果数 |
| `rag_min_score` | `float` | `0.0` | フィルタリング用の最小スコア閾値 |
| `use_rrf` | `bool` | `True` | RRFランク融合を有効化 |

**ChunkSplitterConfig** — チャンク分割の設定。

| Field | Type | Default | Description |
|---|---|---|---|
| `chunk_size` | `int` | `500` | チャンクサイズの目標値 (文字数) |
| `chunk_overlap` | `int` | `50` | チャンク間の重複 (文字数) |
| `lang` | `str` | `"en"` | テキスト分割対象の言語 |
| `md_index_enable` | `bool` | `False` | Markdown見出しベースのチャンク分割を有効化 |

**IngesterConfig** — 取り込みの設定。

| Field | Type | Default | Description |
|---|---|---|---|
| `embed_url` | `str` | `""` | 埋め込みサービスのURL |
| `embed_timeout` | `float` | `5.0` | 埋め込みリクエストのタイムアウト (秒) |
| `batch_size` | `int` | `32` | 埋め込みリクエストのバッチサイズ |

**PipelineConfig** — トップレベルのパイプライン設定。各ステージのネストされた設定を含む。

| Field | Type | Description |
|---|---|---|
| `mqe` | `MqeConfig` | MQEクエリ展開の設定 |
| `fusion` | `FusionConfig` | RRF融合の設定 |
| `rerank` | `RerankConfig` | クロスエンコーダーリランクの設定 |
| `search` | `SearchConfig` | 検索の設定 |

### 実装上の補足

- 本ファイルの全dataclass (`MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`,
  `ChunkSplitterConfig`, `IngesterConfig`, `PipelineConfig`) は `scripts/rag/` 配下の
  どのモジュールからも import・インスタンス化されていない。
  実行時の設定読み込みは `ConfigLoader().load("xxx.toml")` が返す生の `dict` を
  `cfg.get("key", default)` の形で直接参照する方式であり (例:
  `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/ingester.py`)、
  本ファイルのdataclassは経由しない。
  [Explicit in code] — importのグレップ結果より、本ファイルへの参照は自己定義のみ。
- `RagPipeline` が実際に使用する実行時設定コントラクトは
  `shared/types.py` の `RagConfig` (Protocol) であり、そのdocstringには
  「`rag.models_config.*` はingestion TOML向けのファイル形式DTO」と明記されている。
  ただし前述の通り、ingestion側スクリプトも現状はdict直接参照であり、
  本ファイルのdataclassとの接続は確認できない。
  [Needs confirmation] — 将来的な移行を見込んだ未接続の定義か、削除漏れかは
  コードから判断できない。

## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)
- `shared/types.py` の `RagConfig` Protocol — 実行時に実際に使われる設定コントラクト

## Keywords

dto
data-model
unused-dto
