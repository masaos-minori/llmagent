# Implementation Procedure

## Goal

Document the data subcommands (`list`, `load`, `rename`, `delete`) of `/session` alongside the already-listed maintenance subcommands (`REQ-003` / `AC-4`).

## Scope

Modify only `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` (Session Category). Add a data-subcommands description near the existing maintenance-subcommands sentence (current line 38). Documentation-only change.

## Assumptions

- Line 38 currently enumerates only the maintenance subcommands; the data subcommands are undocumented.
- The four data subcommands and their behavior are defined by the implementation in `scripts/agent/commands/cmd_session.py` (the `/session` dispatcher routes `list` / `load` / `rename` / `delete` to its handlers) — read there for accurate one-line descriptions, but do not modify that file.

## Design decisions

- Add a short paragraph (or bullet list) naming the data subcommands with a one-line purpose each, placed immediately before or after the maintenance-subcommands sentence so the two groups read as a pair.
- Keep descriptions at the same abstraction level as the existing doc (user-facing behavior, not internal method names).

## Alternatives considered

- Pointing readers to `cmd_session.py` for data subcommands: rejected — the doc should describe user-facing behavior inline, consistent with how it treats maintenance subcommands.

## Implementation

### Target file

`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`

### Procedure

1. Read line 38 and its surrounding context to match the doc's style and cross-links.
2. Add a data-subcommands block: name `list` (show recent sessions with message count), `load` (resume a session by id), `rename` (set a session title), `delete` (remove a session by id) — one line or a compact list.
3. Verify the new text links consistently to the rest of the document (no dangling references).

### Method

Edit the markdown in place. Do not alter the maintenance-subcommands content or any other section. Keep the language English (per `skills/DESIGN.md` Output language).

### Details

- Do NOT add or reference a mermaid diagram and do NOT touch `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — that file has no session-lifecycle content to correct (`REQ-004` is verify/report only; a Reference File). The authoritative lifecycle is a text flow diagram in `agent_04_01`.

## Compatibility considerations

Documentation-only; no code or config impact.

## Security considerations

N/A: documentation change.

## Rollback considerations

Revert the edit to the doc.

## Validation plan

| Target/Module | Strategy | Command | Expected |
|---|---|---|---|
| `docs/23_agent/agent_07_07...md` | Structural/formatting checker | `uv run python tools/check_docs_quality.py` | Pass |
| `docs/23_agent/agent_07_07...md` | Structure (links, front matter) | `uv run python tools/check_docs_structure.py docs/23_agent/agent_07_07...md` | Pass |
| `docs/23_agent/agent_07_07...md` | Domain cross-check | `uv run python tools/check_docs_consistency.py --domain agent` | Pass |

## Completion criteria

The Session Category doc lists the data subcommands (`list`, `load`, `rename`, `delete`) alongside the maintenance subcommands, and passes the doc checkers above.

## Out of scope

`agent_04_03` verification (`REQ-004`) is a Reference File (verify/report only); no diagram is invented. Code rows are separate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | N/A | — | — | docs-only row |
| 2 | Add or update tests per Validation plan | N/A | — | — | no tests for a doc change |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261014-210736 | 20261014-210736 | doc checkers per routing.md |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261014-210736 | 20261014-210736 | REQ-003 / AC-4 |

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
- **Requirement ID**: `REQ-003` — document the `/session` data subcommands
- **Source issue**: `issues/20261014-150311_sess001_finalize-session-list-command.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261014-160933_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-171726
- **Related target files**: `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`