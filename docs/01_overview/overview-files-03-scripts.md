---
title: "Scripts File Structure: Agent Core & Memory"
area: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
---

# File Structure

Architecture Overview → [`overview-arch-01-process.md`](overview-arch-01-process.md), [`overview-arch-02-pipelines.md`](overview-arch-02-pipelines.md), [`overview-arch-03-features.md`](overview-arch-03-features.md)

## 3. File Structure

### Key Directories and Responsibilities

- `scripts/agent/` — Agent REPL package: entry point, startup sequence, turn control, tool execution and policy, session management, lifecycle of MCP server processes, and diagnostics.
- `scripts/agent/memory/` — Memory subpackage: data model, storage, search, ingestion, injection, and scoring.

For the per-file layout, refer to the repository tree under these directories.

### Notes on Changes

- When changing tool approval flow, check both `tool_approval.py` and `repository_gateway.py` together.
- When changing memory search algorithms, check both `retriever.py` and `scoring.py` together.

## Keywords

scripts
agent
mcp-server
file-structure
