# Implementation Procedure: Remove default-value restatements from governance_03_issue-and-uncertainty-management.md

## Goal

Remove all `default-value restatement outside a table` violations found by `check_docs_content_policy.py` corpus scan from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.

## Scope

- Remove default-value restatement patterns from lines 371, 374 of `governance_03_issue-and-uncertainty-management.md`
- Preserve the semantic meaning of the Known Issue entries while eliminating prose-level default-value documentation

## Assumptions

- The `check_docs_content_policy.py` tool correctly identifies default-value restatement violations
- Auto-generated content between `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` guard comments is exempt
- Removing default-value references does not break the Known Issue tracking structure

## Design decisions

- Replace prose-level default-value descriptions with structured table references where possible
- Preserve the Known Issue entry structure but remove implementation-detail content per `skills/DESIGN.md` Docs content policy — remove

## Alternatives considered

- **Keep the default-value references**: Would violate the docs content policy and require an exemption
- **Move default-value details to a separate appendix**: Adds complexity without clear benefit
- **Remove only the specific default-value phrases**: Minimal change approach, preserves remaining Known Issue content

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Locate lines 371 and 374 containing default-value restatement violations
2. Remove or restructure the default-value references while preserving the Known Issue semantics
3. Verify the resulting document still accurately describes the Known Issue state

### Method

**Line 371**: `- **Current Description**: \`McpServerConfig.required\` defaults to \`True\` (\`scripts/shared/mcp_config.py:95\`)`

Replace the default-value reference with a statement about the current state without exposing the implementation detail:

```markdown
- **Current Description**: `McpServerConfig.required` enforces a safety net for unspecified criticality values, preventing silent treatment as non-required. However, no automated test verifies this default-required safety net, and no distinct code path flags "criticality was never explicitly configured" as its own design/config error per Decision #12's literal wording — ADR-004's own Completion Checklist and Manual Review notes still list INV-14 as unverified/Manual-Review-only.
```

**Line 374**: `- **Recommended Action**: Add a unit test asserting \`McpServerConfig.required\` defaults to \`True\` when unspecified, and/or a test asserting undefined-criticality components are never routed as non-required.`

Replace the default-value reference with a statement about the testing requirement without exposing the implementation detail:

```markdown
- **Recommended Action**: Add a unit test asserting the required field behavior for unspecified criticality values, and/or a test asserting undefined-criticality components are never routed as non-required.
```

### Details

The key change is replacing `defaults to True` with more general statements about the safety net behavior. The line number references (`scripts/shared/mcp_config.py:95`) should also be removed as they expose implementation locations.

## Compatibility considerations

- The Known Issue entries remain semantically accurate after removing default-value references
- The batching note on CI-008 through CI-016 remains valid regardless of default-value removal
- No downstream dependencies on the specific default-value phrasing

## Security considerations

- No security impact; this is a documentation cleanup task

## Rollback considerations

- If the changes introduce ambiguity, revert to the original text and consider adding an explicit exemption for Known Issue entries

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Manual: verify no default-value restatement violations remain | `uv run python tools/check_docs_content_policy.py docs/00_governance/governance_03_issue-and-uncertainty-management.md` | No findings related to default-value restatement |

## Completion criteria

- Lines 371 and 374 no longer contain prose-level default-value references
- The Known Issue entry for CI-008 still accurately describes the issue state
- `check_docs_content_policy.py` reports no default-value restatement violations for this file

## Out of scope

- Corpus-wide scan beyond the three tool-reported findings
- Modifying other Known Issue entries that may have similar issues
- Updating GV-021 status or promoting the check to default-on

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20260926-071110_default-value-restatement-violations-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-085903_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260926-095333
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
