# Implementation Procedure: docs/04_mcp_04_01_web-search-file-read-github.md

## Goal

Add a one-line "See also" cross-reference to
`docs/00_security_02_high-risk-tool-common-policy.md` under the `## github-mcp (Port
8006)` section only, without touching the web-search-mcp or file-read-mcp sections of
this same file.

## Scope

**In-Scope**
- Insert one "See also" line as the first line of the `## github-mcp (Port 8006)`
  section, before its existing body text.

**Out-of-Scope**
- The `web-search-mcp` and `file-read-mcp` sections of this file — the source
  requirement scopes this note to github-mcp only.
- The file-wide `## Related Documents` section — adding
  `00_security_02_high-risk-tool-common-policy.md` there would misleadingly imply the
  policy also governs web-search-mcp/file-read-mcp, which this plan does not intend.

## Assumptions

- **Corrected during implementation-procedure review**: the source plan
  (`plans/20260820-101747_plan.md`) wrote this heading as `## github-mcp（ポート
  8006）` (Japanese full-width parenthesis, "ポート"); the file's current heading is
  `## github-mcp (Port 8006)` (ASCII parenthesis, English "Port") — the doc has since
  been translated to English. This procedure targets the actual current heading.
- `docs/00_security_02_high-risk-tool-common-policy.md` exists — verified during
  implementation-procedure review (confirmed present on disk; its source plan,
  `plans/20260819-174040_plan.md`, has already reached `plans/done/`), so the Phase 1
  precondition this plan gated on is already satisfied.
- The policy doc's own content names `github-mcp` explicitly as a governed high-risk
  tool (`"**GitHub** (github-mcp): GitHub API operations (repos, issues, PRs, files)"`)
  — confirmed by reading `docs/00_security_02_high-risk-tool-common-policy.md`, so the
  cross-reference's premise (this doc's Risks section's third risk) holds.

## Design decisions

- Follow the established "See also: [target](target)" inline-note convention already
  used elsewhere in this file/repo (e.g. `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md`)
  and by the sibling `docs/04_mcp_04_05_git.md` (already implemented — see this plan's
  Scope), rather than inventing new phrasing.
- Place the note as the very first line of the section (immediately after the `##
  github-mcp (Port 8006)` heading, before "**Purpose:**"), so it is visible regardless
  of how far into the section a reader scrolls.
- Link to the policy document as a whole, not to a specific in-page anchor — matches
  the granularity `plans/20260819-174040_plan.md` used for its 19-file pattern, and
  avoids a broken-anchor risk if the policy doc's internal headings shift later.

## Alternatives considered

- Add the reference to the file-wide `## Related Documents` section instead of inline
  under the section heading — rejected per this plan's own Scope/Design: that section
  covers all three MCP servers in this file, and adding the policy reference there
  would misleadingly suggest it also governs web-search-mcp/file-read-mcp.

## Implementation

### Target file
`docs/04_mcp_04_01_web-search-file-read-github.md`

### Procedure
1. Locate the `## github-mcp (Port 8006)` heading.
2. Insert, as the first line of the section body (before "**Purpose:**"):
   ```
   See also: [00_security_02_high-risk-tool-common-policy.md](00_security_02_high-risk-tool-common-policy.md) for the cross-cutting canonical policy governing github-mcp as a high-risk tool.
   ```
3. Confirm no other line in the `web-search-mcp`/`file-read-mcp` sections or the
   file-wide `## Related Documents` section was touched.

### Method
Single-line Markdown insertion; pure addition, no existing text reworded or removed.

### Details
- Confirmed via `rg -n "00_security_02_high-risk"
  docs/04_mcp_04_01_web-search-file-read-github.md` during this review that this file
  currently has zero references to the policy doc — this is genuinely new content, not
  a duplicate of existing text.

## Compatibility considerations

N/A: documentation-only, purely additive change.

## Security considerations

N/A: documentation wording change only; does not alter any enforced security policy,
only adds a pointer to where it is documented.

## Rollback considerations

- Trivially revertable: a single added line with no dependency on the sibling
  `04_mcp_04_03_rag-pipeline-and-cicd.md` edit (each targets a different file).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/04_mcp_04_01_web-search-file-read-github.md | Internal link resolution | `uv run check-mcp-docs` | No broken-link findings introduced |
| docs/04_mcp_04_01_web-search-file-read-github.md | Manual diff review | `git diff docs/04_mcp_04_01_web-search-file-read-github.md` | Diff shows exactly one added line; no existing content altered |

## Out of scope

- `docs/04_mcp_04_05_git.md` — already has this cross-reference; no action (see source
  plan's Scope).
- `docs/04_mcp_04_03_rag-pipeline-and-cicd.md` — covered by its own implementation
  procedure document.

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
- Related target files: docs/04_mcp_04_01_web-search-file-read-github.md
