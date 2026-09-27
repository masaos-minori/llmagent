# Implementation Procedure: Update stale plan references in governance_01_documentation-policy.md

## Goal

Update 8 occurrences of the stale plan reference `plans/20260905-185329_plan.md` to `plans/done/20260905-185329_plan.md` in `governance_01_documentation-policy.md`, per REQ-001.

## Scope

Single-file edit: `docs/00_governance/governance_01_documentation-policy.md`. Only the canonical-source table rows referencing the archived plan are modified. No other content changes.

## Assumptions

- The archived plan file `plans/done/20260905-185329_plan.md` exists and is the correct destination.
- All 8 occurrences found in the Plan's evidence are the complete set; no additional stale references exist elsewhere in the file.
- The annotation text `(Needs Confirmation — path does not exist in repository, see ...)` should be preserved as-is, only the path portion changed.

## Design decisions

- Use a simple find-and-replace within the specific table rows rather than rewriting the entire file. This minimizes diff noise and preserves surrounding formatting.
- Preserve the exact annotation context around each reference; only the path string changes.

## Alternatives considered

- Rewriting the entire canonical-source table: unnecessary scope expansion, higher risk of formatting drift.
- Adding a deprecation note alongside the old path: would leave readers confused about which path is authoritative.

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

Replace all 8 occurrences of `plans/20260905-185329_plan.md` with `plans/done/20260905-185329_plan.md` in the canonical-source table rows.

### Method

1. Open `docs/00_governance/governance_01_documentation-policy.md`.
2. Locate the canonical-source table (Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB subsections).
3. In each row where the Status column contains `see plans/20260905-185329_plan.md`, replace that path with `plans/done/20260905-185329_plan.md`.
4. Verify no other occurrences of `plans/20260905-185329_plan.md` remain outside the canonical-source table.

### Details

Affected lines (confirmed via grep):
- Line 195: Overview → Architecture row
- Lines 200-201: Deployment row
- Line 206: RAG → specification.md row
- Line 212: MCP → specification.md row
- Line 218: Agent → specification.md row
- Line 224: EventBus → specification.md row
- Line 230: Shared/DB → specification.md row

Each line follows the pattern:
```
| <document-path> | Primary/Operational | (Needs Confirmation — path does not exist in repository, see plans/20260905-185329_plan.md) |
```

Change to:
```
| <document-path> | Primary/Operational | (Needs Confirmation — path does not exist in repository, see plans/done/20260905-185329_plan.md) |
```

## Compatibility considerations

This change affects only documentation paths. No code, tooling behavior, or other artifacts consume these references. The archived plan at `plans/done/20260905-185329_plan.md` is the intended destination.

## Security considerations

N/A: documentation-only change, no sensitive data involved.

## Rollback considerations

Revert the 8 path replacements back to `plans/20260905-185329_plan.md`. No data loss risk.

## Validation plan

1. After editing, run `rg 'plans/20260905-185329_plan\.md' docs/00_governance/governance_01_documentation-policy.md` and confirm zero matches.
2. Run `rg 'plans/done/20260905-185329_plan\.md' docs/00_governance/governance_01_documentation-policy.md` and confirm exactly 8 matches.
3. Run `uv run python tools/check_docs_structure.py docs/00_governance/*.md` and confirm none of the flagged findings from the original issue remain.

## Completion criteria

- All 8 occurrences of `plans/20260905-185329_plan.md` in `governance_01_documentation-policy.md` are replaced with `plans/done/20260905-185329_plan.md`.
- No other content in the file is altered.
- `check_docs_structure.py` passes without the stale-reference finding.

## Out of scope

- Canonical-map path shorthand correction (mentioned in the Plan but explicitly out-of-scope).
- Document-size limit decisions.
- Changing any governance rule's substance.
- Editing any document outside `docs/00_governance/`.

## Execution Status

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
- **Requirement ID**: REQ-001: Update stale plan reference from `plans/` to `plans/done/`
- **Source issue**: issues/20260926-174633_cleanup-batch-for-governance-docs:-stale-plan-ref,-illustrative-example-links,-missing-keywords.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-194234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-063107
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
