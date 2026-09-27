# Implementation Procedure: Resolve Status value inconsistency in Area Canonical Maps

## Goal

Resolve the Status value inconsistency in the Area Canonical Maps table of `governance_01_documentation-policy.md`: explain why Governance Primary entries show `Active` while Overview/Deployment/RAG/MCP/Agent/EventBus/Shared/DB Primary entries show `(Needs Confirmation — path does not exist in repository)`, per REQ-001 and REQ-002.

## Scope

Single-file edit: `docs/00_governance/governance_01_documentation-policy.md`. Only the Area Canonical Maps section is modified. No structural changes to the table format.

## Assumptions

- The Status difference is intentional: Governance Primary entries are `Active` because those files exist in the repository; other areas' Primary entries are `(Needs Confirmation — path does not exist in repository)` because those paths do not exist. This is confirmed by comparing the Area Canonical Maps table against the actual repository structure.
- An explanation should be added within the Area Canonical Maps section itself, not as a separate note elsewhere.
- The explanation should clarify both why Governance entries differ from other areas AND why some areas use Needs Confirmation instead of Active.

## Design decisions

- Add a clarifying paragraph after the Area Canonical Maps subsections but before the "Canonical Source Registry" section. This keeps the explanation contextually close to the table it explains without altering the table structure.
- The explanation states that the Status column reflects file existence in the repository, not authority level — this resolves the apparent inconsistency.
- The explanation also notes that Needs Confirmation entries indicate paths that were expected to exist but do not, and references the archived plan (`plans/done/20260905-185329_plan.md`) that identified these missing paths.

## Alternatives considered

- Reconciling Status values to make them uniform: would lose the useful information about which paths exist vs. which are missing.
- Adding a footnote to each Needs Confirmation entry: overly verbose and hard to maintain.
- Creating a separate FAQ section: fragments the explanation away from the table it explains.

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

Add an explanatory paragraph after the Area Canonical Maps subsections that clarifies the Status column semantics and the reason for the observed difference.

### Method

1. Open `docs/00_governance/governance_01_documentation-policy.md`.
2. Navigate to the Area Canonical Maps section (lines 189-239).
3. After the Governance subsection (line 239) and before the Canonical Source Registry section (line 241), insert a clarifying paragraph.
4. Verify no structural changes to the table format.

### Details

Current content around lines 233-244:
```markdown
### Governance
| Document | Authority | Status |
|----------|-----------|--------|
| docs/00_governance_01_documentation-policy.md | Primary | Active |
| docs/governance_02_documentation-metadata.md | Primary | Active |
| docs/governance_03_issue-and-uncertainty-management.md | Primary | Active |
| docs/00_governance_04_documentation-checks.md | Primary | Active |

### Canonical Source Registry

`config/documentation_canonical_sources.toml` is the system of record for
canonical-source ownership, superseding the hand-maintained Primary/Secondary
```

Insert after line 239 (after the Governance subsection closing `|`) and before line 241 (before `### Canonical Source Registry`):

```markdown

**Status column note:** The Status value reflects whether the referenced file exists in the repository, not authority level. Governance Primary entries show `Active` because those governance documents exist in `docs/00_governance/`. Overview Primary shows `Active` for `docs/00_index.md` (which exists) and `(Needs Confirmation — path does not exist in repository)` for `docs/architecture.md` (which does not). Areas whose Primary entries show `(Needs Confirmation — path does not exist in repository)` have paths that were expected to exist but do not; see `plans/done/20260905-185329_plan.md` for the list of such paths.
```

## Compatibility considerations

This change affects only documentation text. No code, tooling behavior, or other artifacts consume this explanation. The explanation preserves the existing table structure and does not alter any Status values.

## Security considerations

N/A: documentation-only change, no sensitive data involved.

## Rollback considerations

Remove the inserted paragraph. No data loss risk.

## Validation plan

1. After editing, verify the Status column semantics are now explicitly documented in the Area Canonical Maps section.
2. Confirm no structural changes to the table format (no new rows, columns, or headers).
3. Verify the explanation correctly distinguishes between file-existence-based Active status and Needs Confirmation status.

## Completion criteria

- A clarifying paragraph explaining the Status column semantics appears in the Area Canonical Maps section.
- The paragraph correctly states that Status reflects file existence, not authority level.
- The paragraph references the archived plan for the list of missing paths.
- No structural changes to the Area Canonical Maps table format.
- Manual verification confirms the Status difference is resolved through explanation.

## Out of scope

- Changing the Area Canonical Maps table structure (rows, columns, headers).
- Updating the Status values themselves (the explanation suffices; reconciliation is not required).
- Modifying any governance rules beyond the Status values.
- Editing any document outside `docs/00_governance/`.

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: this document is the documentation update |

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
- **Requirement ID**: REQ-001: Determine whether Status difference is intentional or inconsistent; REQ-002: Add explanation if intentional
- **Source issue**: issues/20260926-183302_area_canonical_maps_status_inconsistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-194938_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-070839
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
