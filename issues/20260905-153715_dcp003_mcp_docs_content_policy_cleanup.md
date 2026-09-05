# Remove hand-written port numbers and residual listings from MCP docs

## Priority
Medium

## Summary
Remove hand-written literal port numbers, and the remaining
class/function-index and implementation-location findings, from the MCP
domain documents: `docs/04_mcp_01_tool_ownership_matrix.md`,
`04_mcp_02_service_boundaries.md`, `04_mcp_03_03_transport-and-health.md`,
`04_mcp_04_01_web-search-file-read-github.md`,
`04_mcp_04_02_file-write-file-delete-shell.md`,
`04_mcp_04_03_rag-pipeline-and-cicd.md`, `04_mcp_04_04_mdq.md`,
`04_mcp_04_05_git.md`, `04_mcp_05_04_mdq-rag-boundary.md`, and
`04_mcp_06_06_verification-methods.md`, per `skills/DESIGN.md` Docs content
policy — remove/retain.

## Background
`docscope1`/`docscope2` (in `issues/done/`) already established the policy
and the `check_docs_content_policy.py` detection tool (`GV-021`). Their own
evidence section already named this domain's `04_mcp_04_02_...` file's
"## file-write-mcp (Port 8007)" / "## file-delete-mcp (Port 8008)" / "##
shell-mcp (Port 8009)" headings as concrete violation examples.

## Problem
`uv run python tools/check_docs_content_policy.py` reports 59 findings
across these ten files: `04_mcp_01_tool_ownership_matrix.md` (26),
`04_mcp_02_service_boundaries.md` (10),
`04_mcp_03_03_transport-and-health.md` (6),
`04_mcp_04_01_web-search-file-read-github.md` (5),
`04_mcp_04_02_file-write-file-delete-shell.md` (4),
`04_mcp_04_03_rag-pipeline-and-cicd.md` (3), `04_mcp_04_04_mdq.md` (2),
`04_mcp_04_05_git.md` (1), `04_mcp_05_04_mdq-rag-boundary.md` (1), and
`04_mcp_06_06_verification-methods.md` (1). Almost all are "literal port
number" findings. Concretely, `04_mcp_01_tool_ownership_matrix.md`'s
"Tool-to-MCP Server Mapping" table states the port inline in each server
name cell (e.g. `file-read-mcp (port 8005)`), and its "Responsibility
Boundaries" section repeats the same pattern in every subsection heading
(e.g. `### file-read-mcp (port 8005)`). The same file also has a
`<!-- AUTO-GENERATED -->` Server Port & Tool Reference table at the end,
whose fate is decided separately (see Dependencies).

## Reason for Change
A literal port number in prose/headings duplicates
`config/agent.toml`'s `[mcp_servers.*]` sections and goes stale the moment a
port is reassigned — exactly the failure mode `skills/DESIGN.md` "No
concrete configuration values" and the new "literal port number"
remove-category exist to prevent. The responsibility/boundary content these
files already carry (Responsibilities / Explicit non-responsibilities
sections) is the retain-category content the policy wants kept, and does
not depend on the port number being stated alongside it.

## Implementation Intent
For each hand-written port mention (heading, table cell, or prose
sentence), remove the port number and keep the server name and its
responsibility content intact — e.g. `### file-read-mcp (port 8005)`
becomes `### file-read-mcp`. Where a table column exists solely to state
the port (not the case here — port is embedded in the server-name cell),
restructure the cell to name the server only. Do not touch the
`<!-- AUTO-GENERATED -->` block in `04_mcp_01_tool_ownership_matrix.md` —
its disposition is `dcp001`'s decision, applied as a follow-up edit to this
same file once that decision lands.

## Target Files or Areas
- `docs/04_mcp_01_tool_ownership_matrix.md`
- `docs/04_mcp_02_service_boundaries.md`
- `docs/04_mcp_03_03_transport-and-health.md`
- `docs/04_mcp_04_01_web-search-file-read-github.md`
- `docs/04_mcp_04_02_file-write-file-delete-shell.md`
- `docs/04_mcp_04_03_rag-pipeline-and-cicd.md`
- `docs/04_mcp_04_04_mdq.md`
- `docs/04_mcp_04_05_git.md`
- `docs/04_mcp_05_04_mdq-rag-boundary.md`
- `docs/04_mcp_06_06_verification-methods.md`

## Required Changes
1. Remove every hand-written literal port number from headings, table
   cells, and prose across the ten files listed above.
2. Leave the `<!-- AUTO-GENERATED -->`/`<!-- END AUTO-GENERATED -->` block
   in `04_mcp_01_tool_ownership_matrix.md` untouched pending `dcp001`.
3. Confirm each file's remaining Responsibilities / Explicit
   non-responsibilities content still reads coherently once port numbers
   are removed (server names alone should remain unambiguous, since each
   server has one unique name).
4. Re-check `docs/00_governance_03_issue-and-uncertainty-management.md` for
   any Needs Confirmation marker anchored to a heading being edited here,
   and update the anchor text if the heading wording changes.

## Constraints
- Do not remove or alter the `<!-- AUTO-GENERATED -->` block in
  `04_mcp_01_tool_ownership_matrix.md` — out of scope pending `dcp001`.
- Do not change `rules/env.md`, which remains the canonical location for
  concrete port values.
- Do not alter the server-name identifiers themselves (e.g.
  `file-read-mcp`) — only remove the trailing `(port NNNN)` annotation.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero
  hand-written "literal port number" findings for the ten target files
  (the auto-generated block in `04_mcp_01_tool_ownership_matrix.md` may
  still report, pending `dcp001`).
- `uv run python tools/check_docs_consistency.py --domain mcp` passes,
  confirming no broken cross-references or drift introduced by the edit.
- Every Responsibilities/Explicit non-responsibilities section remains
  intact and unambiguous after port-number removal.

## Testing Expectations
Documentation-only change. Run
`uv run python tools/check_docs_content_policy.py`,
`uv run python tools/check_docs_structure.py docs/04_mcp_*.md`, and
`uv run python tools/check_docs_consistency.py --domain mcp`
(`check-mcp-docs` shorthand). No `pytest`/`mypy`/`ruff` run required.

## Documentation Impact
Yes — this issue's deliverable is the port-number removal described above
across the ten listed files.

## Out of Scope
- The `<!-- AUTO-GENERATED -->` table in `04_mcp_01_tool_ownership_matrix.md`
  (tracked in `dcp001`).
- Any file outside the ten listed above.
- Rewriting the Tool-to-MCP Server Mapping table's non-port columns.

## Dependencies
Partially depends on `dcp001` — only for the auto-generated block in
`04_mcp_01_tool_ownership_matrix.md`. All hand-written port removal in this
issue can proceed independently of `dcp001`'s outcome.

## Unresolved Questions
N/A: none — every finding in this domain is a straightforward hand-written
port-number removal once the auto-generated block is excluded.

## AI Implementation Instruction
Remove only the `(port NNNN)` annotations and leave all surrounding
responsibility/boundary prose unchanged. Do not touch the
`<!-- AUTO-GENERATED -->` section. Run
`tools/check_docs_content_policy.py` after each file to confirm the
hand-written findings for that file reach zero before moving to the next.
Stop and ask if a port number appears load-bearing to disambiguate two
similarly-named servers rather than purely decorative.
