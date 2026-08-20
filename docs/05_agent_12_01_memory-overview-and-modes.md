# Memory Layer — Overview and Modes (Part 1)

- Operations and Observability $\rightarrow$ [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration $\rightarrow$ [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Purpose

To allow understanding of the responsibilities and public API scope of modules under `scripts/agent/memory/` without reading the source code.

## Design Intent

The memory layer is **optional**. Since RAG already provides search capabilities, the memory layer is limited to a complementary role. It falls back to FTS5 even if the embedding endpoint is unavailable, ensuring sessions are not interrupted.

It separates semantic memory (long-term rules/decisions) from episodic memory (session-specific failures/Q&A). This is due to differences in injection timing and search strategies. Semantic memory is filtered by an importance threshold and injected at session start; episodic memory is retrieved via hybrid search upon the first user prompt.

## Responsibility Boundary

- **Memory Layer owns:** Cross-session context restoration (rules, decisions, failure patterns, conversation Q&A).
- **Memory Layer does NOT own:** RAG document search, LLM context generation, or tool execution.

## Key Constraints

- If `memory_local_only = true` is set, it forces the embedding endpoint to be a loopback address. Startup fails if `embed_url` is not local.
- Semantic memory injection at session start requires `importance >= 0.5`. Low-importance entries are not automatically injected.
- Pinned entries are always injected at every session start (regardless of the importance threshold).

## Operational Notes

- Set `memory_local_only = true` if data must not leave the machine.
- Current mode can be checked with `/memory status` (Hybrid / FTS-only / Degraded / Disabled).
- Ensure you have tested `/memory rebuild` after restoring a JSONL backup.

## Known Limitations / Unresolved Issues

None

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_01_memory-overview-and-modes.md`


# Memory Layer — Overview and Modes (Part 2)

- Operations and Observability $\rightarrow$ [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration $\rightarrow$ [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Memory Modes

The memory layer operates in four different modes, which can be checked via `/memory status`.

| Mode | Description | Retrieval Behavior |
|---|---|---|
| `Hybrid mode (semantic + FTS)` | Fully operational — Embedding endpoint is available and returning valid embeddings | Hybrid search using RRF merge of vector similarity and FTS results |
| `Memory enabled, embedding disabled (FTS-only)` | Embedding endpoint is unavailable but the circuit is closed | FTS-only search. No vector similarity component |
| `Degraded mode (circuit open, FTS fallback)` | Circuit breaker for embeddings has tripped due to repeated failures | FTS-only search. Same as above, but indicates ongoing issues with the embedding service |
| `Memory layer disabled` | The memory subsystem is completely disabled (`use_memory_layer = false`) | No memory search performed |

**Conditions for each mode:**

- **Hybrid mode**: Default when memory is enabled, the embedding endpoint is reachable, and returns valid embeddings.
- **FTS-only**: When the embedding endpoint fails (network error, timeout, invalid response), the system falls back to FTS only. This happens automatically without manual intervention.
- **Degraded mode**: When the embedding circuit breaker trips due to continuous failures. The circuit breaker threshold can be configured in `embedding_client.py`. Degraded mode uses the same FTS fallback as above but indicates an ongoing issue with the embedding service.
- **Disabled**: When `use_memory_layer = false` is set in `config/agent.toml`. No memory search is performed regardless of embedding availability.

**Transitions between modes:**

- Hybrid $\rightarrow$ FTS-only: Automatic transition on embedding failure.
- FTS-only $\rightarrow$ Hybrid: Automatic transition when embeddings recover.
- Degraded $\rightarrow$ Hybrid: Automatic transition when the circuit breaker closes after a recovery period.
- Any $\rightarrow$ Disabled: Requires configuration change and agent restart.

### Implementation Note: Persistence Order and Failure Handling for `on_session_stop`

When persisting embedded entries at session end, an `upsert` to SQLite is performed first, followed by writing to JSONL. Even if writing to JSONL fails with an `OSError`, no exception is re-raised; a warning is logged and processing continues (the entry remains saved only in SQLite).

If embedding retrieval fails, processing continues and the entry is saved without embeddings (incrementing `stat_embed_skip` and logging `memory.embed_skip` at INFO level).

Only when embedding retrieval succeeds does the duplicate link discovery perform a KNN nearest neighbor search and record related links in the `memory_links` table for entries within a distance less than `DedupPolicy.threshold` (default 0.3). Insertion failures (`OperationalError` / `IntegrityError`) are ignored with only a warning log.

Automatic extraction (`on_session_stop`) applies deduplication via `DedupAction.SKIP_NEW`, but semantic writes / episodic writes (manual writes) intentionally bypass this deduplication.

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_01_memory-overview-and-modes.md`
