## Goal
Relocate `docs/00_governance_03_issue-and-uncertainty-management.md` to
`docs/00_governance/00_governance_03_issue-and-uncertainty-management.md` via `git mv`,
with no filename or content change, implementing `REQ-001`.

## Scope
In scope: the single `git mv` of this file. Out of scope: any content edit, any other
file's move (see the Plan's other 7 implementation procedure documents for those rows).

## Assumptions
- `git mv` preserves `git log --follow` history continuity for this same-content move.
- This is the highest-churn (44 commits) and most heavily depended-on of the 5 moved
  files — 3 tools already expect it at `docs/00_governance/`
  (`tools/check_needs_confirmation_inventory.py`'s `INVENTORY_DOC_PATH`,
  `tools/check_known_deviation_sync.py`'s `_GOVERNANCE_KNOWN_ISSUES_PATH`, and
  `tools/check_dependency_graph_cycles.py` reads `00_governance_01`, not this file —
  the relevant sibling here is the first two), landed by `docsreorg02`; a fourth tool,
  `tools/check_issue_inventory_conformance.py`, is fixed by this Plan's seq 07/08 rows
  (`REQ-003`/`REQ-004`), not by this row.

## Design decisions
None beyond the mechanical move itself. This row's move is what makes seq 07's fix
(`GOVERNANCE_DOC_PATH`) resolve to a real file for the first time, and what makes
`tests/tools/test_check_needs_confirmation_inventory.py::TestGovernanceMetaDocsCurrency::test_named_docs_exist_on_disk`
and
`tests/tools/test_check_dependency_graph_cycles.py::TestRealGraphIntegration::test_real_repo_graph_has_no_cycle`
(both recorded as expected-failing in `docsreorg02`'s Plan until this move lands) start
passing — but neither of those is a code change performed by this row; they are
downstream effects verified in Phase 3.

## Alternatives considered
- Plain filesystem `mv` + `git add`/`git rm`: rejected — the Plan's Constraints require
  `git mv` only.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Confirm the destination directory `docs/00_governance/` exists (created during seq
   01's cycle in this same pass; `mkdir -p docs/00_governance` if resuming out of order
   — this Git version does not auto-create an intermediate directory for `git mv`'s
   destination, verified during seq 01's cycle).
2. Run `git mv docs/00_governance_03_issue-and-uncertainty-management.md docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`.
3. Confirm the destination file exists, the source path no longer exists, and `git
   status` shows the change staged as a rename (status letter R).

### Method
Single Git CLI invocation; no code change, no content diff expected between source and
destination blob.

### Details
- Do not pass any other flag to `git mv` beyond the two paths.
- This file has 2 entries in `tests/tools/test_check_docs_quality.py`'s
  `EXPECTED_WITHIN_FILE_PAIRS` frozenset (both prefixed
  `00_governance_03_issue-and-uncertainty-management.md:`) — seq 06's procedure
  document updates those keys; this row does not touch the test file.

## Compatibility considerations
Bare-filename cross-references to this file from other `docs/*.md` files continue to
resolve after the move via `tools/check_docs_structure.py`'s basename index. Tools with
a hardcoded `DOCS_DIR / "00_governance" / ...` path constant (landed by `docsreorg02`,
and by this Plan's seq 07 row) begin resolving correctly only once this row lands.

## Security considerations
N/A: a file relocation with no content change carries no security-relevant surface.

## Rollback considerations
Revert with `git mv
docs/00_governance/00_governance_03_issue-and-uncertainty-management.md
docs/00_governance_03_issue-and-uncertainty-management.md`, or `git revert` the commit
containing this move if already committed. Reverting this row alone (without also
reverting seq 07/08) would re-break `tools/check_issue_inventory_conformance.py`'s
fixed default path — coordinate any rollback of this row with seq 07/08.

## Validation plan
- `git log --follow -- docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`
  shows continuous history through the move (Plan `AC-1`).
- Deferred to Phase 3: `uv run pytest tests/tools/ -q` confirming
  `TestGovernanceMetaDocsCurrency::test_named_docs_exist_on_disk` and
  `TestRealGraphIntegration::test_real_repo_graph_has_no_cycle` now pass (Plan `AC-2`);
  `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
  schemas/doc_front_matter.json` and `uv run python -m tools.check_docs_quality` (Plan
  `AC-3`, `AC-4`).

## Completion criteria
`docs/00_governance/00_governance_03_issue-and-uncertainty-management.md` exists;
`docs/00_governance_03_issue-and-uncertainty-management.md` no longer exists at the
flat path; the move is recorded as a Git rename.

## Out of scope
Any content edit to this file; any change to the other 4 moved files or any tooling
file (covered by this Plan's other implementation procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git mv docs/00_governance_03_issue-and-uncertainty-management.md docs/00_governance/00_governance_03_issue-and-uncertainty-management.md` | Completed | 20260924-122332 | 20260924-122332 | git mv succeeded as staged rename (git status: R). Corrected Procedure step 1: this Git version does not auto-create the destination directory for git mv -- required mkdir -p docs/00_governance first (adversarial verification finding, procedure corrected). |
| 2 | N/A: no test to add for a content-identical move | Completed | 20260924-122332 | 20260924-122332 | N/A: content-identical move, no test to add. |
| 3 | Confirm `git log --follow` continuity and staged rename status | Completed | 20260924-122332 | 20260924-122332 | git status confirms staged rename (R). Full git log --follow history continuity verification deferred until this change is committed (not part of this code-implementation cycle's scope per repository commit policy). |
| 4 | N/A: no documentation update beyond the move itself | Completed | 20260924-122332 | 20260924-122332 | N/A: no documentation update beyond the move itself; deferred cross-file validation runs once in Phase 3 (seq 06-08 remaining). |

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
- **Requirement ID**: `REQ-001` (git mv the 5 governance files into `docs/00_governance/`)
- **Source issue**: issues/20260923-140944_docsreorg05_move-governance-docs-into-new-governance-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-115855_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121124
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md