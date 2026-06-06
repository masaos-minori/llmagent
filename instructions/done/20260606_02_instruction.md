# rag-pipeline-mcp — Consolidated Specification Addendum

## 1. Purpose

This addendum assumes that the current six-step `RagPipeline` inside the REPL pipeline is integrated into a single MCP server named `rag-pipeline-mcp`.

Current responsibility set:

1. MQE
2. Search
3. RRF
4. Rerank
5. Dedup
6. Augment

Current behavior:

- `AgentREPL._handle_user_message()` calls `ctx.rag.augment()` directly.
- RAG processing is centralized in `agent_rag.py` under `RagPipeline`.

This addendum defines two items:

- `/v1/tools` definition for `rag-pipeline-mcp` (JSON-equivalent)
- `config/agent.json` additions for `mcp_servers` and `tool_definitions`

---

## 2. Background

The current REPL pipeline processes one turn in this order:

1. MQE
2. Search
3. RRF
4. Rerank
5. Dedup
6. Augment
7. LLM call

### 2.1 Step Semantics

- **MQE**
  - expands the query into `N` queries
  - uses the last two user utterances as `history_context`
- **Search**
  - runs KNN (`sqlite-vec`) and BM25 (`FTS5`) for each query
- **RRF**
  - merges results with `Σ 1/(60+rank)`
- **Rerank**
  - re-scores top candidates with an LLM
- **Dedup**
  - prevents excessive chunk injection from the same document
- **Augment**
  - creates a context block in this form:
    - `"[Source: {title} | {url}]\n{content}"`

### 2.2 Why MCP Integration Is Natural

The current Agent already uses MCP servers over HTTP.

- MCP servers expose `/v1/call_tool` and `/v1/tools`
- The Agent performs `tool_definitions` diff checks
- The Agent uses watchdog-based MCP health checks

Therefore, moving the RAG pipeline into the same MCP operational model is a natural design extension.

---

## 3. `/v1/tools` Definition for `rag-pipeline-mcp`

The current common MCP style uses `/v1/tools` mainly for returning tool names and descriptions.

For RAG, a richer format with `input_schema` and `output_schema` is preferred because:

- current MCP responses are centered on `{"result": str, "is_error": bool}`
- RAG needs structured intermediate outputs and debug data

### 3.1 Recommended Extended Format

```json
{
  "server_name": "rag-pipeline-mcp",
  "server_version": "1.0.0",
  "tools": [
    {
      "name": "rag_run_pipeline",
      "description": "Run MQE, Search, RRF, Rerank, Dedup and Augment as a single integrated RAG pipeline.",
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Original user query."
          },
          "history_context": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Recent user utterances used only for MQE."
          },
          "use_mqe": {
            "type": "boolean",
            "description": "Enable or disable MQE."
          },
          "use_search": {
            "type": "boolean",
            "description": "Enable or disable search."
          },
          "use_rrf": {
            "type": "boolean",
            "description": "Enable or disable RRF merge."
          },
          "use_rerank": {
            "type": "boolean",
            "description": "Enable or disable rerank."
          },
          "mqe_n_queries": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of expanded queries for MQE."
          },
          "top_k_search": {
            "type": "integer",
            "minimum": 1,
            "description": "Top-K per query for vector/FTS search."
          },
          "top_k_rerank": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of candidates to rerank."
          },
          "rrf_k": {
            "type": "integer",
            "minimum": 1,
            "description": "RRF smoothing constant."
          },
          "rag_min_score": {
            "type": "number",
            "description": "Minimum rerank score threshold."
          },
          "max_chunks_per_doc": {
            "type": "integer",
            "minimum": 1,
            "description": "Maximum number of chunks selected from the same document."
          },
          "rag_top_k": {
            "type": "integer",
            "minimum": 1,
            "description": "Maximum number of selected hits for augmentation."
          },
          "use_refiner": {
            "type": "boolean",
            "description": "Enable refiner after rerank."
          },
          "use_semantic_cache": {
            "type": "boolean",
            "description": "Enable semantic cache for the full pipeline."
          },
          "debug": {
            "type": "boolean",
            "description": "Return detailed intermediate stage outputs when true."
          }
        },
        "required": ["query"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "query": { "type": "string" },
          "queries": {
            "type": "array",
            "items": { "type": "string" }
          },
          "results_by_query": {
            "type": "array",
            "items": { "type": "object" }
          },
          "merged_hits": {
            "type": "array",
            "items": { "type": "object" }
          },
          "reranked_hits": {
            "type": "array",
            "items": { "type": "object" }
          },
          "deduped_hits": {
            "type": "array",
            "items": { "type": "object" }
          },
          "selected_hits": {
            "type": "array",
            "items": { "type": "object" }
          },
          "augmented_text": {
            "type": "string",
            "description": "Final RAG context block to append to the user message."
          }
        },
        "required": ["query", "selected_hits", "augmented_text"]
      }
    },
    {
      "name": "rag_debug_pipeline",
      "description": "Run the integrated RAG pipeline and always return all intermediate stage outputs for debugging.",
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Original user query."
          },
          "history_context": {
            "type": "array",
            "items": { "type": "string" }
          },
          "mqe_n_queries": {
            "type": "integer",
            "minimum": 1
          },
          "top_k_search": {
            "type": "integer",
            "minimum": 1
          },
          "top_k_rerank": {
            "type": "integer",
            "minimum": 1
          },
          "rrf_k": {
            "type": "integer",
            "minimum": 1
          },
          "rag_min_score": {
            "type": "number"
          },
          "max_chunks_per_doc": {
            "type": "integer",
            "minimum": 1
          },
          "rag_top_k": {
            "type": "integer",
            "minimum": 1
          }
        },
        "required": ["query"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "query": { "type": "string" },
          "queries": {
            "type": "array",
            "items": { "type": "string" }
          },
          "results_by_query": {
            "type": "array",
            "items": { "type": "object" }
          },
          "merged_hits": {
            "type": "array",
            "items": { "type": "object" }
          },
          "reranked_hits": {
            "type": "array",
            "items": { "type": "object" }
          },
          "deduped_hits": {
            "type": "array",
            "items": { "type": "object" }
          },
          "selected_hits": {
            "type": "array",
            "items": { "type": "object" }
          },
          "augmented_text": {
            "type": "string"
          }
        },
        "required": [
          "query",
          "queries",
          "results_by_query",
          "merged_hits",
          "reranked_hits",
          "deduped_hits",
          "selected_hits",
          "augmented_text"
        ]
      }
    }
  ]
}
```

