## Goal
Keep the tool-inventory description of `tools/check_docs_consistency.py` in sync in `tools/TOOL_DESCRIPTIONS.md` if the mechanical branch (this Plan) adds a documented capability (report-only detection of bare snake_case names and/or non-`_db_path` config keys).

## Scope
- Modify exactly `tools/TOOL_DESCRIPTIONS.md`: update the `check_docs_consistency.py` inventory entry to reflect any new capability added by the mechanical branch.
- Only change this if a capability was actually added/changed (i.e. the mechanical branch executed). If the owner recorded an accepted limit, leave this file unchanged.

## Assumptions
- The owner's decision is recorded before this executes (Plan REQ-001); this documents the "tool changed" sub-case so it can be applied once decided.
- Wording stays present-tense per the Current-Specification-Only Policy.

## Design decisions
- Update only the `check_docs_consistency.py` inventory line(s); do not touch other tool entries.
- Mirror the capability wording so CI's tool-description sync stays consistent.

## Alternatives considered
- Editing the tool's own help/docstring here: out of scope — that is `check_docs_consistency.py` (this row documents the inventory only).
- Inferring the owner's decision: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Confirm the owner's decision is recorded (REQ-001) and the mechanical branch executed (REQ-003). If absent, stop and report; do not infer.
2. If a capability was added to `check_docs_consistency.py`, update its inventory entry in `tools/TOOL_DESCRIPTIONS.md` to describe the new report-only identifier-matching scope.
3. Run `check_tool_descriptions_sync.py` to confirm the inventory matches the tool.

### Method
- Locate the `check_docs_consistency.py` entry in the tool inventory. Append/adjust the capability description to mention detection of bare snake_case references and/or non-`_db_path` config keys at Warning level. Preserve the rest of the inventory.

### Details
- Verified at planning time: `tools/TOOL_DESCRIPTIONS.md` exists as the tool inventory. This row fires only when the mechanical branch changes a documented capability; if the accepted-limit branch is chosen, leave this file unchanged. If implementing requires a file not listed in `Implementation Target Files`, that is an additional-target-file discovery — stop and report `Blocked`.

## Compatibility considerations
- Downstream plans reference `TOOL_DESCRIPTIONS.md` as the tool inventory; keeping it accurate maintains a self-consistent contract.

## Security considerations
N/A: documentation-only inventory update; no code, secrets, or access changes.

## Rollback considerations
N/A: revert the commit that edits `TOOL_DESCRIPTIONS.md`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Tool-description sync | `uv run python tools/check_tool_descriptions_sync.py` | Pass |

## Completion criteria
- The `check_docs_consistency.py` inventory entry reflects the new capability (if one was added).
- `check_tool_descriptions_sync.py` passes.
- No other tool entry changed.

## Out of Scope
- Changing any other tool's inventory entry.
- Editing `check_docs_consistency.py` itself (that is the tool row).
- Executing when the accepted-limit branch was chosen.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `check_docs_consistency.py` inventory entry if a capability was added | Pending | — | — | Only if the mechanical branch executed (REQ-001) |
| 2 | Run `check_tool_descriptions_sync.py` | Pending | — | — | Depends on step 1 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (mechanical / accept-limit) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` — keep `tools/TOOL_DESCRIPTIONS.md` in sync with the extended `check_docs_consistency.py` capability
- **Source issue**: `issues/20261021-100351_identmatch_extend-identifier-matching-to-snake_case-names-and-config-keys-in-docs-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-125149_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-135205
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
