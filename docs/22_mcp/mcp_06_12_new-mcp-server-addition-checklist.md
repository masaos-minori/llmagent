---
title: "New MCP Server Addition Checklist"
area: mcp
tags:
  - mcp
  - configuration
related:
  - mcp_00_document-guide.md
  - mcp_06_01_configuration-file-inventory.md
source:
  - mcp_06_01_configuration-file-inventory.md
---

# New MCP Server Addition Checklist

When adding a new server:

- [ ] Create `scripts/mcp_servers/<name>/<name>_server.py` (inherit from `MCPServer` and override `dispatch()`)
- [ ] Declare `own_config_file = "<key>_mcp_server.toml"` within the `MCPServer` subclass — `run_http()` will automatically call `ConfigLoader.restrict_to(own_config_file)`
- [ ] Create `config/<key>_mcp_server.toml` and include **all settings required by the server** (including DB paths, external URLs, etc.; do not refer to `agent.toml`)
- [ ] Add the tool definition to `[[tool_definitions]]` in `config/agent.toml`
- [ ] Declare the tool in the server's `/v1/tools` response with the schema-2.0 fields (this is what makes it routable)
- [ ] Register the tool in the frozenset of `shared/tool_constants.py` (static seed for drift detection, not a routing input); the `tool_names` in the config side is only used for optional drift validation
- [ ] Add the new file to the copy list in `deploy/deploy.sh`
- [ ] Define `[mcp_servers.<key>]` with `startup_mode = "subprocess"` in `config/agent.toml` — the agent starts the server; `deploy/setup_services.sh` has no per-server step
- [ ] For every new tool, add an entry for `tool_safety_tiers` in `config/agent.toml`
- [ ] Update `routing.md` (repository root) if new documentation is required

---

## Keywords

configuration
