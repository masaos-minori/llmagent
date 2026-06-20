# Implementation: scripts/mcp/rag_pipeline/tools.py (update — tool descriptions)

## Goal

Update all 4 RAG pipeline tool description strings to emphasize multi-format support,
semantic/embedding-based retrieval, and production-ready status.

## Scope

**In:**
- 4 top-level `"description"` values in `scripts/mcp/rag_pipeline/tools.py`

**Out:**
- Parameter-level `"description"` values (left unchanged)
- Tool names (must not change)
- Pipeline stage list strings inside the existing multiline description

## Assumptions

- `rag_run_pipeline` and `rag_debug_pipeline` use multiline string descriptions
  (lines 13-15 and 37-40 approximately); the replacement must preserve valid Python syntax
- `rag_list_documents` and `rag_delete_document` use single-line descriptions

## Implementation

### Target file

`scripts/mcp/rag_pipeline/tools.py`

### Procedure

Apply 4 targeted replacements:

#### rag_run_pipeline (line 13)

Current (multiline):
```python
"description": (
    "Run integrated RAG pipeline (MQE→Search→RRF→Rerank→Dedup→Augment). "
    "..."
),
```
New (single string):
```python
"description": "Run the full RAG pipeline (MQE→Search→RRF→Rerank→Dedup→Augment) for multi-format, semantic retrieval. Production-ready.",
```

#### rag_debug_pipeline (line 37)

Current (multiline):
```python
"description": (
    "Run integrated RAG pipeline and return all intermediate stage outputs"
    "..."
),
```
New (single string):
```python
"description": "Run the RAG pipeline and return all intermediate stage outputs for debugging. Multi-format, semantic retrieval. Production-ready.",
```

#### rag_list_documents (line 56)

```
- "List indexed documents in the RAG store."
+ "List indexed documents in the production RAG store (multi-format: PDF, HTML, text, code, Markdown)."
```

#### rag_delete_document (line 75)

```
- "Delete a document and all its chunks from the RAG store by URL."
+ "Delete a document and all its chunks from the production RAG store by URL (multi-format store)."
```

### Method

4 individual `Edit` operations. Read the current multiline description format for
`rag_run_pipeline` and `rag_debug_pipeline` before editing to match exact existing text.

### Details

- The multiline description for `rag_run_pipeline` and `rag_debug_pipeline` should be
  collapsed to a single-line string for consistency; check the actual content first
- All new descriptions include "Production-ready." or "production RAG store" to
  contrast with MDQ's "Experimental."
- Parameter-level descriptions (e.g., `"Original user query."`) are unchanged

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Old rag_list description absent | `grep -n "List indexed documents in the RAG store\." scripts/mcp/rag_pipeline/tools.py` | 0 matches |
| Old rag_delete description absent | `grep -n "Delete a document.*RAG store by URL\." scripts/mcp/rag_pipeline/tools.py` | 0 matches |
| "Production-ready" or "production RAG" present | `grep -c "Production-ready\|production RAG" scripts/mcp/rag_pipeline/tools.py` | >= 4 matches |
| Tool names unchanged | `grep -n '"name":' scripts/mcp/rag_pipeline/tools.py` | Same names as before |
| Lint | `uv run ruff check scripts/mcp/rag_pipeline/tools.py` | 0 errors |
| RAG pipeline service tests pass | `uv run pytest tests/test_rag_pipeline_mcp_service.py -x -v` | all pass |
