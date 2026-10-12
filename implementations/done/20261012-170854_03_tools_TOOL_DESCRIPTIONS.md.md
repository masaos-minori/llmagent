## Goal
- Describe the line-anchored import rule and the (new) marker in the stale detector entry (`REQ-004`).

## Scope
- Only the table row of `stale_detector.py` in the inventory (the only row for this tool). No file is added or removed under `tools/`.

## Assumptions
- The row is written in Japanese like its neighbours and currently says the detector checks line numbers, symbol names, imports and Before blocks, treats any mismatch as stale, and returns exit code 1 when stale.

## Design decisions
- Append two short clauses to the existing row; keep it a single table row.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the row with `grep -n "stale_detector.py" tools/TOOL_DESCRIPTIONS.md`.
2. Append to the description, before the final table pipe: the import is recognized only as a statement at the start of a line (a mention inside a sentence is not checked), and a symbol or import statement written followed by the marker (new) is treated as created by the procedure and excluded from the existence check. Write the clauses in Japanese in the same register as the row.
3. Leave every other row untouched.

### Method
- Edit the row text in place; keep the pipe structure of the table.

### Details
- Do not touch the inventory count in the heading of the file.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` reports no issues.
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03, 04 and 05 (documentation); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- The row describes the two rules; no other row changed; the sync checker passes.

## Out of scope
- Any other row or section of the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Describe the import rule and the marker in the stale detector row | Completed | 20261012-171411 | 20261012-171422 | stale_detector clean changed: tools/TOOL_DESCRIPTIONS.md (stale_detector row: line-anchored imports, (new) marker) |
| 2 | Run the tool description sync check | Completed | 20261012-171422 | 20261012-171422 | check_tool_descriptions_sync passes |

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
- **Requirement ID**: `REQ-004` (document the detection rules)
- **Source issue**: issues/20261012-132457_stale001_fix-stale-detector-false-positives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-132739_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-170854
- **Related target files**: tools/TOOL_DESCRIPTIONS.md