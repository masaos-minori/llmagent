## Goal
Refresh `docs/05_agent_13_reference-api.md`'s guarded block by running
`tools/generate_reference_table.py --type agent` (`REQ-001`, `REQ-005`).

## Scope
In scope: running the generator against this one target document. Out of scope:
any hand-edit of this file's content outside the guarded block; any change to
sections of this file the generator does not own.

## ⚠ Implementation gate — do not execute before this is satisfied
Same gate as seq 01 (`implementations/20260919-114740_01_tools_generate_reference_table_py.md`):
REQ-008 (ADR-015 Accepted/Option B; guard-detection fix landed). Additionally,
this row depends on seq 01's `generate_agent_reference_table()` existing and
being registered under `--type agent` first — this document's own change is
produced entirely by running that code, not by a direct text edit.

## Assumptions
- `docs/05_agent_13_reference-api.md`'s front matter (`title: "Agent Reference
  API — Part 1"`) is unchanged since the Plan was written — re-confirmed.
- No guarded block currently exists in this file (this is its first
  `<!-- AUTO-GENERATED -->` block) — the generator's own logic (see
  `tools/generate_reference_table.py`'s `__main__` block, lines 231-245) appends
  a new heading + guarded block when no existing guard markers are found, rather
  than replacing an existing one — re-confirm this branch is taken (not the
  replace-in-place branch) when actually running the tool.

## Design decisions
This row's "implementation" is purely operational (run a tool), not a text edit
— per `templates/implementation-procedure.md` Notes, the Target file is the file
the change lands in, even when the mechanism is a script rather than a manual
edit.

## Alternatives considered
N/A: the mechanism (running the generator) is fixed by `REQ-005`'s Acceptance
Criteria ("each new generator once (`--dry-run` and live)") — no alternative
implementation approach applies to this row.

## Implementation
### Target file
docs/05_agent_13_reference-api.md

### Procedure
1. Run `python tools/generate_reference_table.py --type agent --dry-run` and
   review the previewed table for plausibility (correct class/function names,
   no truncated signatures).
2. Run `python tools/generate_reference_table.py --type agent` (live) — this
   writes the guarded block into the file per seq 01's
   `generate_agent_reference_table()` implementation.

### Method
Tool invocation (`Bash` tool), not `Edit` — the actual text change is produced
by `tools/generate_reference_table.py`'s own file-write logic.

### Details
- No manual content is authored for this row — verify only that the resulting
  guarded block replaces or appends correctly and that no non-guarded content
  in the file is altered.
- If the generator's append-new-heading branch fires (per Assumptions above),
  confirm the new `## Server Port & Tool Reference (auto-generated)`-style
  heading (adapted for Agent, per `DOMAIN_HEADING["agent"]` from seq 01) reads
  sensibly at the point it was appended (end of file) — if it needs
  repositioning within the document for readability, that repositioning is a
  manual follow-up edit, tracked as a Plan Gap if discovered (not silently done
  here without flagging).

## Compatibility considerations
Only the guarded block (and, on first run, a new heading + block appended at
end-of-file) is affected — no other section of this file is touched by the
generator (confirmed: `tools/generate_reference_table.py`'s guard-replacement
logic only touches text between guard markers, or appends after existing
content when no markers exist).

## Security considerations
N/A: no credentials or network access; reads local `scripts/agent/*.py`, writes
local `docs/05_agent_13_reference-api.md`.

## Rollback considerations
`git checkout -- docs/05_agent_13_reference-api.md` reverts this row
independently.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` against the full `docs/`
  tree — confirm the new guarded block is NOT flagged (depends on seq 01 of
  `plans/done/20260919-104809_plan.md`'s guard-detection fix having landed —
  part of the same REQ-008 gate).
- `uv run python tools/check_docs_quality.py` / `check_docs_structure.py` — no
  new findings.

## Completion criteria
- `docs/05_agent_13_reference-api.md` contains a guarded block matching
  `generate_agent_reference_table()`'s current output.
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
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: generator output, no direct unit test on this doc — verified via seq 05's generator tests + this row's own dry-run/live comparison |
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
- **Requirement ID**: REQ-001, REQ-005 (agent generator; run and verify output)
- **Source issue**: issues/done/20260918-130225_docsref01_extend-generate_reference_table-for-agent-eventbus-memory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105034_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114740
- **Related target files**: docs/05_agent_13_reference-api.md
