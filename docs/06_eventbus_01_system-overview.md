---
title: "Event Bus: System Overview"
category: eventbus
tags:
  - event-bus
  - system-overview
  - architecture
  - pub-sub
  - sse
  - security-model
  - authentication
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_05_02_bind-address-and-start.md
source:
  - index.md
---

# Event Bus: System Overview

## Purpose

The Event Bus provides an internal publish/subscribe infrastructure for LLM agent systems. Producers publish JSON events, and consumers subscribe to topics via SSE and can replay past events.

> **Note:** The Event Bus HTTP API is fully implemented as a standalone service and is operational.
> Integration with the Agent runtime (publishing events from Agents, subscribing to Agent topics via SSE) has been intentionally deferred and is not yet implemented. This documentation describes the Event Bus as an independent component; event generation/consumption on the Agent side will be documented in future releases.

## Architecture

The Event Bus uses an in-memory pub/sub broker (`EventBroker`) for live event delivery. Each subscriber has its own dedicated `asyncio.Queue`, and the broker fans out events to relevant subscribers based on topic filters.

- **Live Delivery**: `EventBroker` provides topic-based fan-out via `asyncio.Queue`.
- **Replay**: Past events are replayed from SQLite through the `/replay` and `/subscribe` endpoints.
- **Persistence**: All events are stored in SQLite, and DLQ events are written as JSONL files.
- **Offset Management**: Offsets are persisted using files to facilitate consumer recovery.

## Security Model

There is **no authentication or ACL** for the Event Bus API.

- **Design Assumption**: Intended for single-node operation on internal networks/trusted hosts.
- **Access Control**: Should be enforced at the network boundary (firewall, Docker network).
- **Exposure Warning**: The Event Bus must NOT be directly accessible from the internet.
- **Startup Guard**: Binding to public/wildcard addresses (0.0.0.0, ::) is rejected by configuration validation unless `allow_public_bind=true` is set in the TOML config. If bound to a public address without authentication, a WARNING is logged.

## Future Integration

The following Agent-side integrations are intentionally unimplemented at this time:

- **Event publishing by Agents**: No event producer exists on the Agent side. While the Event Bus HTTP API supports publishing from any HTTP client, an Agent-specific producer is planned for a future release.
- **SSE subscription by Agents**: There is no Agent-side subscriber consuming events via `/subscribe` SSE. Agent-side consumers are planned for a future release.
- **Agent event topics**: No topics defined by the Agent exist at this time. Topic naming conventions for Agent lifecycle events will be defined when Agent integration is implemented.

These items are also documented as Deferred Items in `docs/06_eventbus_90_inconsistencies_and_known_issues.md`.

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_05_02_bind-address-and-start.md`
