## Goal

Regenerate the generated API reference so it matches the new and removed symbols (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the generated file only; it is regenerated, never hand-edited. Run it after every code row has landed.

## Assumptions

- Verified: the file lists `get_stdin_reader` and `reset_stdin_reader` at lines 139-140 (consumer scan); the tool's modes are `--type`, `--dry-run`, and `--check` (`--help`).

## Design decisions

- Use the tool's agent reference type, then confirm with `--check`.

## Alternatives considered

N/A: generated file.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
1. After the code rows land, run `uv run python tools/generate_reference_table.py --type agent --dry-run` to preview, then without `--dry-run` to write.
2. Run `uv run python tools/generate_reference_table.py --check` and require exit 0.

### Method
Run the generator; do not edit the file by hand.

### Details
- If the written diff touches unrelated rows, report it rather than editing.

## Compatibility considerations

N/A: generated documentation.

## Security considerations

N/A: generated documentation.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- The generated table lists the controller symbols and no removed symbol; `--check` exits 0.

## Out of Scope

Hand edits, other generated domains.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213744 | 20261122-213744 | Changed: docs/23_agent/agent_13_reference-api-generated.md |
| 2 | Run `uv run python tools/generate_reference_table.py --check` and the documentation checkers | Completed | 20261122-213744 | 20261122-213744 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-009` (generated API table reflects the new symbols)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
