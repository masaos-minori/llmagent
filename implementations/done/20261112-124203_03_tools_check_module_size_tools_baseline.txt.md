## Goal
Lower the recorded size of `check_docs_content_policy.py` in the tools size baseline to its size after extraction and widening (`REQ-007` / `AC-7`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The line is `check_docs_content_policy.py<TAB>33240` (verified 2026-11-12, line 6 of the baseline file); the baseline only shrinks, and a stale or too-high entry fails the gate.
- Execute after rows 01 and 02, when the final byte size is known (`wc -c tools/check_docs_content_policy.py`).

## Design decisions
- Record the exact byte size after the last change; if the file falls under 24576 bytes the entry must be removed instead (stale entries fail).

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`tools/check_module_size_tools_baseline.txt`

### Procedure
1. `wc -c tools/check_docs_content_policy.py`.
2. Replace `33240` with that size, or delete the line when under the 24576 gate.

### Method
- Keep the tab separator and the sort order of the file.

### Details
- Do not touch other entries.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — pass.

## Completion criteria
- The recorded size equals the file's size (or the entry is removed); the gate passes.

## Out of Scope
- Raising any baseline entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the recorded size | Completed | — | 20261112-211726 | wc -c = 32102; line 6 updated 33240 -> 32102, tab separator and sort order kept; other entries untouched |
| 2 | Run the tools size gate | Completed | 20261112-211726 | 20261112-211726 | check_module_size.py: OK - no new violations (14 baselined modules) |

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
- **Requirement ID**: `REQ-007` — record the reduced size of `check_docs_content_policy.py`
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-111505_adrrev018_docs-checker-harden.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124203
- **Related target files**: `tools/check_module_size_tools_baseline.txt`