## Goal

Remove ASCII directory trees and per-file descriptions from `docs/01_overview-files-01-build.md`; replace with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries needing joint review. [REQ-001, REQ-003]

## Scope

- Remove the two ASCII tree blocks (lines 27-45): `/opt/llm/` tree and `deploy/` tree
- Replace with prose describing: deploy script responsibilities, deployment lifecycle phases, model acquisition process, and their operational dependencies
- Preserve existing "Implementation Notes" subsection content (expand where it contains design-intent about startup sequence)
- Retain Front Matter, Related Documents, Keywords sections unchanged

## Assumptions

- The six-file split remains unchanged (File Split Rule's 400-line threshold); merge assessment deferred until after rewrite
- The deploy scripts' current behavior (workflow validation, DB existence checks) reflects the intended deployment contract
- LLM model acquisition via `02_deployment.md` section 1.4 remains the canonical reference for model handling

## Design decisions

- Keep thematic grouping as prose structure (e.g., "Deployment Scripts" as a section heading) but replace file-by-file listing with component responsibility descriptions
- Replace bare file enumeration with a single pointer sentence ("see `deploy/` for the current file layout") per `skills/DESIGN.md` Avoid implementation-reference duplication
- Expand "Implementation Notes" into a proper design-intent subsection covering startup sequence dependencies

## Alternatives considered

- Merging this file with `01_overview-files-02-rag.md` (rejected: different deployment domains — build vs. RAG pipeline)
- Converting remaining prose to table format (rejected: prose better conveys causal relationships between deployment phases)

## Implementation

### Target file

`docs/01_overview-files-01-build.md`

### Procedure

1. Identify and remove both ASCII tree blocks (the `/opt/llm/` tree at lines 27-34 and the `deploy/` tree at lines 36-45)
2. Write prose replacing the `/opt/llm/` tree: describe the three deployment components (llama.cpp source/artifacts, chat LLM models, embedding LLM models) as responsible entities with their owned state and dependency direction
3. Write prose replacing the `deploy/` tree: describe the five deploy scripts as a sequential deployment workflow — initial setup (build_sqlite_vec.sh), deployment (deploy.sh), initialization (init_db.sh), service startup (setup_services.sh), and agent launch (start_agent.sh) — including their operational dependencies
4. Expand the existing "Implementation Notes" subsection into a design-intent section covering: workflow definition requirement, DB existence precondition, and the startup sequence ordering
5. Verify Front Matter, Related Documents, and Keywords sections are preserved unchanged

### Method

Read the current file to identify exact tree block boundaries. Write replacement prose that covers: what each component does (responsibility), what it owns (state), which direction its dependencies flow (allowed dependency direction), why it runs separately (reason for process separation), and which boundaries require joint review (design boundaries).

### Details

**Section 1 — Deployment targets (/opt/llm/):**
- llama.cpp: builds and maintains inference runtime artifacts; depends on models directory for GGUF model loading
- Chat LLM models: owned by model acquisition process in `02_deployment.md` section 1.4; consumed by :8080 agent-LLM process
- Embedding LLM models: owned by model acquisition process; consumed by :8081 embed-LLM process

**Section 2 — Deployment scripts:**
- `deploy.sh`: copies Python scripts, configurations, and SQL to /opt/llm/; requires `config/workflows/default.json` exists with valid schema
- `build_sqlite_vec.sh`: downloads and builds sqlite-vec extension (vec0.so); run once during initial deployment
- `init_db.sh`: initializes SQLite schema; depends on deploy.sh completing first
- `setup_services.sh`: starts MCP servers (:8004-:8014) and LLM servers (:8080-:8081) as subprocesses; requires workflow definitions validated and DB tables present
- `start_agent.sh`: starts AgentREPL; prefers /opt/llm/pyproject.toml in production

**Section 3 — Startup sequence dependencies:**
- Workflow validation (default.json + `python -m agent.workflow.validate`) is a hard prerequisite for both deploy.sh and setup_services.sh
- DB existence check (`/opt/llm/db/workflow.sqlite` and required tables) is a precondition for setup_services.sh
- Startup order: build_sqlite_vec.sh → deploy.sh → init_db.sh → setup_services.sh → start_agent.sh

## Compatibility considerations

- Cross-references in other `docs/*.md` files must be updated if section headings change
- The "see `deploy/` for the current file layout" pointer replaces the old inline file references; consumers should verify no stale cross-references remain
- Port numbers in prose (e.g., ":8004-:8014", ":8080-:8081") are illustrative examples labeled as such, not claims about deployed configuration — consistent with `skills/DESIGN.md` No concrete configuration values rule

## Security considerations

No security impact — this is a documentation-only change. The removed ASCII trees contained no secrets or credentials.

## Rollback considerations

To rollback: restore the original file from git history (`git checkout HEAD -- docs/01_overview-files-01-build.md`). The ASCII trees can be recovered from any prior commit before this change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-01-build.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-01-build.md` | Zero findings; structure check passes |

## Completion criteria

- `uv run python tools/check_docs_content_policy.py` reports zero findings for `docs/01_overview-files-01-build.md`
- All ASCII tree-drawing characters (`├─`, `│`, `└─`) removed from the file
- Design-intent prose covers: component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries
- Front Matter, Related Documents, and Keywords sections preserved without loss
- No cross-references broken in other `docs/*.md` files

## Out of scope

- Modifying `rules/env.md` (explicitly out-of-scope per Plan)
- Changing GV-021's report-only status
- Merging or deleting this file outright (File Split Rule's 400-line threshold)
- Deciding the auto-generated port-reference-table exemption (tracked in dcp001)
- Implementing the actual code changes to deploy scripts

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII trees and per-file descriptions | Completed | 2026-09-09 | 2026-09-09 | Removed two ASCII tree blocks (lines 27-45) |
| 2 | Add design-intent prose for deployment components | Completed | 2026-09-09 | 2026-09-09 | Added prose for Deployment Targets, Deployment Scripts, Startup Sequence Dependencies sections |
| 3 | Expand startup sequence dependencies | Completed | 2026-09-09 | 2026-09-09 | Startup order and prerequisites documented |
| 4 | Run validation checkers | Completed | 2026-09-09 | 2026-09-09 | Zero findings; structure check passes |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | Completed | 2026-09-09 | 2026-09-09 | N/A: no docs/00_index.md task-scope mapping for docs/01_overview-files-01-build.md |
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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260905-153715_dcp002_overview_file_structure_docs_redesign.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210427_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-153145
- **Related target files**: docs/01_overview-files-01-build.md
