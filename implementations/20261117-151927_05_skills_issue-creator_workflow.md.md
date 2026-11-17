## Goal

Replace the manual `mktemp` leftover snippet in `skills/issue-creator/workflow.md` Step 10.4 with the checker invocation, keeping the manual brace judgment (REQ-005 / AC-7).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Step 10.4 currently holds a `mktemp` shell snippet plus a manual placeholder search (verified 20261117); the checker-side leftover detection this replaces is delivered by the seq 01 document.
- `wftool005` also targets `skills/issue-creator/workflow.md` (row-level, gated behind this Plan's Phase 1); the batch runs one Plan at a time.

## Design decisions

- Keep the sentence that braces in the author's own content stay a manual judgment: the checker detects only the template's own placeholder lines (plan Decision 5).

## Alternatives considered

- Keep the snippet as a fallback: rejected — REQ-005 names the snippet for removal, and a skipped or mistyped snippet is exactly the gap this Plan closes.

## Implementation
### Target file
`skills/issue-creator/workflow.md`

### Procedure

- In Step 10.4, delete the `mktemp` snippet block and the manual placeholder-search instruction; state that the gate and the `workitem-structure` hook now run `uv run python tools/check_workitem_structure.py --file <path>` automatically on commit, and instruct the author to run the same command explicitly on the new issue file before the hand-off; keep the manual brace judgment sentence.

### Method

N/A: one step's prose and code block; no other step changes.

### Details

- The `<path>` wording here stays a human instruction — this file is not parsed for checker ids.

## Compatibility considerations

- Land after the seq 01 document so the leftover check the step now points to exists.

## Security considerations

N/A: workflow prose.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` report no finding (AC-7).
- Manual read: the step contains no `mktemp` block.

## Completion criteria

- AC-7: Step 10.4 no longer contains the snippet and names the checker invocation.

## Out of Scope

- Other steps of the workflow; the checker code and gate/hook rows (other documents of this plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the Step 10.4 snippet | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (Step 10.4 replaces the snippet with the checker call)
- **Source issue**: `issues/20261117-123330_wftool001_gate-workitem-structure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-124139_wftool001_gate-workitem-structure.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-151927
- **Related target files**: `skills/issue-creator/workflow.md`
