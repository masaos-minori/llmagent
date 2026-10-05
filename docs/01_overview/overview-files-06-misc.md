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
  - overview-files-01-build.md
  - overview-files-02-rag.md
  - overview-files-03-scripts.md
  - overview-files-04-shared.md
  - overview-files-05-config.md
---

# File Structure

Architecture Overview → [`overview-arch-01-process.md`](overview-arch-01-process.md), [`overview-arch-02-pipelines.md`](overview-arch-02-pipelines.md), [`overview-arch-03-features.md`](overview-arch-03-features.md)

## 3. File Structure

See `scripts/eventbus/` for the current file layout. See `conf.d/` for MCP server configuration files.

### Event Bus Architecture

The event bus provides event-driven communication between system components. It uses SQLite-backed persistence for durability and implements publish-subscribe semantics for decoupled messaging. The event bus enables loose coupling between producers and consumers while maintaining delivery guarantees.

### Delivery Mechanisms

At-least-once delivery via SQLite transactional writes ensures no event loss during normal operation. A retry mechanism handles transient failures, with a dead letter queue (DLQ) capturing messages that exceed the maximum retry threshold. DLQ inspection and recovery are performed through dedicated endpoints; requeuing restores events to the active queue. Replay functionality (independent of DLQ recovery) allows consumers to reload from past offsets.

### Persistence Layer

SQLite-based event store with WAL mode for concurrent access. Events are indexed by topic and sequence number.

### Configuration Files (conf.d/)

Per-MCP-server configuration files under `conf.d/`: operational credentials for CI/CD, git, GitHub, and web search providers. These files contain sensitive settings and are managed separately from code.

## Keywords

eventbus
logs
deployment
file-structure
system-configuration
