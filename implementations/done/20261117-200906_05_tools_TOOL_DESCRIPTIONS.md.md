## Goal

Document `tools/generate_issue_batch.py` and its Markdown spec format in
`tools/TOOL_DESCRIPTIONS.md` with new rows only.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 5 of the plan's frozen `Implementation Target Files` table:
`tools/TOOL_DESCRIPTIONS.md` (REQ-007 tool documentation, AC-7).

## Assumptions
- The tool and its rows are created by the seq 01 document; this edit lands after or with
  the tool so the description states true facts.
- Add rows only, edit no existing row: compatible with the other tooling Plans and with the
  archived `implementations/done/20261117-180831_03_tools_TOOL_DESCRIPTIONS.md.md` on this
  file (its rows landed 20261117; plan Assumptions and UNK-02).

## Design decisions
- One Index row plus one detail row in the `## Work Items` table (the lifecycle section),
  rather than the `## Reference Generators` table whose header scopes to `docs/` generators.
- The `--dry-run` Convention writers sentence gains the tool name, consistent with how the
  section lists the other writers.

## Alternatives considered
N/A: row placement follows the file's existing section scopes.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
- Add an Index row after the `generate_workitem.py` row: category `Work item generation`;
  description names the spec-driven batch creation, `--dry-run`, and the post-write
  structure check.
- Add a detail row in the `## Work Items` table after the `complete_doc_procedure.py` row:
  target `issues/` from a Markdown spec; describe the spec format — blocks starting with
  `<!-- issue: {id} {slug} -->` followed by a `templates/issue.md`-shaped document, ids
  unique in the spec, `{{issue:<id>}}` resolves to the allocated path — and the contract:
  whole-spec and collision validation before the first write, `Generated at` is the only
  field the tool sets, atomic writes, exit `0`/`1`/`2`.
- In the `## --dry-run Convention` writers list, add `generate_issue_batch.py`.
### Method
Keep each row a single line; match the neighboring rows' density.
### Details
N/A: no prose outside the three edits.

## Compatibility considerations
Documentation-only; the sync checker requires exactly one row per `tools/*.py`, so no
duplicate rows.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — no finding (row exists for the new
  tool once seq 01 lands; run after the tool file exists).

## Completion criteria
The Index row, the Work Items detail row, and the `--dry-run` writers mention exist, no
existing row changed, and `check_tool_descriptions_sync.py` passes (AC-7).

## Out of Scope
Edits to any existing row; the workflow and SKILL.md text (seq 03, 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261117-225000 | run after the seq 01 tool file exists |
| 2 | Run the documentation checker named in Validation plan | Completed | — | 20261117-225000 | `check_tool_descriptions_sync.py` |

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
- **Requirement ID**: `REQ-007` (tool description and spec format)
- **Source issue**: issues/20261117-123334_wftool005_workitem-batch-generate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125502_wftool005_workitem-batch-generate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-200906
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`