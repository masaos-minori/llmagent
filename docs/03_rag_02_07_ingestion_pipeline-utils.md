---
title: "Ingestion Pipeline Utilities"
category: rag
tags:
  - crawler-utils
  - chunk-english-mixin
  - chunk-japanese-mixin
  - chunk-utils
  - pipeline-utils
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler-part1.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md
  - 03_rag_02_04_ingestion_pipeline-ingester-part1.md
  - 03_rag_02_08_ingestion_pipeline-shared.md
  - 03_rag_02_09_ingestion_pipeline-shared-utilities.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 5. Crawler Utils (`scripts/rag/ingestion/crawler_utils.py`)

### 5.1 モジュール概要

`crawler_utils.py` — WebCrawlerのための純粋関数ユーティリティ群: URLヘルパー、コンテンツ抽出、言語判定、対象URLのパース。`WebCrawler` クラスを400行未満に保つために抽出された。

**モジュールレベルの定数**

| 定数 | 値 | 説明 |
|---|---|---|
| `_SUPPORTED_LANGS` | `frozenset({"en", "ja"})` | 解決後（出力）のlang値としてサポートされる言語コード |
| `_VALID_HINT_LANGS` | `frozenset({"en", "ja", "auto"})` | ページごとのCJK比率判定用の"auto"を含む、有効なヒントlang値 |
| `_CJK_RATIO_THRESHOLD` | `0.1` | この値を超えるとテキストが日本語と判定されるCJK文字比率のしきい値 |
| `_TARGET_URL_ENTRY_LENGTH` | `2` | target_urlsエントリの想定要素数: [url, lang] |
| `MIN_TEXT_LENGTH_FOR_DETECTION` | `100`（`rag.utils` 由来） | 言語判定に必要な最小テキスト長 |

**CJK判定用Unicodeコードポイント範囲**

| 定数 | 範囲 | 説明 |
|---|---|---|
| ひらがな + カタカナ | "぀"–"ヿ" 
| CJK統合漢字 | "一"–"鿿" 
| CJK拡張A | "㐀"–"䶿" 

**公開関数**

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `url_to_slug` | `(url: str) -> str` | URLをファイルシステムで安全なASCIIスラグに変換する（最大80文字）；スキームを除去し、英数字以外をハイフンに置換する |
| `normalize_url` | `(url: str) -> str` | フラグメントと末尾のスラッシュを除去する |
| `same_origin` | `(url: str, base: str) -> bool` | スキームとホスト名が一致する場合にTrueを返す |
| `extract_text` | `(soup: BeautifulSoup) -> str` | soupからノイズタグ（nav、footer、aside、script、style、noscript）を除去する；`include_comments=False`、`include_tables=True`、`no_fallback=False`、`target_language=None` の設定でTrafilaturaを用いて本文テキストを抽出する；フォールバックとしてBS4の `get_text(separator="\n", strip=True)` を使用する |
| `detect_lang` | `(text: str) -> str \| None` | CJK比率判定；比率が0.1以上なら'ja'、それ以外は'en'を返す；100文字未満のテキストではNoneを返す |
| `parse_target_urls` | `(target_raw: list[list[str]]) -> list[tuple[str,str]]` | target_urls設定を検証し(url, lang)のタプルにパースする；URL検証には `rag.utils.validate_url`（http/https限定）を使用する；不正なエントリの場合はValueErrorを発生させる |
| `parse_targets_file` | `(path: Path) -> list[tuple[str,str]]` | `target_urls = [[url, lang], ...]` を含むTOMLファイルをパースする；ファイルが見つからない場合はFileNotFoundError、パースエラーの場合はValueErrorを発生させる |

**実装上の補足:**
- `parse_targets_file` はURL検証にモジュール内の関数を使う。`rag.utils.validate_url`（http/https限定）と異なり `file://` スキームも許可する。docstringには「`--targets-file` クロールパスで使うfile://を扱うため」と明記されている（`crawler_utils.py:31-40`）。一方 `parse_target_urls`（ingester.toml の `target_urls` をパースする方）は `rag.utils.validate_url` を使うためfile://を受け付けない。両関数は同じ「(url, lang)のリストをパースする」役割に見えるが、想定入力元（TOML `--targets-file` vs 設定内リスト）によって許可URLスキームが異なる。(Explicit in code)

---

## 6. Chunk English Mixin (`scripts/rag/ingestion/chunk_english.py`)

### 6.1 モジュール概要

`chunk_english.py` — `ChunkEnglishMixin`: ストップワードフィルタリングと文境界分割を伴う、英語テキスト用の段落/文単位のチャンク化。多重継承により `ChunkSplitter` にミックスインされる。

---

## 7. Chunk Utils (`scripts/rag/ingestion/chunk_utils.py`)

### 7.1 モジュール概要

`chunk_utils.py` — `ChunkEnglishMixin` と `ChunkJapaneseMixin` で共有されるバッファヘルパー。末尾重複バッファの管理と、最小/最大チャンクサイズ制約付きの項目蓄積を提供する。両ミックスインクラスと `chunk_splitter.py` からインポートされる。

**公開関数**

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `start_next_buf` | `(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str` | prevからの末尾重複を任意で行いつつ、新しい蓄積バッファを開始する。`chunk_overlap=0` の場合はnext_itemをそのまま返す。それ以外の場合は、prevの末尾N文字（N = chunk_overlap）をnext_itemの先頭に付加する |
| `merge_text_items` | `(items: list[str], sep: str, min_chunk: int, max_chunk: int, chunk_overlap: int) -> list[str]` | min_chunk ≤ len ≤ max_chunk を満たすように項目をチャンクへ蓄積する。短い末尾項目は破棄されず最後のチャンクに結合される |

**ミックスインでの使用箇所:**

| ミックスイン | 使用する関数 | 目的 |
|---|---|---|
| `ChunkEnglishMixin` | `merge_text_items` | 重複を伴う段落/文の蓄積 |
| `ChunkJapaneseMixin` | `start_next_buf`, `merge_text_items` | 重複を伴う文ペアの蓄積 |
| `ChunkSplitter` | `merge_text_items` | コードブロックの蓄積（空行分割） |

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler-part1.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`
- `03_rag_02_04_ingestion_pipeline-ingester-part1.md`
- `03_rag_02_08_ingestion_pipeline-shared.md`
- `03_rag_02_09_ingestion_pipeline-shared-utilities.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

crawler-utils
chunk-english-mixin
chunk-japanese-mixin
chunk-utils
pipeline-utils
rag
