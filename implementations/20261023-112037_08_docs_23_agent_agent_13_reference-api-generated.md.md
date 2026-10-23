## Goal

Regenerate `docs/23_agent/agent_13_reference-api-generated.md` so its printed signatures for
the two changed entry points include the new required keyword-only `guard: ToolLoopGuard`
parameter, then re-check the generated file for drift (`REQ-008`, `AC-8`).

## Scope

Only `docs/23_agent/agent_13_reference-api-generated.md`. Regenerate it from source and
confirm the two signature rows reflect the new parameters. This is a documentation-only,
generated-file change.

Reference reads only: `tools/generate_reference_table.py:198-234` (how the signature table is
built).

## Assumptions

- The table prints the current signature of every public top-level function in
  `scripts/agent/*.py`; after rows 1-2 land, both entry points carry the new parameter:
  - `async def execute_one_tool_call(ctx, pc, *, guard: ToolLoopGuard) -> tuple[...]`
  - `async def execute_all_tool_calls(ctx, tool_calls, turn, out_failed_keys, *, guard: ToolLoopGuard) -> None`
- At HEAD the stale rows are `:184` (`execute_one_tool_call(ctx, pc)`) and `:185`
  (`execute_all_tool_calls(ctx, tool_calls, turn, out_failed_keys)`).

## Design decisions

- **Regenerate, do not hand-edit**: the table is machine-generated; editing it by hand would
  drift from the next generation. Run the generator, then `--check` to prove no residual
  drift.

## Alternatives considered

- Manually updating the two rows — rejected by `REQ-008`: the generator is the source of
  truth; a manual edit would be overwritten and could diverge.

## Implementation

### Target file

`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure

1. Implement rows 1-7 first (the signatures depend on the landed code).
2. Run `uv run python tools/generate_reference_table.py --type agent`.
3. Run `uv run python tools/generate_reference_table.py --check --type agent` and confirm
   zero drift.
4. Confirm `docs/23_agent/agent_13_reference-api-generated.md:184-185` now show the new
   `guard` parameter on both signatures.

### Method

The generator introspects the live signatures; once rows 1-2 add the required keyword-only
`guard` to both entry points, regeneration picks them up automatically.

### Details

- Also run `uv run python tools/check_docs_consistency.py --domain agent` to confirm no
  broken function reference.

## Compatibility considerations

- The regenerated rows must match the landed signatures exactly; `--check` failing is the
  signal that a signature was changed without regenerating.

## Security considerations

- N/A: documentation only.

## Rollback considerations

- N/A: revert the commit; the file is regenerated from source.

## Validation plan

- `uv run python tools/generate_reference_table.py --check --type agent` reports no drift.
- `uv run python tools/check_docs_consistency.py --domain agent` reports no broken reference.
- Confirm `:184-185` show the new `guard` parameter.

## Completion criteria

The generated table's `execute_one_tool_call` and `execute_all_tool_calls` rows include the
required keyword-only `guard: ToolLoopGuard`; `generate_reference_table.py --check` reports
no drift; `check_docs_consistency.py --domain agent` is clean.

## Out of Scope

- Any hand-edit of the signature rows beyond what the generator produces.
- Production threading/recording (rows 1-2) and the test migrations (rows 4-7).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the API reference table (`--type agent`) | Pending | — | — | REQ-008; requires rows 1-2 landed first |
| 2 | Re-check for drift (`--check --type agent`) + docs consistency | Pending | — | — | AC-8; zero drift expected |

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
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-092413_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-112037
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
