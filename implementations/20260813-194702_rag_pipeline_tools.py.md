## Goal

Add the schema-2.0 tool-metadata contract (`is_write`, `requires_serial`,
`resource_scope_kind`, `resource_scope_keys`) to every entry in
`scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py::TOOL_LIST`, so that
`McpToolDiscoveryService` (once its own required-field validation lands) can
discover and register the rag-pipeline-mcp server's tools instead of rejecting
them as incomplete.

## Scope

In scope:
- The 4 `TOOL_LIST` entries in `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py`:
  `rag_run_pipeline`, `rag_debug_pipeline`, `rag_list_documents`,
  `rag_delete_document`.

Out of scope:
- Any other MCP server's `TOOL_LIST` (covered by sibling implementation docs).
- `scripts/agent/services/mcp_tool_discovery.py`'s validator/registry logic
  (covered by a sibling implementation doc for that file).
- `scripts/shared/resource_scope.py` (a dependency of this change, owned by a
  different implementation cycle — see Assumptions).
- Any `docs/*.md` edit.

## Assumptions

- This file currently has **no** schema-2.0 fields on any of its 4 entries —
  confirmed by reading the file in full: every entry has only `name`,
  `description`, `inputSchema`, `status`. This is a fresh add for all 4 tools,
  not a backfill.
- `implementations/done/20260620-145230_rag_pipeline_tools.py.md` exists from
  a prior implementation cycle (dated 2026-06-20, before schema-2.0 existed).
  It predates and is unrelated to this plan's `resource_scope_kind`/
  `resource_scope_keys` contract — a coincidental filename match, not this
  plan's change. Confirmed by grep: no `resource_scope_kind`/
  `resource_scope_keys` string exists anywhere in `scripts/` or `tests/`
  today.
- A shared contract validator (`scripts/shared/resource_scope.py`, per the
  plan's Phase 1) is assumed to land as a dependency before or alongside this
  change; it defines the canonical kind-prefixed scope-string shape
  (`f"{resource_scope_kind}:{normalized_value}"`) this doc's `resource_scope_kind`
  values must be drawn from. That module is out of scope here and is not
  written by this implementation cycle.
- `rag_delete_document`'s single argument is `url` (a document URL, not a
  filesystem path); its scope is store-level, not argument-derived — the tool
  operates against "the production RAG store" as a whole (per its own
  description), so no single argument key identifies a narrower resource.
  This matches the plan's Affected-areas note: "fixed store scope."

## Design decisions

- `rag_delete_document` is the only state-changing tool in this file (it
  deletes a document and all its chunks). It gets `is_write=True`,
  `requires_serial=True` (mutating the shared store; conservative, matching
  the plan's `rag_store`/`mdq_store` fixed-scope precedent for RAG/MDQ),
  `resource_scope_kind="rag_store"`, and `resource_scope_keys=[]` — an empty
  list because the scope is fixed at the store level (`"rag_store:default"`,
  per the plan's Design section's scope-string catalogue), not derived from
  any single argument's runtime value. This mirrors the plan's stated
  intent ("fixed store scope") rather than keying off `url`.
- `rag_run_pipeline` and `rag_debug_pipeline` (query/read pipeline execution)
  and `rag_list_documents` (listing) are read-only: `is_write=False`,
  `requires_serial=False`, `resource_scope_kind=""`, `resource_scope_keys=[]`.
  None of their arguments (`query`, `history_context`, `debug`, `lang`,
  `limit`) identify a resource to scope against, and read-only tools carry no
  serialization requirement under the plan's conflict-graph design (read/read
  pairs are never edges).
- Field ordering in each dict: the 4 new fields are appended after the
  existing `status` key, preserving the file's current key order for the
  first 4 keys and keeping a stable, greppable position for the new fields
  across all 10 servers in this plan.

## Alternatives considered

