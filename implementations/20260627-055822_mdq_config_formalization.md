## Goal

Formalize config/mdq_mcp_server.toml by defining and loading all production configuration fields for MDQ including db_path, allowed_dirs, include_globs, exclude_globs, limits, enable flags, and audit_log_path.

## Scope

**In-Scope**:
- Add all 12 required configuration fields to config/mdq_mcp_server.toml
- Fix ConfigLoader integration (mdq_mcp_server.toml not in _BASE_CONFIG_FILES)
- Load all config values in service.py
- Use config values instead of hardcoded defaults

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' configuration

## Assumptions

1. ConfigLoader needs mdq_mcp_server.toml added to _BASE_CONFIG_FILES for automatic loading
2. Safe defaults should be used when config values are missing
3. Empty allowlist denies indexing and file parsing (fail-closed)

## Implementation

### Target file: scripts/shared/config_loader.py

**Procedure**: Add mdq_mcp_server.toml to _BASE_CONFIG_FILES for automatic loading.

**Method**: Modify _BASE_CONFIG_FILES tuple in config_loader.py.

**Details**:
1. Add `"mdq_mcp_server.toml"` to _BASE_CONFIG_FILES tuple (after `mcp_servers.toml`)

### Target file: config/mdq_mcp_server.toml

**Procedure**: Update config file with all required fields and remove irrelevant timeout fields.

**Method**: Replace current config file content with clean configuration.

**Details**:
1. Remove all irrelevant timeout fields (file_search, file_grep, file_tree, etc.)
2. Add/update the following 12 required fields:
   - `status = "production"` — keep existing
   - `db_path = "/opt/llm/db/mdq.sqlite"` — keep existing
   - `allowed_dirs = []` — keep existing (fail-closed)
   - `include_globs = ["*.md"]` — new field
   - `exclude_globs = [".git/**", "__pycache__/**"]` — new field
   - `max_search_results = 100` — rename from max_search_results (keep existing)
   - `max_snippet_chars = 500` — keep existing
   - `max_chunk_chars = 10000` — keep existing
   - `max_file_chars = 100000` — keep existing
   - `search_timeout_sec = 30` — keep existing
   - `enable_refresh = true` — new field (controls whether refresh_index is enabled)
   - `audit_log_path = "/opt/llm/logs/mdq_audit.log"` — new field

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Load all config values from ConfigLoader, replace hardcoded defaults.

**Method**: Modify service.py __init__ and relevant methods to load config values.

**Details**:
1. In MdqService.__init__(), load config values from ConfigLoader:
   - `db_path = config.get("mdq_mcp_server.db_path", "/opt/llm/db/mdq.sqlite")`
   - `allowed_dirs = config.get("mdq_mcp_server.allowed_dirs", [])`
   - `include_globs = config.get("mdq_mcp_server.include_globs", ["*.md"])`
   - `exclude_globs = config.get("mdq_mcp_server.exclude_globs", [".git/**", "__pycache__/**"])`
   - `max_search_results = config.get("mdq_mcp_server.max_search_results", 100)`
   - `max_snippet_chars = config.get("mdq_mcp_server.max_snippet_chars", 500)`
   - `max_chunk_chars = config.get("mdq_mcp_server.max_chunk_chars", 10000)`
   - `max_file_chars = config.get("mdq_mcp_server.max_file_chars", 100000)`
   - `search_timeout_sec = config.get("mdq_mcp_server.search_timeout_sec", 30)`
   - `enable_refresh = config.get("mdq_mcp_server.enable_refresh", True)`
   - `audit_log_path = config.get("mdq_mcp_server.audit_log_path", "/opt/llm/logs/mdq_audit.log")`
2. Replace all hardcoded defaults with config values in relevant methods

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Add config validation on startup.

**Method**: Add validation method called during MdqService.__init__().

**Details**:
1. Validate required fields on startup:
   - db_path must be a valid path string
   - allowed_dirs must be a list (can be empty for fail-closed)
2. Log warning for missing optional fields with safe defaults

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| config_loader.py | Verify mdq_mcp_server.toml is loaded | Check _BASE_CONFIG_FILES tuple | mdq_mcp_server present |
| config file | Verify all 12 fields exist | Check TOML file | All required fields present |
| service.py | Verify all config values are loaded | Add debug logging, check startup | No hardcoded defaults used |

## Risks

- **Risk**: ConfigLoader change may affect other servers that depend on _BASE_CONFIG_FILES | **Likelihood**: Low | **Mitigation**: Test other MCP server configs after change | False
- **Risk**: Missing config values cause service startup failure | **Likelihood**: Medium | **Mitigation**: Use safe defaults for all optional fields | False
