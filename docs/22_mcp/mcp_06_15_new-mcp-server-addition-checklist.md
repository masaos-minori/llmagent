---
title: "New MCP Server Addition Checklist"
area: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# New MCP Server Addition Checklist

When adding a new server:

- [ ] Create `scripts/mcp_servers/<name>/<name>_server.py` (inherit from `MCPServer` and override `dispatch()`)
- [ ] Declare `own_config_file = "<key>_mcp_server.toml"` within the `MCPServer` subclass — `run_http()` will automatically call `ConfigLoader.restrict_to(own_config_file)`
- [ ] Create `config/<key>_mcp_server.toml` and include **all settings required by the server** (including DB paths, external URLs, etc.; do not refer to `agent.toml`)
- [ ] Add the tool definition to `[[tool_definitions]]` in `config/agent.toml`
- [ ] Register the tool in the frozenset of `shared/tool_constants.py` (automatic routing on startup); the `tool_names` in the config side is only used for arbitrary drift validation
- [ ] Add the new file to the copy list in `deploy/deploy.sh`
- [ ] Add startup procedures to `deploy/setup_services.sh`
- [ ] For every new tool, add an entry for `tool_safety_tiers` in `config/agent.toml`
- [ ] Update `routing.md` if new documentation is required

---

## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
