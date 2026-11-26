## Goal

Remove the unprovable `RAG hits` enumeration from the `/stats` row and keep the `not yet implemented, SHARED-003`
parenthetical, which is verified accurate (REQ-004; AC-2).

## Scope
**Release unit**: N/A: no release unit

## Assumptions

- Confirmed in Step 3a: the row at `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md:106`
  enumerates `RAG hits`, but the stats model has no RAG hits field (`scripts/agent/commands/models.py:30-47`) and
  `cmd_config_stats.py` prints no RAG count; `rag_db_configured` only gates a hint line at `:141-143`.
- Confirmed in Step 3a: the aggregate-state clause's parenthetical is accurate — `cmd_config_stats.py:130-136` prints
  memory aggregate counters only, no Repository Context aggregate state, and SHARED-003 is still `open` in
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.
- The remaining enumerated items are printed by the implementation (`:112-114`, `:127`, `:141`) and the named test
  proves the output format (`tests/agent/commands/test_agent_cmd_config.py:99-115`). Per REQ-007 the verification
  record against source is the evidence for a documentation sentence, since no test proves a sentence by itself.
- `tests/agent/commands/test_agent_cmd_config.py` is a validation reference, not a modification target: it is not a
  row of the Plan's target table.
- Statements no test proves are reported, not written: the memory aggregate lines and the `Debug mode` line have no
  asserting test, so no new statement about them is added here.

## Design decisions

- Only the enumeration is changed. The privacy scope sentence and the SHARED-003 parenthetical stay, because removing
  the parenthetical would state as implemented something the source does not implement.

## Alternatives considered

- Removing the parenthetical as the Issue's Required Changes suggested — rejected by Step 3a verification and the
  maintainer decision of 2026-11-26: the aggregate-state reporting it names is not implemented.
- Rewriting the row to list only test-asserted labels — rejected: that would remove accurate statements and exceed
  the row's change responsibility.

## Implementation
### Target file
`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
### Procedure

- Delete `RAG hits` from the parenthesized enumeration in the `/stats` row at `:106`.

### Method

- Cell-level edit of one row; the rest of the row, including the privacy scope and the parenthetical, is unchanged.

### Details

- Keep the row's other enumerated items and the `changes nothing` clause as they are.

## Compatibility considerations

- `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` holds the canonical `/stats` specification owned
  by cliplc011; this Plan changes only the copy in this file, so the two documents must not diverge — the change here
  removes a claim, it does not add one.

## Security considerations

- N/A: documentation-only change; the privacy scope statement is preserved.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_agent_cmd_config.py`: passes; no unprovable enumeration item
  remains in the row.
- Docs gate — `uv run python tools/check_docs_consistency.py --domain agent`.
- Sequence: format → lint → type → arch → security → test → coverage (`rules/toolchain.md`).

## Completion criteria

- The row lists only output the implementation produces, the SHARED-003 parenthetical and the privacy scope remain,
  the corrected statement matches the implementation, and the docs gate reports no finding.

## Out of Scope

- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (UNK-03, reported to the maintainer).
- `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (owned by cliplc011).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the enumeration item per Procedure/Method/Details | Pending | — | — | Plan Phase 4 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Plan Phase 7 |

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
- **Requirement ID**: `REQ-004` (stale claim removed where the implementation contradicts it)
- **Source issue**: `issues/20261119-145312_cliplc014_cli-docs-consolidation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-223853_cliplc014_cli-docs-consolidation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-001124
- **Related target files**: `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
