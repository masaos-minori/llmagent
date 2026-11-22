## Goal

Render the approval prompt with the request id and preview source, passing every rendered string through the shared masker as a final defense (REQ-005, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/tool_output.py`; assertions live in the approval test row.

## Assumptions

- Verified: `emit_approval_prompt` writes the preview verbatim (`scripts/agent/tool_output.py:34-40`).

## Design decisions

- Add keyword-only `request_id` and `preview_source` parameters with empty defaults so existing callers keep working.
- Apply the masker used by `tool_result_formatter` to the preview and to the denial reason; truncation already happened upstream.

## Alternatives considered

N/A: small single-function change.

## Implementation
### Target file
`scripts/agent/tool_output.py`

### Procedure
1. Extend `emit_approval_prompt` with the two parameters and print the id and source in the header line.
2. Mask the preview and `emit_denied` reason text before writing.

### Method
Edit two functions; import the masker module-level like the formatter does.

### Details
- Header format: tag, risk, tool name, then the short request id and the source in parentheses.

## Compatibility considerations

Output gains text; defaults keep older callers and test doubles working.

## Security considerations

Last-resort redaction if an upstream caller forgets to mask (AC-4).

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent -k tool_approval -q`
- `uv run ruff check scripts/agent/tool_output.py && uv run mypy scripts/agent/tool_output.py`

## Completion criteria

- The prompt shows the request id and source; masked text only; existing callers unchanged.

## Out of Scope

Preview construction (approval row), audit fields.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213744 | 20261122-213744 | Changed: scripts/agent/tool_output.py |
| 2 | Run the validation sequence (`rules/toolchain.md`); the approval tests are in the approval test row | Completed | 20261122-213744 | 20261122-213744 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-005` (request id shown), `REQ-006` (rendering through the masker)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/tool_output.py`
