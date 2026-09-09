---
title: "Shared Infrastructure File Structure: venv/db/ + scripts/db/ (Part 1/2)"
area: overview
tags:
  - shared
  - db
  - sqlite
  - file-structure
related:
  - 01_overview-files-04-shared.md
---

# File Structure

Architecture Overview → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. File Structure

See `venv/` for the virtual environment contents. See `db/` for the DB layer package. See `shared/` for the current file layout.

### Virtual Environment (venv/)

Python virtual environment managed by uv; `uv.lock` tracks the dependency list. Owned by the build/deployment process; consumed by all Python processes.

### Database Domains (db/)

Four isolated SQLite databases: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`. Each operates in WAL mode; persistence separated into four domains to isolate different write patterns, limit failure impact, and clarify ownership. See ADR-008 for the rationale behind four-domain separation. Shared DB path builder via `DbConfig` dataclass in `config.py`.

### DB Layer Package (scripts/db/)

Schema initialization, connection management (WAL mode, busy_timeout), and maintenance operations. Protocol abstraction layer defining VectorStore, DocumentStore, and SessionStore interfaces with SQLite implementations. Data models for checkpoint counts, purge counts, health metrics, document rows, session rows, and message rows. Consistency checking, rotation, and recovery utilities.

### Shared Infrastructure Components (scripts/shared/)

**LLM Client/Transport** — SSE streaming, exponential backoff retry, transport error handling, payload handling.

**Tool Routing/Execution** — MCP server routing, tool registry, runtime tool metadata, route resolution.

**Configuration** — TOML/JSON loader, typed value accessors, validators, MCP server configuration dataclasses, health tracking.

**Other Utilities** — Type definitions, action results, events, formatters, git helper, HTTP transport, JSON utilities, logging, OpenTelemetry, token counting.

**protocols/** — ShellPolicy protocol definition.

### Design Intent and Operational Specifications

#### Caching Strategy

`ToolResultCache` is a standalone LRU+TTL cache utility, currently unused in the codebase.

#### Health Check-Based Dispatch Control

Health checks using `mcp_health.py` enable dispatch control based on server status (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN).

#### Drift Validation Behavior

Config Drift defaults to warnings, raises RuntimeError if `routing_drift_strict` enabled. Live Drift defaults to warnings, becomes FATAL if `tool_definitions_strict` enabled or `security_profile == PRODUCTION`. Ownership Duplication always results in FATAL regardless of mode.

## Related Documents

- `01_overview-files-04-shared.md`
- [01_overview.md](01_overview.md)

## Keywords

shared
db
sqlite
file-structure
