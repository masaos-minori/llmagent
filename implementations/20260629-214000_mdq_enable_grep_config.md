## 1. Goal
- Add `enable_grep` and `index_roots` configuration fields to `config/mdq_mcp_server.toml` and wire them into `MdqService` so that all production paths and limits are driven from config with safe defaults.

## 2. Scope
- **In-Scope**:
  - Add `enable_grep` field to `config/mdq_mcp_server.toml` (default: `true`)
  - Add `index_roots` field to `config/mdq_mcp_server.toml` as an alias/complement to `allowed_dirs`
  - Read `enable_grep` in `MdqService.__init__` and enforce it in `grep_docs` (raise `MdqAuthorizationError` or return early when `false`)
  - Conditionally exclude `grep_docs` from tool list exposed by `GET /v1/tools` when `enable_grep=false`
  - Verify no production path or limit value remains hardcoded (audit `service.py` defaults vs config)
  - Add/update unit tests for `enable_grep=false` behavior and `index_roots` semantics
- **Out-of-Scope**:
  - Implementing `index_roots` as a distinct authorization mechanism separate from `allowed_dirs` (treat as alias unless clarified — see UNK-01)
  - Any DB schema changes
  - Changes to `shared/config_loader.py` (already loads `mdq_mcp_server.toml`)
  - Embedding/hybrid search (`use_embedding`) — separate concern

## 3. Requirements
### Functional
- `enable_grep = false` blocks `grep_docs` tool invocation with an error and removes it from the tool schema returned by `GET /v1/tools`
- `index_roots` is an alias for `allowed_dirs`: both control which filesystem paths MDQ may index and read; if both are set, they are merged (union, deduplicated)
- Safe defaults in `service.py` remain as fallbacks when the TOML field is absent

### Non-functional
- Config is read at startup (`__init__`); no mid-operation restart required
- No agent-layer or shared-layer changes needed

## 4. Architecture
### Concurrency Model
- Config read at `MdqService.__init__()` once; no runtime config reload
- Dynamic tool list filtering in `list_tools()` requires config-aware filtering at request time

### Component Boundaries
```
config/mdq_mcp_server.toml (enable_grep, index_roots)
  └── MdqService.__init__() → reads config, merges index_roots into allowed_dirs
        ├── grep_docs → guard: if not self.enable_grep, raise MdqAuthorizationError
        ├── refresh_index → optional guard: if not self.enable_refresh, raise MdqAuthorizationError
        └── server.py::list_tools() → filter _MCP_TOOLS based on enable_grep config
```

## 5. Module Design
### Dependency Graph
```
scripts/mcp/mdq/server.py (MCP server)
  └── scripts/mcp/mdq/service.py (MdqService — config reading + enforcement)
        └── config/mdq_mcp_server.toml (enable_grep, index_roots)
```

No changes to dependency direction. `server.py` reads config in `list_tools()` to filter tool list; same pattern as `health()`.

## 6. Interface Design
### New/Modified Methods

```python
# service.py
class MdqService:
    def __init__(self, db_path: str = ..., allowed_dirs: list[str] | None = ...):
        # MODIFIED: read config from mdq_mcp_server.toml
        self.enable_grep: bool = cfg.get("enable_grep", True)  # default True
        self.index_roots: list[str] = cfg.get("index_roots", [])

        # Merge index_roots into allowed_dirs (union, deduplicated)
        if self.index_roots and not allowed_dirs:
            allowed_dirs = self.index_roots
        elif self.index_roots and allowed_dirs:
            allowed_dirs = list(dict.fromkeys(allowed_dirs + self.index_roots))  # dedup preserving order
        self._allowed_dirs: list[str] = allowed_dirs or []

    def grep_docs(self, pattern: str, path_prefix: str | None = None) -> list[dict]:
        # MODIFIED: add enforcement guard at top
        if not self.enable_grep:
            raise MdqAuthorizationError("grep_docs is disabled by configuration")
        # ... existing logic

# server.py
class MdqMCPServer(MCPHttpServer):
    def list_tools(self) -> list[dict]:
        # MODIFIED: filter _MCP_TOOLS based on enable_grep config
        tools = _MCP_TOOLS.copy()
        if hasattr(self, "service") and self.service and not self.service.enable_grep:
            tools = [t for t in tools if t["name"] != "grep_docs"]
        return tools
```

### TOML Config

```toml
# config/mdq_mcp_server.toml
enable_grep = true  # When false, grep_docs tool is disabled (blocked + excluded from tool list)
index_roots = []    # Alias for allowed_dirs; merged with allowed_dirs if both are set

[server]
host = "127.0.0.1"
port = 8013

[db]
path = "/opt/llm/db/mdq.sqlite"
```

