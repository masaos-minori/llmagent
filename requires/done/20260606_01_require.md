# Markdown Context Compression Engine MCP Server — Implementation Plan

## 0. Assumptions and Design Policy

- Current ingestion pipeline:
  - `web_crawler.py`
  - `chunk_splitter.py`
  - `rag_ingester.py`
- `chunk_splitter.py` already supports Markdown snippet splitting by heading boundary via `md_index_enable`.
- The current Agent assumes HTTP MCP servers.
  - Uses `/v1/call_tool` and `/v1/tools`.
  - Performs tool-definition diff checks at startup.
  - Uses watchdog-based health monitoring.
- The current `file-mcp` provides:
  - `read_text_file`
  - `search_files`
  - `grep_files`
- These support search-oriented access to large documents.
- They do not support:
  - Markdown heading structure
  - heading-path based partial retrieval
- Therefore, introduce a new MCP server: `mdq-mcp`.
  - separate from `file-mcp`
  - provides a Markdown-specific index
  - provides partial retrieval APIs optimized for large Markdown documents

### Scope Assumptions

- Target documents:
  - local Markdown files
  - ADRs
  - specifications
  - `SKILL.md`
- Index storage:
  - local index DB equivalent to `.mdq/index.sqlite`
- Agent usage rule:
  - use `search_docs` before `read_file`
- Phase 1 core:
  - BM25
  - grep
  - heading traverse
- Phase 2 extensions:
  - embedding index
  - summary cache

---

## 1. Purpose

Implement a dedicated MCP server that compresses large Markdown while preserving meaning and retrieves only the necessary parts for injection.

The current RAG implementation assumes:

- web-derived documents
- generic chunk ingestion

It does not treat the following Markdown-specific concepts as first-class entities:

- heading hierarchy
- section boundaries
- heading path

At the same time, `chunk_splitter.py` already provides the foundation for Markdown heading-based splitting.

### Core Value

- Handle large Markdown without reading the full file.
- Use heading-level local search and local retrieval.
- Make the Agent follow this flow during document reference:
  - search
  - retrieve only relevant chunks
  - avoid full-file reading
- Integrate naturally into the existing MCP operating model:
  - HTTP
  - OpenRC
  - `/mcp`
  - `/v1/tools`
  - watchdog

---

## 2. Scope

### 2.1 Included

- AST parsing of Markdown files, or heading-aware parsing
- section-level chunk generation
- index construction equivalent to `.mdq/index.sqlite`
- `search_docs(query)`
- `get_chunk(chunk_id)`
- `outline(path)`
- path / tag / heading filters
- BM25 / grep / heading traverse
- incremental indexing
- MCP server implementation
- Agent-side policy update so that `search_docs` is preferred over `read_file`

### 2.2 Excluded from Initial Scope

- automatic integration of web-crawled Markdown
- semantic extraction from images, Mermaid, or binary attachments
- full normalization of complex Markdown extension syntax into AST
- distributed server architecture or external vector DB from the first iteration

---

## 3. Reuse of Existing Assets

### 3.1 Reuse Markdown Heading Splitting in `chunk_splitter.py`

Current `chunk_splitter.py`, when `md_index_enable=true`, can split:

- `.md`
- `.markdown`
- `.mdx`
- plain text containing headings

into snippets at heading boundaries.

It also supports fallback behavior when `md_snippet_max_chars` is exceeded.

This fits the first stage of Markdown Context Compression Engine.

#### Policy

- In Phase 1, import this heading-splitting logic into the `mdq-mcp` indexer.
- Store results in a dedicated Markdown index DB, not in `rag-src/chunk/*.txt`.

### 3.2 Reuse Existing SQLite / FTS5 / sqlite-vec Design

The current implementation uses SQLite with:

- `documents`
- `chunks`
- `chunks_vec`
- `chunks_fts`

It also uses:

- FTS5
- sqlite-vec

For Japanese, `normalized_content` is separated for FTS use.

This design can be reused for Markdown indexing.

#### Policy

- Use FTS5 as the primary search engine in `.mdq/index.sqlite`.
- Keep the schema extensible so a `chunks_vec`-equivalent table can be added later.
- Reuse the existing Sudachi-based normalization concept for Japanese search.

### 3.3 Keep MCP Server Base Aligned with Existing HTTP MCP

Current MCP servers use a unified interface based on FastAPI + Uvicorn:

