## Goal

Regenerate the API-reference table in `docs/23_agent/agent_13_reference-api-generated.md`
from live code so it reflects the new/changed public symbols in rows 1-10 (notably the
`TerminationOutcome` enum from row 1 and any signature changes). This is a **generated
file**: the procedure is to run the generator, not to hand-edit the table.

## Scope

`docs/23_agent/agent_13_reference-api-generated.md` only, produced by
`tools/generate_reference_table.py --type agent`. Reference: all rows 1-10 whose public
API may have changed. No hand-written table content.

## Assumptions

- The generator reads public symbols from `scripts/agent` and writes the agent reference
  table; adding `TerminationOutcome` (row 1) and any signature changes should appear after
  regeneration.
- A prior committed version exists to diff against.

## Design decisions

- **Regenerate, then verify.** Run the generator and confirm the output includes the new
  public symbols:
  ```bash
  python tools/generate_reference_table.py --type agent
  ```
  Then validate drift-free:
  ```bash
  python tools/generate_reference_table.py --check --type agent
  ```
- **Diff before committing.** `git diff docs/23_agent/agent_13_reference-api-generated.md`
  should show the expected additions (e.g., `TerminationOutcome`) and no unrelated churn.
- **If the diff shows unexpected removals or missing symbols**, investigate whether a
  public symbol in rows 1-10 is undocumented (add a docstring/`__all__` entry) rather than
  forcing the generator.

## Alternatives considered

- Hand-editing the generated table — rejected: it is regenerated from live code and would
  drift on the next run.

## Implementation

### Target file

`docs/23_agent/agent_13_reference-api-generated.md` (generated)

### Procedure

1. Confirm the current committed state: `git diff --stat HEAD -- docs/23_agent/agent_13_reference-api-generated.md`.
2. Regenerate: `python tools/generate_reference_table.py --type agent`.
3. Validate: `python tools/generate_reference_table.py --check --type agent` (exit 0 = no drift).
4. Review `git diff` for the expected additions (`TerminationOutcome`, any signature
   changes from rows 2-10); ensure no unrelated churn.
5. If `--check` exits 1, reconcile the source symbol (document it) and re-run.

### Method

Run the generator; review the diff; do not hand-edit the table.

### Details

- AC-9 (the reference-table check) is satisfied by the `--check --type agent` pass passing
  after regeneration.
- This row depends on rows 1-10 being implemented; if run during the document-only phase,
  the generator reflects current HEAD and the diff will be empty until the source changes
  land.

## Compatibility considerations

- Generated-doc only; no source or behavioral impact.

## Security considerations

- N/A.

## Rollback considerations

- Single logical commit; `git checkout -- docs/23_agent/agent_13_reference-api-generated.md`
  restores HEAD. Reversible.

## Validation plan

- `python tools/generate_reference_table.py --check --type agent` exits 0.
- `git diff` shows only the expected public-symbol additions.
- `uv run ruff check tools/generate_reference_table.py` if the tool is in scope.

## Completion criteria

`agent_13_reference-api-generated.md` is regenerated from live code, `--check --type agent`
passes, and the diff contains the expected new public symbols with no unrelated churn.

## Out of Scope

- The vocabulary (row 1), the source changes (rows 2-10), the source tests (rows 12-17),
  and the hand-written doc corrections (rows 18-20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate reference table (`--type agent`) | Pending | — | — | Generated file |
| 2 | Validate drift-free (`--check --type agent`) | Pending | — | — | AC-9 |

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
- **Requirement ID**: AC-9
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
