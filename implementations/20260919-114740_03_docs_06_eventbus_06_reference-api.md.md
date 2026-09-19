## Goal
Refresh `docs/06_eventbus_06_reference-api.md`'s guarded block by running
`tools/generate_reference_table.py --type eventbus` (`REQ-002`, `REQ-005`).

## Scope
In scope: running the generator against this one target document. Out of scope:
any hand-edit of this file's content outside the guarded block.

## ⚠ Implementation gate — do not execute before this is satisfied
Same gate as seq 01/02: REQ-008 (ADR-015 Accepted/Option B; guard-detection fix
landed). Additionally depends on seq 01's `generate_eventbus_reference_table()`
existing and registered under `--type eventbus` first.

## Assumptions
- `docs/06_eventbus_06_reference-api.md`'s front matter (`title: "Event Bus:
  Reference API"`) is unchanged since the Plan was written — re-confirmed.
- No guarded block currently exists in this file — same append-new-heading
  branch consideration as seq 02.

## Design decisions
Same as seq 02: this row's "implementation" is running the tool, not a direct
text edit.

## Alternatives considered
N/A: same as seq 02 — mechanism fixed by `REQ-005`.

## Implementation
### Target file
docs/06_eventbus_06_reference-api.md

### Procedure
1. Run `python tools/generate_reference_table.py --type eventbus --dry-run` and
   review the previewed table.
2. Run `python tools/generate_reference_table.py --type eventbus` (live).

### Method
Tool invocation (`Bash` tool), not `Edit`.

### Details
- No manual content authored for this row — verify the guarded block correctly
  reflects `scripts/eventbus/*.py`'s current public surface and that no other
  section of the file is altered.
- Same append-vs-replace branch consideration as seq 02: if a new heading is
  appended at end-of-file and reads awkwardly in context, treat repositioning
  as a Plan Gap to flag, not a silent extra edit.

## Compatibility considerations
Only the guarded block (or a newly appended heading + block) is affected.

## Security considerations
N/A: no credentials or network access; reads local `scripts/eventbus/*.py`,
writes local `docs/06_eventbus_06_reference-api.md`.

## Rollback considerations
`git checkout -- docs/06_eventbus_06_reference-api.md` reverts this row
independently.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` against the full `docs/`
  tree — confirm the new guarded block is not flagged (depends on the
  guard-detection fix half of the REQ-008 gate).
- `uv run python tools/check_docs_quality.py` / `check_docs_structure.py` — no
  new findings.

## Completion criteria
- `docs/06_eventbus_06_reference-api.md` contains a guarded block matching
  `generate_eventbus_reference_table()`'s current output.
- `--dry-run` output matches the live-written content exactly.
- `tools/check_docs_content_policy.py` does not flag the new guarded block.

## Out of scope
Any hand-edit of this file's non-guarded content; executing before the REQ-008
gate clears.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Gated on REQ-008 and on seq 01 landing first |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: generator output, verified via seq 05's generator tests + this row's dry-run/live comparison |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `tools/check_docs_content_policy.py` + `tools/check_docs_quality.py`/`check_docs_structure.py` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own Target file IS the documentation being updated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | REQ-008 gate not satisfied — re-verified 20260919-121854: guard-detection fix has landed but ADR-015 is still `Proposed`, not `Accepted` (gate requires both); also depends on seq 01 landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-005 (eventbus generator; run and verify output)
- **Source issue**: issues/done/20260918-130225_docsref01_extend-generate_reference_table-for-agent-eventbus-memory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105034_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114740
- **Related target files**: docs/06_eventbus_06_reference-api.md
