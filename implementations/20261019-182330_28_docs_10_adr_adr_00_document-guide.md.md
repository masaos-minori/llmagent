## Goal
- Update `docs/10_adr/adr_00_document-guide.md` for the grouped ADR file names (`REQ-002` (replace old ADR file names), `REQ-005` (state the naming rule and registry)).

## Scope
- In scope: `docs/10_adr/adr_00_document-guide.md` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- Names only; no prose rewording beyond the listed changes.

## Alternatives considered
- N/A: the Plan fixes the approach.

## Implementation
### Target file

`docs/10_adr/adr_00_document-guide.md`

### Procedure
1. Apply the exact-basename replacement of the 14 old ADR file names to this file only (the shared throwaway script in the Plan Design section, restricted to this path; dry run first, then write); the names are unique tokens, so links, `related:` entries, and prose are all covered and link style is unchanged.
2. Update the Reading Order table and `related:` entries.
3. Add the naming rule `adr_02_<GG>_<NNN>_<group>-<topic>.md` and the group registry (01 platform: 002, 004; 02 agent: 001, 003, 014; 03 mcp: 007, 012; 04 eventbus: 006, 013; 05 db: 008; 06 rag: 005, 009, 010; 07 docs: 015), and state where a new ADR records its group.
### Method
Old to new names found in this file (count of occurrences, measured 2026-10-19):
  - adr_02_001_workflow-engine-mandatory.md to adr_02_02_001_agent-workflow-engine-mandatory.md (1 occurrence(s))
  - adr_02_002_config-isolation.md to adr_02_01_002_platform-config-isolation.md (1 occurrence(s))
  - adr_02_003_runtime-tool-registry-routing-authority.md to adr_02_02_003_agent-runtime-tool-registry-routing-authority.md (1 occurrence(s))
  - adr_02_004_environment-failure-handling-policy.md to adr_02_01_004_platform-environment-failure-handling-policy.md (1 occurrence(s))
  - adr_02_005_rag-source-derived-index-relationships.md to adr_02_06_005_rag-source-derived-index-relationships.md (1 occurrence(s))
  - adr_02_006_eventbus-sqlite-persistence-and-sse-delivery.md to adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md (1 occurrence(s))
  - adr_02_007_http-mcp-adoption-and-stdio-non-support.md to adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md (1 occurrence(s))
  - adr_02_008_sqlite-4db-separation.md to adr_02_05_008_db-sqlite-4db-separation.md (1 occurrence(s))
  - adr_02_009_rag-fts5-text-separation.md to adr_02_06_009_rag-fts5-text-separation.md (1 occurrence(s))
  - adr_02_010_rag-fallback.md to adr_02_06_010_rag-fallback.md (1 occurrence(s))
  - adr_02_012_git-mcp-server-side-write-enforcement.md to adr_02_03_012_mcp-git-server-side-write-enforcement.md (1 occurrence(s))
  - adr_02_013_eventbus-authentication-authorization.md to adr_02_04_013_eventbus-authentication-authorization.md (1 occurrence(s))
  - adr_02_014_agent-control-plane-responsibility-boundaries.md to adr_02_02_014_agent-control-plane-responsibility-boundaries.md (1 occurrence(s))
  - adr_02_015_reference-document-class-disposition.md to adr_02_07_015_docs-reference-document-class-disposition.md (2 occurrence(s))
### Details
- 15 reference(s) to ADR file names; Reading Order table.

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
| 1 | Update the references and patterns | Pending | — | — | |
| 2 | Run the documentation checkers | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: issues/done/20261019-170548_adrname001_group-adr-file-names-by-theme.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-173513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-182330
- **Related target files**: docs/10_adr/adr_00_document-guide.md
