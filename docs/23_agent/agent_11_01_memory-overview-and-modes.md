---
title: "Memory Layer — Repository Context and Episodic Memory"
area: agent
tags:
  - agent
  - memory
  - overview
related:
  - agent_11_02_memory-gate-data-model-search.md
  - agent_11_03_memory-module-reference.md
  - agent_00_document-guide.md
  - agent_10_01_operations-and-observability-startup-and-health.md
  - agent_08_03_configuration-tools-memory.md
---
# Memory Layer — Repository Context and Episodic Memory

- Operations and Observability → [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration → [agent_08_03_configuration-tools-memory.md](agent_08_03_configuration-tools-memory.md)

## Purpose

To allow understanding of the responsibilities and public API scope of modules under `scripts/agent/memory/` without reading the source code.

## Design Intent

The Agent has two separate context mechanisms (ADR-008 Decision Detail #24). Repository Context is read-only context loaded from explicitly configured repository files. Episodic Memory is the Agent's only persistent long-term memory. They are separate because their sources, lifecycles, and recovery differ: Repository Context follows its source files, while Episodic Memory follows the Session DB.

The Episodic Memory layer is **optional**. Since RAG already provides search capabilities, it is limited to a complementary role. It falls back to FTS5 even if the embedding endpoint is unavailable, ensuring sessions are not interrupted.

### Independence from Conversation Sessions

Episodic Memory has a lifecycle independent from conversation sessions. Deleting, purging, loading, exporting, undoing, or compressing a session does not modify it, and no command gives users a way to delete it. Its retention and consistency are managed internally (retention is configurable per event type and state-aware, and age alone never authorizes deletion (ADR-008 Decision Details #23 and #24); the period values are undecided (SHARED-005)). The canonical statement of the session/memory boundary is in agent_04_01.

## Responsibility Boundary

- **Episodic Memory Layer owns:** Cross-session restoration of reusable work context.
- **Repository Context owns:** Read-only context taken from configured repository files for the active turn.
- **Neither owns:** RAG document search, LLM context generation, or tool execution.

## Repository Context

Repository Context is read-only context taken from explicitly configured repository files. The source files stay authoritative.

- It is not persisted: it is not stored in SQLite or JSONL, it is not part of the Session DB backup, and it has no persistent FTS or Vector index.
- It is loaded at startup and reloaded atomically through `/reload` (all sources load into a candidate snapshot; a validation failure rejects the complete reload and keeps the active snapshot; the new snapshot applies only to subsequent turns).
- Selected sections are injected only for the active turn.
- Authority values such as `canonical` and `observed`, the source list, and the configuration keys are undefined, and the loader is not implemented yet (SHARED-003).

## Episodic Memory

Episodic Memory is the Agent's only persistent long-term memory.

- It is generated internally from reusable work events, not from generic Q&A. Assistant-generated proposals are not persisted as durable rules.
- It is stored in `session.sqlite`: events and relations are authoritative, and the FTS and Vector indexes are derived (see agent_09_01).
- It has no user-facing add, list, search, pin, delete, prune, or rebuild operation.
- Internal retention, consistency, backup, and recovery manage it; it is recovered only from a verified SQLite backup.
- The initial event types are `failure`, `resolution`, `review_finding`, `investigation_result`, `work_result`, and `decision_history`; this document owns the taxonomy (ADR-008 Decision Detail #24). Retention is configurable per event type and state-aware; the period values are undecided (SHARED-005) and the retention itself is not implemented (SHARED-004). Episodic full-text search is required and Vector search is optional derived functionality.

## Context Budget

The final payload is budgeted across the system prompt, Repository Context, Episodic Memory, conversation history, tool schemas, the current input, and the response reserve. Reduction order: low-ranked Episodic Memory first, then low-ranked Repository Context sections, then older conversation history. Mandatory canonical Repository Context is never silently removed. The failure behavior when mandatory input alone exceeds the context limit is undefined (SHARED-007). `/context` reports the usage (see agent_07_08).

## Key Constraints

- If `memory_local_only = true` is set, it forces the embedding endpoint to be a loopback address. Startup fails if `embed_url` is not local.
- Injected memory snippets enter the system role as data, never as instructions: on both the session-start and per-turn paths they are neutralized to single-line text and presented under a fixed framing statement that marks them as recalled notes. The residual risk is stated in the trust-boundary document (security_01).

### Memory Modes

The Episodic Memory layer operates in four different retrieval modes. The diagnostics owner is `/stats` (not yet implemented, SHARED-003).

| Mode | Description | Retrieval Behavior |
|---|---|---|
| `Hybrid mode (semantic + FTS)` | Fully operational — Embedding endpoint is available and returning valid embeddings | Hybrid search using RRF merge of vector similarity and FTS results |
| `Memory enabled, embedding disabled (FTS-only)` | Embedding is disabled by configuration (`memory_embed_enabled = false`) | FTS-only search. No vector similarity component |
| `Degraded mode (circuit open, FTS fallback)` | Circuit breaker for embeddings has tripped due to repeated failures | FTS-only search. Same as above, but indicates ongoing issues with the embedding service |
| `Memory layer disabled` | The memory subsystem is completely disabled (`use_memory_layer = false`) | No memory search performed |

**Conditions for each mode:**

- **Hybrid mode**: Default when memory is enabled, the embedding endpoint is reachable, and returns valid embeddings.
- **FTS-only**: When `memory_embed_enabled = false` (or no embedding client exists), only FTS is used. This is a configuration state, not a reaction to a failed embedding health check: an unreachable embedding service at startup fails the readiness check (FATAL) instead of entering this mode. The mode table in `agent_08_03_configuration-tools-memory.md` is the canonical definition. Separately, an individual retrieval whose embedding call fails (network error, timeout, invalid response) falls back to FTS only for that retrieval; this happens automatically without manual intervention.
- **Degraded mode**: When the embedding circuit breaker trips due to continuous failures. The circuit breaker threshold can be configured in `embedding_client.py`. Degraded mode uses the same FTS fallback as above but indicates an ongoing issue with the embedding service.
- **Disabled**: When `use_memory_layer = false` is set in `config/agent.toml`. No memory search is performed regardless of embedding availability.

**Transitions between modes:**

- Hybrid → FTS-only: Requires configuration change (`memory_embed_enabled`). Individual retrievals fall back to FTS automatically on embedding failure.
- FTS-only → Hybrid: Requires configuration change (`memory_embed_enabled`).
- Degraded → Hybrid: Automatic transition when the circuit breaker closes after a recovery period.
- Any → Disabled: Requires configuration change and agent restart.

### Memory Injection Failure (Per-Turn Degraded State)

This degraded state is distinct from Degraded mode above: it reports a failed per-turn memory-injection call, whereas Degraded mode reports an embedding circuit-breaker trip during retrieval. It is not one of the four modes.

- **When it appears:** any user prompt whose memory-injection call raises (network error, timeout, or backend failure). The state is tracked per turn, not held for the whole session.
- **Automatic recovery:** memory context is retrieved and injected on every user prompt with no manual intervention; a successful attempt, including one that returns no snippets, clears the state on that same turn. The startup-time failure path is recovered the same way by the first successful per-turn injection.
- **User-visible signal:** one warning per degradation period — a single warning when the state is entered and one when it clears. Persistent failures stay quiet on the following turns rather than warning on every turn, so a long outage does not flood the log.

### Implementation Note: Persistence for `on_session_stop`

When persisting entries at session end, the entry is written to SQLite only; there is no JSONL write.

If embedding retrieval fails, processing continues and the entry is saved without embeddings (incrementing `stat_embed_skip` and logging `memory.embed_skip` at INFO level).

Only when embedding retrieval succeeds does the duplicate link discovery perform a KNN nearest neighbor search and record related links in the `memory_links` table for entries within a distance less than `DedupPolicy.threshold`. Insertion failures (`OperationalError` / `IntegrityError`) are ignored with only a warning log.

Automatic extraction (`on_session_stop`) applies deduplication via `DedupAction.SKIP_NEW`.

## Operational Notes

- Set `memory_local_only = true` if data must not leave the machine.
- The current retrieval mode (Hybrid / FTS-only / Degraded / Disabled) is reported by `/stats` once the diagnostics are implemented (SHARED-003).

## Known Limitations / Unresolved Issues

- Repository Context and its diagnostics are not implemented, and the code still implements the old memory model (SHARED-003).
- The retention period per Episodic event type is undecided (SHARED-005) and the context-overflow failure behavior is undefined (SHARED-007); the Session DB schema-mismatch handling is final (archive and recreate, Episodic Memory not carried over; ADR-008 Decision Detail #22).


## Keywords

- repository context
- episodic memory
- memory layer
- memory modes
- optional memory layer
- FTS5 fallback
- embedding endpoint
- deduplication
- on_session_stop
- ctx.services.memory
