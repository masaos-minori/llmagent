## Goal
Extend this ADR's front matter `related:` so it covers every document its body Related Documents block references (REQ-005: front matter becomes the flat superset for ADR documents).

## Scope
- In: this file's front matter `related:` block only.
- Out: the body, including the `## Related Documents` block and its sub-headings; every other file.

## Assumptions
- Verified by scan on 20261004: the body block references 5 document(s) of which 5 are absent from front matter.
- ADR bodies stay (owner review at the Step 3 gate of the Plan, UNK-01); if that decision changes, this row changes.
- The tool's output, not this list, is authoritative at apply time.

## Design decisions
- Apply through the `merge-related` subcommand rather than by hand so ordering and notation match the other documents.
- Front matter entries use basenames.

## Alternatives considered
- Hand edit: rejected; error-prone across 13 ADR documents.
- Remove the body block: rejected; the ADR section list is mandated and `check_known_deviation_sync.py` reads it.

## Implementation
### Target file
`docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`

### Procedure
1. Run the dry-run for this file and confirm the additions: `mcp_03_01_dispatch-and-routing.md`, `mcp_03_02_tool-registry.md`, `mcp_03_06_tool-runtime-availability-metadata.md`, `agent_06_01_tool-execution-and-approval-execution.md`, `shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`.
2. Run `merge-related --fix` for this file.
3. Confirm only the front matter `related:` block changed and the body is byte-identical.

### Method
- `uv run python tools/manage_frontmatter.py merge-related docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md` (dry-run), then the same command with `--fix`.
- Expected additions: `mcp_03_01_dispatch-and-routing.md`, `mcp_03_02_tool-registry.md`, `mcp_03_06_tool-runtime-availability-metadata.md`, `agent_06_01_tool-execution-and-approval-execution.md`, `shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`.

### Details
- Existing entries keep their order; new entries are appended in body order.
- Front matter `related:` shape in this file: block.

## Compatibility considerations
- No link target changes; inbound references and the body block are unaffected.

## Security considerations
- Documentation only; no secrets or configuration values are involved.

## Rollback considerations
- Revert the commit that applied this ADR group (ADR documents are applied together in one commit).

## Validation plan
- `uv run python tools/check_docs_structure.py` (ADR coverage rule once row 005 lands).
- `uv run python tools/check_known_deviation_sync.py` to confirm the body block is still readable.
- `git diff` shows changes only inside the front matter.

## Completion criteria
- Front matter `related:` covers every document referenced in the body block.
- The body is unchanged.
- Structure and quality checkers report no new findings for this file.

## Out of scope
- Any body edit, ADR renumbering, or edits to other ADR documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the front matter extension via `merge-related --fix` | Completed | 20261004-125317 | 20261004-130515 | front matter extension applied in the working tree (5 entries, +240 bytes) but the file now exceeds the size limit; decision needed front matter extended via merge-related; size over the limit resolved by owner-accepted exception (SIZE_EXCEPTIONS in tools/check_docs_structure.py, ceiling = accepted size) |
| 2 | N/A: documentation file; covered by checker runs | Completed | 20261004-130515 | 20261004-130515 | N/A: documentation file; check_size exception covered by 3 new tests in row 006's file |
| 3 | Run `check_docs_structure.py` and `check_known_deviation_sync.py` | Completed | 20261004-130515 | 20261004-130515 | check_docs_structure.py: All checks passed; full suite 8094 passed, 7 failed (same unrelated baseline) |
| 4 | N/A: this file is the documentation change | Completed | 20261004-130515 | 20261004-130515 | N/A: this file is the documentation change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | docs/10_adr/ADR-003 grew from 24568 to 24808 bytes after the required front matter extension; `tools/check_docs_structure.py` limit is 24576 bytes (232 over). Options: accept an exception, raise the limit, shorten ADR-003 body (out of this Plan's scope) | No | Resolved: owner accepted option 1 (per-file exception); see `SIZE_EXCEPTIONS` in `tools/check_docs_structure.py` |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` (extend ADR front matter `related:` to cover body references)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md