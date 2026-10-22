## Goal
Define the meaning and allowed values of the `Blocking` field in Part 2 of `governance_03` and give NC-041 a valid value (REQ-002: "Blocking Values" definition; REQ-003: NC-041 value; REQ-001: owner decision gate).

## Scope
- Add a "Blocking Values" section after "Priority Values" in Part 2 and set NC-041's `Blocking` value.
- No other NC-041 field changes; Part 3 and Part 4 are untouched.

## Assumptions
- The owner has chosen Option A (the `Blocking` value names the NC item this entry blocks, or `None`); this is gate step 1 of the Plan: if the decision is Option B or another definition, stop and amend the Plan before editing (Plan UNK-01).
- The checker change in the sibling procedure accepts the exact value `None`; this procedure must not land before it, or NC-041 would produce a warning.
- The `Related NC` field already uses `None` as its "no value" convention (verified in NC-041).

## Design decisions
- Section content (current behavior, no history): a known NC id names the item this entry blocks; `None` records that the entry was assessed and blocks no other item; an empty value means not yet assessed. The Part 3 `Blocking` / `Non-blocking` vocabulary does not apply to this field.
- NC-041's `Blocking` becomes `None`.

## Alternatives considered
- Option B (release/deployment classification): not chosen, it requires a checker migration and owner needs for release gating (Plan UNK-01, UNK-02).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Confirm the owner's decision is recorded (gate); stop if it is not Option A.
2. Insert "### Blocking Values" between "### Priority Values" and "### Extraction Process" with the three bullets (NC id, `None`, empty) in the style of the Status and Priority sections.
3. Change NC-041's `- **Blocking:**` line to `- **Blocking:** None`.

### Method
- Minimal in-place edits; re-read the file before editing (the Configuration Drift procedure edits Part 4 and NC-041's Resolution Target of the same file; apply sequentially).
- Do not alter any other NC-041 field or its evidence.

### Details
- Keep the heading level and the "- **value** — meaning" bullet style used by the neighbouring value sections.
- No counts, no implementation detail.

## Compatibility considerations
N/A: documentation only; the sibling tool procedure keeps the checker consistent with this definition.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py` (no `Blocking` warning for NC-041), `check_issue_inventory_conformance.py`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- Part 2 defines the meaning, allowed values, and the empty (not assessed) case; NC-041's `Blocking` is `None`; no other NC-041 field differs; checkers pass.

## Out of Scope
- Deciding the `github` outcome, release-impact recording (Plan UNK-02), and any other inventory schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the owner's decision on the `Blocking` semantics (gate) | Completed | 20261022-115448 | 20261022-115448 | Owner decision recorded: Option A, confirmed by the user in this session |
| 2 | Add the "Blocking Values" section and set NC-041's `Blocking` | Completed | 20261022-115448 | 20261022-115448 | Changed: docs/00_governance/governance_03_issue-and-uncertainty-management.md |
| 3 | Run the inventory and documentation checkers | Completed | 20261022-115448 | 20261022-115448 | validated; full suite 9689 passed, 14 skipped; ruff, mypy, bandit on edited tools pass; docs checkers pass |

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
- **Requirement ID**: `REQ-001` (owner decision gate), `REQ-002` (Blocking Values definition), `REQ-003` (NC-041 value)
- **Source issue**: `issues/20261021-104533_blockingdef_define-the-blocking-field-in-the-needs-confirmation-inventory.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094758_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101832
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md