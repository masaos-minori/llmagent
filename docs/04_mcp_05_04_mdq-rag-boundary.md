---
title: "MCP Security and Safety Model: MDQ vs RAG Boundary"
category: mcp
tags:
  - mcp
  - security
  - safety-model
  - mdq
  - rag
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_02_auth-profiles-and-sandboxing.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 04_mcp_05_05_mdq-enforcement-and-lockdown.md
---

# MCP セキュリティと安全性モデル: MDQ 対 RAG の境界

## MDQ 対 RAG の境界

> **正典の場所。** 本セクションは、以前 `04_mcp_07_mdq_rag_boundary.md`（コミット f24efc1 で削除）にあった内容を統合したものである。

### 目的

MDQ（Markdown Context Compression Engine）と RAG（Retrieval Augmented Generation）の間の所有権の境界を明確に定義し、エンジニアが特定のタスクにどちらのシステムを使用すべきか判断できるようにする。

---

### MDQ を使用する場面

以下の場合に MDQ を使用する。

- コンテンツが **Markdown のみ**（`.md`, `.markdown` ファイル）である。
- クエリが **構造を意識した検索**に関するもの: outline、見出し、階層的コンテキスト。
- **Markdown 特有の解析**が必要（セクション抽出、見出しに沿ったチャンク境界）。
- ワークロードが**低〜中程度の量**（数千〜数万件のドキュメント）である。

MDQ は、セマンティック埋め込みの品質よりも構造理解が重要となる Markdown ドキュメントに最適化されている。

**ツール:** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`
**データベース:** `mdq.sqlite`（`rag.sqlite` とは別）
**状態:** 本番運用可能

---

### RAG を使用する場面

以下の場合に RAG を使用する。

- コンテンツが **マルチフォーマット**: PDF、HTML、テキスト、コード、Markdown など。
- 埋め込みによる**セマンティック検索**（類似度ベースの検索）が必要。
- 見出しに沿った分割を超える**チャンク化戦略**（再帰的、トークンベースなど）が必要。
- ワークロードが**大量**である、または**精緻化**（リランク、RRF によるハイブリッド検索）が必要。
- メタデータ抽出とバリデーションを伴う**ドキュメント取り込みパイプライン**が必要。

RAG はエージェント層の主要なドキュメント検索システムである。全コンテンツタイプに対する汎用的な検索をサポートする。

**ツール:** `ingest`, `search`, `get_document`, `delete_document`, `list_documents`（rag-pipeline-mcp 経由）
**データベース:** `rag.sqlite`
**状態:** 本番運用可能

---

### データ所有権

| システム | データベース | 所有者 | 管理者 |
|---|---|---|---|
| MDQ | `mdq.sqlite` | MCP 層（`mcp_servers/mdq/`） | mdq-mcp サーバー（ポート 8013） |
| RAG | `rag.sqlite` | MCP 層（`scripts/mcp_servers/rag_pipeline/`） | rag-pipeline-mcp サーバー |

いずれのシステムも他方のデータベースに直接アクセスすることはない。それぞれが独自のスキーマ、インデックス、検索ロジックを保持する。

---

### エージェントのアクセスパターン

エージェント層は、両システムに **MCP ツール呼び出し**のみを通じてアクセスする。

1. **主経路（推奨）:** エージェントは MCP ルーティング（`ToolRouteResolver`）経由でツールを呼び出す。全てのツール呼び出しは MCP サーバーの抽象化層を通過する。
2. **管理者バイパス:** エージェント REPL の `/db` コマンドは、保守作業のために `rag.sqlite` に直接アクセスできる。これは管理者専用であり、通常の運用には含まれない。
3. **直接 DB アクセス（非推奨）:** アプリケーションコードは `mdq.sqlite` や `rag.sqlite` に対して `sqlite3` を直接 import してはならない。常に MCP ツールを使用すること。

---

### ルーティング方針

#### 1. ルーティングのヒューリスティック（分類器）

エージェントは軽量な分類器（`agent/mdq_rag_classifier.py`）を使用して、
ユーザーのクエリに基づき MDQ と RAG のどちらのツールを選ぶかを誘導する。

Markdown の構造に関する用語（例: "heading", "outline", "hierarchy",
"section", ".md", "table of contents"）を含むクエリは MDQ として分類され、それ以外はデフォルトで RAG となる。

分類器は各 LLM ターンの前に、1行のシステムプロンプトヒント（約20〜40トークン）を注入する。
LLM がそれに従わない場合もあり得るため、決定的なルーティングが必要な場合はオーバーライドモードを使用すること。

#### 2. 可用性フォールバック

| 条件 | 挙動 |
|---|---|
| MDQ が選択され、mdq-mcp が利用不可 | WARNING をログ出力; RAG ヒントにフォールバック |
| RAG が選択され、rag-pipeline-mcp が利用不可 | エラーを返す; フォールバックなし |
| オーバーライドモードで、強制指定したサーバーが利用不可 | エラーを返す |

RAG は常に本番環境で優先されるフォールバックである。

---

### 移行基準: MDQ から RAG へ

以下の場合に MDQ から RAG への移行を検討する。

- コンテンツ量が約10万ドキュメントを超える。
- Markdown 以外のコンテンツタイプを Markdown と併せて取り込む必要がある。
- セマンティック類似度検索の品質がボトルネックになる。
- ドキュメント間の重複排除、または重複排除を考慮した検索が必要になる。

自動的な移行パスは存在しない。移行には RAG パイプラインを介した再取り込みが必要である。

---

### 現在の状態

- **MDQ:** 本番運用可能。FTS5 検索とインデックス化を実装済み。
- **RAG:** 本番運用可能。完全な取り込みパイプライン、埋め込みサポート、ハイブリッド検索（RRF）が利用可能。

汎用的なドキュメント検索を伴う本番ワークロードには `rag-pipeline-mcp` を優先すること。
`mdq-mcp` は、埋め込み品質が重要でない Markdown 特有の構造的クエリにのみ使用すること。

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_02_auth-profiles-and-sandboxing.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `04_mcp_05_05_mdq-enforcement-and-lockdown.md`

## Keywords

mcp
security
safety-model
mdq
rag
mdq-rag-boundary
routing
classifier
data-ownership
migration-criteria
