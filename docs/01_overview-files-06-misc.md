---
title: "Miscellaneous File Structure"
area: overview
tags:
  - eventbus
  - logs
  - deployment
  - file-structure
  - system-configuration
related:
  - 01_overview-files-01-build.md
  - 01_overview-files-02-rag.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-04-shared.md
  - 01_overview-files-05-config.md
---

# File Structure

Architecture Overview → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. File Structure

See `eventbus/` for the current file layout. See `conf.d/` for MCP server configuration files.

### Event Bus Architecture

The event bus provides event-driven communication between system components. It uses SQLite-backed persistence for durability and implements publish-subscribe semantics for decoupled messaging. The event bus enables loose coupling between producers and consumers while maintaining delivery guarantees.

### Message Types

**Workflow events** — Lifecycle events for workflow execution (start, complete, fail). Owned by the workflow engine; consumed by monitoring and notification systems.

**Session events** — User interaction events (message received, response sent). Owned by the AgentREPL runtime; consumed by analytics and audit logging.

**Tool execution events** — Tool invocation events (tool called, result returned). Owned by the tool routing layer; consumed by observability dashboards.

### Delivery Mechanisms

At-least-once delivery via SQLite transactional writes ensures no event loss during normal operation. A retry mechanism handles transient failures, with a dead letter queue (DLQ) capturing messages that exceed the maximum retry threshold. DLQ inspection and recovery are performed through dedicated endpoints; requeuing restores events to the active queue. Replay functionality (independent of DLQ recovery) allows consumers to reload from past offsets.

### Event Handlers

**Workflow handler** — Processes workflow lifecycle events. **Session handler** — Processes session-related events. **Tool handler** — Processes tool execution events. **Notification handler** — Sends notifications on significant events.

### Persistence Layer

SQLite-based event store with WAL mode for concurrent access. Event schema includes version tracking for migration compatibility. Index optimization targets query performance for time-range and event-type lookups.

### Configuration Files (conf.d/)

Per-MCP-server configuration files under `conf.d/`: `cicd-mcp` (GITHUB_TOKEN settings), `git-mcp` (allowed_repo_paths / read_only settings), `github-mcp` (GITHUB_TOKEN settings), `web-search-mcp` (API key settings for each search provider). These files contain operational credentials and are managed separately from code.

## Related Documents

- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- [01_overview.md](01_overview.md)

## Keywords

eventbus
logs
deployment
file-structure
system-configuration
