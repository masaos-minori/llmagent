## Goal

Replace the "coverage is uneven across tools" paragraph in
`docs/91_security/security_02_high-risk-tool-common-policy.md` with a resolved per-category pointer, so the
policy document no longer states an open gap once every tool category records its own coverage
(REQ-011, AC-011).

## Scope

- Rewrite the single paragraph that currently names Known Issue MCP-006.
- Remove the MCP-006 citation from this file, which is the only citation outside the ledger itself.
- Leave the Layered protection model table and the rest of the document unchanged.

## Assumptions

- Every Plan documentation row (rows 12-17) has landed before this edit, so the pointer this paragraph
  writes actually resolves to a layer-coverage section in each tool document.
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` still carries the MCP-006 entry
  when this row runs; Plan row 19 removes it afterwards.

## Design decisions

- Keep the paragraph's warning function: state that a layer is implemented only where the tool's own
  document records it, instead of stating that coverage is uneven. The policy stops describing a gap
  without becoming a place that lists per-tool implementation detail.
- Do not add a coverage table here: the Plan's documentation shape makes each tool document the single
  source for its own coverage.

## Alternatives considered

- Mark the paragraph as resolved while keeping the MCP-006 citation: rejected — the Current-Specification-Only
  Policy keeps no resolved items in active documents, and `check_known_deviation_sync.py` reports a
  citation to a removed ID as an error.
- Move the per-category facts into this policy document: rejected — it would duplicate the tool documents
  and create a second place to keep in sync.

## Implementation

### Target file

`docs/91_security/security_02_high-risk-tool-common-policy.md`

### Procedure

1. Replace the paragraph at `docs/91_security/security_02_high-risk-tool-common-policy.md:56` with a
   paragraph that states each high-risk tool category records its own layer coverage in its own document.
2. Name the tool documents to consult, using the same relative-link style the document already uses.
3. Keep the closing caution that a layer is not implemented merely because this policy defines it.

### Method

One paragraph replaced by one paragraph; no heading, table, or list changes.

### Details

- The paragraph to replace is `docs/91_security/security_02_high-risk-tool-common-policy.md:56`, which is
  the only place outside the ledger that cites MCP-006.
- The replacement must not contain the string `MCP-006`, because Plan row 19 removes the ledger entry in
  the same phase and a citation to a removed ID fails `check_known_deviation_sync.py`.
- The categories to name are the ones the Plan's Design decision table covers: file-write, file-delete,
  shell, git, github, mdq, cicd.

## Compatibility considerations

- The document's category table and allowed-paths sections are unchanged, so readers who arrived from
  those sections keep their entry points.
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` is the only file that may still
  reference MCP-006 after this row, and only until Plan row 19 runs.

## Security considerations

N/A: documentation-only row; the change removes a statement of an open gap and adds no implementation
detail beyond pointers.

## Rollback considerations

N/A: revert the commit. Reverting restores the policy-level claim that coverage is uneven, which
contradicts the tool documents once rows 12-17 have landed.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_known_deviation_sync.py`
- `uv run python tools/check_workitem_structure.py --file implementations/20261017-162434_18_docs_91_security_security_02_high-risk-tool-common-policy.md.md`

## Completion criteria

- The file contains no `MCP-006` citation and no sentence stating that coverage is uneven across tools
  (AC-011).
- The paragraph points at each tool document for its layer coverage (AC-009).
- The docs checkers report no findings for this file.

## Out of scope

- Removing the MCP-006 ledger entry, which is Plan row 19.
- Changing the Layered protection model definitions.
- Recording per-tool coverage detail in this policy document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the open-gap paragraph with the per-category pointer | Pending | — | — | REQ-011 |
| 2 | Run the docs checkers | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-011
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `docs/91_security/security_02_high-risk-tool-common-policy.md`
