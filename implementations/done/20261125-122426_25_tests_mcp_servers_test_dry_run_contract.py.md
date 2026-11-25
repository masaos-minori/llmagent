## Goal

Add the cross-server dry-run contract test (REQ-010): previews of file, Git, and GitHub tools leave no durable or overlay state whatever the formatter wording, and a real execution after a preview is not blocked.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The durable-store fixtures of `tests/mcp_servers/test_mcp_dispatch.py` (`DedupStore` with a temp database) are the model for a store fixture here; the module is self-contained and does not import from that test file.
- The preview-capability map is set explicitly with `configure_tool_preview_capabilities` in this test, because it does not run through `run_http`.

## Design decisions

- Stub handlers return the three real wording styles (`[DRY RUN] ...`, `Dry-run: ...`, JSON `"dry_run": true`) so the test fails if any wording starts to matter again.

## Alternatives considered

Driving the real services was rejected as slower and dependent on Git and network state; the contract is the dispatcher's, and the wording styles are copied from the real formatters.

## Implementation
### Target file
`tests/mcp_servers/test_dry_run_contract.py` (new)

### Procedure
Create the test module with a parametrized contract over tool families and wording styles.

### Method
- Parametrize over (tool name, wording): `git_commit` with the `[DRY RUN]` style, `write_file` with the `Dry-run:` style, and a GitHub write tool from `GITHUB_WRITE_TOOLS` with the JSON style.
- Preview case: dispatch with a context of mode `preview`, assert the ledger and `_duplicate_cache` are empty, `execution_mode == "preview"`, `side_effect_applied is False`.
- Dry-run then real: after the preview, dispatch the same key as `applied` and assert the handler runs and the row is `completed`.
- Wording regression: patch each stub's output to a different string and assert the same outcome.
- Keyless side-effecting call is rejected with idempotency_key_required; a read-only keyless call executes; a replay returns no_op.

### Details
- Use `tmp_path` for the store database; close the store in teardown.

## Compatibility considerations

New test module only.

## Security considerations

N/A: test code.

## Rollback considerations

N/A: delete the file.

## Validation plan

- `uv run pytest tests/mcp_servers/test_dry_run_contract.py`
- `uv run ruff check`, `uv run ruff format`, `uv run mypy tests/mcp_servers/test_dry_run_contract.py`

## Completion criteria

- Every wording style yields the same no-state preview outcome.
- Dry-run then real execution succeeds for each tool family.

## Out of Scope

- Testing the formatters themselves.
- Agent-side behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test file described in Implementation > Procedure/Method/Details | Completed | 20261125-174903 | 20261125-174903 | new file; parametrized over 3 families/wordings; deviation: the JSON wording is rendered by string replacement because .format() treats the literal braces as a field; ledger assertion includes the 'attempt' row the acquire writes before completion |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-180342 | 20261125-180342 | 12 cases (3 families x 3 contract tests + keyless side-effecting, keyless read-only, replay); 12 passed plan batch: end-of-batch full-suite run pending; targeted run 12 passed. This procedure has 2 rows (test-only), so the validation row is Step 2, not Step 3 end-of-batch full-suite run: 14369 passed, 4 skipped; diff-cover 92% (>=90) on changed lines; run_validation_gates.py passes |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `tests/mcp_servers/test_dry_run_contract.py`