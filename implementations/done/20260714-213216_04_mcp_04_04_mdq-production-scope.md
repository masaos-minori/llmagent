# Implementation Procedure: Clarify MDQ Production-Ready Scope and Hybrid Search Status

## Goal

Make it explicit that MDQ is production-ready only for FTS5-based Markdown structural search, while hybrid embedding/vector search must not be presented as production-ready since it is stubbed and returns empty results.

## Scope

- `docs/04_mcp_00_document-guide.md`
- `docs/04_mcp_04_04_mdq.md`
- `docs/04_mcp_90_inconsistencies_and_known_issues.md`

**Out-of-Scope:**
- Implementing MDQ hybrid search (Non-Goal)
- Changing MDQ database schema (Non-Goal)
- Changing RAG behavior (Non-Goal)
- Changing routing (Non-Goal)

## Assumptions

1. This is primarily a documentation task; no source code changes are required.
2. Implementation inspection from Task 11 confirmed hybrid search is stubbed:
   - `scripts/mcp_servers/mdq/search.py:151-157`: `_search_vector()` returns empty list
   - `scripts/mcp_servers/mdq/tools.py:35`: Tool description states `"bm25/grep (hybrid is not yet supported)"`
   - `scripts/mcp_servers/mdq/service.py:88-92`: Config fields exist but only used for DB schema creation
   - DB schema creates vector table conditionally but never populates or queries it meaningfully

## Implementation

### Procedure

#### Step 1: Update `04_mcp_00_document-guide.md` AI Query Routing Table

Current L43 says "mdq-mcpは本番稼働可能か" without qualification. Add caveat about hybrid search.

Replace L43:
```markdown
| web-search/github/shell/mdq各mcpが提供するtoolは。mdq-mcpは本番稼働可能か | `04_mcp_04`(mdq-mcpは実装済み) |
```

With:
```markdown
| web-search/github/shell/mdq各mcpが提供するtoolは。mdq-mcpのFTS5検索は本番稼働可能、ハイブリッド検索は未実装 | `04_mcp_04`(mdq-mcpはFTS5検索のみ実装済み) |
```

#### Step 2: Update `04_mcp_04_04_mdq.md` production readiness statement

Add explicit production-ready scope statement in the MDQ section. After the tool status line (L25), add:

```markdown
**本番稼働範囲:** FTS5ベースのMarkdown構造的検索のみが本番稼働可能。`use_embedding = true`によるハイブリッド検索はstub（空リストを返す）であり、本番環境では使用できない。
```

#### Step 3: Update MDQ "Search modes" table

Current L66-72 lists hybrid mode without noting it's non-functional. Add note to the hybrid row.

After L72:
```markdown
| ハイブリッド（フェーズ2） | FTS5 + セマンティックベクトル検索を RRF で統合 | `use_embedding = true` |
```

Add a new row below:
```markdown
| ハイブリッド（フェーズ2） | **非稼働** — FTS5 + セマンティックベクトル検索を RRF で統合 | `use_embedding = true` |
```

And update L73-78 to clarify:
```markdown
**ハイブリッド検索（フェーズ2）:**

`use_embedding = true` の場合、MDQ はハイブリッド検索を試みるが、`_search_vector()` は空リストを返すため、結果は FTS5 のみとなる。
```

#### Step 4: Update "MDQ hybrid vs RAG decision criteria" table

Current L80-88 presents hybrid search as an operational option. Replace with:

Replace L80-88:
```markdown
**MDQ ハイブリッド対 RAG の判断基準:**

| 使用場面 | 推奨 | 理由 |
|---|---|---|
| Markdown の構造的クエリ（見出し、セクション、outline） | MDQ ハイブリッド | MDQ は Markdown ドキュメント構造を理解する; FTS5 はドキュメント内のキーワードマッチングに高精度 |
| 全インデックス済みコンテンツに対する汎用的なセマンティック検索 | RAG パイプライン | RAG はより広いコーパスカバレッジと成熟した埋め込みモデル統合を持つ |
| ドキュメント間の構造比較 | MDQ ハイブリッド | MDQ の chunk_id には見出しの階層情報が含まれる（level, parent_path, ordinal） |
```

With:
```markdown
**MDQ FTS5対 RAG の判断基準:**

| 使用場面 | 推奨 | 理由 |
|---|---|---|
| Markdown の構造的クエリ（見出し、セクション、outline） | MDQ FTS5 | MDQ は Markdown ドキュメント構造を理解する; FTS5 はドキュメント内のキーワードマッチングに高精度 |
| 全インデックス済みコンテンツに対する汎用的なセマンティック検索 | RAG パイプライン | RAG はより広いコーパスカバレッジと成熟した埋め込みモデル統合を持つ |
| ドキュメント間の構造比較 | MDQ FTS5 | MDQ の chunk_id には見出しの階層情報が含まれる（level, parent_path, ordinal） |

> **注記:** MDQ のハイブリッド検索（`use_embedding = true`）は未実装（stub）。セマンティック検索が必要な場合は RAG パイプラインを使用すること。
```

#### Step 5: Add entry to `04_mcp_90_inconsistencies_and_known_issues.md`

Add a new known issue documenting the hybrid search stub status:

```markdown
### MDQ ハイブリッド検索はstub（未実装）

MDQ の `use_embedding = true` 設定でハイブリッド検索が有効になるが、`_search_vector()` は常に空リストを返す。セマンティック検索の結果は得られない。

- **影響:** `use_embedding = true` を設定しても、検索結果は FTS5 のみ
- **対応:** ハイブリッド検索を本番投入するには、`_search_vector()` の実装が必要
- **関連ファイル:** `scripts/mcp_servers/mdq/search.py:151-157`, `scripts/mcp_servers/mdq/tools.py:35`
```

## Method

- Pattern-based search followed by targeted text replacement via file edit.
- Preserve surrounding context and formatting.
- Use consistent terminology across all documents.

## Validation plan

1. Verify no document presents MDQ hybrid search as production-ready.
2. Confirm all mentions of `use_embedding=true` include caveat about stubbed implementation.
3. Check operators would not attempt to rely on hybrid search for production use cases.
4. Verify summary sections consistently qualify MDQ production readiness.
5. Run `uv run pytest` if linting is configured.
