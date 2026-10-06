## Goal

Update the repeated ADR canonical header order in `skills/python-refactoring/path-c.md`
so its `Related Documents` token becomes `Related ADRs` then `Implementation References`,
matching the corrected `governance_01` list (`REQ-001`: no stale copy of the old ADR
header list remains; AC-1).

## Scope

- **In-Scope**: the single ordered ADR header list embedded in `path-c.md` (plan line
  153 area): replace `Related Documents` with `Related ADRs`, `Implementation References`.
- **Out-of-Scope**: any other text in `path-c.md`; the `Change History` token stays as-is
  (not part of this change).

## Assumptions

- Only the `Related Documents` token changes; every other header (including `Change
  History`) is preserved exactly.

## Design decisions

- Replace the one token in-place, preserving surrounding order and the parenthetical
  context `[Problem, Constraints]` etc.

## Alternatives considered

- Reconciling `Change History` with `governance_01`'s list (which omits it) — rejected:
  out of scope; the plan changes only the `Related Documents` token here.

## Implementation

### Target file

`skills/python-refactoring/path-c.md`

### Procedure

In the canonical header-order sentence, replace `..., Approval, Related Documents,
Change History, Completion Checklist.` with `..., Approval, Related ADRs, Implementation
References, Change History, Completion Checklist.`

### Method

`rg -n "Related Documents" skills/python-refactoring/path-c.md` to locate the token, then
edit it in place. Confirm exactly one occurrence and that `Change History` is preserved.

### Details

- Current (plan line 153): `..., Approval, Related Documents, Change History, Completion
  Checklist.`
- New: `..., Approval, Related ADRs, Implementation References, Change History,
  Completion Checklist.`

## Compatibility considerations

- This list mirrors `governance_01`'s ADR header standardization. Its `Related ADRs` /
  `Implementation References` order must match that file's new list.

## Security considerations

N/A: documentation text only.

## Rollback considerations

One-token edit in one skill file; revert the edit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `path-c.md` header list | Documentation review | Read the header-order sentence | Shows `Related ADRs` then `Implementation References`; `Change History` preserved; no `Related Documents` token |

## Completion criteria

- The ADR header-order list in `path-c.md` shows `Related ADRs` then `Implementation
  References` before `Change Checklist`/`Completion Checklist`, with no `Related
  Documents` token.

## Out of scope

- Other skill files, governance files, the 20 ADR bodies, tool code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261006-204118 | 20261006-204118 | REQ-001 / AC-1 |
| 2 | Add or update tests per Validation plan | Completed | 20261006-204118 | 20261006-204118 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-204118 | 20261006-204118 | documentation review |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-204118 | 20261006-204118 |  |

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
- **Requirement ID**: `REQ-001` — no stale copy of the old ADR header list remains (AC-1)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `skills/python-refactoring/path-c.md`