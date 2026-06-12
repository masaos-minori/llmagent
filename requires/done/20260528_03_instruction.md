# Persistent Semantic Memory Implementation Plan

Source file: `persistent_semantic_memory_implementation_plan_20260528_ja.md`
Date: 2026-05-28

## Goal

- Add a persistent memory layer that can be reused across sessions.
- Implement two memory layers: semantic memory and episodic memory.
- Save memory when a conversation ends, and retrieve relevant memory at SessionStart and UserPromptSubmit.
- Keep all data local. Use JSONL as the source of truth and SQLite as the index.
- Integrate naturally with the existing REPL and RAG design, while keeping future vector search support possible.

## Scope

### In scope

- Define the persistent memory model.
- Implement semantic memory and episodic memory.
- Add append-only JSONL storage.
- Build a SQLite index.
- Add memory hooks for SessionStart, UserPromptSubmit, and Stop.
- Add memory search APIs.
- Inject MemoryLayer into AgentContext and ServiceContainer.
- Control enablement, thresholds, and retention through `config/agent.json`.
- Add visibility through `/context` and related surfaces.

### Out of scope

- External cloud databases.
- Distributed memory synchronization.
- Full knowledge graph integration such as Neo4j.
- Autonomous rule updating itself.
- Replacing the full existing RAG pipeline.

## Assumptions

- The current REPL injects components into AgentContext through AgentREPL, and delegates turn handling to Orchestrator. citeturn44search3turn44search13
- AgentContext and ServiceContainer already have a `memory` slot, and `use_memory_layer` is already defined. citeturn44search5turn44search7
- Conversation history is already stored in `sessions` and `messages`, and notes are already stored in `notes`. citeturn44search4turn44search9
- `/context` can already display memory-layer status, so there is an existing integration point. citeturn44search11turn44search7
- The current RAG stack already uses SQLite, FTS5, and sqlite-vec, and the agent already follows a local retrieval-and-injection pattern. citeturn44search9turn44search10

## Unknowns

- How strict the extraction rules should be for semantic memory versus episodic memory.
- What storage granularity should be used per turn, and how to keep consistency with compressed history.
- Whether embeddings should be generated synchronously, at Stop time, or in the background.
- Whether vector search should be enabled in Phase 1 or added after FTS5-first rollout.
- What granularity should be used for project, repo, branch, and session weighting.
- How far the UI and CLI should go for pinned memory versus auto-extracted memory.
- What size limits and masking rules are required if code fragments are stored as memory.

## Affected areas

### Core runtime

- `agent_repl.py`
- `orchestrator.py`
- `agent_context.py`
- `agent_config.py`
- `agent_session.py`
- `history_manager.py`
- `agent_commands.py`

### New modules

- `memory_layer.py`
- `memory_store.py`
- `memory_index.py`
- `memory_retriever.py`
- `memory_extract.py`
- `memory_types.py`

### Storage

- append-only JSONL
- new SQLite tables
- optional embedding index tables

### CLI / observability

- `/context`
- optional `/memory` commands
- audit and log updates

## Design

### 1. Memory model

Persistent memory uses a two-layer structure.

#### semantic memory

- rules
- policies
- durable facts
- project-specific constraints
- decision results

Characteristics:
- stores stable information
- has higher reuse priority
- is suitable for automatic injection at SessionStart

#### episodic memory

- raw Q&A
- failure logs
- fix history
- past consultations
- temporary reasoning

Characteristics:
- stores conversation and work history
- is mainly used for related retrieval at UserPromptSubmit
- emphasizes recency

### 2. Storage model

Memory storage uses two layers.

#### source of truth

- append-only JSONL
- one entry per line
- canonical source for audit and reconstruction

#### search index

- SQLite
- FTS5 as the base search method
- schema prepared for future vector search extension

### 3. Recommended data structures

#### JSONL entry

Required fields:

- `memory_id`
- `memory_type` (`semantic` / `episodic`)
- `source_type` (`conversation` / `decision` / `rule` / `failure` etc.)
- `session_id`
- `turn_id`
- `project`
- `repo`
- `branch`
- `content`
- `summary`
- `tags`
- `importance`
- `pinned`
- `created_at`
- `updated_at`

#### SQLite tables

- `memories`
  - base metadata
- `memories_fts`
  - FTS5 index
- `memory_links`
  - related memory references
- `memory_embeddings` (optional / Phase 2)
  - embedding BLOB

### 4. Retrieval timing

#### SessionStart

- inject top semantic-memory entries
- prioritize pinned memory
- inject a limited number of recent important episodic memories

#### UserPromptSubmit

- search related memory from the input query
- score semantic and episodic memory separately
- inject only top-ranked entries into context

#### Stop

- extract new memory candidates
- append them to JSONL
- update the SQLite index
- generate embeddings if needed

### 5. Scoring

Use the following weighted score as the base:

- BM25
- embedding similarity
- recency decay
- project / repo / branch match
- pinned / importance boost

Recommended policy:

