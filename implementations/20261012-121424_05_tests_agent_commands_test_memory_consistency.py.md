## Goal
- Remove the unused `mem_store` fixture and the redundant origin patch in `import_ops_fake_helper` (`REQ-002`).

## Scope
- Only this file: the fixtures near lines 164 to 185 and the imports they leave unused.

## Assumptions
- `grep -rn mem_store tests` finds only the definition, so removing the fixture changes no test.
- `import_ops_fake_helper` replaces `import_ops.SQLiteHelper` and `write_ops.SQLiteHelper` by hand, so its `db.helper` patch adds nothing (Plan `UNK-02`).

## Design decisions
- Delete the dead fixture; unwrap the `with patch(...)` in `import_ops_fake_helper` and keep the manual swap and restore.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/commands/test_memory_consistency.py`

### Procedure
1. Delete the `mem_store` fixture (decorator and body).
2. In `import_ops_fake_helper`, remove the `with patch("db.helper.SQLiteHelper", ...)` wrapper and dedent its body; adjust the comment that mentions patching.
3. Remove imports that become unused (`patch`, `MemoryStore`) if ruff reports them.

### Method
- Run the file after step 2 and after step 3; if a test fails because of step 2, revert step 2 and instead add `# mock-patch-ok: redundant origin patch; bound references are replaced manually` to that patch line (Plan `UNK-02`).

### Details
- Keep the manual restore of the two module references after `yield`.

## Compatibility considerations
N/A: test-only change; no runtime or public interface is affected.

## Security considerations
N/A: no input handling, credentials, or I/O boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_memory_consistency.py -v`; `uv run ruff check tests/agent/commands/test_memory_consistency.py`.

## Completion criteria
- `grep -rn mem_store tests` is empty; the file passes with ruff clean.

## Out of scope
- Changing any test body or the `_FakeSQLiteHelper` class.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the `mem_store` fixture and unwrap the redundant patch in `import_ops_fake_helper` | Pending | — | — | |
| 2 | Remove imports left unused | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) for the touched files | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (remove the dead fixture and the redundant origin patches)
- **Source issue**: issues/20261012-120426_mock001_fix-ineffective-mock-patch-targets-in-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-120856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-121424
- **Related target files**: tests/agent/commands/test_memory_consistency.py
