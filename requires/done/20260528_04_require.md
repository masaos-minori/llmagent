# Advanced Context Management (Memory Layer & Token Limit) — Build Plan

Source file: `context_management_memory_layer_token_limit_implementation_plan_20260528_ja.md`
Date: 2026-05-28

## Goal

- Implement an accurate Token Limit and replace character-based approximation.
- Implement a long-term Memory Layer to preserve important facts, settings, and context that would otherwise be lost during compression.
- Improve the stability of local LLM context management under limited context windows.
- Enable context recovery across multiple sessions.
- Integrate naturally with the current REPL, HistoryManager, RagPipeline, and `/context` output.

## Scope

### In scope

- Token Limit implementation
  - exact token counting instead of character-based estimation
  - compression trigger based on `context_token_limit`
  - `/context` output update
- Memory Layer implementation
  - extract important facts from compressible history
  - persist them in SQLite
  - recall them through vector search
  - inject them dynamically into the final prompt
- Extend the existing `HistoryManager`
- Formally use the existing `AgentContext` / `ServiceContainer` memory slot
- Add memory search to the existing `RagPipeline`
- Add required settings to `config/agent.json`

### Out of scope

- external cloud memory backends
- distributed memory synchronization
- full knowledge graph integration
- autonomous rule update behavior itself
- full RAG redesign

## Assumptions

- The current REPL initializes components in AgentREPL, and Orchestrator handles turn processing. citeturn49search1
- `AgentConfig` already defines `context_token_limit`, `history_protect_turns`, `budget_warn_ratio`, and `use_memory_layer`. citeturn49search1
- `AgentContext` / `ServiceContainer` already have a `memory` slot, so MemoryLayer can be injected. citeturn49search1
- `HistoryManager` currently starts compression based on character count. citeturn49search1
- `/context` currently shows `Token estimate` and also has a Memory Layer status field. citeturn49search1
- Embeddings use `embed_url` and sqlite-vec, with 384-dimensional float32 little-endian BLOBs. citeturn49search1
- Conversation history is stored in `sessions` / `messages`, and existing notes are stored in the `notes` table. citeturn49search1

## Unknowns

- Whether `/tokenize` endpoint latency is acceptable for every turn.
- Whether a local LLM can stably extract only facts that should be persisted.
- Whether token counting should depend only on the LLM server API, or also use a local tokenizer.
- What similarity threshold should be used for long-term memory deduplication.
- How to balance Memory Layer injection volume against normal RAG injection volume.
- How far `/clear` and `/clear memory` should be separated at the CLI level.

## Affected areas

### Core runtime

- `agent_repl.py`
- `orchestrator.py`
- `history_manager.py`
- `agent_context.py`
- `agent_config.py`
- `agent_commands.py`
- `agent_session.py`
- `agent_rag.py`
- token-count call path in the LLM client layer

### New modules

- `memory_layer.py`
- `memory_store.py`
- `memory_index.py`
- `memory_retriever.py`
- `memory_extract.py`
- `memory_types.py`
- `token_counter.py` or an equivalent addition to the existing LLM utility layer

### Storage

- `memories` table
- `memories_vec` table
- optional JSONL source of truth

### CLI / observability

- `/context`
- optional `/clear memory`
- audit / log updates

## Design

### 1. Token Limit

#### 1.1 Basic policy

- Downgrade `chars / 4` from active control to fallback display only.
- Use exact token count for actual control.
- Make `context_token_limit` the primary trigger.
- Keep `context_char_limit` only for backward compatibility or as a secondary guard.

#### 1.2 Counting method

Use the following order.

1. Use the LLM server `/tokenize` endpoint.
2. Use a lightweight local tokenizer as fallback.
3. Fall back to `chars / 4` only when the above fail.

#### 1.3 Compression trigger

- Emit a warning at 80% of `context_token_limit`.
- Trigger `HistoryManager.compress()` when the limit is reached or exceeded.
- Use `history_protect_turns` to exclude recent turns from compression.

#### 1.4 `/context` output

- Show exact token usage instead of Token estimate.
- Explicitly mark the value as estimated only when real counting fails.
- Show remaining budget in tokens, not characters.

### 2. Memory Layer

#### 2.1 Purpose

- Preserve important information that would otherwise disappear during history compression.
- Reuse user facts, settings, and project context across sessions.
- Search and inject conversation-derived memory separately from normal RAG.

#### 2.2 Memory model

For the initial implementation, classify memory as:

- `user_preference`
- `project_context`
- `general_fact`
- `decision_reason`
- `failure_pattern`

In the initial phase, category-based storage is acceptable even if semantic / episodic separation is not yet strict.

#### 2.3 Storage structure

##### `memories`

- `id`
- `content`
- `category`
- `session_id`
- `turn_id`
- `created_at`
- `updated_at`
- `importance`
- `source_kind`

##### `memories_vec`

