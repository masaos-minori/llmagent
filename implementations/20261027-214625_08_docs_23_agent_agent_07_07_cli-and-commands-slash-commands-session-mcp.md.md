# Implementation Procedure: State the `/undo` parity guarantee in the slash-commands doc

## Goal

Update the `/undo` section of `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` (L34) to state the parity guarantee: memory and DB are trimmed from the same deleted-row set, and when they already diverge `/undo` restores parity (or logs a reload fallback). (`REQ-002`, `REQ-003`, `REQ-007`)

## Scope

One documentation file, `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`. Update the single `/undo` sentence at L34. No other section changed.

## Assumptions

- The current L34 text describes `/undo` as popping "from both the history and the DB" without parity semantics under divergence (Plan evidence).
- This doc is mapped to the Plan via `docs/00_index.md` → `agent_07`; the `/undo` section is the only place `/undo`'s failure behavior is described here.
- Overlap: this file is not targeted by any other active Frozen Plan (overlap scan found none).

## Design decisions

- Extend the existing sentence (do not restructure the section): add that memory and DB are trimmed from the exact same set of deleted rows, and that if they had already diverged, `/undo` still converges them — trimming by row identity, and reloading memory from the DB (logging the decision) when the deleted rows cannot be matched.
- Keep the existing boundary behavior sentence ("Messages that existed when the history was last compressed ... cannot be undone") unchanged.

## Alternatives considered

- Adding a new subsection — rejected: the `/undo` behavior is one sentence; extend it in place to keep the section's structure and cross-links intact.

## Implementation

### Target file
`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`

### Procedure
1. At L34, append the parity guarantee to the `/undo` sentence: memory and DB are removed from the same set of rows; when they had already diverged, `/undo` restores parity by trimming memory to the exact deleted rows, and falls back to reloading memory from the DB (logged) when those rows cannot be matched.

### Method
One sentence extension. No structural change.

### Details
- Example addition (integrate into the existing sentence, do not duplicate it):
  > When memory and the DB have already diverged, `/undo` still converges them: it trims memory to exactly the rows it deletes, and if those rows cannot be matched it reloads memory from the DB and logs the decision.

## Compatibility considerations

- Documentation-only; no code or frontmatter change. The `/undo` boundary sentence and the rest of the section are preserved.

## Security considerations

- N/A: documentation only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run tools/check_docs_quality.py docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
- `uv run tools/check_docs_structure.py docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
- `uv run tools/check_docs_content_policy.py --strict docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
- `uv run tools/check_docs_consistency.py --domain agent docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
- `uv run tools/check_docs_japanese.py docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`

## Completion criteria

- The `/undo` section states the parity guarantee and the divergence failure behavior; all five doc checks pass.

## Out of Scope

- Production changes (rows 01-04).
- Test updates (rows 05-07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the `/undo` sentence with the parity guarantee | Pending | — | — | |
| 3 | Run the documentation check sequence | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-007`
- **Source issue**: issues/20261026-224959_undo002_undo-db-memory-set-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074657_undo002_undo-db-memory-set-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-214625
- **Related target files**: docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md