## 7. Data Model & Serialization
No changes to data models. `enable_grep` is a runtime boolean flag; `index_roots` is a list of strings merged into `_allowed_dirs`.

## 8. Error Handling & Resource Lifecycle
### Failure Modes
- `index_roots` merge with `allowed_dirs` creates duplicate entries → **Mitigation**: Use `dict.fromkeys()` to deduplicate before storing as `_allowed_dirs`; add a test that verifies deduplication
- Filtering `_MCP_TOOLS` in `list_tools()` on every request adds latency due to config file I/O → **Mitigation**: Cache the config result at module level on first load (pattern already used in `MdqService.__init__`)
- Adding `enable_refresh` guard may break existing agents that rely on `refresh_index` being always available → **Mitigation**: Default `enable_refresh = true` in config and in code fallback; enforce guard only when explicitly `false`

### Resource Lifecycle
- Config read once at `MdqService.__init__()`; no runtime reload
- No connection pooling; each operation opens and closes its own connection (unchanged)

## 9. Configuration
- `config/mdq_mcp_server.toml`: add `enable_grep = true` and `index_roots = []` with comments
- Safe defaults in `service.py` remain as fallbacks when TOML fields are absent

## 10. Test Strategy
### Unit Tests
- `test_grep_docs_disabled_by_config`: patch `enable_grep=False`, assert `MdqAuthorizationError` raised
- `test_index_roots_merged_into_allowed_dirs`: set `index_roots=["/tmp/a"]`, verify `allowed_dirs` contains `/tmp/a`; test deduplication when both `allowed_dirs` and `index_roots` set
- `test_list_tools_excludes_grep_when_disabled`: TestClient GET /v1/tools with `enable_grep=False` config → `grep_docs` absent from response

### Integration Tests
- Full mdq regression: `uv run pytest tests/test_mdq_service.py tests/test_mdq_error_taxonomy.py tests/test_mdq_incremental_refresh.py -v`

## 11. Implementation Plan
### Phase 1: Config and Service
- Add `enable_grep = true` and `index_roots = []` fields to `config/mdq_mcp_server.toml` with comments
- In `MdqService.__init__`, read `enable_grep` (default `True`) and `index_roots` (default `[]`)
- Merge `index_roots` into `_allowed_dirs` (union, deduplicated) so both fields control the same allowlist
- Add enforcement guard at top of `grep_docs`: if `not self.enable_grep`, raise `MdqAuthorizationError("grep_docs is disabled by configuration")`
- (Optional but recommended) Add enforcement guard in `refresh_index`: if `not self.enable_refresh`, raise `MdqAuthorizationError("refresh_index is disabled by configuration")`

### Phase 2: Dynamic Tool List
- In `server.py::list_tools()`, filter out `grep_docs` from `_MCP_TOOLS` when `enable_grep=false`
- Load config inline in `list_tools()` (same pattern as `health()`) — or cache at module level using `functools.lru_cache` if startup cost matters

### Phase 3: Tests and Verification
- Add tests for `enable_grep=false`, `index_roots` merging, and tool list filtering
- Run lint/type check: `uv run ruff check scripts/mcp/mdq/ && uv run mypy scripts/mcp/mdq/`
- Run full mdq regression suite

## 12. Risks / Open Questions
- **UNK-01**: Relationship between `index_roots` and `allowed_dirs`: alias, superset, or separate semantics? → **Resolution**: Treat as alias (merge); document in TOML comment. No user clarification needed to proceed.
- **UNK-02**: `enable_refresh` enforcement: `service.py` stores the flag but `refresh_index()` does not check it before dispatching → **Resolution**: Add enforcement guard for `enable_refresh` alongside `enable_grep` as part of this task, or file separate issue.
- **UNK-03**: Dynamic tool list filtering: does `GET /v1/tools` need to reflect `enable_grep=false` at runtime? The tool list is built at import time from `_MCP_TOOLS` constant → **Resolution**: Add config-aware filtering in `list_tools()` endpoint; `_MCP_TOOLS` stays as source-of-truth but is filtered on response.
- **Risk**: `enable_grep=false` with `grep_docs` still in `_MCP_TOOLS` (if dynamic filtering is skipped) means the agent can still call the tool and receive an error, which is confusing → **Mitigation**: Implement dynamic `list_tools` filtering as part of Phase 2 to prevent the tool from being offered in the first place.
