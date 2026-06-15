# Implementation Plan: Agent Documentation Restructuring (Plan 20260615-154200)

## Goal

Reorganize 12 existing agent documentation files into 13 new files (`docs/05_agent_00_*` through `docs/05_agent_12_*`) with top-down reading structure, deduplication, and explicit Spec Conflict annotations.

## Scope

**In:**
- Create 13 new doc files under `docs/05_agent_XX_*.md` naming convention
- Update `docs/00_llm-implementation-guide.md` with new file references
- Update `routing.md` agent task entries

**Out:**
- Source doc deletion (old files kept until verification complete)
- `docs/05_spec_agent.md` (kept as-is, referenced from overview)
- MCP/RAG/DB doc reorganization (separate tasks)

## Assumptions

1. Chapter template sections are omitted if not applicable (not forced).
2. Spec Conflict sections created where impl-* docs contradict ref-* docs.
3. Cross-references between new files use relative links `docs/05_agent_XX_YZZ.md`.
4. All source content preserved; deduplication uses canonical + summary pattern.

## Implementation

### Target Files (13 new)

| # | File | Primary Sources | Lines (est.) |
|---|---|---|---|
| 00 | `docs/05_agent_00_document-guide.md` | Derived | ~60 |
| 01 | `docs/05_agent_01_system-overview.md` | 05_agent.md §1-2, 05_spec_agent.md §1-2 | ~100 |
| 02 | `docs/05_agent_02_runtime-architecture.md` | 05_agent-impl-class.md, ref-repl.md, ref-context.md | ~150 |
| 03 | `docs/05_agent_03_turn-processing-flow.md` | 05_agent-impl-flow.md, ref-history.md | ~120 |
| 04 | `docs/05_agent_04_state-and-persistence.md` | ref-context.md, ref-session.md, ref-history.md | ~100 |
| 05 | `docs/05_agent_05_llm-and-streaming.md` | ref-llm.md | ~140 |
| 06 | `docs/05_agent_06_tool-execution-and-approval.md` | ref-repl.md, impl-flow.md §3.4, spec_agent.md | ~180 |
| 07 | `docs/05_agent_07_cli-and-commands.md` | 05_agent.md §3, impl-class.md §1.3, ref-commands.md | ~200 |
| 08 | `docs/05_agent_08_configuration.md` | ref-config.md, 05_agent.md §5 | ~250 |
| 09 | `docs/05_agent_09_data-layer.md` | ref-session.md, spec_agent.md data sections | ~100 |
| 10 | `docs/05_agent_10_operations-and-observability.md` | 05_agent-ops.md, spec_agent.md operations | ~160 |
| 11 | `docs/05_agent_11_extension-points.md` | spec_agent.md plugins, ref-commands.md | ~80 |
| 12 | `docs/05_agent_12_reference-api.md` | All ref-* files condensed | ~300 |

### Procedure (15 Steps)

#### Step 1: Create file structure

Create all 13 files with chapter template header:
```markdown
# <File Title>

## Purpose
<one sentence>

## Scope
- In: ...
- Out: ...

## Canonical sources
- [List of source files]

## Key concepts
- <Abbreviation>: <Definition>

## Related chapters
- [Links to other 05_agent_XX files]
```

#### Step 2: Create §00 document-guide

Content:
- Purpose: "This document set provides top-down reading structure for the agent REPL system"
- Audience: "Human engineers (top-to-bottom reading), AI systems (question-based lookup)"
- Reading order: Overview → Architecture → Flow → State → Communication → Tools → Commands → Config → Data → Operations → Extension → API Reference
- Canonical source rules: ref-* > impl-* > overview documents
- Glossary: SSE, REPL, MCP, RAG, OTel, FTS, RRF, MQE, FTS5, KNN, BM25, etc.
- Spec Conflict / Open Question interpretation guide

#### Step 3: Create §01 system-overview

Sources: `05_agent.md` Sections 1-2, `05_spec_agent.md` Sections 1-2
Content:
- Entry point: `python -m agent` (`scripts/agent/__main__.py`)
- Interaction model: CLI REPL with `agent>` prompt, SSE streaming responses
- Tool-calling model: LLM function calling → MCP server HTTP POST → result to LLM
- High-level: sessions (SQLite), SSE (server-sent events), history compression (char limit)
- Out-of-scope: MCP server implementation, RAG pipeline, DB schema, shared libraries

