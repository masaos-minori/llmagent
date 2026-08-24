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

Directory structure at deployment target:

``` text
/opt/llm/
├─ scripts/
│   └─ eventbus/                        # Event Bus package
│       ├─ app.py                       # FastAPI application
│       ├─ broker.py                    # Message broker
│       ├─ config.py                    # Event Bus configuration
│       ├─ db.py                        # Database access layer
│       ├─ offsets.py                   # Offset management
│       ├─ dlq.py                       # DLQ (Dead Letter Queue)
│       ├─ publish_route.py             # publish endpoint
│       ├─ subscribe_route.py           # subscribe endpoint
│       ├─ ack_route.py                 # ack endpoint
│       ├─ dlq_route.py                 # DLQ endpoint
│       ├─ replay_route.py              # Replay endpoint
│       ├─ health_route.py              # Health check endpoint
│       ├─ route_helpers.py             # Common route handlers
│       ├─ schema.sql                   # Event Bus DB schema
│       └─ __init__.py                  # Event Bus package initialization
```

Event delivery failure and recovery flow:
When a message rejection (nack) occurs, the `delivery_failure_count` in `db.py` is incremented via `ack_route.py`. Once this count reaches `max_retry`, the event is promoted to the DLQ (Dead Letter Queue) by `dlq.py`, which adds a `dlq_at` timestamp. DLQ inspection and recovery are performed through `dlq_route.py`; you can list them using `dlq_list` or requeue them back into the active queue using `dlq_requeue`. Note that the replay functionality provided by `offsets.py` and `replay_route.py` is an independent mechanism for consumer catch-up (reloading from past offsets) and is separate from recovery from the DLQ.


Repository Root:
``` text
conf.d/
├─ cicd-mcp                             # GITHUB_TOKEN (Personal Access Token) settings
├─ git-mcp                              # allowed_repo_paths (fail-closed) / read_only settings
├─ github-mcp                           # GITHUB_TOKEN (Personal Access Token) settings
└─ web-search-mcp                       # API key settings for each search provider (priority specified in web_search_mcp_server.json)
```

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
