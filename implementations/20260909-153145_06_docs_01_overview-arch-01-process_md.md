## Goal

Remove ASCII directory trees and per-file descriptions from `docs/01_overview-arch-01-process.md`; replace with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries needing joint review. [REQ-001, REQ-003]

## Scope

- Remove the ASCII tree block (lines 27-47): `/opt/llm/arch/` directory tree
- Replace with prose describing: architecture documentation structure, process documentation responsibilities, and design decision rationale
- Preserve existing Front Matter, Related Documents, Keywords sections unchanged

## Assumptions

- The architecture documentation follows a structured approach with ADRs (Architecture Decision Records)
- Process documentation includes operational procedures and deployment steps
- The six-file split remains unchanged (File Split Rule's 400-line threshold)

## Design decisions

- Keep the thematic grouping as prose structure (e.g., "Architecture Documentation Structure", "Process Documentation Responsibilities") but replace file-by-file listing with component responsibility descriptions
- Replace bare file enumeration with a single pointer sentence ("see `arch/` for the current file layout") per `skills/DESIGN.md` Avoid implementation-reference duplication

## Alternatives considered

- Merging this file with other overview files (rejected: different domain — architecture/process docs vs. build/RAG/shared/config/misc)
- Converting remaining prose to table format (rejected: prose better conveys causal relationships between architecture decisions and their rationale)

## Implementation

### Target file

`docs/01_overview-arch-01-process.md`

### Procedure

1. Identify and remove the ASCII tree block (the `/opt/llm/arch/` tree at lines 27-47)
2. Write prose replacing the tree: describe the architecture documentation directory as containing ADRs and process documentation
3. Verify Front Matter, Related Documents, and Keywords sections are preserved unchanged

### Method

Read the current file to identify the exact tree block boundary. Write replacement prose that covers: what each document type serves (responsibility), what it owns (state), which direction its dependencies flow (allowed dependency direction), why each runs separately (reason for process separation), and which boundaries require joint review (design boundaries).

### Details

**Section 1 — Architecture Documentation Structure:**

The architecture documentation directory contains Architecture Decision Records (ADRs) that capture key architectural decisions made during the project's evolution. Each ADR documents the context, decision, consequences, and status of an architectural choice. This provides traceability and rationale for architectural decisions.

**Section 2 — Process Documentation Responsibilities:**

Process documentation captures operational procedures including:
- Deployment procedures (how to deploy the system)
- Maintenance procedures (how to maintain the system)
- Troubleshooting procedures (how to diagnose and fix issues)
- Monitoring procedures (how to monitor system health)

Each process document serves as a reference for operators and developers to understand how to interact with the system operationally.

**Section 3 — Design Boundaries Requiring Joint Review:**

- Architecture decisions that affect multiple subsystems require joint review by all affected teams
- Process documentation that impacts operational procedures requires review by operations stakeholders
- Changes to ADRs that alter architectural rationale require review by the architecture committee

## Compatibility considerations

- Cross-references in other `docs/*.md` files must be updated if section headings change
- The "see `arch/` for the current file layout" pointer replaces the old inline file references; consumers should verify no stale cross-references remain

## Security considerations

No security impact — this is a documentation-only change. The removed ASCII tree contained no secrets or credentials.

## Rollback considerations

To rollback: restore the original file from git history (`git checkout HEAD -- docs/01_overview-arch-01-process.md`). The ASCII tree can be recovered from any prior commit before this change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-arch-01-process.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-arch-01-process.md` | Zero findings; structure check passes |

## Completion criteria

- `uv run python tools/check_docs_content_policy.py` reports zero findings for `docs/01_overview-arch-01-process.md`
- All ASCII tree-drawing characters (`├─`, `│`, `└─`) removed from the file
- Design-intent prose covers: component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries
- Front Matter, Related Documents, and Keywords sections preserved without loss
- No cross-references broken in other `docs/*.md` files

## Out of scope

- Modifying `rules/env.md` (explicitly out-of-scope per Plan)
- Changing GV-021's report-only status
- Merging or deleting this file outright (File Split Rule's 400-line threshold)
- Deciding the auto-generated port-reference-table exemption (tracked in dcp001)
- Implementing the actual code changes to architecture documentation

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII tree and per-file descriptions | Pending | — | — | |
| 2 | Add design-intent prose for architecture docs | Pending | — | — | |
| 3 | Document process documentation responsibilities | Pending | — | — | |
| 4 | Run validation checkers | Pending | — | — | |

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
- **Related target files**: docs/01_overview-arch-01-process.md