#### Step 4: Create §02 runtime-architecture

Sources: `05_agent-impl-class.md` Sections 1.2/1.7, `ref-repl.md`, `ref-context.md`
Content:
- Text diagram of component relationships (AgentREPL → Orchestrator → Context → services)
- Component responsibilities table (10 components + memory services)
- Dependency graph: AgentREPL depends on Context; Context depends on services
- Spec Conflict: Check impl-class vs ref-repl for differing method signatures

#### Step 5: Create §03 turn-processing-flow

Sources: `05_agent-impl-flow.md` Sections 1-2, `ref-history.md`
Content:
- Flow diagram: memory injection → append → compress → LLM → tool loop
- Each stage: inputs, outputs, state changes, failure handling
- History compression: char_limit trigger, compress_turns count, protected turns
- Partial completion persistence rules

#### Step 6: Create §04 state-and-persistence

Sources: `ref-context.md`, `ref-session.md`, `ref-history.md`
Content:
- AgentContext state model: conv (history, llm_url), turn (current_turn_id), stats, services
- Session persistence: sessions/messages/notes tables, AgentSession methods
- Data classification: session-scoped (ctx.conv), turn-scoped (ctx.turn), persisted (SQLite)
- HistoryManager compression algorithm and protected turns

#### Step 7: Create §05 llm-and-streaming

Source: `ref-llm.md`
Content:
- LLMClient responsibility: SSE streaming, exponential backoff retry, payload construction
- LLMTransportError: kind, phase, url, status_code, retryable, partial_text, detail
- RobustSSEParser: incremental UTF-8 decode, heartbeat tracking, malformed frame counter
- Reconnect behavior: sse_reconnect_max retries, partial completion policy
- Configuration impact: llm_url, http_timeout, llm_max_retries

#### Step 8: Create §06 tool-execution-and-approval

Sources: `ref-repl.md`, `impl-flow.md` Section 3.4, `spec_agent.md`
Content:
- ToolExecutor responsibility: HTTP/stdio transport, routing, TTL cache
- Parallel vs sequential: asyncio.gather() default, serial_tool_calls override, side-effect detection
- Approval flow: pre-flight (allowed_tools, allowed_root, GitHub repos), risk classification, dry_run
- Plan mode: plan_blocked_tools auto-blocking
- Tool result summarization: use_tool_summarize, tool_summarize_threshold
- Safety controls: allowed_root path validation, GitHub repo allowlist

#### Step 9: Create §07 cli-and-commands

Sources: `05_agent.md` Section 3, `impl-class.md` Section 1.3, `ref-commands.md`
Content:
- REPL I/O model: CLIView role, readline setup, multiline input (\ continuation)
- Command categorization (11 groups):
  - Session: /session list/load/rename/delete
  - MCP: /mcp status/install
  - Config/Stats/Reload: /config /stats /set /reload
  - Context/Clear/Undo/History/System: /context /compact /clear /undo /history /system
  - DB: /db stats/urls/clean/rebuild-fts
  - Tool/Plan: /tool list/show /plan
  - Note: /note add/list/delete
  - Debug/Audit: /debug [audit/verbose/normal] /audit
  - Ingest/Export/RAG: /ingest /export /rag search
  - Memory: /memory list/search/show/pin/unpin/delete/prune
- Command table format: category, command, purpose, side effects, related state

#### Step 10: Create §08 configuration

Sources: `ref-config.md`, `05_agent.md` Section 5
Content:
- AgentConfig structure: LLMConfig, RAGConfig, ToolConfig, MemoryConfig, MCPConfig, ApprovalConfig, ObservabilityConfig
- Config file split: common.toml, llm.toml, http.toml, rag.toml, context.toml, tools.toml, memory.toml, otel.toml, security.toml, system_prompts.toml, mcp_servers.toml, tools_definitions.toml
- Validation rules: transport http/stdio, url required for http, char_limit >= 1, etc.
- Reload scope: /reload updates ctx.cfg fields and syncs to services
- Restart-required settings: transport type (http/stdio), MCP server URLs/commands

#### Step 11: Create §09 data-layer

