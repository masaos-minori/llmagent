# Implementation Procedure: docs/04_mcp_04_03_rag-pipeline-and-cicd.md

## Goal

Add a one-line "See also" cross-reference to
`docs/00_security_02_high-risk-tool-common-policy.md` under the `## cicd-mcp (Port
8012)` section only, without touching the rag-pipeline-mcp section of this same file.

## Scope

**In-Scope**
- Insert one "See also" line as the first line of the `## cicd-mcp (Port 8012)`
  section, before its existing body text.

**Out-of-Scope**
- The `rag-pipeline-mcp` section of this file — the source requirement scopes this
  note to cicd-mcp only.
- The file-wide `## Related Documents` section — adding
  `00_security_02_high-risk-tool-common-policy.md` there would misleadingly imply the
  policy also governs rag-pipeline-mcp, which this plan does not intend.

## Assumptions

- **Corrected during implementation-procedure review**: the source plan
  (`plans/20260820-101747_plan.md`) wrote this heading as `## cicd-mcp（ポート
  8012）` (Japanese full-width parenthesis, "ポート"); the file's current heading is
  `## cicd-mcp (Port 8012)` (ASCII parenthesis, English "Port") — the doc has since
  been translated to English, matching the same translation found in the sibling
  `04_mcp_04_01_web-search-file-read-github.md` procedure. This procedure targets the
  actual current heading.
- `docs/00_security_02_high-risk-tool-common-policy.md` exists — verified during
  implementation-procedure review (confirmed present on disk; its source plan,
  `plans/20260819-174040_plan.md`, has already reached `plans/done/`), so the Phase 1
  precondition this plan gated on is already satisfied.
- The policy doc's own content names `cicd-mcp` explicitly as a governed high-risk tool
  (`"**CI/CD** (cicd-mcp): CI/CD pipeline operations"`) — confirmed by reading
  `docs/00_security_02_high-risk-tool-common-policy.md`, so the cross-reference's
  premise holds.

## Design decisions

- Same convention as the sibling `04_mcp_04_01_web-search-file-read-github.md`
  procedure and the already-implemented `docs/04_mcp_04_05_git.md` reference: a
  "See also: [target](target)" inline note, not a new phrasing.
- Place the note as the very first line of the section (immediately after the `##
  cicd-mcp (Port 8012)` heading, before its existing body text).
- Link to the policy document as a whole, not a specific in-page anchor.

## Alternatives considered

- Add the reference to the file-wide `## Related Documents` section instead — rejected
  for the same reason as the sibling procedure: that section also covers
  rag-pipeline-mcp, and adding the policy reference there would misleadingly suggest it
  governs that server too.

## Implementation

### Target file
`docs/04_mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure
1. Locate the `## cicd-mcp (Port 8012)` heading.
2. Insert, as the first line of the section body:
   ```
   See also: [00_security_02_high-risk-tool-common-policy.md](00_security_02_high-risk-tool-common-policy.md) for the cross-cutting canonical policy governing cicd-mcp as a high-risk tool.
   ```
3. Confirm no other line in the `rag-pipeline-mcp` section or the file-wide `##
   Related Documents` section was touched.

### Method
Single-line Markdown insertion; pure addition, no existing text reworded or removed.

### Details
- Confirmed via `rg -n "00_security_02_high-risk"
  docs/04_mcp_04_03_rag-pipeline-and-cicd.md` during this review that this file
  currently has zero references to the policy doc — this is genuinely new content.

## Compatibility considerations

N/A: documentation-only, purely additive change.

## Security considerations

N/A: documentation wording change only.

## Rollback considerations

- Trivially revertable: a single added line, independent of the sibling
  `04_mcp_04_01_web-search-file-read-github.md` edit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/04_mcp_04_03_rag-pipeline-and-cicd.md | Internal link resolution | `uv run check-mcp-docs` | No broken-link findings introduced |
| docs/04_mcp_04_03_rag-pipeline-and-cicd.md | Manual diff review | `git diff docs/04_mcp_04_03_rag-pipeline-and-cicd.md` | Diff shows exactly one added line; no existing content altered |

## Out of scope

- `docs/04_mcp_04_05_git.md` — already has this cross-reference; no action (see source
  plan's Scope).
- `docs/04_mcp_04_01_web-search-file-read-github.md` — covered by its own
  implementation procedure document.

## Execution Status

##### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-101747_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-203018
- Related target files: docs/04_mcp_04_03_rag-pipeline-and-cicd.md
