## Goal
Update `tools/TOOL_DESCRIPTIONS.md`'s two existing rows for
`generate_reference_table.py` to mention the new `agent`/`eventbus`/`memory`
`--type` values (`REQ-007`).

## Scope
In scope: the 2 existing rows' description text. Out of scope: any other row in
this file.

## ⚠ Implementation gate — do not execute before this is satisfied
Same gate as seq 01-03: REQ-008. This row can technically be edited independent
of the gate (it is pure text), but must not land ahead of seq 01 actually adding
the 3 functions — a `TOOL_DESCRIPTIONS.md` claiming `--type memory` exists while
`main()`'s `choices=` list does not register it (per seq 01's deferred
`--type memory` registration, pending `UNK-01`) would itself be a
documentation/code drift — describe `agent`/`eventbus` as available and
`memory` as "function implemented, `--type` registration pending target-document
confirmation" rather than claiming full parity across all 3.

## Assumptions
- Rows unchanged since the Plan was written — re-confirmed at
  `tools/TOOL_DESCRIPTIONS.md:36` ("RAG/MCP/デプロイメントのリファレンス表生成") and
  `:81` ("`--type rag|mcp|deployment` で指定").

## Design decisions
Extend both rows' existing Japanese description text with the new type names,
matching the file's existing language and terseness (a single short phrase per
row, consistent with every other row in this file).

## Alternatives considered
N/A: format is fully determined by the existing 2 rows' own style — no
alternative phrasing structure was considered.

## Implementation
### Target file
tools/TOOL_DESCRIPTIONS.md

### Procedure
1. Update the description-column text at line 36 to add Agent/EventBus (and
   note Memory as pending), e.g. "RAG/MCP/デプロイメント/Agent/EventBusのリファレンス表生成
   (Memory型は対象文書確定待ち)".
2. Update the usage-column text at line 81 to add the new `--type` choices,
   e.g. "`--type rag|mcp|deployment|agent|eventbus` で指定(`memory`は対象文書確定後に追加予定)".

### Method
Direct text edit (`Edit` tool) — two single-cell text updates in an existing
Markdown table, no structural change.

### Details
- Keep both updates consistent with each other (same set of types named in both
  rows) and with seq 01's actual `main()` `choices=` list at execution time —
  re-read seq 01's committed code before finalizing this row's wording, since
  `--type memory`'s exact availability depends on whether `UNK-01` was resolved
  by the time this row executes.

## Compatibility considerations
Text-only change to 2 existing table cells — no other row affected.

## Security considerations
N/A: documentation-only.

## Rollback considerations
`git checkout -- tools/TOOL_DESCRIPTIONS.md` reverts this row independently.

## Validation plan
- Run `uv run python tools/check_tool_descriptions_sync.py` — confirm it still
  passes (no drift between `tools/*.py` and this file's descriptions).
- Manual review: confirm the description matches seq 01's actual `--type`
  choices at execution time.

## Completion criteria
- Both rows accurately describe the tool's actual `--type` choices as of
  execution time (not necessarily all 3 new types, if `memory` registration is
  still pending `UNK-01`).
- `uv run python tools/check_tool_descriptions_sync.py` passes.

## Out of scope
Any other row in this file; claiming `--type memory` works before it is
actually registered.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Should land alongside/after seq 01 to avoid describing types that don't exist yet; gated on REQ-008 for the overall row set |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `uv run python tools/check_tool_descriptions_sync.py` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own Target file IS the documentation being updated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | REQ-008 gate not satisfied; wording also depends on seq 01's final `--type` choices | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007 (update TOOL_DESCRIPTIONS.md's 2 rows)
- **Source issue**: issues/done/20260918-130225_docsref01_extend-generate_reference_table-for-agent-eventbus-memory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105034_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114740
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