- `GET /health`
- `GET /v1/tools`
- `POST /v1/call_tool`

The Agent already assumes this model for:

- tool-definition diff checks
- watchdog behavior

#### Policy

- Implement `mdq-mcp` with the same protocol.
- Add it as an OpenRC service.
- Include it in `/mcp` and watchdog targets.

---

## 4. To-Be Architecture

### 4.1 Server Name and Placement

- Server name: `mdq-mcp`
- Example files:
  - `scripts/mdq_mcp_server.py`
  - `config/mdq_mcp_server.json`
  - `init.d/mdq-mcp`
- Database:
  - `.mdq/index.sqlite`
  - `/opt/llm/db/mdq.sqlite`

### 4.2 Recommended Processing Flow

```text
Markdown files
  ↓
AST Parse / Heading-aware Parse
  ↓
Semantic Section Extraction
  ↓
SQLite Index (.mdq/index.sqlite)
  ↓
search_docs / outline / get_chunk
  ↓
Selected snippets only
  ↓
LLM Input
```

This flow connects the required design:

- AST Parse
- Semantic Index
- Relevant Extraction
- LLM Input

with the current pattern:

- chunk split
- SQLite ingestion

### 4.3 Agent Usage Order

```text
User asks about a large spec / ADR / SKILL.md
  ↓
mdq-mcp.search_docs(query, path/tag filters)
  ↓
mdq-mcp.get_chunk(chunk_id) or mdq-mcp.outline(path)
  ↓
Relevant snippets only
  ↓
LLM prompt injection
```

#### Usage Rule

- Use `search_docs` before `read_file`.
- Use `outline(path)` first to inspect structure.
- Then use `get_chunk(chunk_id)` for local retrieval.
- `grep_files` / `search_files` remain fallback options.

---

## 5. Index Design

### 5.1 DB Placement Policy

Use a dedicated DB equivalent to `.mdq/index.sqlite` instead of mixing with `rag.sqlite`.

#### Reasons

- Web/RAG chunks and local Markdown chunks have different meanings.
- Markdown needs dedicated metadata such as:
  - `heading_path`
  - `outline_depth`
  - `tags`
  - `section_kind`
- Local document updates have a different lifecycle from web ingestion.

### 5.2 Recommended Table Structure

#### `md_documents`

- `doc_id`
- `source_path`
- `title`
- `mtime`
- `etag_hash`
- `lang`
- `doc_hash`

#### `md_chunks`

- `chunk_id`
- `doc_id`
- `heading_path`
- `heading_level`
- `section_title`
- `tags`
- `token_count`
- `char_count`
- `content`
- `normalized_content`
- `anchor`
- `chunk_order`

#### `md_chunks_fts`

- FTS5 virtual table
- index over `COALESCE(normalized_content, content)`

#### `md_chunks_vec` (Phase 2 and later)

- embedding BLOB
- `chunk_id`
- `embedding`

This follows the existing `chunks_vec` / sqlite-vec approach.

#### `md_summary_cache` (Phase 2 and later)

- `chunk_id`
- `summary_key`
- `summary_text`
- `llm_model`
- `updated_at`

### 5.3 Required Metadata

Mandatory:

- heading path
- chunk id
- tags
- source path
- token count

Strongly recommended:

- `heading_level`
- `section_title`
- `chunk_order`
- `content_hash`
- `mtime`
- `lang`

---

## 6. Parser and Chunking Policy

### 6.1 Phase 1: heading-aware parse

Phase 1 uses a parser based on heading boundaries, leveraging the current Markdown heading-splitting logic in `chunk_splitter.py`.

This approach is:

- faster to introduce
- more stable initially
- more compatible with the existing implementation

### 6.2 Phase 2: AST Parse

The final target is AST-based parsing.

#### Target Node Types

- heading node
- paragraph node
- fenced code block
- list
- blockquote
- table
- frontmatter
- tag extraction

#### Recommended Phase Policy

- Phase 1: heading-aware parser
- Phase 2: Markdown AST parser
- Phase 3: section type / semantic tag estimation

---

## 7. MCP Tool Specification

### 7.1 Required Tools

#### `search_docs`

**Purpose**

Search only Markdown sections relevant to the query.

**Input Example**

```json
{
  "query": "watchdog healthcheck OpenRC",
  "limit": 10,
  "mode": "hybrid",
  "path_prefix": "/opt/llm/docs",
  "tag_filter": ["ops", "openrc"],
  "heading_prefix": "Deployment"
}
```

