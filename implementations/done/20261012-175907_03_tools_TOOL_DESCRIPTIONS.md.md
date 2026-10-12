## Goal
- Describe the five recognized classes of non-Python names in the `stale_detector.py` entry (`REQ-005`).

## Scope
- The single table row for `stale_detector.py` in `tools/TOOL_DESCRIPTIONS.md`; no other row.

## Assumptions
- Lightweight fill: the row is one long Japanese table cell already describing the checks, the (new) marker, and the declared-new target rule; the new sentence is appended in the same style.
- The file's convention is Japanese descriptions with half-width alphanumerics; identifiers stay as written in code.

## Design decisions
- Append one sentence rather than restructure the cell, keeping the table syntax intact.

## Alternatives considered
N/A: single-sentence note.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. In the `stale_detector.py` row, append a sentence in Japanese stating: どの`.py`にも存在しないシンボルのうち、builtin名・dunder名、lintルールコード(英大文字1〜4字+数字2〜4桁)、兄弟手順書番号(`_`+数字のみ)、`docs/`配下のファイル名の接頭辞に一致する章id、config系ファイル(`config/`・`conf.d/`・`schemas/`・`deploy/`・`init.d/`・`pyproject.toml`・`tox.ini`)のkey位置に現れる名前はsymbol_missingとして報告しない。コメント内の言及はkeyとみなさない。

### Method
- Keep the pipe-delimited row on one line and do not use a pipe character inside the added text.

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
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03 (documentation); the new-class tests must be seen failing before the code is edited.

## Completion criteria
- The row lists the five classes and the comment rule, and the sync checker reports no issues.

## Out of scope
- Other rows and the descriptions of other tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the recognized-classes sentence to the entry | Completed | 20261012-180706 | 20261012-180706 | stale_detector clean; changed: tools/TOOL_DESCRIPTIONS.md (stale_detector.py row) |
| 2 | Run the tool description sync checker | Completed | 20261012-180706 | 20261012-180706 | check_tool_descriptions_sync pass |

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
- **Source issue**: issues/done/20261012-172959_stale003_stop-flagging-non-python-names-as-missing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-175722_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-175907
- **Related target files**: tools/TOOL_DESCRIPTIONS.md