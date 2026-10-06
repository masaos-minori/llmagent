## Goal

Replace the `## Related Documents` entry in the ADR standard header list with two
top-level sections, `## Related ADRs` and `## Implementation References`, so the
governance rule encodes the new single-store ADR structure (`REQ-001`: remove the last
ADR exception to the single-store rule; the ADR structure must define no `## Related
Documents`).

## Scope

- **In-Scope**: edit the ADR Section Header Standardization list in
  `governance_01` so `Related Documents` becomes `Related ADRs` then
  `Implementation References`, both placed immediately before `Completion Checklist`.
- **Out-of-Scope**: any other heading in `governance_01`; the 20 ADR bodies; tool code;
  other governance files (handled by their own rows).

## Assumptions

- The recommended target structure (UNK-01) is adopted: `## Related ADRs` and
  `## Implementation References` are top-level (`##`) sections before
  `## Completion Checklist`.
- `## Known Deviations` stays in the list unchanged (its Known Issue IDs are not moved
  here).

## Design decisions

- Replace the single `Related Documents` token in the ordered header list with two
  tokens in the order the plan mandates (`Related ADRs`, then `Implementation References`).
- Keep every other header in the list byte-for-byte; only the one token changes.

## Alternatives considered

- Renaming `Related Documents` to only `Related ADRs` and dropping implementation
  references — rejected: the plan requires both promoted sections (AC-1).
- Inserting the two sections at a different position — rejected: they must precede
  `Completion Checklist` (UNK-01).

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

Edit the "ADR Section Header Standardization" paragraph so the ordered list reads
`..., Approval, Related ADRs, Implementation References, Completion Checklist.` instead
of `..., Approval, Related Documents, Completion Checklist.`

### Method

Locate the single standardized list (the "ADR Section Header Standardization" heading),
find the `Related Documents` token between `Approval` and `Completion Checklist`, and
replace it with the two tokens in plan order. Confirm no other `Related Documents`
token exists in this file's ADR header list.

### Details

- Current text (plan line 310 area): `..., Review Triggers, Approval, Related Documents, Completion Checklist.`
- New text: `..., Review Triggers, Approval, Related ADRs, Implementation References, Completion Checklist.`
- Do not reorder or drop any other header in the list.

## Compatibility considerations

- `governance_04` (its own row) repeats this header list and its structure-check
  description; `skills/python-refactoring/path-c.md` repeats it too. Those are separate
  rows and must be updated in the same coordinated change so no stale copy remains
  (AC-1).

## Security considerations

N/A: documentation text only.

## Rollback considerations

A single-line edit to one governance file; revert the one edit to restore the old list.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `governance_01` header list | Documentation review | Read the "ADR Section Header Standardization" list | List shows `Related ADRs` then `Implementation References` before `Completion Checklist`; no `Related Documents` token remains |
| Docs quality | Automated | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria

- The ADR standard header list in `governance_01` contains `Related ADRs` then
  `Implementation References` immediately before `Completion Checklist`.
- No `Related Documents` token remains anywhere in `governance_01`.

## Out of scope

- Other governance files, the 20 ADR bodies, and tool code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001 / AC-1 |
| 2 | Add or update tests per Validation plan | N/A: documentation-only change | Pending | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs-quality checker |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: this file IS the documentation | Pending | — | |

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
- **Requirement ID**: `REQ-001` — define the ADR structure without `## Related Documents`, with `## Related ADRs` and `## Implementation References` as top-level sections (AC-1)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`
