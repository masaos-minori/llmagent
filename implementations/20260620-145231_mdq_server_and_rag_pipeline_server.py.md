# Implementation: mdq/server.py + rag_pipeline/server.py (update — server descriptions)

## Goal

Update the `description=` argument in `MdqMCPServer` and `RagPipelineMCPServer`
class definitions to reflect MDQ's experimental/Markdown-only scope and RAG's
multi-format/production-ready role.

## Scope

**In:**
- `scripts/mcp/mdq/server.py:45` — `description=` argument
- `scripts/mcp/rag_pipeline/server.py:63` — `description=` argument

**Out:**
- Module-level docstrings (lines 3 in each file) — unchanged
- Any other attribute or method

## Assumptions

- `description=` is a string kwarg passed to the parent `MCPServer` class
- Current values:
  - MDQ: `"Markdown Context Compression Engine MCP server"`
  - RAG: `"RAG Pipeline MCP server (MQE→Search→RRF→Rerank→Dedup→Augment)"`

## Implementation

### Target files

- `scripts/mcp/mdq/server.py`
- `scripts/mcp/rag_pipeline/server.py`

### Procedure

#### mdq/server.py line 45

```
- description="Markdown Context Compression Engine MCP server",
+ description="Markdown Context Compression Engine MCP server (Markdown-only, structure-aware retrieval, experimental)",
```

#### rag_pipeline/server.py line 63

```
- description="RAG Pipeline MCP server (MQE→Search→RRF→Rerank→Dedup→Augment)",
+ description="RAG Pipeline MCP server — multi-format semantic retrieval, production-ready",
```

### Method

Two individual `Edit` operations, one per file, targeting the exact `description=` line.

### Details

- The MDQ description adds a parenthetical to the existing string; the server name
  ("Markdown Context Compression Engine") is preserved
- The RAG description replaces the pipeline stage list with a role-emphasizing phrase;
  the stage list is available in the tool description for `rag_run_pipeline`
- No other lines in either file are affected

## Validation plan

| Check | Command | Expected |
|---|---|---|
| MDQ old description absent | `grep -n '"Markdown Context Compression Engine MCP server",' scripts/mcp/mdq/server.py` | 0 matches |
| MDQ new description present | `grep -n "experimental" scripts/mcp/mdq/server.py` | 1 match at line 45 |
| RAG old description absent | `grep -n "MQE.*Search.*RRF" scripts/mcp/rag_pipeline/server.py` | 0 matches in description= line |
| RAG new description present | `grep -n "production-ready" scripts/mcp/rag_pipeline/server.py` | 1 match at line 63 |
| Lint | `uv run ruff check scripts/mcp/mdq/server.py scripts/mcp/rag_pipeline/server.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp/mdq/server.py scripts/mcp/rag_pipeline/server.py` | 0 errors |
| MDQ server tests pass | `uv run pytest tests/test_mdq_service.py -x -v` | all pass |
| RAG pipeline tests pass | `uv run pytest tests/test_rag_pipeline_mcp_service.py -x -v` | all pass |
