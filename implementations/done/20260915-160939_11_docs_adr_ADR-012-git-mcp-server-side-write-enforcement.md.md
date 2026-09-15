## Goal
Remove ADR-012's redundant file/class/config/test list from `## Implementation
Notes` once reconciled into `### Implementation References`, per `REQ-011`.

## Scope
- In scope: reconcile 3 missing files (`git_service.py`, `git_server.py`,
  `git_models.py`) with their symbols, plus 2 currently-unpaired symbols
  (`RepositoryState.snapshot()`, `WriteProtectionPipeline.run()`), plus all 6
  cited test files, into References; delete the Notes list; insert the one-line
  pointer.
- Out of scope: this ADR's own pre-existing `## Known Deviations` section
  (lines 209-213) — untouched, unrelated to this row's edit.

## Assumptions
- The one-line pointer is used verbatim.
- The 6 test file paths were not independently `ls`-verified during Plan creation
  (`UNK-03`) — verify them in this procedure before adding to References.

## Design decisions
- References currently lists only 3 of the 6 files Notes cites
  (`repository_state.py`, `git_security.py`, `format_output.py`) — `git_service.py`,
  `git_server.py`, `git_models.py` are entirely absent, along with their symbols.
  This is a substantial reconciliation gap, not a minor omission — confirmed via
  `ls` that all three files exist.

## Alternatives considered
- N/A — straightforward addition of confirmed-existing, currently-missing
  entries.

## Implementation
### Target file
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   201-203 and References at 245-247 (this ADR's own `## Known Deviations` at
   209-213 is unaffected and unrelated).
2. Re-confirm via `ls scripts/mcp_servers/git/git_service.py
   scripts/mcp_servers/git/git_server.py scripts/mcp_servers/git/git_models.py`
   that all three still exist and are still absent from References.
3. Verify all 6 test files exist via `ls`; correct paths if stale.
4. Add `scripts/mcp_servers/git/git_service.py` — `GitService.get_dispatch_table()`
   to References.
5. Add `scripts/mcp_servers/git/git_server.py` — `call_tool()` endpoint, audit
   logging to References.
6. Add `scripts/mcp_servers/git/git_models.py` — `GitConfig`, request models to
   References.
7. Update References' existing `repository_state.py` bullet to also include
   `RepositoryState.snapshot()` and `WriteProtectionPipeline.run()` (currently
   only `RepositoryState`, `WriteProtectionPipeline` are named without their
   specific methods).
8. Add the 6 verified test files to References as a new bullet.
9. Delete the Notes list (lines 201-203: Implementation files / Key symbols /
   Corresponding tests).
10. Insert: "See Related Documents > Implementation References for the current
    file/symbol list."

### Method
Use `Edit` (exact-string replacement) — one call per step 4-10.

### Details
- Do not touch this ADR's `## Known Deviations` section (209-213) at all.
- Re-confirm `GitService.get_dispatch_table()` still exists via `grep` before
  adding it as a specific method citation.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` if
validation fails.

## Validation plan
- `ls scripts/mcp_servers/git/{git_service,git_server,git_models}.py` — all 3 must resolve.
- `ls <each of the 6 test files>` — all must resolve before adding.
- Manual diff: confirm References includes all 6 files with symbols and all 6 tests; confirm Notes list removed.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- References includes all 6 files (`repository_state.py`, `git_security.py`,
  `git_service.py`, `format_output.py`, `git_server.py`, `git_models.py`) with
  their symbols, and all 6 test files.
- `## Implementation Notes` contains only the one-line pointer plus boilerplate.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- This ADR's `## Known Deviations` section.
- Any other section of ADR-012.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-163244 | Verified all 6 test paths exist (UNK-03 resolved); reconciled 3 missing files + symbols + tests into References; deleted Notes list; inserted pointer |
| 2 | Add or update tests per Validation plan | Completed | 20260915-163244 | 20260915-163244 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-163244 | 20260915-163244 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 1 pre-existing unrelated finding, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-163244 | 20260915-163244 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-011 — reconcile 3 missing files + symbols + 6 tests, delete Notes list
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md