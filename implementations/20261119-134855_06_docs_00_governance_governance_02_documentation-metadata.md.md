## Goal

- Correct the optional-front-matter-field miscount in `docs/00_governance/governance_02_documentation-metadata.md` per the Plan (`REQ-018`): the document must consistently state two optional fields (`status`, `class`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the miscount fix at the "Front Matter Example" section (lines 80–81) and its example block.
- Out of scope: every other statement in the file, including line 49 ("Two optional metadata fields", already correct) and line 96 ("`status` is optional", consistent with two optional fields).

## Assumptions

- Verified 2026-11-19: line 49 already states "Two optional metadata fields beyond the four required fields"; the defective wording is lines 80–81 — "the four required fields plus the one\noptional field". The Plan's row-6 evidence anchors were swapped during re-verification (2026-11-19) and corrected in the Plan.
- The file's "Recommended Additional Fields" section documents exactly two fields: `### status` (line 51) and `### class` (line 65).

## Design decisions

- Edit lines 80–81 to read "the four required fields plus the two optional fields (`status`, `class`)" and add one `class:` line to the example block so the "Complete ... plus the two optional fields" claim is literally true. `class: Reference` is used — an allowed value per the `### class` section (lines 71–72). Verified 2026-11-19: the example block currently shows only `status: stable`, not `class`.

## Alternatives considered

- Reword to "the four required fields plus one of the two optional fields" without touching the block — rejected: `AC-14` requires the document to state two optional fields consistently, and a "Complete" example that omits the second documented optional field keeps the inconsistency alive.

## Implementation
### Target file
`docs/00_governance/governance_02_documentation-metadata.md`
### Procedure
1. In the "Front Matter Example" intro (lines 80–81), replace "plus the one optional field:" with "plus the two optional fields (`status`, `class`):".
2. Add a `class: Reference` line to the YAML example block (after `status: stable`) so the block matches the corrected sentence (`AC-14`).
3. Run the doc gates.

### Method
- Single-line wording fix; validated by the CI lint doc gates (Plan: "doc gates via CI lint").

### Details
- Keep the `## Keywords` and other doc-lint requirements of the file untouched; the diff must be the wording change only.

## Compatibility considerations

- Consumers: doc lint gates only (Plan target-table row 6). No checker, registry, or generated artifact references this sentence.
- The file is the canonical source kind for the `documentation-metadata` claim type in the Resolution Matrix (governance_01 line 135); the fix strengthens that role and feeds the `REQ-016`/`REQ-019` row decision in seq 03.

## Security considerations

- N/A: documentation wording fix.

## Rollback considerations

- Single-commit revert of the wording change.

## Validation plan

- Text review of the two optional-field statements (Plan `T13`): lines 49 and 80–81 both state two optional fields (`AC-14`).
- CI doc lint gates pass (`rules/toolchain.md` doc-check steps; Plan: doc gates via CI lint).

## Completion criteria

- `AC-14` holds: `governance_02` states two optional fields consistently in both places; doc gates pass.

## Out of Scope

- The `REQ-017` Matrix proposal (seq 05) and GV-code renumbering (adrchk011).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the "one optional field" wording at lines 80–81 (`REQ-018`) | Pending | — | — | |
| 2 | Run the doc lint gates | Pending | — | — | |

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
- **Requirement ID**: `REQ-018` (optional-field miscount fix)
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-115842_adrchk010_canonical-registry-checkers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-19 13:48:55
- **Related target files**: `docs/00_governance/governance_02_documentation-metadata.md`