**Returned Fields**

- `chunk_id`
- `source_path`
- `heading_path`
- `score`
- `snippet`
- `token_count`
- `tags`

**Search Modes**

- `bm25`
- `grep`
- `hybrid`

#### `get_chunk`

**Purpose**

Get the body of the target section by `chunk_id`.
Optionally include sibling / parent heading context.

**Input Example**

```json
{
  "chunk_id": 1821,
  "with_neighbors": true
}
```

#### `outline`

**Purpose**

Return only the heading structure of a file.
Use this to understand structure without full-file reading.

**Input Example**

```json
{
  "path": "/opt/llm/docs/05_agent.md"
}
```

**Returned Fields**

- `path`
- `title`
- `outline[]`
  - `heading_path`
  - `heading_level`
  - `chunk_id`
  - `token_count`

### 7.2 Recommended Administrative Tools

#### `index_paths`

Index a target directory or file set.

#### `refresh_index`

Re-index only incremental updates.

#### `stats`

Return:

- indexed document count
- chunk count
- latest update time
- FTS size

#### `grep_docs`

Search Markdown chunks with regex priority.
Useful for logs and configuration lookup.

---

## 8. MCP Response Format

Current MCP returns `{"result": str, "is_error": bool}`.
Markdown Context Compression Engine requires structured data.

### 8.1 Recommended Extended Format

```json
{
  "result": "search_docs completed. hits=5",
  "result_text": "search_docs completed. hits=5",
  "result_data": {
    "hits": [
      {
        "chunk_id": 1821,
        "source_path": "/opt/llm/docs/05_agent.md",
        "heading_path": "3 > 3.1 > Tool Calling",
        "score": 12.48,
        "snippet": "agent.py は RAG 検索と MCP ツールコーリング...",
        "token_count": 148,
        "tags": ["agent", "mcp"]
      }
    ]
  },
  "is_error": false,
  "error_code": null,
  "truncated": false,
  "meta": {
    "mode": "hybrid",
    "latency_sec": 0.043,
    "fts_hits": 12,
    "grep_hits": 4
  }
}
```

### 8.2 Policy

- `result_text`: human-readable summary
- `result_data`: actual data
- `meta`: search mode, hit count, latency, filter conditions
- `truncated=true`: indicates hit count or snippet content was limited

---

## 9. `config/agent.json` Integration

### 9.1 `mcp_servers` Addition Example

```json
{
  "mcp_servers": {
    "mdq": {
      "transport": "http",
      "url": "http://127.0.0.1:8008",
      "cmd": [],
      "openrc_service": "mdq-mcp"
    }
  }
}
```

This matches the current MCP server configuration style and integrates naturally with watchdog and `/mcp` display.

### 9.2 `tool_definitions` Addition Example

```json
[
  {
    "type": "function",
    "function": {
      "name": "search_docs",
      "description": "Search indexed Markdown sections before reading full files.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": { "type": "string" },
          "limit": { "type": "integer" },
          "mode": { "type": "string" },
          "path_prefix": { "type": "string" },
          "tag_filter": {
            "type": "array",
            "items": { "type": "string" }
          },
          "heading_prefix": { "type": "string" }
        },
        "required": ["query"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_chunk",
      "description": "Get a Markdown chunk by chunk_id.",
      "parameters": {
        "type": "object",
        "properties": {
          "chunk_id": { "type": "integer" },
          "with_neighbors": { "type": "boolean" }
        },
        "required": ["chunk_id"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "outline",
      "description": "Get Markdown heading outline for a file.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": { "type": "string" }
        },
        "required": ["path"]
      }
    }
  }
]
```

This addition exposes Markdown-specific retrieval tools to the LLM. The current Agent already gives `tool_definitions` function-calling tools to the LLM and checks `/v1/tools` consistency through `tool_definitions_strict`.

### 9.3 System Prompt Rule

Add the following rule on the Agent side.

> When reading Markdown / ADR / SKILL.md / specifications, use `search_docs` or `outline` before `read_file` by default. Use full-file reading only as a last resort.

This prevents large documents from consuming context window unnecessarily. The current Agent already manages context size, history compression, and RAG search control, so this rule is consistent with current behavior.

---

## 10. `mdq-mcp` Implementation Targets

