# Implementation Procedure: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md

## Goal
Residual sweep of sections 8c-11: remove migration-era policy content that compatrm001's core
rewrite does not claim (migration contract text, CLI contract, "Removal condition: Never" policy
table, minimum-supported-schema policy).

## Scope
- Target file: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (MODIFY,
  residual sweep after compatrm001's rewrite).
- Release unit: `policy-finalization`.
- Related requirement / acceptance criteria: REQ-002, REQ-005, REQ-006 / AC-004 (frozen target
  row 12).

## Assumptions
- Ownership split verified at freeze: compatrm001 owns §8 intro (lines 27-30 area), the
  Migration guarantees subsection (lines 56-69), and the core rewrite; this document owns the
  residual sections 8c-11 — subsection 8e (lines 80-99, policy table at 84-86) and §9-11.
- Edits execute strictly after compatrm001's procedure for this file lands; line numbers are
  pre-rewrite anchors and must be re-located by section heading at execution time.

## Design decisions
- Section retitle is out (filename/title changes are a doc-scope decision, not this residual
  sweep); instead §8-§11 narrative shifts to: current-only contract, schema scaling without
  version migration, and one clearly-marked historical subsection describing what was removed.
- The "Removal condition: Never" policy table (84-86) is deleted — it describes retention of
  machinery that no longer exists.
- Minimum-supported-schema policy is replaced by exact-match policy wording.

## Alternatives considered
- Claiming the whole document under compatrm001: rejected at plan level (frozen overlap judgment:
  compatrm001's rewrite is section-scoped); duplication would create merge conflicts.

## Implementation

### Target file
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (MODIFY).

### Procedure
1. Re-locate residual sections by heading after compatrm001's edit: subsection 8e onward.
2. Rewrite 8e (former lines 80-99): migration-contract text becomes the exact-match startup
   contract; delete the policy table rows that promise permanent migration retention.
3. §9: CLI contract — remove the migration CLI usage (`migrate_db.py` era, already marked as
   removed history by compatrm001's section); describe only the canonical creation path.
4. §10-§11: scaling / minimum-supported-version policy rewritten to exact-match policy; any
   historical reference keeps a marker word on or above the line.
5. Whole-file sweep for the five doc-claim phrases and the retired names in REQ-001 consolidated
   set.

### Method
- Heading-anchored edits (line numbers shift after prerequisite rewrite); checker doc-claim pass.

### Details
- If compatrm001's rewrite already deleted one of the target passages, skip it and note the skip
  in Execution Status — do not re-add content just to delete it.

## Compatibility considerations
- Strictly sequenced after compatrm001's edit of the same file (frozen Assumptions judged the
  overlap compatible: disjoint sections).

## Security considerations
- None.

## Rollback considerations
- Single-file revert; sequencing means rollback should also restore compatrm001's state only if
  reverting the whole unit.

## Validation plan
- Checker blocking run exit 0; docs consistency CI; structure checker for db docs.

## Completion criteria
- No live migration contract/CLI/policy text remains in §8c-§11; historical mentions marked;
  checker green.

## Out of Scope
- §8 intro and Migration guarantees subsection (owned by compatrm001).

## Execution Status
| Step | Status | Notes |
|---|---|---|
| 1 Locate residuals post-001 | Pending | heading-anchored |
| 2 Rewrite 8e + table deletion | Pending | |
| 3 §9 CLI contract | Pending | |
| 4 §10-§11 policy rewrite | Pending | |
| 5 Sweep | Pending | |

### Blocker Log
- None. (Dependency note: blocked until compatrm001's procedure for this file executes — planned
  sequencing, not an incident.)

### Work Items Created
- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-005, REQ-006 / AC-004
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
