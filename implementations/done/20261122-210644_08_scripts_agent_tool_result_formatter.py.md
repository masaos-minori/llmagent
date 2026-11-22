## Goal

Correct the `mask_args` docstring, which says masking is not applied to the interactive approval preview (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: docstring text only; no behavior change.

## Assumptions

- Verified: the claim sits at `scripts/agent/tool_result_formatter.py:69-71`; after the approval row it is false.

## Design decisions

- State that the approval path masks arguments before building the static preview.

## Alternatives considered

N/A: documentation-only change.

## Implementation
### Target file
`scripts/agent/tool_result_formatter.py`

### Procedure
1. Edit the `mask_args` docstring sentence so it says masking applies before logging, audit writes, and the interactive approval preview.

### Method
Docstring edit only.

### Details
- Do not change `build_preview` or the masking functions.

## Compatibility considerations

N/A: no behavior change.

## Security considerations

N/A: documentation only; keeps the stale-claim checker quiet.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run ruff check scripts/agent/tool_result_formatter.py`
- the checkers listed in `rules/tool-gates.md` for a changed `scripts/` file

## Completion criteria

- The docstring matches the approval path's behavior; no code change.

## Out of Scope

Any change to `build_preview` or masking logic; the open mdq dry-run Issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213744 | 20261122-213744 | Changed: scripts/agent/tool_result_formatter.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) and the documentation checkers named in `rules/tool-gates.md` | Completed | 20261122-213744 | 20261122-213744 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-006` (documentation of masked approval previews)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/tool_result_formatter.py`
