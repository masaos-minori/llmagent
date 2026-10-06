# Fix embed-llm unreachable connection

## Summary

The RAG embedding endpoint (`embed_url`) is unreachable, causing a non-fatal warning during startup. This disables RAG embedding functionality. The configured URL points to `http://192.168.11.238:8081` which is not reachable.

## Background

The agent connects to an external embedding service at the URL configured in `agent.toml`. The current URL is `http://192.168.11.238:8081` (no path component). The health check derives the probe URL by stripping the path from `embed_url` and appending `/health`, resulting in `http://192.168.11.238:8081/health`. The actual embedding endpoint path is `/embedding` (per `shared/llm_client.py:EMBEDDING_PATH`).

## Problem

Startup output includes:
```
[non-fatal] embed-llm unreachable at http://192.168.11.238:8081/health: All connection attempts failed
```

Note: The health check probes `http://192.168.11.238:8081/health` (derived by stripping the path from `embed_url` and appending `/health`). The actual embedding endpoint path is `/embedding` (per `shared/llm_client.py:EMBEDDING_PATH`). Whether the service has a `/health` endpoint is unknown.

## Reason for Change

Without a reachable embedding endpoint, RAG features (semantic search, memory retrieval) are disabled. This affects the agent's ability to use context from previous sessions. Two approaches are possible:
1. Update `embed_url` to point to a reachable external embedding service
2. Enable local embedding (if available) — see `scripts/agent/memory/embedding_client.py:116-120` for `local_only` logic

## Implementation Intent

Two options:

### Option A: Update embed_url to a reachable external service

Update the `embed_url` configuration to point to a reachable embedding service:

```toml
embed_url = "http://<reachable-host>:<port>"
```

The health check probes `{host}:{port}/health` (derived by stripping the path from `embed_url` and appending `/health`). The actual embedding endpoint path is `/embedding` (per `shared/llm_client.py:EMBEDDING_PATH`).

### Option B: Enable local embedding

If a local embedding service is available, enable it via the `local_only` flag. See `scripts/agent/memory/embedding_client.py:116-120` for the `local_only` logic that rejects non-local embed URLs.

## Target Files or Areas

- `/opt/llm/config/agent.toml` — embed_url setting

## Required Changes

Update the embedding URL to a reachable endpoint:
```toml
embed_url = "http://<reachable-host>:<port>"
```

Or enable local embedding if available.

## Constraints

- The embedding service must support the expected health check endpoint (`/health`)
- Do not change other RAG configuration settings

## Out of Scope

- Adding new embedding services
- Modifying the embedding client implementation
- Changing the RAG pipeline architecture

## Dependencies

- A reachable embedding service must be available

## Acceptance Criteria

- [ ] No "embed-llm unreachable" warning during startup
- [ ] RAG embedding functionality works
- [ ] Semantic search and memory retrieval operate correctly

## Testing Expectations

- Run `bash /opt/llm/start_agent.sh` and verify no embed-llm warnings
- Test semantic search and memory retrieval operations

## Documentation Impact

Update deployment documentation to document the embedding service requirement.

## Unresolved Questions

- What is the correct `embed_url` for the local embedding service?

## Evidence

- Startup output: `[non-fatal] embed-llm unreachable at http://192.168.11.238:8081/health: All connection attempts failed`
- Source: `/opt/llm/config/agent.toml` (`embed_url = "http://192.168.11.238:8081"` at line 10)
- Source: `scripts/agent/services/mcp_health.py:75` (embed-llm health check — probes `{host}:{port}/health`)
- Source: `scripts/shared/llm_client.py:28` (`EMBEDDING_PATH = "/embedding"` — actual embedding endpoint)
- Source: `scripts/agent/memory/embedding_client.py:116-120` (`local_only` logic for rejecting non-local embed URLs)

## Priority

Low
