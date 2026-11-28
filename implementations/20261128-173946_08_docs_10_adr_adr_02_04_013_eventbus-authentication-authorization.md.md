## Goal
- Name the new function in the `auth.py` line of the ADR-013 "Implementation References" list, with no decision change (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- Final procedure of the Plan: it also carries the validation run and the deploy hand-off.

## Assumptions
- Verified at the Plan's evidence revision (`tools/check_evidence_freshness.py check`: 23 unchanged, 0 changed).
- Sequencing (Step 2 overlap judgment): the admin TTL-precedence Plan (adrr001) is archived but its procedures are not yet executed; they edit `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`, and the ADR-013 Decision Detail 12. `plan_dependency_order.py` reports this Plan ready because adrr001 left `plans/`, but its procedures MUST be implemented first; re-read the target before editing. Line numbers are deliberately not cited.
- The `auth.py` line in "Implementation References" lists `attach_request_id_middleware()`, `require_role()`, `require_consumer_identity()` (checked at the Plan's evidence revision).
- The ADR is also edited by the admin TTL-precedence procedures (Decision Detail 12) and the invariant-coverage Plan (Automated Tests table); this edit is in a different section.

## Design decisions
- Append `publish_generation_if_current()` to that line only; no Decision Detail text changes.

## Alternatives considered
N/A: one-line list edit.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure
1. Add `publish_generation_if_current()` to the `scripts/eventbus/auth.py` bullet of "Implementation References".

### Method
- Keep the bullet's existing format (backticked names separated by commas).

### Details
- Decision Details 9 and 14 stay as they are; Decision Detail 15 already states the restart behavior.

## Compatibility considerations
N/A: list entry only.

## Security considerations
N/A: no credential content.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/generate_reference_table.py --check`, then `uv run python tools/run_validation_gates.py --full`.
- Deploy hand-off: `scripts/` changed (procedures 01 to 03), so commit and push first, then hand off to `skills/deploy/SKILL.md`; deploying is the user's decision (it has an approval gate).

## Completion criteria
- The bullet names the new function; the ADR checkers report no findings; the full gate run passes.

## Out of Scope
- Any decision text; the Automated Tests table (adrr003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Name `publish_generation_if_current()` in the `auth.py` bullet of `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Pending | — | — | |
| 2 | Run the ADR and documentation checkers, the full gate run, and the deploy hand-off | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (ADR component list names the new function)
- **Source issue**: issues/20261125-103308_adrr002_authz-publication-invariant.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172526_adrr002_authz-publication-invariant.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-173946
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
