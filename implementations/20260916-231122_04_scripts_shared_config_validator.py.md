## Goal

Correct `RagConfigValidator._check_removed_semantic_cache_keys()`'s validation message in `scripts/shared/config_validator.py` to cite the complete, correctly-pathed issue references — `issues/done/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md` and `issues/done/20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md` — replacing the current truncated/mis-pathed text.

## Scope

- Correct the string-literal in `_check_removed_semantic_cache_keys()` (lines 66-72) in `scripts/shared/config_validator.py`
- No other files are modified in this row

## Assumptions

- The two full, correct filenames exist at their exact paths under `issues/done/`:
  - `20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md`
  - `20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md`
- `tests/shared/test_config_validator.py` asserts on the `errors`/`warnings` structure, not the message's exact issue-reference substring (confirmed by read).
- This is a string-literal-only change — no import, signature, schema, or control-flow change.

## Design decisions

- Replacing the truncated ellipsis text with the full, correctly-pathed issue references rather than removing the references entirely — the Issue's AC requires "Validation messages contain actionable current references rather than ellipses".

## Alternatives considered

- Removing the historical references — rejected: they provide actionable context for users encountering the error; the Issue's AC requires them to be replaced with current references, not removed.

## Implementation

### Target file

`scripts/shared/config_validator.py`

### Procedure

Correct the semantic-cache issue references in `config_validator.py`'s validation message.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/shared/config_validator.py` lines 66-72.
2. Verify the two full, correct filenames exist at their exact paths under `issues/done/`:
   ```bash
   ls issues/done/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
   ls issues/done/20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md
   ```
3. Correct the string-literal in `_check_removed_semantic_cache_keys()` (lines 66-72):
   - Replace `issues/done/20260902-150339_semcacherm_...` with `issues/done/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md`
   - Replace `issues/20260902-150341_semcachedocs_...` with `issues/done/20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md`

### Details

```python
# Lines 66-72: correct the string-literal:
# Before:
            return (
                f"Configuration key(s) {keys_str} are no longer supported -- "
                "the semantic cache feature was removed (see issues/done/20260902-150339_semcacherm_..."
                " and issues/20260902-150341_semcachedocs_...); "
                f"remove {keys_str} from your configuration."
            )

# After:
            return (
                f"Configuration key(s) {keys_str} are no longer supported -- "
                "the semantic cache feature was removed (see issues/done/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md"
                " and issues/done/20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md); "
                f"remove {keys_str} from your configuration."
            )
```

## Compatibility considerations

- No production code depends on the specific string-literal text being changed.
- `tests/shared/test_config_validator.py` must continue to pass unmodified — only asserts on the `errors`/`warnings` structure, not the message's exact issue-reference substring (confirmed by read).

## Security considerations

- No security impact. This is a string-literal correction, not a security boundary change.

## Rollback considerations

- Reverting this change restores the original string-literal. If needed later, the string-literal should be corrected again to match the current state of the referenced files.

## Validation plan

- Regression: run `uv run pytest tests/shared/test_config_validator.py -v` to confirm no failures introduced.
- Static analysis: `uv run ruff check scripts/shared/config_validator.py`, `uv run mypy scripts/shared/config_validator.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `_check_removed_semantic_cache_keys()`'s validation message cites both full, correctly-pathed issue filenames.
- All existing tests in `tests/shared/test_config_validator.py` continue to pass without modification.
- No new lint/type errors introduced.

## Out of scope

- Changes to `docs/*.md` — not applicable to this row.
- Modifying any other file — covered by separate rows (REQ-001, REQ-002, REQ-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct semantic-cache issue references in config_validator.py validation message | Completed | 20260917-201932 | 20260917-201932 |  |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-201933 | 20260917-201933 |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260914-103349_mcpagent09_routing-discovery-test-config-documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-131528_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-231122
- **Related target files**: scripts/shared/config_validator.py