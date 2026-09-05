## Goal

Register `tools/check_docs_content_policy.py` in `tools/TOOL_DESCRIPTIONS.md`,
per `routing.md`'s requirement that a new `tools/` file be documented in the
same change (REQ-008).

## Scope

- In-scope: one new backtick-quoted entry in `tools/TOOL_DESCRIPTIONS.md`.
- Out-of-scope: implementing the script
  (`implementations/20260905-112812_01`); the Governance doc registration
  (`implementations/20260905-112812_02`); the test file
  (`implementations/20260905-112812_03`).

## Assumptions

- **Blocking precondition**: this row describes the tool's purpose, so it
  should be written once the tool's actual detection scope is confirmed
  (same as `implementations/20260905-112812_01`/`_02`), though the entry
  itself does not require the tool to be fully implemented before drafting.
- `tools/check_tool_descriptions_sync.py`'s enforcement mechanism
  (`_live_tool_files()`/`_documented_tool_files()`, re-confirmed present this
  cycle) only checks that a backtick-quoted `.py` filename appears somewhere
  in `tools/TOOL_DESCRIPTIONS.md` — the exact prose describing it is not
  mechanically checked, only its presence.

## Design decisions

Add one new row to `tools/TOOL_DESCRIPTIONS.md`'s existing table, matching
the format of the confirmed existing entries (e.g. the `check_docs_quality.py`
row: tool name | usage/scope | description).

## Alternatives considered

Omitting the entry and relying only on the Governance doc registration
(`implementations/20260905-112812_02`) — rejected: `routing.md`'s rule is
explicit and separate from Governance-doc registration; omitting this entry
was the original gap this Plan's post-Freeze cross-check found and corrected.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. Confirm the existing table structure and its `check_docs_quality.py` /
   `check_docs_structure.py` / `check_docs_consistency.py` entries are still
   present (re-confirmed this cycle via direct grep).
2. Add a new row for `check_docs_content_policy.py`, describing its scope
   (`docs/*.md` full corpus) and what it detects (the five remove-categories),
   matching the existing rows' column format.

### Method

Direct `Edit`: insert one new table row, alphabetically or logically
adjacent to the other `check_docs_*.py` entries (matching this file's
existing grouping, if any — confirmed via direct read at edit time).

### Details

New row content: tool name `check_docs_content_policy.py`; scope column
`docs/*.md` 全体 (matching `check_docs_quality.py`'s row's scope-column
style); description summarizing the five remove-categories it detects and
its report-only status.

## Compatibility considerations

No interface change — documentation registration entry only. Does not alter
any existing `tools/TOOL_DESCRIPTIONS.md` row.

## Security considerations

N/A — documentation-only.

## Rollback considerations

Single-row edit under version control; revert via `git revert` if the
description proves inaccurate once the actual tool lands.

## Validation plan

`uv run python tools/check_tool_descriptions_sync.py` — reports no missing
entry for `tools/check_docs_content_policy.py`.

## Completion criteria

`tools/TOOL_DESCRIPTIONS.md` contains a backtick-quoted
`check_docs_content_policy.py` entry, and
`tools/check_tool_descriptions_sync.py` passes.

## Out of scope

Implementing the script this entry describes. Any other
`tools/TOOL_DESCRIPTIONS.md` row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Sequenced after `implementations/20260905-112812_01` per Plan Phase 3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, no test file (existing `check_tool_descriptions_sync.py` validates it) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `check_tool_descriptions_sync.py`, per Validation plan |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this row's target file is itself the documentation being updated |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/done/20260903-200135_docscope2_build-content-policy-detection-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-102139_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-112812
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
