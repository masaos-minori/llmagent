## Goal

Extend `tests/mcp_servers/file/test_file_write_mcp_service.py` with the cases that pin the new
file-write guards: the `edit_file` byte limit, the atomic write path, post-write size verification, and
post-move verification (REQ-004, REQ-005).

## Scope

- Add an `edit_file` over-limit rejection test.
- Add an `edit_file` atomic-path test that asserts the tmp-file write path is used.
- Add a post-write size-mismatch test for `write_file` and for `edit_file`.
- Add post-move verification tests for `move_file`: missing destination and surviving source.
- Leave every existing test unchanged.

## Assumptions

- The existing `service` fixture sets `max_write_bytes` to 1 MiB, so an over-limit case must build its
  own service with a small limit rather than reuse the fixture's limit.
- Simulating a partial write by replacing `_atomic_write` with an under-writing stand-in is the
  deterministic way to reach the verification branch without filesystem or OS fakery.

## Design decisions

- Use `pytest.raises(FileValidationError, match="post-write verification failed")` and
  `match="post-move verification failed"` so the tests assert which guard fired, not merely that
  something raised.
- Assert the over-limit case raises before any write by checking the file content is unchanged.

## Alternatives considered

- Trigger the size mismatch by patching `os.replace`: rejected — `_atomic_write` then fails on the
  missing target before verification runs, so the test would exercise the wrong branch.
- Trigger it with a read-only directory: rejected — not portable and it raises through the permission
  path instead.

## Implementation

### Target file

`tests/mcp_servers/file/test_file_write_mcp_service.py`

### Procedure

1. Add a class for the byte limit and atomic path.
2. Add a class for post-write verification.
3. Add a class for post-move verification.

### Method

Build services directly with `WriteFileService(allowed_dirs=[tmp_path], max_write_bytes=...)` where a
specific limit is needed, and use `unittest.mock.patch.object` on `WriteFileService._atomic_write` or on
`shutil.move` in `mcp_servers.file.write_service` to simulate a mutation that did not produce the
expected resulting state.

### Details

- Over-limit case: service with `max_write_bytes=8`, existing file `abc`, one edit producing 20
  characters, `recursive`-free `EditFileRequest` with `dry_run=False`; assert
  `FileValidationError` and that the file still contains `abc`.
- Atomic-path case: patch `WriteFileService._atomic_write` with a recorder and assert it is called once
  for an `edit_file` that changes content, and that no `.tmp_` file remains afterwards.
- Post-write mismatch cases: patch `WriteFileService._atomic_write` with a stand-in that writes
  `content[:-1]` and returns the short size; assert `FileValidationError` matching
  `post-write verification failed` for both `write_file` and `edit_file`.
- Post-move cases: patch `mcp_servers.file.write_service.shutil.move` with a no-op to assert the
  missing-destination rejection, and with `shutil.copy2` to assert the surviving-source rejection; both
  expect `FileValidationError` matching `post-move verification failed`.
- `dry_run` behaviour is already covered by the existing classes in this file and is not re-tested here.

## Compatibility considerations

- No existing assertion is changed; the file's current dry-run and happy-path tests must keep passing,
  which is the regression check for the service changes in Plan row 4.

## Security considerations

N/A: test-only change; the cases assert guards are enforced rather than relaxed.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest -q tests/mcp_servers/file/test_file_write_mcp_service.py`
- `uv run pytest -q tests/mcp_servers/file/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`

## Completion criteria

- The four new groups pass against the implementation from Plan row 4 (AC-004, AC-005).
- Each new failure test names the guard it exercises through its `match` pattern.
- All pre-existing tests in the file still pass.

## Out of scope

- `create_directory` behaviour.
- Server-layer audit-record tests, which live in Plan row 7.
- Changing `max_write_bytes` defaults.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the byte-limit and atomic-path cases | Completed | 20261017-190500 | 20261017-192200 | REQ-005 |
| 2 | Add the post-write and post-move verification cases | Completed | 20261017-190500 | 20261017-192200 | REQ-004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-190500 | 20261017-192200 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The "Leave every existing test unchanged" assumption does not hold: Plan row 4 routes `edit_file` through `_atomic_write`, which writes `.tmp_readonly.txt` before the target, so the existing `test_edit_write_permission_error_raises_auth_error` patch — keyed on the exact name `readonly.txt` — stopped firing. Its predicate was widened to `{"readonly.txt", ".tmp_readonly.txt"}` during the Plan row 4 cycle so the test still asserts the permission-error mapping. | True | 20261017-182951 |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `tests/mcp_servers/file/test_file_write_mcp_service.py`