## Goal

Document the `is_async` contract in `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`: `is_async` selects the dispatcher's call form, is validated at registry
construction (a mismatch is a startup `TypeError`), and a contributor adding a `CommandDef`
must ensure `is_async` matches the handler's kind. This closes the gap that let a mismatch
stay invisible until a command was invoked.

## Scope

Modify `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` only. Extend the
`## Responsibility Boundary` statement (currently `:70`) and the `### Adding New Commands`
guidance (`:61-65`). No code change; no other doc edited.

## Assumptions

- The chapter currently owns the statements about `CommandRegistry` (mapped by
  `docs/00_index.md:144`), including a `Responsibility Boundary` sentence at `:70` and an
  `Adding New Commands` subsection at `:61-65`.
- No existing wording contradicts the new rule (`grep -n "is_async" docs/23_agent/*.md`
  returns no match), so this is additive, not a correction of a conflicting statement.

## Design decisions

- **Extend `Responsibility Boundary`** to state that construction validation covers handler
  *kind*, not just handler *string*.
- **Extend `Adding New Commands`** with the explicit rule "`is_async` must match the
  handler's kind, because it is checked at startup" so a contributor hits the failure at
  build/run time rather than at invoke time.
- **State the resulting behavior, not a stronger one**: a mismatch is a startup
  `TypeError`; there is no runtime retry.

## Alternatives considered

- **Put the rule only in `Responsibility Boundary`.** Rejected: the "how do I add a
  command?" question lives in `Adding New Commands`; the contract belongs there too.
- **Link to `registry.py` only.** Rejected: this is the canonical agent-facing chapter; the
  policy statement belongs here with the code as reference.

## Implementation
### Target file
`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (Modify)

### Procedure
1. Read `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` to locate the
   `Responsibility Boundary` statement (`:70`) and the `Adding New Commands` subsection
   (`:61-65`); confirm current heading text before editing.
2. In `Responsibility Boundary`, extend the existing construction-validation sentence to
   state that `CommandRegistry.__init__` validates that each `CommandDef.is_async` matches
   the actual kind of its handler (coroutine function vs sync callable), raising a
   `TypeError` at startup on mismatch.
3. In `Adding New Commands`, add the rule that `is_async` must equal whether the handler is
   an `async def`, and that getting it wrong fails at registry construction (startup), not
   when the command runs.
4. Keep wording consistent with the existing chapter tone; do not rewrite other sections.

### Method
- `edit` tool, additive inserts matching existing heading levels and list style.
- Do not reformat or restructure the chapter.

### Details
- Reference `scripts/agent/commands/registry.py` (`__init__` validation loop,
  `_invoke_handler`) as the source of truth; do not duplicate code spans.
- Do not claim any cancellation/interruption behavior here (that belongs in
  `agent_07_07`); keep this chapter scoped to the `is_async` contract.
- Because no usage code span changes, `tools/check_docs_consistency.py`'s argument-contract
  comparison (GV-023) is unaffected (AC-6); only prose carries the new statements.

## Compatibility considerations

Doc-only edit. Must stay consistent with row 02's `registry.py` behavior and with
`agent_07_07` (which documents the execution boundary, not the contract).

## Security considerations

Documentation edit. No security impact.

## Rollback considerations

Revert the single doc edit (`git checkout docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`).
No other file touched.

## Validation plan

1. Re-read the chapter to confirm the two additions render correctly and headings are
   consistent.
2. Confirm `tools/check_docs_consistency.py --domain agent` reports no GV-023 argument-contract
   drift (AC-6).
3. Run the docs checkers in the plan's Validation plan for this chapter.

## Completion criteria

- `Responsibility Boundary` states the handler-kind construction check.
- `Adding New Commands` states the `is_async`-matches-kind startup rule.
- Docs checkers pass; no argument-contract drift (AC-6).

## Out of Scope

- The production check itself (row 02, `registry.py`).
- The execution-boundary / long-running policy (`agent_07_07`).

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
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008
- **Source issue**: issues/done/20261021-093421_cmd003-commands-block-the-event-loop-and-are-uncancellable.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-020701_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-023109
- **Related target files**: docs/23_agent/agent_07_03_cli-and-commands-command-registry.md
