## Goal

Update `governance_04` so its tool descriptions, automated-check list, compliance
header-list copy, and GV-005 entry all reflect the new ADR structure with no `## Related
Documents` block (`REQ-001`, `REQ-003`: keep the governance rules consistent with the
changed tools and the removed ADR exception; AC-1, AC-3).

## Scope

- **In-Scope**: (1) the automated-check description that requires a `## Related
  Documents` section and that ADR front matter covers the body block (lines 155-156);
  (2) the `check_known_deviation_sync.py` description that references the `### Known
  Issues` subsection (line 195); (3) the stale ADR header-list copy in the manual-check
  compliance items (lines 262-263); (4) the GV-005 row (line 322).
- **Out-of-Scope**: any other check in `governance_04`; tool code; the 20 ADR bodies.

## Assumptions

- The `## Related Documents` requirement is dropped entirely (AC-3).
- ADR front-matter `related:` coverage is redefined to scan body `.md` references
  (UNK-05), not a now-absent body block.
- `check_known_deviation_sync.py` no longer parses the `### Known Issues` subsection
  (REQ-004), so its description must drop that reference.

## Design decisions

- Remove the phrase requiring a `## Related Documents` section and replace the coverage
  clause with the body-reference scan definition.
- Replace the compliance-item `Related Documents` token with `Related ADRs` then
  `Implementation References` (matching the governance_01 header list).
- Update GV-005 wording from "ADR block required ... front matter covers body references"
  to the redefined body-reference coverage.

## Alternatives considered

- Leaving the tool descriptions untouched and updating only the header list — rejected:
  the doc would describe a `## Related Documents` requirement and a `### Known Issues`
  parse that no longer exist, violating "keep rules/tools/docs consistent".

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

Make four edits:

1. Lines 155-156 (automated-check / structure-check description): drop the
   "Related Documents section required for ADR documents only" requirement and redefine
   front-matter `related:` coverage to cover documents referenced by the ADR body
   (body `.md` references), not a body block.
2. Line 195 (`check_known_deviation_sync.py` description): remove the reference to the
   `### Known Issues` subsection; keep the `## Known Deviations` reference.
3. Lines 262-263 (compliance header list): replace item `13. Related Documents` with
   `13. Related ADRs` and insert `14. Implementation References` before `Completion
   Checklist` (item 14).
4. Line 322 (GV-005 row): update the description to the redefined body-reference
   coverage and the new section names.

### Method

`rg -n "Related Documents|Known Issues|Completion Checklist"` in the file to locate each
target, then edit each occurrence to the new wording. Re-read the four regions after
editing to confirm no `## Related Documents` requirement or `### Known Issues` parse
reference remains.

### Details

- Line 155 currently: "Keywords section; Related Documents section required for ADR
  documents only, and no body Related section in other documents".
- Line 156 currently: "Front matter `related:` of each ADR covers the documents its body
  Related Documents block references".
- Lines 262-263 currently: `13. Related Documents` / `14. Completion Checklist`.
- Line 322 currently: "Related section placement (ADR block required; no body Related
  section elsewhere; ADR front matter covers body references)".

## Compatibility considerations

- This doc cross-references `governance_01` ("ADR Section Header Standardization") and
  names the changed tools. Keep the cross-reference intact; the header-list copy here
  must match `governance_01`'s new order.

## Security considerations

N/A: documentation text only.

## Rollback considerations

Four localized edits to one governance file; revert them to restore the old wording.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `governance_04` text | Documentation review | Read lines 155-156, 195, 262-263, 322 | No `## Related Documents` requirement; header list shows `Related ADRs`/`Implementation References`; GV-005 reworded; no `### Known Issues` parse reference |
| Docs quality | Automated | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria

- `governance_04` no longer requires a `## Related Documents` section and no longer
  describes parsing a `### Known Issues` subsection.
- The compliance header-list copy shows `Related ADRs` then `Implementation References`.
- GV-005 describes the redefined body-reference coverage.

## Out of scope

- Tool code, the 20 ADR bodies, other governance files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001, REQ-003 / AC-1, AC-3 |
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
- **Requirement ID**: `REQ-001` / `REQ-003` — keep governance rules consistent with the removed ADR exception and the changed `check_docs_structure.py` (AC-1, AC-3)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
