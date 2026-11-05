## Goal

Give the partial-completion counter a single owner: the live runner increments
`ctx.stats.stat_partial_completions`, which every reader already reads, so `/stats`,
the REPL warning, and the exit session summary all report the same value.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `RuntimeStats.stat_partial_completions` already exists on the context and is the
  field every reader consumes.
- The diagnostic-row persistence and best-effort logging inside
  `_handle_llm_error` are unchanged; only the increment target moves.

## Design decisions

- Own the counter on `RuntimeStats`, not on the LLM client attribute, so the writer
  and all readers share one field (`REQ-001`).
- Change only the increment expression; leave the partial/non-partial branching and
  diagnostic writes intact.

## Alternatives considered

- Incrementing the client attribute and keeping a parallel `RuntimeStats` field:
  rejected; two owners reintroduce the drift this Plan removes.
- Adding a new `RuntimeStats` field: rejected; the field already exists.

## Implementation
### Target file
`scripts/agent/llm_turn_runner.py`

### Procedure

- In `_handle_llm_error`, replace
  `ctx.services_required.llm.stat_partial_completions += 1`
  with `ctx.stats.stat_partial_completions += 1`.

### Method

- The change is a single-target swap inside the existing `if e.partial_text:` branch,
  after the two diagnostic rows are persisted and inside the same best-effort
  `try/except` wrapper.

### Details

- `RuntimeStats.stat_partial_completions` is defined on `AgentContext.stats`
  (`scripts/agent/context.py`); all four readers read `ctx.stats.stat_partial_completions`.
- Keep the `await ctx.diagnostics.save(...)` calls and the `logger.warning` guard
  unchanged.

## Compatibility considerations

- Readers are unaffected; they already read `ctx.stats`. The removed client attribute
  is deleted in the companion `scripts/shared/llm_client.py` document.

## Security considerations

- N/A: no auth, secret, or input-handling change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Run the runner-path partial-completion tests and the orchestrator partial tests.
- Confirm `/stats`, the REPL warning, and the exit summary still report the count.

## Completion criteria

- `_handle_llm_error` increments `ctx.stats.stat_partial_completions`; no remaining
  writer touches the client attribute.

## Out of Scope

- Any change to how partial text is stored, shown, or retried.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-084444_01_scripts_agent_llm_turn_runner.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 — give the partial-completion counter one owner
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115736_partialcount001_partial-completion-counter-dead.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-084444
- **Related target files**: scripts/agent/llm_turn_runner.py