### 3.2 Rationale for Two Tools

The two-tool split matches the current separation between:

- the normal `augment()` path
- observation / validation paths such as `/rag search` and debug output

Use:

- `rag_run_pipeline` for the standard lightweight path
- `rag_debug_pipeline` when all intermediate results must be returned

### 3.3 Minimal Compatibility Format

If strict compatibility with existing `/v1/tools` is required, use the minimal name/description format.

```json
{
  "tools": [
    {
      "name": "rag_run_pipeline",
      "description": "Run MQE, Search, RRF, Rerank, Dedup and Augment as a single integrated RAG pipeline."
    },
    {
      "name": "rag_debug_pipeline",
      "description": "Run integrated RAG pipeline and return all intermediate stage outputs for debugging."
    }
  ]
}
```

This is the most compatible format with the current MCP convention.

---

## 4. `config/agent.json` — `mcp_servers` Addition Example

The current Agent calls MCP servers over HTTP and performs both:

- `/v1/tools` diff checks at startup
- watchdog-based health checks

To add `rag-pipeline-mcp` as a peer MCP server, add its connection information and OpenRC service name to `mcp_servers`.

### 4.1 Example

Port `8007` is used as an example because existing MCP servers already use `8004`, `8005`, and `8006`.

```json
{
  "mcp_servers": {
    "web_search": {
      "transport": "http",
      "url": "http://127.0.0.1:8004",
      "cmd": [],
      "openrc_service": "web-search-mcp"
    },
    "file": {
      "transport": "http",
      "url": "http://127.0.0.1:8005",
      "cmd": [],
      "openrc_service": "file-mcp"
    },
    "github": {
      "transport": "http",
      "url": "http://127.0.0.1:8006",
      "cmd": [],
      "openrc_service": "github-mcp"
    },
    "rag_pipeline": {
      "transport": "http",
      "url": "http://127.0.0.1:8007",
      "cmd": [],
      "openrc_service": "rag-pipeline-mcp"
    }
  }
}
```

### 4.2 Addition Policy

- Use `rag_pipeline` as the key name.
  - This makes dedicated routing in `ToolExecutor` straightforward.
  - It also matches the naming granularity of `web_search`, `file`, and `github`.
- Use `transport="http"`.
  - The current Agent uses HTTP MCP as the standard operating model.
- `openrc_service` must match the OpenRC script name.
  - The watchdog uses `rc-service restart` and resolves service names from `mcp_servers[*].openrc_service`.

