## Goal

Remove the `/mdq` call site and mention from the runtime architecture doc (REQ-004: update documentation).

## Scope

- Delete one table row, renumber two rows, edit one paragraph. The call-site table (row 2 at line 64) and the Pattern 1 paragraph (line 80).

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Delete the row for `scripts/agent/commands/cmd_mdq.py`, renumber the remaining rows 3 and 4 to 2 and 3.
- Pattern 1 then names only `cmd_context.py`: change the heading mention to `(cmd_context.py)` and the next bullet to singular wording; keep the sentence "Two distinct patterns exist".

## Alternatives considered

N/A: the docs follow the code removal

## Implementation

### Target file

`docs/23_agent/agent_02_runtime-architecture.md`

### Procedure

Apply the edits in Design decisions.

### Method

Edit with the Edit tool, by section; re-read the table after the edit. This doc had 16 commits in 30 days, so fetch and rebase first.

### Details

Do not touch Pattern 2 or the Exempt Paths table.

## Compatibility considerations

N/A: docs-only change

## Security considerations

N/A: docs-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` pass.
- `rg -n -i 'cmd_mdq|/mdq' <this file>` has no match.

## Completion criteria

- Rows are numbered 1 to 3 and Pattern 1 names only `cmd_context.py`.

## Out of scope

- Other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the table and paragraph | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: docs/23_agent/agent_02_runtime-architecture.md
