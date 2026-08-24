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

Directory structure at deployment target:

``` text
/opt/llm/
├─ config/
│   ├─ workflows/                           # Workflow definition files
│   │   └─ default.json                     # Default workflow definition
│   ├─ agent.toml                           # Global agent settings (includes DB paths, embedding URLs, etc.)
│   ├─ crawler.toml                         # Crawler settings
│   ├─ chunk_splitter.toml                  # Chunk splitter settings
│   ├─ ingester.toml                        # Ingester settings
│   ├─ web_search_mcp_server.toml           # Web Search MCP server settings (:8004)
│   ├─ file_read_mcp_server.toml            # File Read MCP server settings (:8005, allowed directories)
│   ├─ github_mcp_server.toml               # GitHub MCP server settings (:8006)
│   ├─ file_write_mcp_server.toml           # File Write MCP server settings (:8007)
│   ├─ file_delete_mcp_server.toml          # File Delete MCP server settings (:8008)
│   ├─ shell_mcp_server.toml                # Shell MCP server settings (:8009, allowed commands)
│   ├─ rag_pipeline_mcp_server.toml         # RAG Pipeline MCP server settings (:8010)
│   ├─ cicd_mcp_server.toml                 # CI/CD MCP server settings (:8012)
│   ├─ mdq_mcp_server.toml                  # MDQ MCP server settings (:8013)
│   ├─ git_mcp_server.toml                  # Git MCP server settings (:8014)
│   └─ eventbus.toml                        # Event Bus server settings (:8015)
```

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
