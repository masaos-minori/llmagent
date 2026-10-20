---
title: Replay Endpoint
tags: [api-reference, replay, sse]
area: eventbus
related:
  - eventbus_02_api-reference-index.md
  - eventbus_06_persistence_schema_and_replay.md
---

# Replay Endpoint

## Overview

The `/replay` endpoint replays events from a given sequence number. Supports both Server-Sent Events (SSE) streaming and JSON response formats.

## Endpoint

```
GET /replay
```

## Authentication

**Operator role required.**

Requires `Bearer ${OPERATOR_TOKEN}` in the Authorization header.

## Parameters

| Parameter | Required | Default | Constraints | Description |
|-----------|----------|---------|-------------|-------------|
| `since_seq` | No | `0` | `>= 0` | Replay events with `seq` greater than this value (exclusive); `0` replays all events |
| `format` | No | `sse` | `sse`, `json` | Response format: SSE stream or JSON |
| `limit` | No | route default | bounded (see route definition) | Maximum number of events to return |
| `offset` | No | `0` | `>= 0` | Offset into the event set for pagination |

## Success Response

### SSE Format (default)

**HTTP 200 OK** with `Content-Type: text/event-stream`

Each event is emitted as an SSE message:

```
id:{seq}
data:{json_event}

```

The SSE stream covers only the requested page (`limit`/`offset`); it closes after the page is streamed and does not wait for new events. When no events exist after `since_seq`, the connection closes without sending any event.

### JSON Format

**HTTP 200 OK** with `Content-Type: application/json`

A pagination envelope (`total`, `limit`, `offset`) plus an `items` array of event objects. `total` counts all events after `since_seq`, and is available only in this format.

When no events exist after `since_seq`, the JSON response has `total: 0` and an empty `items` array.

## Invalid Parameters

- Missing parameters use the defaults in the Parameters table.
- `since_seq` below 0, `limit` below 1 or above the maximum bound, `offset` below 0, or an unknown `format` value: HTTP 422 (FastAPI validation).

## Ordering and Consistency

Events are ordered by `seq` ascending (insertion order). The page and the total count are fetched under the global DB lock in a single acquisition, so the returned events and `total` form a consistent snapshot; concurrent writes do not affect the result set.

## Keywords

- replay endpoint
- since_seq
- SSE replay
- JSON pagination
