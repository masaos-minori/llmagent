---
title: "New MCP Server Addition Checklist"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration_and_operations.md
source:
  - 04_mcp_06_configuration_and_operations.md
---

# New MCP Server Addition Checklist

## New MCP Server Addition Checklist

When adding a server:

- [ ] Create `scripts/mcp/<name>/server.py` (inherit `MCPServer`, override `dispatch()`)
- [ ] Declare `own_config_file = "<key>_mcp_server.toml"` in the `MCPServer` subclass — `run_http()` calls `ConfigLoader.restrict_to(own_config_file)` automatically
- [ ] Create `config/<key>_mcp_server.toml` with **all settings the server needs** (DB パス・外部 URL 等を含む; `agent.toml` は参照しない)
- [ ] Add tool definitions to `config/tools_definitions.toml`
- [ ] Tools are registered in `shared/tool_constants.py` frozensets (auto-routed at startup); config `tool_names` is optional drift validation only
- [ ] Add new files to `deploy/deploy.sh` copy list
- [ ] Add startup step to `deploy/setup_services.sh`
- [ ] Add `tool_safety_tiers` entries to `config/agent.toml` for all new tools
- [ ] Update `routing.md` if new documentation is needed

---


## Related Documents

- [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
