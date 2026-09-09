## Goal

Remove ASCII directory trees and per-file descriptions from `docs/01_overview-files-04-shared.md`; replace with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries needing joint review. [REQ-001, REQ-002, REQ-003]

## Scope

- Remove the two ASCII tree blocks: `/opt/llm/` venv/db/scripts/tree tree (lines 21-46) and the `scripts/shared/` per-file description list (lines 64-119)
- Replace with prose describing: Python virtual environment purpose, SQLite database domain separation rationale, DB layer package architecture, and shared infrastructure component responsibilities
- Preserve existing "Design Intent and Operational Specifications" subsection content (expand where it contains design-intent about caching and drift validation)
- Retain Front Matter, Related Documents, Keywords sections unchanged

## Assumptions

- The four-domain DB separation (RAG/Session/Workflow/EventBus) reflects the intended data isolation strategy
- WAL mode across all four databases is the intended concurrency model
- ADR-008 provides the rationale for the four-domain separation
- The six-file split remains unchanged (File Split Rule's 400-line threshold)
- `ToolResultCache` being unused is a known state, not a design intent

## Design decisions

- Keep thematic grouping as prose structure (e.g., "Virtual Environment", "Database Domains", "DB Layer Package", "Shared Infrastructure Components") but replace file-by-file listing with component responsibility descriptions
- Replace bare file enumeration with a single pointer sentence ("see `venv/` for the virtual environment contents", "see `db/` for the DB layer package", "see `shared/` for the current file layout") per `skills/DESIGN.md` Avoid implementation-reference duplication
- Expand the existing "Design Intent and Operational Specifications" into a proper design-intent section covering caching strategy and drift validation behavior

## Alternatives considered

- Merging this file with `01_overview-files-06-misc.md` (rejected: different domains — shared infrastructure vs. eventbus/miscellaneous)
- Converting remaining prose to table format (rejected: prose better conveys causal relationships between infrastructure layers)

## Implementation

### Target file

`docs/01_overview-files-04-shared.md`

### Procedure

1. Identify and remove both ASCII tree blocks (the `/opt/llm/` tree at lines 21-46 and the `scripts/shared/` per-file description list at lines 64-119)
2. Write prose replacing the `/opt/llm/` tree: describe the three shared infrastructure components (venv, db/, scripts/) as responsible entities with their owned state and dependency direction
3. Write prose replacing the `scripts/shared/` per-file list: describe the five thematic groups (LLM Client/Transport, Tool Routing/Execution, Configuration, Other Utilities, protocols/) as component families with their collective responsibility
4. Expand the existing "Design Intent and Operational Specifications" subsection into a design-intent section covering: caching strategy (ToolResultCache as standalone utility), health-check-based dispatch control, and drift validation behavior
5. Verify Front Matter, Related Documents, and Keywords sections are preserved unchanged

### Method

Read the current file to identify exact tree block boundaries. Write replacement prose that covers: what each component does (responsibility), what it owns (state), which direction its dependencies flow (allowed dependency direction), why each runs separately (reason for process separation), and which boundaries require joint review (design boundaries).

### Details

**Section 1 — Virtual Environment (venv/):**
- Python virtual environment managed by uv; `uv.lock` tracks dependency list
- Owned by build/deployment process; consumed by all Python processes

**Section 2 — Database Domains (db/):**
- Four isolated SQLite databases: rag.sqlite, session.sqlite, workflow.sqlite, eventbus.sqlite
- Each operates in WAL mode; persistence separated into four domains to isolate write patterns, limit failure impact, and clarify ownership
- See ADR-008 for the rationale behind four-domain separation
- Shared DB path builder via `DbConfig` dataclass in `config.py`

**Section 3 — DB Layer Package (scripts/db/):**
- Schema initialization (`create_schema.py`, `schema_sql.py`)
- Connection management (`helper.py`) — WAL mode, busy_timeout
- Maintenance operations (`maintenance.py`)
- Protocol abstraction (`store.py`, `store_protocols.py`) — VectorStore, DocumentStore, SessionStore
- SQLite implementations (`store_impl.py`) — SQLiteVectorStore, SQLiteDocumentStore, SQLiteSessionStore
- Data models (`models.py`) — WalCheckpointCounts, PurgeCounts, DbHealthMetrics, DocumentRow, SessionRow, MessageRow
- Consistency checking (`rag_consistency.py`)
- Rotation (`rotation.py`) and recovery (`recovery.py`)

**Section 4 — Shared Infrastructure Components (scripts/shared/):**
- LLM Client/Transport: SSE streaming, exponential backoff retry, transport error handling, payload handling
- Tool Routing/Execution: MCP server routing, tool registry, runtime tool metadata, route resolution
- Configuration: TOML/JSON loader, typed value accessors, validators, MCP server configuration dataclasses, health tracking
- Other Utilities: type definitions, action results, events, formatters, git helper, HTTP transport, JSON utilities, logging, OpenTelemetry, token counting
- protocols/: ShellPolicy protocol definition

**Section 5 — Design Intent and Operational Specifications:**
- Caching: `ToolResultCache` is a standalone LRU+TTL cache utility, currently unused in the codebase
- Health checks using `mcp_health.py` enable dispatch control based on server status (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN)
- Drift validation behavior: Config Drift defaults to warnings, raises RuntimeError if `routing_drift_strict` enabled; Live Drift defaults to warnings, becomes FATAL if `tool_definitions_strict` enabled or `security_profile == PRODUCTION`; Ownership Duplication always results in FATAL regardless of mode

## Compatibility considerations

- Cross-references in other `docs/*.md` files must be updated if section headings change
- The "see `shared/` for the current file layout" pointer replaces the old inline file references; consumers should verify no stale cross-references remain
- Port numbers in prose (e.g., ":8004-:8014") are illustrative examples labeled as such, not claims about deployed configuration — consistent with `skills/DESIGN.md` No concrete configuration values rule

## Security considerations

No security impact — this is a documentation-only change. The removed ASCII trees contained no secrets or credentials.

## Rollback considerations

To rollback: restore the original file from git history (`git checkout HEAD -- docs/01_overview-files-04-shared.md`). The ASCII trees can be recovered from any prior commit before this change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-04-shared.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-04-shared.md` | Zero findings; structure check passes |

## Completion criteria

- `uv run python tools/check_docs_content_policy.py` reports zero findings for `docs/01_overview-files-04-shared.md`
- All ASCII tree-drawing characters (`├─`, `│`, `└─`) removed from the file
- All per-file one-line descriptions removed from the file
- Design-intent prose covers: component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries
- Existing design-intent subsections preserved without loss of content
- Front Matter, Related Documents, and Keywords sections preserved without loss
- No cross-references broken in other `docs/*.md` files

## Out of scope

- Modifying `rules/env.md` (explicitly out-of-scope per Plan)
- Changing GV-021's report-only status
- Merging or deleting this file outright (File Split Rule's 400-line threshold)
- Deciding the auto-generated port-reference-table exemption (tracked in dcp001)
- Implementing the actual code changes to shared infrastructure components

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII trees and per-file descriptions | Completed | 2026-09-09 | 2026-09-09 | Removed two ASCII tree blocks (venv/db/scripts/tree at lines 21-46; scripts/shared/ per-file list at lines 64-119) |
| 2 | Add design-intent prose for shared infrastructure | Completed | 2026-09-09 | 2026-09-09 | Added prose for Virtual Environment, Database Domains, DB Layer Package, Shared Infrastructure Components sections |
| 3 | Expand design-intent subsections | Completed | 2026-09-09 | 2026-09-09 | Expanded Design Intent subsections: Caching Strategy, Health Check-Based Dispatch Control, Drift Validation Behavior |
| 4 | Run validation checkers | Completed | 2026-09-09 | 2026-09-09 | Zero findings; structure check passes |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | Completed | 2026-09-09 | 2026-09-09 | N/A: no docs/00_index.md task-scope mapping for docs/01_overview-files-04-shared.md |
| 6 | Validate documentation updates | Completed | 2026-09-09 | 2026-09-09 | N/A: no documentation changes to validate |
| 7 | Move the implementation procedure file to `implementations/done/` | Completed | 2026-09-09 | 2026-09-09 | Moved via git mv |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260905-153715_dcp002_overview_file_structure_docs_redesign.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210427_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-153145
- **Related target files**: docs/01_overview-files-04-shared.md
