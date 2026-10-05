---
title: "Configuration File Structure"
area: overview
tags:
  - configuration
  - toml
  - agent-toml
  - mcp-server-config
  - rag-config
  - file-structure
related:
  - overview-files-01-build.md
  - overview-files-02-rag.md
  - overview-files-03-scripts.md
  - overview-files-04-shared.md
  - overview-files-06-misc.md
---

# File Structure

Architecture Overview → [`overview-arch-01-process.md`](overview-arch-01-process.md), [`overview-arch-02-pipelines.md`](overview-arch-02-pipelines.md), [`overview-arch-03-features.md`](overview-arch-03-features.md)

## 3. File Structure

See `config/` for the current file layout.

### Configuration Directory Structure

**`config/workflows/default.json`** — Default workflow definition file; required by deploy.sh and setup_services.sh for startup validation. Owned by the deployment process; consumed by all services requiring workflow definitions.

**`config/agent.toml`** — Global agent settings including DB paths, embedding URLs, and MCP server configurations. Owned by the agent process; provides shared configuration for the AgentREPL runtime.

**`config/<key>_mcp_server.toml`** — Per-MCP-server configuration files (one per server, for example `shell_mcp_server.toml`); each contains the server's service-specific settings such as allowlists and the auth token reference.

### Per-Process Config Isolation Policy

Each process reads only its own config file — no cross-process config sharing. This prevents configuration drift between processes and ensures that changes to one process's config do not affect others. The MCP servers read their respective `<key>_mcp_server.toml` files; the agent reads `agent.toml`.

### MCP Server Configuration Responsibilities

MCP server configs define service-specific settings (allowlists, limits, auth token reference). Transport, URL, and startup settings for each server are defined in `config/agent.toml` (`McpServerConfig`). Each MCP server has its own config file because each server operates independently and may have different requirements.

## Keywords

configuration
toml
agent-toml
mcp-server-config
rag-config
file-structure
