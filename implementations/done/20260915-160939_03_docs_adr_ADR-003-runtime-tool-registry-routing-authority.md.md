## Goal
Remove ADR-003's redundant file/class/config/test list from `## Implementation Notes`
once reconciled into `### Implementation References`, per `REQ-003`.

## Scope
- In scope: reconcile `scripts/shared/mcp_health.py` (`McpServerHealthRegistry`) and
  `scripts/shared/tool_executor.py` (`ToolExecutor`) — both currently marked
  "参照のみ" (reference-only) in Notes — plus the 2 cited test files, into
  References; delete the Notes list; insert the one-line pointer.
- Out of scope: any other ADR-003 content.

## Assumptions
- The one-line pointer is used verbatim, per the Plan's Assumptions.
- The 2 test file paths were not independently `ls`-verified during Plan creation
  (`UNK-03`) — verify them in this procedure.

## Design decisions
- "参照のみ" (reference-only) items in Notes are still genuine file/symbol
  citations that duplicate what References should contain — their exclusion from
  References today is the discrepancy this row fixes, not an intentional
  convention to preserve.

## Alternatives considered
- Treat "参照のみ" markings as a signal these two items should NOT be added to
  References (i.e., they are deliberately reference-only and excluded) — rejected;
  nothing in the ADR's text explains this as an intentional exclusion rule, and the
  issue's own reconciliation principle treats any Notes-only citation as a gap to
  close, not a convention to honor absent explicit justification.

## Implementation
### Target file
`docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   404-423 and References at 492-496 (content may have shifted since this
   procedure was generated).
2. Verify `tests/...` (the 2 cited test files) exist via `ls`; correct paths if
   stale before proceeding.
3. Add `scripts/shared/mcp_health.py` — `McpServerHealthRegistry` to References.
4. Add `scripts/shared/tool_executor.py` — `ToolExecutor` to References.
5. Add the 2 verified test files to References.
6. Delete the Notes list (the nested sub-bullets under the 4 category headers,
   lines 404-423).
7. Insert: "See Related Documents > Implementation References for the current
   file/symbol list."

### Method
Use `Edit` (exact-string replacement) — one call per step 3-7.

### Details
- Re-confirm `McpServerHealthRegistry` and `ToolExecutor` still exist at these
  file paths via `grep` immediately before editing, not from memory of this
  document alone.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` if
validation fails.

## Validation plan
- `ls scripts/shared/mcp_health.py scripts/shared/tool_executor.py` — both must resolve.
- `ls <the 2 test files>` — both must resolve before adding.
- Manual diff: confirm Notes list removed, pointer inserted, References includes the 2 new files/symbols and 2 tests.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- `## Implementation Notes` contains only the one-line pointer plus boilerplate.
- `### Implementation References` includes `mcp_health.py`, `tool_executor.py`, and both test files.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- Any other section of ADR-003.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-162506 | Reconciled mcp_health.py/tool_executor.py+tests; ALSO found and fixed a gap the procedure did not flag: config/agent.toml + tool_constants.py config citations were about to be lost, migrated to References before deleting Notes list |
| 2 | Add or update tests per Validation plan | Completed | 20260915-162506 | 20260915-162506 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-162506 | 20260915-162506 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 10 pre-existing unrelated findings, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-162506 | 20260915-162506 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-003 — reconcile mcp_health.py/tool_executor.py + tests, delete Notes list
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-003-runtime-tool-registry-routing-authority.md