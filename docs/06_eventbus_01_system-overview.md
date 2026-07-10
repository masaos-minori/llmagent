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

The Event Bus provides an internal publish/subscribe backbone for the LLM agent system. Producers publish JSON events; consumers subscribe to topics via SSE and replay past events.

> **Note:** The Event Bus HTTP API is fully implemented and operational as a standalone service.
> Agent runtime integration (publishing events from the Agent, subscribing to Agent topics via SSE)
> is intentionally deferred and not yet implemented. This document describes the Event Bus as an
> independent component; Agent-side event production/consumption will be documented in a future
> release.

## Architecture

The Event Bus uses an in-memory pub/sub broker (`EventBroker`) for live event delivery. Each subscriber gets a dedicated `asyncio.Queue`; the broker fans out events to matching subscribers based on topic filters.

- **Live delivery**: `EventBroker` provides topic-aware fan-out via asyncio Queues
- **Replay**: past events are replayed from SQLite via `/replay` and `/subscribe` endpoints
- **Persistence**: all events are stored in SQLite; DLQ events are written as JSONL files
- **Offset management**: file-based offset persistence for consumer recovery

### EventBroker

`EventBroker` maintains a list of `_Subscriber` dataclasses, each with an asyncio Queue and optional topic filter. `publish()` fans out events to matching subscribers, dropping on queue full (with WARNING log). `shutdown()` sends None sentinels to unblock all subscriber queues.

Queue maxsize=1000; slow consumer threshold=100 items.

## Security model

The Event Bus API has **no authentication or ACL**.

- **Design assumption**: single-node deployment on an internal network / trusted hosts
- **Access control**: enforced at the network boundary (firewall, Docker network)
- **Do not expose publicly**: the Event Bus must not be directly reachable from the internet
- **Startup guard**: config validation rejects binding to public/wildcard addresses (0.0.0.0, ::) unless `allow_public_bind=true` is set in TOML config. A WARNING log message is emitted when a public address is bound without authentication.

### Future authentication options

If requirements arise:
- API-key authentication via FastAPI `Depends`
- mTLS for service-to-service authentication

Not implemented at this time. Evaluate based on the actual threat model before adding.

## Future Integration

The following Agent-side integrations are intentionally not implemented at this time:

- **Agent event publishing**: No Agent-side event producer is implemented. The Event Bus HTTP API supports publishing from any HTTP client; Agent-specific producers will be added in a future release.
- **Agent SSE subscription**: No Agent-side subscriber for consuming events via `/subscribe` SSE. Agent-side consumers will be added in a future release.
- **Agent event topics**: No Agent-defined topics exist today. Topic conventions for Agent lifecycle events will be defined when Agent integration is implemented.

These items are also documented as Deferred Items in `docs/06_eventbus_90_inconsistencies_and_known_issues.md`.

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_05_02_bind-address-and-start.md`

## Keywords

event-bus
system-overview
architecture
pub-sub
sse
security-model
authentication