### 10.1 New Files

- `scripts/mdq_mcp_server.py`
- `scripts/mdq_indexer.py`
- `scripts/mdq_parser.py`
- `scripts/mdq_search.py`
- `scripts/mdq_models.py`
- `config/mdq_mcp_server.json`
- `init.d/mdq-mcp`

### 10.2 Existing Files to Modify

- `tool_executor.py`
  - add routing for `search_docs` / `get_chunk` / `outline` to `mdq`
- `agent_repl.py`
  - enforce preferred flow before large Markdown reading
- `agent_commands.py`
  - add `mdq-mcp` to `/mcp` display targets
- `deploy/deploy.sh`
- `deploy/setup_services.sh`

### 10.3 Reused Existing Code

- reuse the Markdown heading-splitting design in `chunk_splitter.py`
- reuse `SQLiteHelper`, `logger`, `config_loader`, and the shared MCP server base

---

## 11. Implementation Phases

## Phase 1: Minimal Introduction

### Goal

- basic `mdq-mcp` operation
- `search_docs` / `get_chunk` / `outline`
- FTS5 + heading path
- incremental indexing

### Implementation Scope

- heading-aware parse
- `.mdq/index.sqlite`
- `index_paths`
- `refresh_index`
- `search_docs(mode=bm25|grep|hybrid)`
- `get_chunk`
- `outline`

### Success Conditions

- Local retrieval is possible before full-file reading for large `SKILL.md`, ADRs, and specifications.
- Connectivity can be verified through `/mcp`.
- Operational rules can enforce `search_docs` before `read_file`.

## Phase 2: Precision Improvement

### Implementation Scope

- AST parser
- tag extraction
- section type estimation
- embedding index (`md_chunks_vec`)
- improved hybrid ranking
- summary cache

### Effects

- lower-noise relevant extraction
- support for expression variation and vocabulary gaps beyond BM25
- faster reuse through summary cache

## Phase 3: Agent Optimization

### Implementation Scope

- force `search_docs first` in the Agent prompt rules
- recommend the chain `outline -> search_docs -> get_chunk`
- automatically control snippet count and token budget passed back to the LLM
- integrate with `/context` and audit-related systems

### Effects

- sustained reduction of context window pressure
- more stable document-driven development answers
- lower-memory operation suitable for local LLMs

---

## 12. Risks and Countermeasures

### Risk 1: Incomplete Markdown Parser Coverage

**Countermeasure**

Use heading-aware parse in Phase 1. Defer complex syntax handling to the AST parser in Phase 2. This matches the staged approach already used by `chunk_splitter.py` for Markdown heading splitting.

### Risk 2: SQLite Index Growth

**Countermeasure**

- incremental indexing by path
- content hash / mtime comparison
- snippet length limits
- pruning of old summary cache entries

### Risk 3: Agent Keeps Using `read_file`

**Countermeasure**

- explicitly add the rule to `tool_definitions` and the system prompt
- add a review criterion: “for Markdown, use `search_docs` first”
- optionally issue a warning on large `read_text_file` calls

### Risk 4: Variability in Japanese Search Precision

**Countermeasure**

Use normalized FTS fields as in the current RAG system. The current system already uses `normalized_content` and Sudachi-normalized forms for Japanese search.

---

## 13. Test Plan

### Unit Tests

- heading extraction
- heading path generation
- outline correctness
- incremental indexing
- grep / BM25 / hybrid search

### Integration Tests

- `index_paths -> search_docs -> get_chunk`
- `outline -> get_chunk`
- tool calling from the Agent
- `/v1/tools` definition diff check
- watchdog / OpenRC startup verification

### Performance Tests

- large `SKILL.md`
- more than 100 ADR files
- compare BM25 / grep / hybrid
- compare token and latency impact vs direct `read_file`

---

## 14. Adoption Decision

This plan is a practical addition that optimizes large Markdown reference **without significantly changing the current architecture**.

It is especially implementable because the current system already has:

- a foundation for Markdown heading splitting
- SQLite / FTS5 / sqlite-vec / MCP HTTP infrastructure
- Agent-side `/mcp`, watchdog, and `tool_definitions` management

Therefore, even **Phase 1 alone** has high value.

Recommended initial landing point:

- `mdq-mcp`
- `.mdq/index.sqlite`
- `search_docs` / `get_chunk` / `outline`
- Agent-side usage rule introduction
