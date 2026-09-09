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
  - 01_overview-files-01-build.md
  - 01_overview-files-02-rag.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-04-shared.md
  - 01_overview-files-06-misc.md
---

# File Structure

Architecture Overview → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. File Structure

See `config/` for the current file layout.

### Configuration Directory Structure

**`config/workflows/default.json`** — Default workflow definition file; required by deploy.sh and setup_services.sh for startup validation. Owned by the deployment process; consumed by all services requiring workflow definitions.

**`config/agent.toml`** — Global agent settings including DB paths, embedding URLs, and MCP server configurations. Owned by the agent process; provides shared configuration for the AgentREPL runtime.

**`config/mcp_<name>.toml`** — Per-MCP-server configuration files (one per server); each contains the server's transport URL, timeout, and retry settings. These port numbers are illustrative examples of the current deployment configuration, not claims about deployed configuration.

**`config/embedding.toml`** — Embedding service configuration including model path and endpoint URLs. Owned by the embedding service; consumed by the embed-LLM process.

**`config/tool_registry.json`** — Tool registry mapping tool names to their implementations. Owned by the tool routing layer; consumed by all MCP servers requiring tool discovery.

### Per-Process Config Isolation Policy

Each process reads only its own config file — no cross-process config sharing. This prevents configuration drift between processes and ensures that changes to one process's config do not affect others. The MCP servers read their respective `mcp_<name>.toml` files; the agent reads `agent.toml`; the embedding service reads `embedding.toml`.

### MCP Server Configuration Responsibilities

MCP server configs define: transport type (SSE/HTTP), target URL, timeout duration, retry count, and health-check interval. Each MCP server has its own config file because each server operates independently and may have different requirements.

## Related Documents

- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-06-misc.md`
- [01_overview.md](01_overview.md)

## Keywords

configuration
toml
agent-toml
mcp-server-config
rag-config
file-structure
