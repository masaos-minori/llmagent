## Goal
Correct the stale `--strict` documentation claims for `tools/check_metadata_field_policy.py` in `tools/TOOL_DESCRIPTIONS.md` so they reflect the actual report-only-by-default behavior (unknown flags such as `--strict` are rejected by argparse at exit 2, never exit 1).

## Scope
- Edit the `check_metadata_field_policy.py` row in `tools/TOOL_DESCRIPTIONS.md` (line 97) to remove the "`--strict` exits 1" claim and state the true report-only-by-default behavior.
- Optionally update the documented trigger wording if the owner's decision adds an automated trigger (REQ-002).
- Do not modify the checker's source, any other tool's row, or the module docstring here (the docstring correction is covered by REQ-004 too — see Details).

## Assumptions
- The owner's trigger decision is recorded before this executes (Plan REQ-001); the `--strict` correction stands regardless of the automation decision.
- The live corpus has 0 findings.

## Design decisions
- Correct only the inaccurate `--strict` claim; leave the rest of the row's description intact.
- Keep the description present-tense and factual about exit behavior.

## Alternatives considered
- Inferring the owner's decision and rewriting the trigger wording beyond the `--strict` fix: the trigger wording change belongs to the REQ-002 automation branch; this procedure focuses on the REQ-004 `--strict` correction and notes where trigger wording may also change.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the `check_metadata_field_policy.py` row (line 97).
2. Replace the "`--strict` exits 1" clause with the correct behavior: the checker is report-only by default (warnings, exit 0); `--strict` is NOT implemented and argparse rejects it (exit 2).
3. If the owner decided an automated trigger, align the trigger wording with the `routing.md` / `governance_04` changes (REQ-002); otherwise leave the trigger wording as the manual/periodic state.
4. Leave every other tool row untouched.

### Method
- `sed`/edit line 97: change "`Warning` (report-only by default; `--strict` exits 1)" to "`Warning` (report-only by default; `--strict` is not implemented — argparse rejects unknown flags at exit 2)".
- Cross-check against `tools/check_metadata_field_policy.py` `main()` (registers only `--root`) and `report_and_exit()`.

### Details
- The same stale `--strict` claim appears in the checker's module docstring (`tools/check_metadata_field_policy.py`, near line 19) and possibly in the source issue text; REQ-004 covers correcting the docstring too, but that file is NOT a listed Implementation Target File here — if executing the REQ-004 docstring correction, treat it as an additional-target-file discovery and stop for a Plan amendment, OR scope this procedure's `tools/TOOL_DESCRIPTIONS.md` edit only. Per the frozen inventory, only `tools/TOOL_DESCRIPTIONS.md` is a target; the docstring correction is flagged for owner/plan clarification.
- `check_tool_descriptions_sync.py` cross-checks this file against the actual `tools/*.py`, so the corrected wording must match the real exit behavior.

## Compatibility considerations
- `check_tool_descriptions_sync.py` validates this file against the live tools; the correction keeps them in sync.

## Security considerations
N/A: documentation-only wording correction; no code, secrets, or access changes.

## Rollback considerations
N/A: revert the commit that edits `tools/TOOL_DESCRIPTIONS.md`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Tool-description sync | `uv run python tools/check_tool_descriptions_sync.py` | Pass |

## Completion criteria
- The `--strict` "exits 1" claim is removed and replaced with the correct report-only-by-default / exit-2-on-unknown-flag behavior.
- `check_tool_descriptions_sync.py` passes.
- No other tool row changed.

## Out of Scope
- Modifying the checker's source or docstring (additional-target-file; requires Plan amendment).
- Deciding or wiring the automated trigger (REQ-002 automation branches).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the stale `--strict` claim in the `check_metadata_field_policy.py` row | Pending | — | — | Applies regardless of automation decision (REQ-004) |
| 2 | Run check_tool_descriptions_sync.py | Pending | — | — | Must match real exit behavior |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Docstring correction in `check_metadata_field_policy.py` is outside the frozen target set | N/A: additional-target-file clarification needed | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` — correct the stale `--strict` documentation claims in `tools/TOOL_DESCRIPTIONS.md`
- **Source issue**: `issues/20261021-100307_gv016_decide-whether-to-wire-the-gv-016-metadata-field-policy-check-into-automation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-122245_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-133341
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
