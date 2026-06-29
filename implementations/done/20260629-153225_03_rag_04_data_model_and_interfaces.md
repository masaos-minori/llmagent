# Implementation: RAG Documentation Schema Field Completeness

## Goal

Fix malformed Markdown structure (missing JSON fields, broken inline code, table consistency) in the two canonical RAG documentation files to ensure accurate parsing by humans and AI agents.

## Scope

- **In-Scope**:
  - `docs/03_rag_04_data_model_and_interfaces.md` — add missing schema fields to §1.1 and §1.2 JSON examples; fix inline code around `<pre>` tag reference; verify all tables render correctly
  - `docs/03_rag_02_ingestion_pipeline.md` — read-only verification of §2.4 and §3.4
  - Add Markdown lint configuration for the two docs
- **Out-of-Scope**:
  - Runtime file format changes
  - Rewriting the entire RAG documentation set
  - Translating the Japanese §2.0 table in `03_rag_04_data_model_and_interfaces.md`

## Assumptions

- The canonical crawler JSON schema has 11 fields: `schema_version`, `artifact_type`, `created_by`, `url`, `title`, `lang`, `fetched_at`, `content`, `code_blocks`, `etag`, `last_modified` — as shown in `03_rag_02_ingestion_pipeline.md` §2.4
- The canonical chunk JSON schema has 14 fields: `schema_version`, `artifact_type`, `created_by`, `url`, `title`, `lang`, `source_file`, `chunk_index`, `chunk_type`, `chunking_strategy`, `content`, `normalized_content`, `etag`, `last_modified` — as shown in §3.4
- `03_rag_02_ingestion_pipeline.md` §2.4 and §3.4 already have correct headings and fenced `json` blocks

## Implementation

### Target file: `docs/03_rag_04_data_model_and_interfaces.md`

#### Procedure

1. **Fix §1.1 (crawler output)** — add 5 missing fields to JSON example and field table
2. **Fix §1.2 (chunk output)** — add 3 missing fields to JSON example and field table
3. **Fix inline code** around `<pre>` tag reference in the `code_blocks` table row if needed
4. **Verify all table separator rows** use `|---|---|---|` consistently

#### Method

Direct file edit — insert missing fields into JSON examples and table rows.

#### Details

**§1.1 Crawler output (lines 15-23):**

Current JSON example has 6 fields. Add 5 missing fields to match §2.4 in `03_rag_02_ingestion_pipeline.md`:

```json
{
  "schema_version": "1",
  "artifact_type": "crawl",
  "created_by": "crawler",
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "fetched_at": "2024-01-01T12:00:00",
  "content": "body text",
  "code_blocks": ["code block 1", "code block 2"],
  "etag": "optional-http-etag",
  "last_modified": "optional-http-date"
}
```

**§1.1 field table (lines 26-34):** Add rows for `schema_version`, `artifact_type`, `created_by`, `etag`, `last_modified`:

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Schema version (e.g. "1") |
| `artifact_type` | string | Artifact type ("crawl") |
| `created_by` | string | Creator identifier ("crawler") |
| `etag` | string \| null | HTTP ETag from original crawl |
| `last_modified` | string \| null | HTTP Last-Modified from original crawl |

**§1.2 Chunk output (lines 39-53):** Add 3 missing fields to JSON example:

```json
{
  "schema_version": "1",
  "artifact_type": "chunk",
  "created_by": "chunk_splitter",
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "source_file": "20240101120000-example.json",
  "chunk_index": 0,
  "chunk_type": "text",
  "chunking_strategy": "text",
  "content": "original chunk text",
  "normalized_content": "normalized form (JA only; null for EN/code)",
  "etag": "optional-etag-string",
  "last_modified": "optional-http-date"
}
```

**§1.2 field table (lines 55-67):** Add rows for `schema_version`, `artifact_type`, `created_by`:

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Schema version (e.g. "1") |
| `artifact_type` | string | Artifact type ("chunk") |
| `created_by` | string | Creator identifier ("chunk_splitter") |

**Inline code fix:** If the `<pre>` inline code in the `code_blocks` table row is flagged by a linter, apply escaping: `` `<pre>` `` → `\`<pre>\`` or equivalent.

### Target file: `docs/03_rag_02_ingestion_pipeline.md`

#### Procedure

Read-only verification — confirm §2.4 and §3.4 headings and JSON fenced blocks are complete. No changes expected.

### Target file: `.markdownlint.json` (new) or `pyproject.toml` script entry

#### Procedure

Add Markdown lint configuration targeting the two docs:
- Disable rules that conflict with intentional style (MD013 line length, MD033 inline HTML for `<pre>` references)
- Enable structural rules (MD003 heading style, MD031 fenced code blocks, MD055/056 table pipe style)

#### Method

Add `.markdownlint.json` at project root with minimal configuration:

```json
{
  "default": true,
  "MD013": false,
  "MD033": false,
  "MD003": {"style": "atx"},
  "MD031": true,
  "MD055": true,
  "MD056": true
}
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_04_data_model_and_interfaces.md` §1.1 | Field-by-field comparison against `03_rag_02_ingestion_pipeline.md` §2.4 | Manual diff + `grep schema_version docs/03_rag_04_data_model_and_interfaces.md` | All 11 crawler JSON fields present in both example and table |
| `docs/03_rag_04_data_model_and_interfaces.md` §1.2 | Field-by-field comparison against `03_rag_02_ingestion_pipeline.md` §3.4 | Manual diff + `grep schema_version docs/03_rag_04_data_model_and_interfaces.md` | All 14 chunk JSON fields present in both example and table |
| Both docs | Markdown structure lint | `npx markdownlint docs/03_rag_02_ingestion_pipeline.md docs/03_rag_04_data_model_and_interfaces.md` | Exit code 0, zero lint errors |
| Both docs | JSON fenced block validation | `grep -c '^\`\`\`json' docs/03_rag_04_data_model_and_interfaces.md` | At least 2 fenced json blocks (§1.1 and §1.2) |
