## Goal

Remove ASCII directory trees and handle literal port numbers in `docs/01_overview-files-05-config.md`; replace with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries needing joint review. [REQ-001, REQ-003, REQ-006]

## Scope

- Remove the ASCII tree block (lines 27-47): `/opt/llm/config/` directory tree
- Handle literal port numbers in the tree descriptions (e.g., `(:8004)`, `(:8005)`, etc.) per dcp001's decision — dcp001 covers auto-generated port tables only (`docs/04_mcp_01_tool_ownership_matrix.md`), NOT hand-written port mentions in prose/config descriptions within this file
- Replace with prose describing: configuration file structure, per-process config isolation policy, and MCP server configuration responsibilities
- Preserve existing Front Matter, Related Documents, Keywords sections unchanged

## Assumptions

- dcp001's exemption decision (auto-generated port tables) does not apply to literal port numbers in prose/config descriptions within this file; these are hand-written operational values documenting the current deployment configuration
- The six-file split remains unchanged (File Split Rule's 400-line threshold)
- Per-process config isolation policy (each process reads only its own config file) is the intended design

## Design decisions

- Keep the thematic grouping as prose structure (e.g., "Configuration Directory Structure", "Per-Process Config Isolation Policy") but replace file-by-file listing with component responsibility descriptions
- Replace bare file enumeration with a single pointer sentence ("see `config/` for the current file layout") per `skills/DESIGN.md` Avoid implementation-reference duplication
- Literal port numbers in prose are retained as illustrative examples explicitly labeled as such — consistent with `skills/DESIGN.md` No concrete configuration values rule's carve-out for "a short, explicitly-labeled illustrative port number inside a worked example"

## Alternatives considered

- Removing all literal port numbers from this file (rejected: they serve as concrete examples of the current deployment configuration, which is useful for operators; dcp001 does not cover this case)
- Converting remaining prose to table format (rejected: prose better conveys causal relationships between config files and their processes)

## Implementation

### Target file

`docs/01_overview-files-05-config.md`

### Procedure

1. Identify and remove the ASCII tree block (the `/opt/llm/config/` tree at lines 27-47)
2. Write prose replacing the tree: describe the configuration directory as containing per-process config files, each serving a specific process
3. Address literal port numbers: retain them as illustrative examples in prose (not as claims about deployed configuration), consistent with `skills/DESIGN.md` No concrete configuration values rule's exception for explicitly-labeled illustrative examples
4. Verify Front Matter, Related Documents, and Keywords sections are preserved unchanged

### Method

Read the current file to identify the exact tree block boundary. Write replacement prose that covers: what each config file serves (responsibility), what it owns (state), which direction its dependencies flow (allowed dependency direction), why each process has its own config (reason for per-process config separation), and which boundaries require joint review (design boundaries).

### Details

**Section 1 — Configuration Directory Structure:**

- `config/workflows/default.json`: Default workflow definition file; required by deploy.sh and setup_services.sh for startup validation
- `config/agent.toml`: Global agent settings including DB paths, embedding URLs, and `[mcp_servers.*]`
- `config/mcp_<name>.toml`: Per-MCP-server configuration files (one per server); each contains the server's transport URL, timeout, and retry settings
- `config/embedding.toml`: Embedding service configuration including model path and endpoint URLs
- `config/tool_registry.json`: Tool registry mapping tool names to their implementations

**Section 2 — Per-Process Config Isolation Policy:**

Each process reads only its own config file — no cross-process config sharing. This prevents configuration drift between processes and ensures that changes to one process's config do not affect others. The MCP servers read their respective `mcp_<name>.toml` files; the agent reads `agent.toml`; the embedding service reads `embedding.toml`.

**Section 3 — MCP Server Configuration Responsibilities:**

MCP server configs define: transport type (SSE/HTTP), target URL, timeout duration, retry count, and health-check interval. Each MCP server has its own config file because each server operates independently and may have different requirements.

## Compatibility considerations

- Cross-references in other `docs/*.md` files must be updated if section headings change
- The "see `config/` for the current file layout" pointer replaces the old inline file references; consumers should verify no stale cross-references remain
- Literal port numbers in prose are illustrative examples labeled as such, not claims about deployed configuration — consistent with `skills/DESIGN.md` No concrete configuration values rule

## Security considerations

No security impact — this is a documentation-only change. The removed ASCII tree contained no secrets or credentials.

## Rollback considerations

To rollback: restore the original file from git history (`git checkout HEAD -- docs/01_overview-files-05-config.md`). The ASCII tree can be recovered from any prior commit before this change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-05-config.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-05-config.md` | Zero findings; structure check passes |

## Completion criteria

- `uv run python tools/check_docs_content_policy.py` reports zero findings for `docs/01_overview-files-05-config.md`
- All ASCII tree-drawing characters (`├─`, `│`, `└─`) removed from the file
- Design-intent prose covers: component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries
- Literal port numbers retained as illustrative examples (per dcp001's scope limitation)
- Front Matter, Related Documents, and Keywords sections preserved without loss
- No cross-references broken in other `docs/*.md` files

## Out of scope

- Modifying `rules/env.md` (explicitly out-of-scope per Plan)
- Changing GV-021's report-only status
- Merging or deleting this file outright (File Split Rule's 400-line threshold)
- Deciding the auto-generated port-reference-table exemption (tracked in dcp001)
- Implementing the actual code changes to configuration files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII tree and handle literal port numbers | Completed | 2026-09-09 | 2026-09-09 | Removed ASCII tree block (lines 27-47); literal port numbers retained as illustrative examples |
| 2 | Add design-intent prose for configuration | Completed | 2026-09-09 | 2026-09-09 | Added prose for Configuration Directory Structure, Per-Process Config Isolation Policy, MCP Server Configuration Responsibilities sections |
| 3 | Document per-process config isolation policy | Completed | 2026-09-09 | 2026-09-09 | Included in Section 2 above |
| 4 | Run validation checkers | Completed | 2026-09-09 | 2026-09-09 | Zero findings; structure check passes |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | Completed | 2026-09-09 | 2026-09-09 | N/A: no docs/00_index.md task-scope mapping for docs/01_overview-files-05-config.md |
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
- **Requirement ID**: REQ-001, REQ-003, REQ-006
- **Source issue**: issues/20260905-153715_dcp002_overview_file_structure_docs_redesign.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210427_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-153145
- **Related target files**: docs/01_overview-files-05-config.md