---

## 5. `config/agent.json` — `tool_definitions` Addition Example

The current Agent provides `tool_definitions` to the LLM and allows the LLM to select MCP tools through tool calling.

Therefore, if `rag-pipeline-mcp` is introduced as an integrated MCP server, both RAG tools must also be added to `tool_definitions`.

### 5.1 OpenAI-Compatible Function Calling Example

```json
{
  "tool_definitions": [
    {
      "type": "function",
      "function": {
        "name": "rag_run_pipeline",
        "description": "Run MQE, Search, RRF, Rerank, Dedup and Augment as a single integrated RAG pipeline.",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Original user query."
            },
            "history_context": {
              "type": "array",
              "items": { "type": "string" },
              "description": "Recent user utterances used only for MQE."
            },
            "debug": {
              "type": "boolean",
              "description": "Return detailed intermediate outputs when true."
            }
          },
          "required": ["query"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "rag_debug_pipeline",
        "description": "Run integrated RAG pipeline and return all intermediate stage outputs for debugging.",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Original user query."
            },
            "history_context": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["query"]
        }
      }
    }
  ]
}
```

### 5.2 Addition Policy

- `rag_run_pipeline`
  - use for the standard path
  - this is the logical replacement for `ctx.rag.augment()`
- `rag_debug_pipeline`
  - use for `/rag search`-style or debug retrieval
  - this corresponds to the current observation path handled by `/rag search` and `debug_mode`
- Whether the LLM selects these tools directly or the REPL calls them internally is a design choice.
  - However, adding them to `tool_definitions` unifies startup-time `/v1/tools` checks and strict-mode validation.
  - In the current system, `tool_definitions_strict=true` causes startup failure when diffs exist.

---

## 6. Integrated `agent.json` Addition Example (Excerpt)

The following example shows `mcp_servers` and `tool_definitions` added together.

```json
{
  "mcp_servers": {
    "web_search": {
      "transport": "http",
      "url": "http://127.0.0.1:8004",
      "cmd": [],
      "openrc_service": "web-search-mcp"
    },
    "file": {
      "transport": "http",
      "url": "http://127.0.0.1:8005",
      "cmd": [],
      "openrc_service": "file-mcp"
    },
    "github": {
      "transport": "http",
      "url": "http://127.0.0.1:8006",
      "cmd": [],
      "openrc_service": "github-mcp"
    },
    "rag_pipeline": {
      "transport": "http",
      "url": "http://127.0.0.1:8007",
      "cmd": [],
      "openrc_service": "rag-pipeline-mcp"
    }
  },
  "tool_definitions": [
    {
      "type": "function",
      "function": {
        "name": "rag_run_pipeline",
        "description": "Run MQE, Search, RRF, Rerank, Dedup and Augment as a single integrated RAG pipeline.",
        "parameters": {
          "type": "object",
          "properties": {
            "query": { "type": "string" },
            "history_context": {
              "type": "array",
              "items": { "type": "string" }
            },
            "debug": { "type": "boolean" }
          },
          "required": ["query"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "rag_debug_pipeline",
        "description": "Run integrated RAG pipeline and return all intermediate stage outputs for debugging.",
        "parameters": {
          "type": "object",
          "properties": {
            "query": { "type": "string" },
            "history_context": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["query"]
        }
      }
    }
  ]
}
```

---

## 7. Implementation Notes

### 7.1 REPL-Side Change Assumption

The above `tool_definitions` can also support future LLM-autonomous selection of `rag_run_pipeline` / `rag_debug_pipeline`.

However, the safer initial design is:

- let `AgentREPL._handle_user_message()` call the MCP server directly as an internal orchestration step

This is natural because the current `AgentREPL` already treats:

- RAG context injection
- tool loop execution

as separate paths.

### 7.2 Consistency Between `/v1/tools` and `tool_definitions`

The current Agent compares `/v1/tools` and `tool_definitions` at startup.

If `tool_definitions_strict=true`, startup is aborted on mismatch.

Therefore, when adding `rag-pipeline-mcp`, the following must stay aligned:

- tool names
- descriptions
- required parameters

### 7.3 Additional OpenRC / Deploy Targets

To deploy `rag-pipeline-mcp` into real operation, add the following.

- `scripts/rag_pipeline_mcp_server.py`
- `config/rag_pipeline_mcp_server.json`
- `init.d/rag-pipeline-mcp`
- update `deploy/deploy.sh`
- update `deploy/setup_services.sh`
