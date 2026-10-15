## Goal

Regenerate `docs/23_agent/agent_11_04_memory-module-reference-generated.md` from
live code after implementation and verify it agrees with the final subcommand set
(REQ-012).

## Scope

Modify `docs/23_agent/agent_11_04_memory-module-reference-generated.md` only, via
the reference generator (`python tools/generate_reference_table.py --type memory`).
Do not hand-edit the generated section.

## Assumptions

- The generator crawls `scripts/agent/memory/*.py` top-level public classes and
  functions and writes the table between its guard comments; new public symbols
  (e.g. `append_event`, `iter_records`, `reindex`, `collect_prunable_ids`) appear
  automatically once implemented.
- The doc must reflect the new behavior and agree with the final `/memory`
  subcommand set (REQ-012).

## Design decisions

- Regenerate mechanically rather than editing by hand: the doc is auto-generated
  between guard comments, so any hand edit would be overwritten on the next run.

## Alternatives considered

- Hand-editing the generated table: rejected. It is machine-generated; edits are
  lost on regeneration and drift from the code.

## Implementation

### Target file

`docs/23_agent/agent_11_04_memory-module-reference-generated.md`

### Procedure

1. Implement the source changes first (rows 1-29).
2. Regenerate the table.
3. Verify agreement with the final subcommand set.

### Method

- After implementation, run:

  ```bash
  python tools/generate_reference_table.py --type memory
  ```

  (Use `--dry-run` to preview the table before writing.)

- Confirm the regenerated table now includes the new public symbols added by this
  work (for example `JsonlMemoryStore.append_event`,
  `JsonlMemoryStore.iter_records`, `rebuild_ops.reindex`,
  `SQLiteMemoryDeleteStore.collect_prunable_ids`) and reflects the removed
  `rebuild_fts`/`rebuild_vec` command surface where relevant.

### Details

- Do not hand-edit between the `<!-- AUTO-GENERATED ... -->` /
  `<!-- END AUTO-GENERATED -->` guards.
- Verify the slash-command docs (`agent_07_10`, `agent_07_03`) and
  `command_defs_list.py` agree with the final subcommand set as part of REQ-012.

## Compatibility considerations

Regeneration replaces the generated section in place; surrounding hand-authored
content is preserved.

## Security considerations

N/A: documentation generation only.

## Rollback considerations

Revert the commit; the regenerated section is restored to its prior content.

## Validation plan

- Run the docs checker listed in `routing.md` for this doc type.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The regenerated `agent_11_04` reference table reflects the new code and agrees
with the final `/memory` subcommand set.

## Out of scope

The implementation that produces the new symbols (rows 1-29) are separate target
rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate `agent_11_04` from code | Pending | — | — | REQ-012 |
| 2 | Verify agreement with final subcommand set | Pending | — | — | REQ-012 |
| 3 | Run the docs checker + validation sequence | Pending | — | — | |

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
- **Requirement ID**: `REQ-012`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: docs/23_agent/agent_11_04_memory-module-reference-generated.md
