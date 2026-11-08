## Goal
Correct both workflow-table lists in the deployment doc — the `setup_services.sh` pre-flight
responsibilities bullet and the `init_db.sh` responsibilities bullet — so they name all five
current tables including `tool_call_state` (`REQ-004`).

## Scope
**Release unit**: wfaudit003-full (Phase 2)

- Covers Plan `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md` row 5 only:
  `docs/90_deployment/deployment_01_deployment.md`, L165 and L300.
- Documentation-only change; no code or test edits.

## Assumptions
- Procedures `144827_02`/`144827_03` (the two shell mirrors) land with this document; the bullets
  describe the post-change pre-flight behavior of those scripts.
- Sibling procedures with lower seqs (`134201_*`, `135741_*`) do not target this file (verified
  via `check_plan_target_overlaps` output and the plans' target tables), so no sequencing
  dependency applies to this document.

## Design decisions
- Edit both bullets in place with a one-token list extension each: the bullets are operator-facing
  responsibility summaries of the scripts, so they must equal the scripts' constants.
- No restructure of the responsibilities lists; no addition of a fifth-script or gate internals
  narrative — the doc's deployment policy sections stay as-is.

## Alternatives considered
- Collapsing the two bullets into a single "required tables" definition elsewhere in the doc:
  rejected — the two bullets describe two different scripts in two different deploy phases; a
  shared definition would decouple the claims from the per-script responsibility framing the
  section is built on.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md` — L165 (setup_services pre-flight bullet) and
L300 (init_db.sh responsibilities bullet).

### Procedure
Extend both table lists.

### Method
Replace L165:

> - Re-checks that `workflow.sqlite` exists with all required tables (`tasks`, `attempts`,
>   `processed_events`, `artifacts`); it performs no schema-version comparison

with:

> - Re-checks that `workflow.sqlite` exists with all required tables (`tasks`, `attempts`,
>   `processed_events`, `artifacts`, `tool_call_state`); it performs no schema-version comparison

and replace L300:

> - Creates `workflow.sqlite` and its mandatory tables (tasks, attempts, processed_events,
>   artifacts)

with:

> - Creates `workflow.sqlite` and its mandatory tables (tasks, attempts, processed_events,
>   artifacts, tool_call_state)

### Details
- Two single-list extensions; surrounding bullets stay untouched.

## Compatibility considerations
- N/A: documentation-only change. `wfaudit010`'s doc edits confirmed no deployment doc describes
  `execution_snapshots` as required.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- Reverting this document alone is safe; the `REQ-004` acceptance grep over `docs/90_deployment`
  would flag the stale four-table forms if procedures 02/03 land without it.

## Validation plan
- Docs checkers per `routing.md`:
  - `uv run python tools/check_docs_quality.py`
  - `uv run python tools/check_docs_structure.py docs/90_deployment/deployment_01_deployment.md`
  - `uv run python tools/check_docs_consistency.py --domain deployment`
- Acceptance grep: `grep -rn "tasks.*attempts.*processed_events.*artifacts" docs/41_db docs/90_deployment`
  shows only five-table forms after procedures 04-07 land.

## Completion criteria
- Both bullets list five tables; docs checkers exit 0; no four-table form remains in
  `docs/90_deployment`.

## Out of Scope
- The other responsibilities bullets in both lists, deploy script behavior itself (procedures
  02/03), and the `docs/41_db` rows (procedures 04-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-072224 | 20261109-072224 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261109-072224 | 20261109-072224 | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-072224 | 20261109-072224 | Docs checkers |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-072224 | 20261109-072224 | This document is the documentation change |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261107-203216_wfaudit003_schema-gate-table-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-144827
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`