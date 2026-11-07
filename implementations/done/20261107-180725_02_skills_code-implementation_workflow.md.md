## Goal

Add a fourth explicit exception to the "exactly once per cycle" full-suite rule in
`skills/code-implementation/workflow.md` Step 4 (REQ-002 / AC-002), so a batch of
procedures confined to one directory tree may share one full-suite run instead of running
the full suite once per cycle.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The owner has decided that a single-directory batch may share one full-suite run
  (recorded in the source issue's owner decision); this edit records the decided policy,
  it does not decide it.
- The existing three exceptions to "exactly once per cycle" remain valid: ordinary-failure
  re-run, conflict-detected case, and declared release unit.
- Targeted tests still run per cycle; only the full-suite run is shared. The shared run
  still feeds the coverage gate.
- The confinement condition is path-based: all target files of the batch are confined to one
  directory tree (e.g. `tools/` and `tests/tools/`), with no `scripts/` change. This matches
  the source issue's own example (UNK-01 resolved toward path-based scoping).

## Design decisions
- Add exactly one parallel bullet after the existing "third exception" (declared release
  unit) bullet, stating the single-directory batch exception and its conditions.
- Keep the four exceptions parallel in structure so they read as a set.

## Alternatives considered
- Keying the exception on a declared file list instead of changed paths: the source issue's
  UNK-01 left this open; resolved here toward path-based scoping (all target files in one
  directory tree). If the owner prefers a declared list, the executed doc is a one-line
  change.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
In Step 4, add a fourth exception bullet to the "exactly once per cycle" full-suite rule,
immediately after the existing "third exception" (declared release unit) bullet.

### Method
Edit the bullet list in place; do not alter the existing three exceptions or any other
Step.

### Details
The third exception currently ends with (approximately lines 451-452):
```
   For a declared release unit, the single run is the end-of-unit run (see Multi-file processing >
   Batch mode (release unit)); this is a third exception to "exactly once per cycle", scoped to a unit.
```
Append a fourth bullet directly after it:
```
   For a batch whose target files are all confined to one directory tree (e.g. `tools/` and
   `tests/tools/`) under the same Plan, with no `scripts/` change, the full-suite run is
   shared: one run at the end of the batch instead of one per cycle. Targeted tests still
   run per cycle, and this shared run feeds the coverage gate. This is a fourth exception to
   "exactly once per cycle", scoped to a single-directory batch.
```

## Compatibility considerations
N/A: a skill prose edit; no tool behavior, build, or shipped-artifact changes. The
exception is scoped to a single-directory batch and cannot apply to a mixed-directory batch.

## Security considerations
N/A: no security-relevant change; a workflow-gate wording update.

## Rollback considerations
N/A: revert the commit that makes this edit.

## Validation plan
- Run `uv run python tools/check_skills_references.py` to confirm every backtick-quoted
  `rules/`/`skills/` reference still resolves after the edit.
- Run `uv run python tools/check_skills_heading_cycles.py` to confirm no cross-file heading
  cycle was introduced.
- Run `uv run python tools/amend_plan.py --help` to confirm `--class` is still
  `fallout|scope` (REQ-003 / AC-003).

## Completion criteria
- `skills/code-implementation/workflow.md` Step 4 contains the new single-directory batch
  exception, stating its conditions (same Plan, all target files confined to one directory
  tree, no `scripts/` change, targeted tests still per cycle, shared run feeds the coverage
  gate), parallel to the other three exceptions.

## Out of Scope
- Changing the existing release-unit batch mode (`### Batch mode (release unit)`).
- Any change outside Step 4's "exactly once per cycle" rule.
- Editing documents beyond `skills/code-implementation/workflow.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the single-directory batch full-suite exception to `skills/code-implementation/workflow.md` (REQ-002) | Completed | — | 20261107-182300 |  |
| 2 | Add or update tests per Validation plan | N/A: docs-only, no tests | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261107-182300 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: this document is the documentation change | — | — |  |

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
- **Requirement ID**: `REQ-002` — allow a single-directory batch to share one full-suite run
- **Source issue**: `issues/20261106-123524_ownerdec001_amendment-policy-and-batch-test-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-175321_ownerdec001_amendment-policy-and-batch-test-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-180725
- **Related target files**: `skills/code-implementation/workflow.md`