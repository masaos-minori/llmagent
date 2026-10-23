## Goal

Document in `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` that
certain `/session` subcommands run for a long time off the event loop, and that a shutdown
request does not interrupt an in-progress storage call. This records the `cmd003` execution
boundary so contributors and operators understand the responsiveness guarantee and its limit.

## Scope

Modify `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` only.
Extend the `### Session Category` section (`:32-64`). No code change; no other doc edited
(this chapter is not mapped in `docs/00_index.md`, so it is the per-command chapter
`agent_07_03` delegates to).

## Assumptions

- The `### Session Category` section currently lists the `/session` subcommands with no
  statement about duration, blocking, or shutdown interaction (plan evidence).
- UNK-01's policy ("a command's storage call is allowed to finish, not interruptible")
  gates the exact wording. Per the plan, this row documents "allowed to finish"; if the
  owner confirms a different policy, the wording must change (Step 6 prerequisite).

## Design decisions

- **Name the long-running subcommands explicitly** (`stats`, `health`, `checkpoint`,
  `vacuum`, `purge`, `recover`, `rag-consistency`, `rag-rebuild-fts`, `rag-rebuild-vec`,
  `export`) so operators know which calls may take seconds.
- **State the execution boundary**: these run outside the event loop (via the offloaded
  `db_dispatch` table), so the REPL stays responsive while they run.
- **State the limit precisely**: a shutdown request does not interrupt an in-progress
  storage call; the call runs to completion, and interpreter shutdown joins the worker. This
  is what the mechanism produces (REQ-006); do not imply stronger cancellation.

## Alternatives considered

- **Point only to `cmd_session.py`.** Rejected: this is the canonical agent-facing session
  chapter; the policy statement belongs here with the code as reference.
- **Claim commands can be cancelled at shutdown.** Rejected: stronger than the mechanism
  provides (UNK-01 / AC-6); the wording must reflect "allowed to finish."

## Implementation
### Target file
`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` (Modify)

### Procedure
1. Read `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` and
   locate `### Session Category` (`:32-64`); confirm current wording before editing.
2. In `### Session Category`, add a statement that the maintenance/export/RAG subcommands
   (`stats`, `health`, `checkpoint`, `vacuum`, `purge`, `recover`, `rag-consistency`,
   `rag-rebuild-fts`, `rag-rebuild-vec`, `export`) may run for a long time and run outside
   the event loop, keeping the REPL responsive.
3. Add the non-interruption rule: a shutdown request does not interrupt an in-progress
   storage call; the call finishes on its own, and process shutdown joins it.
4. Cross-reference `agent_07_03` for the `is_async` contract and
   `tests/agent/commands/test_command_blocking_offload.py` as the regression guard.
5. Keep wording consistent with the existing chapter; do not rewrite other sections.

### Method
- `edit` tool, additive insert into `### Session Category` matching existing heading levels
  and list style.
- Do not restructure the chapter.

### Details
- Wording of the non-interruption rule depends on UNK-01's confirmed policy (plan Step 6).
  Until confirmed, document the mechanism-accurate "allowed to finish" behavior (REQ-006);
  if the owner confirms interruption is desired, that is a separate DB-layer follow-up and
  this doc must not claim it.
- Because no usage code span changes, `tools/check_docs_consistency.py`'s argument-contract
  comparison (GV-023) is unaffected (AC-6); only prose carries the new statements.
- `docs/00_index.md` has no row for this chapter, so the statement belongs here rather than
  in `agent_07_03` (plan Documentation Impact).

## Compatibility considerations

Doc-only edit. Must stay consistent with `agent_07_03` (which documents the `is_async`
contract) and with row 02's offload behavior.

## Security considerations

Documentation edit. No security impact.

## Rollback considerations

Revert the single doc edit
(`git checkout docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`).
No other file touched.

## Validation plan

1. Re-read the chapter to confirm the additions render correctly and headings are
   consistent.
2. Confirm `tools/check_docs_consistency.py --domain agent` reports no GV-023 drift (AC-6).
3. Run the docs checkers in the plan's Validation plan for this chapter.

## Completion criteria

- `### Session Category` names the long-running subcommands and states off-loop execution.
- The non-interruption rule is stated accurately (mechanism-accurate, per REQ-006/UNK-01).
- Docs checkers pass; no argument-contract drift (AC-6).

## Out of Scope

- The offload implementation itself (row 02, `cmd_session.py`).
- The `is_async` contract (row 05, `agent_07_03`).
- DB-layer interruptibility (out of scope for the whole Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261023-164331 | 20261023-164331 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261023-164331 | 20261023-164331 | N/A: doc-only edit, no tests. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-164331 | 20261023-164331 | check_docs_quality/structure/content_policy/consistency(--domain agent)/japanese/skills_references all pass. UNK-01 owner confirmation (plan Step 6) is still Pending; wording documents the mechanism-accurate 'allowed to finish' per REQ-006 and the source issue's measured behavior, not a stronger guarantee. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261023-164331 | 20261023-164331 |  |

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
- **Requirement ID**: REQ-006, REQ-008
- **Source issue**: issues/done/20261021-093421_cmd003-commands-block-the-event-loop-and-are-uncancellable.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-020701_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-023109
- **Related target files**: docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md