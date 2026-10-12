## Goal
- Describe the declared-new target rule and its two new mismatch types in the `stale_detector.py` entry (`REQ-005`).

## Scope
- The single table row for `stale_detector.py` in `tools/TOOL_DESCRIPTIONS.md`; no other row.

## Assumptions
- Lightweight fill: the row is one long Japanese table cell that already lists the checks and the (new) marker for symbols and imports; the new rule is appended in the same style.
- The file's own convention is Japanese descriptions with half-width alphanumerics; tool and mismatch names stay as written in code.

## Design decisions
- Append one sentence instead of restructuring the cell, keeping the row's table syntax intact.

## Alternatives considered
N/A: single-sentence note.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. In the `stale_detector.py` row, append a sentence in Japanese stating: the Target file section の絶対パスの後ろに (new) を付けると新規作成ファイルとして宣言でき、存在確認を省略し、親ディレクトリの存在を要求し(不在は new_target_dir_missing)、既にファイルが存在する場合は new_target_exists として報告し、symbol/import/Before の検査は空ファイルに対して行い、対象ファイルに解決される行番号引用は検査しない。(new) 無しで対象が存在しない場合は従来どおり source_missing。

### Method
- Keep the pipe-delimited row on one line and escape nothing new; do not use a pipe character inside the added text.

### Details
- Do not touch other rows; the sync checker compares the tool list, not the wording.

## Compatibility considerations
- No change to the table shape or the list of tools.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`.
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03, 04 and 05 (documentation); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- The row mentions the declared-new rule and both mismatch types, and the sync checker reports no issues.

## Out of scope
- Other rows and the descriptions of other tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the declared-new target rule to the entry | Completed | 20261012-174543 | 20261012-174543 | stale_detector clean; changed: tools/TOOL_DESCRIPTIONS.md (stale_detector.py row) |
| 2 | Run the tool description sync checker | Completed | 20261012-174543 | 20261012-174543 | check_tool_descriptions_sync pass |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/done/20261012-172916_stale002_allow-new-target-files-in-stale-detector.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-173651_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-173855
- **Related target files**: tools/TOOL_DESCRIPTIONS.md