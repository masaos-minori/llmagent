## Goal
Update the GV-016 matrix row (Timing / Gate / Follow-up) in `docs/00_governance/governance_04_documentation-checks.md` so it states the owner's decided trigger and gate for `check_metadata_field_policy.py`.

## Scope
- Modify only the GV-016 row (line 332) of the Verification Matrix in `docs/00_governance/governance_04_documentation-checks.md`: its `Timing`, `Gate`, and `Follow-up` cells.
- Do not change the checker's logic or permitted field sets, any other rule's row, gate, timing, or blocking status.

## Assumptions
- The owner's trigger + gate decision is recorded before this executes (Plan REQ-001); this procedure documents every branch so either can be applied once decided.
- The live corpus has 0 findings (measured during planning), so a new gate will not fail on existing content.
- Wording stays present-tense per the Current-Specification-Only Policy.

## Design decisions
- Change only the GV-016 row's Timing/Gate/Follow-up cells; leave every other column (Rule, Doc, Method, Tool/Review, Status) and every other rule untouched.
- Document all four branches here because the owner decision gates which one executes.

## Alternatives considered
- Editing only the matrix and not `routing.md` / `TOOL_DESCRIPTIONS.md`: rejected, the trigger must be stated consistently across all three (Acceptance Criteria).
- Inferring the owner's decision: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Confirm the owner's trigger + gate decision is recorded (REQ-001). If absent, stop and report; do not infer.
2. Edit the GV-016 row (L332) to match the decided branch:
   - **Routing-only**: `Timing = Periodic`, `Gate = Warning`, `Follow-up = "Run per routing.md 'When to run which tool'"`.
   - **Warning automation**: `Timing = PR` or `Pre-commit`, `Gate = Warning`, `Follow-up = "Run by <pre-commit/CI> (warning, non-blocking)"`.
   - **Blocking automation**: `Timing = PR`, `Gate = Error`, `Follow-up = "Run by <pre-commit/CI>; requires --strict (see REQ-004)"` — only if the owner signed off a blocking gate.
   - **Keep manual**: `Timing = Periodic`, `Gate = Warning`, `Follow-up = "Intentionally periodic and unwired; run by hand"`.
3. Confirm the wording is consistent with the `routing.md` and `TOOL_DESCRIPTIONS.md` changes.

### Method
- Locate the GV-016 row by Rule ID at line 332 (currently `... Periodic | Warning | Existing | Not run by CI or pre-commit`).
- Replace the `Timing`, `Gate`, and `Follow-up` cells with the decided values; preserve the row's column order and the surrounding matrix.

### Details
- The current `Follow-up` text "Not run by CI or pre-commit" MUST be replaced unless "keep manual" is the decided state, in which case it becomes an explicit design choice ("intentionally unwired").
- A `Gate = Error` (blocking) cell is valid ONLY when a working `--strict` exists; the checker currently has no `--strict` (registers only `--root`; unknown flags exit 2), so a blocking gate needs explicit owner sign-off per `rules/coding.md` before this cell is used.

## Compatibility considerations
- Downstream plans reference `governance_04` as the verification contract; keeping the GV-016 row accurate maintains a self-consistent contract.

## Security considerations
N/A: documentation-only update of a governance matrix row; no code, secrets, or access changes.

## Rollback considerations
N/A: revert the commit that edits `governance_04_documentation-checks.md`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Docs quality / structure / content policy | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` | Pass |
| Manual | GV-016 Timing/Gate/Follow-up matches the recorded decision | Manual review | Matches REQ-001 decision |

## Completion criteria
- The GV-016 row's Timing/Gate/Follow-up cells match the owner's recorded decision.
- "Not run by CI or pre-commit" is gone unless "keep manual" was decided and stated as a design choice.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` pass.
- No other rule's row, gate, timing, or status changed.

## Out of Scope
- Changing the checker's logic or permitted field sets.
- Wiring other tools. Remediating findings beyond what is needed to keep a new gate green.
- Changing another rule's gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the GV-016 matrix Timing/Gate/Follow-up cells per the recorded owner decision | Pending | — | — | Branch selected by owner decision (REQ-001) |
| 2 | Run the docs quality/structure/content-policy checks | Pending | — | — | check_docs_quality.py, check_docs_structure.py, check_docs_content_policy.py |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner trigger/gate decision not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` — update the GV-016 matrix row (Timing/Gate/Follow-up) to match the decided trigger
- **Source issue**: `issues/20261021-100307_gv016_decide-whether-to-wire-the-gv-016-metadata-field-policy-check-into-automation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-122245_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-133341
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
