## Goal

Update `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS` keys for the 2 entries keyed to `docs/databases/active_databases.md`, reflecting the file's new location at `docs/41_db/active_databases.md`.

## Scope

- **In-Scope**: Updating exactly these 2 test baseline entries in `tests/tools/test_check_docs_quality.py`.
- **Out-of-Scope**: Modifying any other test logic or assertions; adding/removing test cases; changing the structure of `EXPECTED_WITHIN_FILE_PAIRS`.

## Assumptions

- `docsreorg01` and `docsreorg02` have landed before merging this move (confirmed via repository evidence).
- The 2 entries in `EXPECTED_WITHIN_FILE_PAIRS` are keyed to `docs/databases/active_databases.md` (confirmed during issue drafting).
- The file `docs/databases/active_databases.md` has been moved to `docs/41_db/active_databases.md` before this step.

## Design decisions

- Update the key string from `docs/databases/active_databases.md` to `docs/41_db/active_databases.md` in both entries.
- Preserve the value portion of each entry unchanged.

## Alternatives considered

- Regenerating the entire `EXPECTED_WITHIN_FILE_PAIRS` constant: rejected — unnecessary scope expansion; only the 2 affected entries need updating.
- Using a glob pattern instead of exact paths: rejected — would change test semantics beyond the Plan's scope.

## Implementation

### Target file

`tests/tools/test_check_docs_quality.py`

### Procedure

1. Locate the 2 entries in `EXPECTED_WITHIN_FILE_PAIRS` keyed to `docs/databases/active_databases.md`.
2. Replace the key string in each entry from `docs/databases/active_databases.md` to `docs/41_db/active_databases.md`.
3. Verify the updated file passes existing tests.

### Method

Use `sed` or an editor to perform targeted string replacement within the `EXPECTED_WITHIN_FILE_PAIRS` dictionary literal.

### Details

```bash
# Before: find the 2 entries
grep -n "databases/active_databases" tests/tools/test_check_docs_quality.py

# After: replace the key in both entries
sed -i 's|docs/databases/active_databases.md|docs/41_db/active_databases.md|g' tests/tools/test_check_docs_quality.py
```

After execution:
- Confirm `docs/databases/active_databases.md` no longer appears as a key in `EXPECTED_WITHIN_FILE_PAIRS`.
- Confirm `docs/41_db/active_databases.md` appears as a key in `EXPECTED_WITHIN_FILE_PAIRS`.

## Compatibility considerations

- Running `uv run pytest tests/tools/ -q` after the update should pass all existing tests.
- No other code depends on the old key string.

## Security considerations

N/A: This is a test baseline update with no security implications.

## Rollback considerations

To rollback, reverse the sed substitution: `sed -i 's|docs/41_db/active_databases.md|docs/databases/active_databases.md|g' tests/tools/test_check_docs_quality.py`.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/tools/test_check_docs_quality.py | Unit: verify test suite passes after update | `uv run pytest tests/tools/ -q` | All tests pass |

## Completion criteria

- Both entries in `EXPECTED_WITHIN_FILE_PAIRS` use `docs/41_db/active_databases.md` as the key.
- Neither entry uses `docs/databases/active_databases.md` as a key.
- `uv run pytest tests/tools/ -q` passes without errors.

## Out of scope

Modifying any other test logic or assertions; adding/removing test cases; changing the structure of `EXPECTED_WITHIN_FILE_PAIRS`; modifying any source code file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update EXPECTED_WITHIN_FILE_PAIRS keys for active_databases.md entries | Pending | — | — | |
| 2 | Verify test suite passes after update | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (update test baseline for moved file)
- **Source issue**: issues/20260923-141205_docsreorg10_move-database-docs-into-new-db-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-070314_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-101817
- **Related target files**: tests/tools/test_check_docs_quality.py
