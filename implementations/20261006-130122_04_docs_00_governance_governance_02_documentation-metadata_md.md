## Goal

Update the single-store rule text in `governance_02` so it records that the ADR
exception to the single-store rule is removed: ADR front matter `related:` is now the
only cross-reference store, with no classified body block (`REQ-001`: remove the last
exception to the single-store rule; AC-1).

## Scope

- **In-Scope**: the `related` field description paragraph (plan lines 24-27 area) that
  states ADR documents keep a classified `## Related Documents` body block.
- **Out-of-Scope**: other metadata fields in `governance_02`; the example front matter;
  other files.

## Assumptions

- The single-store rule now applies uniformly: general AND ADR documents carry no body
  Related section; `related:` is authoritative for both.

## Design decisions

- Rewrite the ADR sentence to state that ADRs no longer keep a classified body block and
  that `related:` covers all cross-references for ADRs too.
- Keep the first two sentences about `related:` being the single authoritative store
  unchanged.

## Alternatives considered

- Deleting the ADR sentence entirely — rejected: the field description should still note
  that ADRs follow the same single-store rule (no body block), for reader clarity.

## Implementation

### Target file

`docs/00_governance/governance_02_documentation-metadata.md`

### Procedure

Edit the `related` field description so the clause "ADR documents keep a classified
`## Related Documents` block in the body (Specifications, Operations, Known Issues, and
similar), and their front matter `related:` must cover every..." is replaced with a
statement that ADRs no longer keep a body block and that `related:` is the sole
cross-reference store for ADRs as well.

### Method

`rg -n -i "single.store|ADR" docs/00_governance/governance_02_documentation-metadata.md`
to locate the description, edit it, then re-read lines 24-27 to confirm the ADR
exception no longer asserts a body block.

### Details

- Current (plan lines 24-27): "...general documents carry no body Related section. ADR
  documents keep a classified `## Related Documents` block in the body (Specifications,
  Operations, Known Issues, and similar), and their front matter `related:` must cover
  every..."
- New: "...general documents carry no body Related section. ADR documents also carry no
  body Related section; `related:` is the sole cross-reference store for ADRs, which keep
  `## Related ADRs` and `## Implementation References` as ordinary top-level sections."

## Compatibility considerations

- Cross-references to the single-store rule elsewhere (e.g. `governance_04`) must agree;
  those are separate rows.

## Security considerations

N/A: documentation text only.

## Rollback considerations

Localized edit to one governance file; revert it.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `governance_02` `related` description | Documentation review | Read lines 24-27 | States ADRs carry no body Related section; `related:` is the sole store; no `## Related Documents` body-block assertion |
| Docs quality | Automated | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria

- `governance_02` records that the ADR exception to the single-store rule is removed and
  that ADRs carry no body `## Related Documents` block.

## Out of scope

- Other metadata fields, other governance files, the 20 ADR bodies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261006-204118 | 20261006-204118 | REQ-001 / AC-1 |
| 2 | Add or update tests per Validation plan | Completed | 20261006-204118 | 20261006-204118 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-204118 | 20261006-204118 | docs-quality checker |
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
- **Requirement ID**: `REQ-001` — note the ADR exception to the single-store rule is removed (AC-1)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `docs/00_governance/governance_02_documentation-metadata.md`