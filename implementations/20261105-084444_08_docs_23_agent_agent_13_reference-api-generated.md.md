## Goal

Regenerate the generated agent reference so the deleted module's three functions are
removed from the output.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The document currently lists the three functions of the deleted module
  (`handle_llm_transport_error`, `handle_partial_completion`,
  `handle_non_partial_error`).
- `tools/generate_reference_table.py --type agent` rebuilds the table from live source.

## Design decisions

- Regenerate rather than hand-edit, so the table stays in sync with the source.

## Alternatives considered

- Manually deleting the three rows: rejected; drift-prone and not reproducible.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure

- Run `uv run python tools/generate_reference_table.py --type agent`.
- Confirm the deleted module's three functions no longer appear in the table.

### Method

- Regeneration rewrites the generated section; no manual edits follow.

### Details

- Before the change `--check` reports no drift; after deleting the module and
  regenerating, `--check` still reports no drift.

## Compatibility considerations

- N/A: documentation-only regeneration.

## Security considerations

- N/A: documentation-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Run `tools/generate_reference_table.py --check` and confirm no drift.
- Confirm the three deleted functions are absent from the table.

## Completion criteria

- The generated reference lists only live symbols; the deleted module is gone.

## Out of Scope

- Any change to the reference format beyond what regeneration produces.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `generate_reference_table.py --check` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-084444_08_docs_23_agent_agent_13_reference-api-generated.md.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 — regenerate the agent reference without the deleted module
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115736_partialcount001_partial-completion-counter-dead.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-084444
- **Related target files**: docs/23_agent/agent_13_reference-api-generated.md
