## Goal
- Regenerate the EventBus reference document so its `auth.py` table lists `publish_generation_if_current` (new) (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Verified at the Plan's evidence revision (`tools/check_evidence_freshness.py check`: 23 unchanged, 0 changed).
- Sequencing (Step 2 overlap judgment): the admin TTL-precedence Plan (adrr001) is archived but its procedures are not yet executed; they edit `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`, and the ADR-013 Decision Detail 12. `plan_dependency_order.py` reports this Plan ready because adrr001 left `plans/`, but its procedures MUST be implemented first; re-read the target before editing. Line numbers are deliberately not cited.
- The `auth.py` table of `docs/24_eventbus/eventbus_08_reference_api.md` is a guarded generated block (ADR-015 INV-01); it is never hand-edited.

## Design decisions
- Produced by the same generator run as procedure 06; run it once and review both diffs.

## Alternatives considered
N/A: generated output.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py` (or confirm procedure 06's run already updated this file).
2. Review `git diff docs/24_eventbus/eventbus_08_reference_api.md`: expect one added row under `scripts/eventbus/auth.py`.

### Method
- Stop and report on unrelated drift; do not hand-edit.

### Details
- English only; the row text comes from the docstring first line.

## Compatibility considerations
N/A: generated documentation.

## Security considerations
N/A: no credential content.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`; `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The table lists the new function and the generator check reports no drift.

## Out of Scope
- Hand edits; the manifest (procedure 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate and review `docs/24_eventbus/eventbus_08_reference_api.md` | Pending | — | — | |
| 2 | Run `uv run python tools/generate_reference_table.py --check` and the documentation gates | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (generated reference names the new function)
- **Source issue**: issues/20261125-103308_adrr002_authz-publication-invariant.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172526_adrr002_authz-publication-invariant.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-173946
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`