- Phase 1 uses BM25 plus rule-based boosting.
- Phase 2 adds embedding similarity.
- semantic memory prioritizes importance over recency.
- episodic memory gives stronger weight to recency.

### 6. Integration with existing components

#### AgentContext / ServiceContainer

- Inject `MemoryLayer` into `ctx.services.memory`. Use the existing `memory` slot as the formal integration point. citeturn44search5turn44search7
- If `use_memory_layer` is false, keep `None` and preserve current behavior. citeturn44search5turn44search7

#### AgentREPL / Orchestrator

- Build MemoryLayer inside `_init_components()`. citeturn44search3turn44search13
- Call a UserPromptSubmit hook before `handle_turn()`. citeturn44search3
- Call a SessionStart hook when a session begins, by inserting it into the current `run()` plus session-start flow. citeturn44search3turn44search4
- Call Stop-equivalent save logic when the session ends or when a turn completes.

#### AgentSession

- Either extend responsibility so it can manage memory tables in addition to `sessions`, `messages`, and `notes`, or delegate memory storage to a dedicated memory store. citeturn44search4
- Use existing session IDs and message history as input for memory extraction. citeturn44search4turn44search9

#### HistoryManager

- Preserve important data before compression so it can be passed into memory extraction. The current history compression replaces older turns with summaries, so the memory side must preserve the original fragments before compression. citeturn44search12turn44search10

#### `/context`

- Extend the current memory-layer display with `enabled`, `entries`, `last_sync`, and similar fields. citeturn44search11turn44search5

### 7. Extraction policy

#### semantic memory extraction targets

- explicit rules
- long-lived design decisions
- continuously reused constraints
- user-emphasized policies

#### episodic memory extraction targets

- recent interaction
- failure cases
- fix intent
- reusable Q&A

#### extraction guards

- do not save very short conversations
- store noisy conversations with low importance
- separate pinned memory from auto-extracted memory
- deduplicate against existing notes

## Implementation steps

### Phase 1: Minimum implementation

1. Add `memory_types.py`.
   - MemoryEntry
   - MemoryQuery
   - MemoryHit
2. Add `memory_store.py`.
   - JSONL append
   - SQLite insert / update
3. Add `memory_index.py`.
   - create `memories` and `memories_fts`
   - update FTS5 indexes
4. Add `memory_extract.py`.
   - initial semantic / episodic extraction rules
5. Add `memory_retriever.py`.
   - FTS5 search
   - importance / pin / recency adjustment
6. Add `memory_layer.py`.
   - SessionStart
   - UserPromptSubmit
   - Stop
   - save / search / inject
7. Add MemoryLayer settings to `agent_config.py`, or formally activate the existing `use_memory_layer` path.
8. Add hooks to `agent_repl.py` and `orchestrator.py`.
9. Add memory display to `/context`.

### Phase 2: Search quality improvement

1. Add an embedding generation path.
2. Add `memory_embeddings`.
3. Implement hybrid search.
4. Optimize separate scoring for semantic versus episodic memory.
5. Add deduplication and nearby-memory links.

### Phase 3: Operational hardening

1. Add CLI commands such as pin / unpin / search.
2. Add audit logs for memory save rules.
3. Add memory pruning and retention policy.
4. Add integration points for Rule / Skill extraction.

## Validation plan

### Unit tests

- memory entry creation
- semantic / episodic extraction decisions
- JSONL append
- SQLite insert / FTS update
- BM25 search
- importance / pin / recency score adjustment

### Integration tests

- memory is injected at session start
- related memory search works on user input
- memory is saved when a session ends
- `/context` reflects memory status
- current behavior is unchanged when `use_memory_layer=false`

### Regression tests

- RAG pipeline behavior remains correct
- conversation history storage remains correct
- memory save continues to work after HistoryManager compression
- memory search continues to work after `/session load`

### Performance checks

- added latency at SessionStart
- added latency at UserPromptSubmit search
- JSONL / SQLite size growth
- CPU usage during embedding generation

## Risks

### 1. Memory noise accumulation

- Unnecessary conversations may reduce retrieval quality.
- Mitigation:
  - separate semantic and episodic memory
  - assign importance
  - separate pinned and auto memory
  - define save thresholds

### 2. Inconsistency with compressed history

- If original information is lost after history compression, memory replay quality decreases.
- Mitigation:
  - extract memory before compression
  - keep original logs in JSONL

### 3. Increased retrieval cost

- Searching every turn may increase response latency.
- Mitigation:
  - use FTS5 first in Phase 1
  - limit injection count
  - add embeddings gradually

### 4. Over-retention of sensitive data

- Long-term retention of conversation or code fragments may increase operational burden.
- Mitigation:
  - retention policy
  - mask target definitions
  - repo / project scope control

### 5. Responsibility conflict with the existing note feature

- If note and memory roles are unclear, operations become confusing.
- Mitigation:
  - notes are manually fixed knowledge
  - memory is auto-extracted knowledge
  - separate display and save paths