Sources: `ref-session.md`, `spec_agent.md` data sections, `ref-context.md`
Content:
- SQLite structures: sessions, messages, notes, documents, chunks, chunks_fts, chunks_vec, memories, memories_fts, memories_vec
- Data ownership boundaries: agent layer owns sessions/messages/notes; RAG layer owns documents/chunks; memory layer owns memories
- Responsibility overlap: AgentSession handles /db clean (RAG operation) for convenience — consider migrating to RAG MCP service

#### Step 12: Create §10 operations-and-observability

Source: `05_agent-ops.md`, `spec_agent.md` operations sections
Content:
- Startup procedure: deploy.sh → init_db.sh → start LLM services → python -m agent
- Operational verification: DB stats query, /mcp health check, sample conversation
- Health checks: embed-llm curl /health, LLM service connectivity
- Audit log: audit.log turn_end events, elapsed_ms extraction
- OTel: ConsoleSpanExporter config, span name filtering (compress, llm)
- Token metrics: input_tokens/output_tokens from audit.log, /context token estimate fallback
- Troubleshooting table: symptoms, causes, fixes (7 cases)

#### Step 13: Create §11 extension-points

Sources: `spec_agent.md` plugins/extension sections, `ref-commands.md`
Content:
- Plugin architecture: @register_tool decorator, plugin directory loading
- register_command: CommandRegistry mixin pattern, slash command dispatch
- register_pipeline_stage: RAG pipeline stage registration (if applicable)
- Extension rules: built-in features take priority, extensions cannot override core commands
- Spec Conflict: Check spec_agent.md vs ref-commands.md for differing extension mechanisms

#### Step 14: Create §12 reference-api

Sources: All ref-* files condensed
Content: Per-module summary tables:
| Module | Role | Classes/Functions | Public APIs | Callers | Config | Commands | Failure Behavior |
|--------|------|-------------------|-------------|---------|--------|----------|------------------|
| agent/repl.py | Coordinator | AgentREPL | run() | agent.py (entry) | AgentConfig | N/A | Finally cleanup |
| agent/orchestrator.py | Turn logic | Orchestrator | _run_turn() | AgentREPL | context.toml | N/A | Tool loop guard |
| agent/context.py | State hub | AgentContext | ctx.conv/turn/stats/services | All components | AgentConfig | N/A | None (data holder) |
| ... | ... | ... | ... | ... | ... | ... | ... |

#### Step 15: Update cross-references

Update `docs/00_llm-implementation-guide.md`:
- Add 13 new file entries (05_agent_00_* through 05_agent_12_*)
- Remove old entries: 05_agent.md, 05_agent-impl-class.md, 05_agent-impl-flow.md, 05_agent-ops.md, 05_ref-agent-*.md

Update `routing.md`:
- Update agent task entries to reference new file pattern
- Example: "Agent REPL slash commands" → `docs/05_agent_07_cli-and-commands.md`

Validate all internal links with Python script.

### Details

- Each new file follows chapter template: Purpose, Scope, Canonical sources, Key concepts, Main components, Inputs, Outputs, State changes, Configuration impact, Failure handling, Observability, Related chapters
- Deduplication: slash command list canonical in §07, startup procedure canonical in §10, history compression canonical in §03+§04
- Spec Conflict sections created where: impl-class.md warns about mixed old/new specs; ref-* files may differ from spec_agent.md
- Abbreviations defined at first occurrence in each file

## Validation Plan

| Check | Method | Target |
|---|---|---|
| All source content preserved | Line count comparison, grep for key terms from 12 source files | No information loss |
| No broken internal links | Python script checking all `](...)` patterns in docs/05_agent_*.md | 0 broken references |
| Chapter template applied | Manual review of each file's section headers | All applicable sections present |
| Cross-references valid | Verify 00_llm-implementation-guide.md and routing.md reference new files | 13 new entries added |
| Spec Conflict section exists | Grep for "Spec Conflict" in output files | At least one such section created |
| Deduplication verified | Check command list appears only once in full detail | Canonical + summary pattern applied |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Information loss during consolidation | Medium | Preserve all source content; use "see also" references instead of deleting |
| Spec Conflict between old impl-* and ref-* docs | High | Create explicit Spec Conflict sections; prefer ref-* as canonical |
| Over-fragmentation — 13 files still too many | Low | Each file has single responsibility per requirement rules |
| Cross-reference breakage during restructuring | Medium | Fix all refs in dedicated step (Step 15); validate with automated script |