- Scoping `rag_delete_document` by `resource_scope_keys=["url"]` (keying off
  the argument value) instead of a fixed empty-keys store scope: rejected
  because the plan's Affected-areas row explicitly calls out "fixed store
  scope" for this tool, and RAG/MDQ store-level concurrency has not been
  analyzed (per the plan's Assumptions — "SQLite-backed RAG/MDQ mutation
  concurrency is out of scope to verify here; the fixed store-level scope
  ... is a conservative placeholder"). Per-URL scoping would understate the
  real serialization requirement if the underlying store cannot safely
  interleave concurrent deletes against different URLs.
- Treating `rag_run_pipeline`/`rag_debug_pipeline` as writes because they may
  have side effects (e.g. cache population): rejected — the file's own
  docstrings describe them as retrieval/debug operations, and the plan's
  Scope section labels this file's "pipeline/listing tools" as read-only.

## Implementation

### Target file: `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py`

### Procedure

1. Read the current `TOOL_LIST` in full (already done for this doc — 4
   entries, no schema-2.0 fields present).
2. For each of the 3 read-only entries (`rag_run_pipeline`,
   `rag_debug_pipeline`, `rag_list_documents`), append 4 keys after `"status":
   "production",`.
3. For `rag_delete_document`, append the same 4 keys with write-tool values
   after its `"status": "production",` line.
4. Leave `inputSchema`, `description`, `required` lists, and all other
   existing keys unchanged.

### Method

Direct literal-dict edit of the existing `TOOL_LIST` module-level list; no
new imports, no `TypedDict` needed (this file currently types `TOOL_LIST` as
`list[dict[str, Any]]`, unlike `mdq_tools.py`'s `MCPToolSchema` `TypedDict` —
kept consistent with this file's own existing style rather than introducing a
new typed structure here).

### Details

```python
TOOL_LIST: list[dict[str, Any]] = [
    {
        "name": "rag_run_pipeline",
        ...
        "status": "production",
        "is_write": False,
        "requires_serial": False,
        "resource_scope_kind": "",
        "resource_scope_keys": [],
    },
    {
        "name": "rag_debug_pipeline",
        ...
        "status": "production",
        "is_write": False,
        "requires_serial": False,
        "resource_scope_kind": "",
        "resource_scope_keys": [],
    },
    {
        "name": "rag_list_documents",
        ...
        "status": "production",
        "is_write": False,
        "requires_serial": False,
        "resource_scope_kind": "",
        "resource_scope_keys": [],
    },
    {
        "name": "rag_delete_document",
        ...
        "status": "production",
        "is_write": True,
        "requires_serial": True,
        "resource_scope_kind": "rag_store",
        "resource_scope_keys": [],
    },
]
```

## Compatibility considerations

- Additive-only change to dict literals; no function signatures change.
  `McpToolDiscoveryService`'s *current* `_validate_and_normalize_entry()`
  type-checks these fields only `if field_name in entry` (optional today), so
  this change is backward compatible with the discovery service's current
  behavior. It becomes load-bearing once the sibling implementation for
  `mcp_tool_discovery.py` makes the 4 fields required — without this doc's
  change, discovery would then reject all 4 of this file's tools.
- No consumer downstream of `TOOL_LIST` (e.g. `server.py`'s `/v1/tools`
  endpoint) needs a code change; it already serializes whatever dict shape
  `TOOL_LIST` contains.

## Security considerations

- Marking `rag_delete_document` `is_write=True`/`requires_serial=True`
  strengthens (not weakens) its scheduling safety — previously the DAG
  scheduler had no explicit metadata for this tool and would have relied on
  `build_runtime_tool()`'s silent defaults at discovery time.
- No change to `shell`/argument-injection surfaces; this file has no
  executable-command arguments.

## Rollback considerations

- Revert is a pure dict-literal removal (drop the 4 appended keys per entry);
  no data migration, no schema version bump on the wire format beyond the
  additive keys themselves.

## Validation plan

- `uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v` (new,
  per the plan's Phase 2 — not written by this doc) should pass for this
  file's 4 entries once the shared validator lands.
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_runtime_tool_routing_integration.py -v` — per the plan's Validation
  plan row, confirms round-trip preservation of all 4 fields for tools
  discovered from this server.

## Out of scope

- Any change to `scripts/shared/runtime_tool.py`, `tool_spec.py`, or
  `resource_scope.py` (renamed/new fields consumed by this data, owned by a
  different file in the plan).
- Any change to `scripts/mcp_servers/server.py`'s envelope-level
  `MCP_TOOL_SCHEMA_VERSION`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-194702
- Related target files: scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py