- `id` → `memories.id`
- `embedding` BLOB

An optional JSONL source of truth may also be added.

#### 2.4 Memory fixation

- Before or inside `HistoryManager.compress()`, pass the compressible message group to the LLM.
- Force the prompt to extract only user settings, facts, and project context that should be kept.
- Normalize extracted output into line-based or bullet-based entries.
- Generate embeddings and store them in `memories` / `memories_vec`.

#### 2.5 Memory recall

- During `RagPipeline.augment()`, perform memory search independently from normal document search.
- Run KNN search on `memories_vec` using the query embedding and retrieve about top K=3.
- Inject the result as a `[Memory Layer]` block at the end of the prompt.
- Keep it separate from `[Notes]`.

#### 2.6 Relation to the existing note feature

- `notes` remain manually fixed knowledge.
- `memory layer` stores automatically extracted knowledge.
- Separate display, deletion, and save paths.

### 3. Integration with existing components

#### AgentContext / ServiceContainer

- Inject `MemoryLayer` into `ctx.services.memory`. citeturn49search1
- When `use_memory_layer=false`, keep `None` and preserve current behavior. citeturn49search1

#### HistoryManager

- Extend control from `count_chars()`-centered logic to token-aware logic. citeturn49search1
- Insert memory extraction before `compress()` completes.

#### RagPipeline

- Add a memory-search step to `augment()`. Inject memory results as a separate block in addition to current RAG results. citeturn49search1

#### AgentSession / DB

- Either extend responsibility to manage memory tables in addition to `sessions` / `messages` / `notes`, or delegate to a dedicated store. citeturn49search1

#### CLIView / `/context`

- Replace `disabled`-style display for Token Limit and Memory Layer with actual values. citeturn49search1

## Implementation steps

### Phase 1: Enable Token Limit

- Add the following settings to `config/agent.json`:
  - `use_token_limit`
  - `token_limit_max` or `context_token_limit`
- Add matching fields to `AgentConfig`, or formally activate the existing fields.
- Add `token_counter.py`, or implement `get_token_count(text) -> int` in the current LLM utility.
- Switch the HistoryManager compression trigger to token-based control.
- Update `/context` to show token usage, hard limit, and remaining budget.

### Phase 2: Implement Memory Layer persistence

- Add migrations for `memories` and `memories_vec`.
- Add:
  - `memory_types.py`
  - `memory_store.py`
  - `memory_extract.py`
  - `memory_layer.py`
- Add the memory extraction routine inside `HistoryManager.compress()`.
- Vectorize extracted facts through the embedding API and store them in SQLite.
- Add similarity lookup before memory write for deduplication.

### Phase 3: Add recall and integration

- Add `search_memory_layer(query, db)` to `RagPipeline`.
- Inject memory search results as a `[Memory Layer]` block.
- Add memory-layer initialization and invocation to AgentREPL / Orchestrator turn processing.
- Make `/clear` remove only conversation history while preserving persistent memory.
- If needed, add `/clear memory` or `/memory purge`.

## Validation plan

### Unit tests

- exact token counting
- tokenize fallback behavior
- compression trigger at token limit
- normalization of extracted memory
- memory persistence
- memory deduplication
- memory KNN search

### Integration tests

- `/context` shows actual token values for long input
- auto-compression triggers at token limit
- memory is saved during compression
- memory is recalled in the next turn
- memory remains after `/clear`

### Scenario tests

1. Enter: `My current development project name is Project-Genesis.`
2. Send enough dummy conversation to exceed the token limit.
3. After the original message disappears from normal history, verify through `/context` that Memory Layer is enabled and has entries.
4. Ask: `What was my project name?` and verify correct recall.

### Performance checks

- latency of token count API calls
- added compress time from memory extraction
- added RAG latency from memory search
- CPU usage during embedding generation

## Risks

### 1. Increased latency

- Running token count, normal RAG, and memory search in every turn may increase TTFT.
- Mitigation:
  - cache token counts
  - run memory search and normal RAG in parallel with `asyncio.gather()`
  - create embeddings only during compression

### 2. Low extraction precision

- A small LLM may save noisy or low-value memory.
- Mitigation:
  - use low temperature
  - constrain output categories
  - apply deduplication and importance thresholds

### 3. Memory growth

- Repeatedly storing similar facts may turn memory into noise.
- Mitigation:
  - cosine-similarity deduplication
  - merge or skip on updates
  - add retention policy

### 4. Responsibility conflict with notes

- If note and memory roles become ambiguous, operation becomes confusing.
- Mitigation:
  - notes = manually fixed knowledge
  - memory = automatically extracted knowledge
  - separate display and deletion commands

### 5. DB size increase

- Adding memory and vector BLOBs will increase SQLite size.
- Mitigation:
  - set entry limits or retention policy
  - prefer summary storage for text
  - move raw logs to JSONL when necessary
