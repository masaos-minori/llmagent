## Goal
- Update `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` for the grouped ADR file names (`REQ-002` (replace old ADR file names)).

## Scope
- In scope: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- Names only; no prose rewording beyond the listed changes.

## Alternatives considered
- N/A: mechanical reference update.

## Implementation
### Target file

`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

### Procedure
1. Apply the exact-basename replacement of the 14 old ADR file names to this file only (the shared throwaway script in the Plan Design section, restricted to this path; dry run first, then write); the names are unique tokens, so links, `related:` entries, and prose are all covered and link style is unchanged.
### Method
Old to new names found in this file (count of occurrences, measured 2026-10-19):
  - adr_02_002_config-isolation.md to adr_02_01_002_platform-config-isolation.md (2 occurrence(s))
### Details
- 2 reference(s); first at line 14 (`adr_02_002_config-isolation.md`).

## Compatibility considerations
- Documentation only; files reach the deployed docs directory with the next deploy.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py`, `check_docs_quality.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, and (for ADR-related content) `check_adr_reference.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`.

## Completion criteria
- No old ADR file name or glob/placeholder form remains in the file.
- The document checkers pass.

## Out of Scope
- Modifying any file other than the target file; ADR decisions, IDs, status, and invariants; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the references and patterns | Completed | 20261019-204543 | 20261019-204543 |  |
| 2 | Run the documentation checkers | Completed | 20261019-204543 | 20261019-204543 | Stale check clean; replacement count matched procedure. Step 5/6: docs edit is the change itself (N/A index mapping); check_docs_quality, content_policy --strict, japanese, consistency (5 domains) pass; check_docs_structure leaves only pending adr_00/adr_01 links and ADR size/ID findings fixed by cycles 03/28/29. Order changed by user. |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/done/20261019-170548_adrname001_group-adr-file-names-by-theme.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-173513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-182330
- **Related target files**: docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md