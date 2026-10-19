## Goal
- Rename ADR-005 to its grouped file name and update the ADR file name references inside it (`REQ-001` (rename the ADR files), `REQ-002` (replace old ADR file names)).

## Scope
- In scope: `docs/10_adr/adr_02_005_rag-source-derived-index-relationships.md` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- Rename with `git mv` so `git log --follow` keeps history.
- Only names change; the equivalence check (old content with names replaced equals new content) proves it.

## Alternatives considered
- Use `tools/rename_doc.py --apply`: rejected as the only mechanism, because it reports `../10_adr/` links as unresolved and does not rewrite prose mentions (Plan Problem).

## Implementation
### Target file

`docs/10_adr/adr_02_005_rag-source-derived-index-relationships.md`

### Procedure
1. Run `git mv docs/10_adr/adr_02_005_rag-source-derived-index-relationships.md docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` (new).
2. Apply the exact-basename replacement of the 14 old ADR file names to this file only (the shared throwaway script in the Plan Design section, restricted to this path; dry run first, then write); the names are unique tokens, so links, `related:` entries, and prose are all covered and link style is unchanged.
### Method
Old to new names found in this file (count of occurrences, measured 2026-10-19):
  - adr_02_002_config-isolation.md to adr_02_01_002_platform-config-isolation.md (1 occurrence(s))
  - adr_02_004_environment-failure-handling-policy.md to adr_02_01_004_platform-environment-failure-handling-policy.md (1 occurrence(s))
### Details
- ADR-005 belongs to group rag in the registry. The ADR ID, status, decisions, invariants, and content stay unchanged; only names change. After the replacement, record the file size (`wc -c`) for the size ceilings.

## Compatibility considerations
- Inbound links from other files are updated by the other rows of this Plan in the same commit; `adr_00` and `adr_01` file names are unchanged.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit (git restores the old names).

## Validation plan
- `uv run python tools/check_docs_structure.py` and `uv run python tools/check_adr_structure.py`
- Equivalence check for this file (Plan Validation plan).

## Completion criteria
- The file exists under the new name and not under the old name.
- Old content with the 14 names replaced equals the new content.

## Out of Scope
- Modifying any file other than the target file; ADR decisions, IDs, status, and invariants; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename with git mv | Pending | — | — | |
| 2 | Replace the old ADR file names inside the file | Pending | — | — | |
| 3 | Run the equivalence check and the documentation checkers | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: issues/done/20261019-170548_adrname001_group-adr-file-names-by-theme.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-173513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-182330
- **Related target files**: docs/10_adr/adr_02_005_rag-source-derived-index-relationships.md
