## Goal

Regenerate `registry/manifests/agent_api.yaml` so the generated contract matches the code (fallout amendment, 2026-11-22).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the generated manifest only; regenerated, never hand-edited.

## Assumptions

- Verified: `uv run python tools/generate_reference_table.py --check` reported `registry/manifests/agent_api.yaml` stale after the code rows landed (new controller symbols, removed CLIView symbols).

## Design decisions

- Run the generator in manifest mode; do not edit the file by hand.

## Alternatives considered

N/A: generated file.

## Implementation
### Target file
`registry/manifests/agent_api.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests`, then `uv run python tools/generate_reference_table.py --check` and require exit 0.

### Method
Generator run; review the diff for only expected symbol or field changes.

### Details
- If the written diff touches unrelated entries, report it instead of editing.

## Compatibility considerations

N/A: generated contract.

## Security considerations

N/A: generated contract.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- The manifest is current and `--check` exits 0.

## Out of Scope

Hand edits and other manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213744 | 20261122-213744 | Changed: registry/manifests/agent_api.yaml |
| 2 | Run `uv run python tools/generate_reference_table.py --check` | Completed | 20261122-213744 | 20261122-213744 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-009` (generated API contract; plan amendment, fallout)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `registry/manifests/agent_api.yaml`
