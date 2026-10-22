## Goal
- Make the link at the end of the tool-name paragraph resolve to the current heading of the failure-diagnosis document (`REQ-001`: replace the stale anchor; `REQ-002`: confirm the anchor Warning is gone).

## Scope
- Change only the `#anchor` of the one link on line 107 of the target file. No other text, no other document, no heading rename.

## Assumptions
- The GitHub-style slug of `## LLM sees a tool but execution fails with "Unknown tool"` (`docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md:72`) is `llm-sees-a-tool-but-execution-fails-with-unknown-tool`; falsified if the anchor Warning persists after the edit.
- No other document links to the old anchor (an `rg` over `docs`, `scripts`, `tests`, and `tools` found only line 107 of the target file).

## Design decisions
- Fix the link, not the heading, because other documents may link to the heading.
- Keep the surrounding sentence byte-identical so the diff is one token.

## Alternatives considered
N/A: a one-token link fix has no meaningful alternative.

## Implementation
### Target file
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

### Procedure
1. Replace `#llm-called-a-tool-but-execution-failed-with-unknown-tool` with `#llm-sees-a-tool-but-execution-fails-with-unknown-tool` in the link at line 107.
2. Run the validation commands below.

### Method
- Use Edit with the exact old and new anchor strings; the old string occurs once in the file.

### Details
- Link before: `[MCP Failure Diagnosis](mcp_06_07_mcp-failure-diagnosis.md#llm-called-a-tool-but-execution-failed-with-unknown-tool)`.
- Link after: the same text with the anchor `#llm-sees-a-tool-but-execution-fails-with-unknown-tool`.
- `docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md` and `tools/_docs_consistency_lib.py` are reference only and are not modified.

## Compatibility considerations
N/A: documentation link only; no code, config, or test references the anchor.

## Security considerations
N/A: no code or data handling is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain mcp` — no anchor Warning.
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
- `uv run python tools/check_docs_content_policy.py`
- `rg -n "llm-called-a-tool" docs` — no match.

## Completion criteria
- `git diff` shows exactly one changed line in the target file, differing only in the anchor.
- The MCP domain consistency check reports no anchor Warning, and the three docs checkers pass for the edited file.

## Out of Scope
- Other documents, other anchors, the target heading, and the anchor check itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the stale anchor in the link at line 107 (Implementation > Procedure step 1) | Pending | — | — | |
| 2 | Run the MCP domain consistency check and the docs checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (replace the stale anchor), `REQ-002` (confirm the Warning is gone)
- **Source issue**: issues/20261022-104121_mcpanchor_fix-stale-anchor-mcp-dispatch-doc.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-121556_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-122641
- **Related target files**: docs/22_mcp/mcp_03_01_dispatch-and-routing.md
