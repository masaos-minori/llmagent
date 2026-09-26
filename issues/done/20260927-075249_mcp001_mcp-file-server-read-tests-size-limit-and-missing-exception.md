# MCP file server read tests size limit and missing exception

## Priority
Medium

## Summary
Two unrelated single-test failures in the MCP file server's read path: a directory-validation test hits an unexpected file-size limit error, and a get-file-info test expects a `FileValidationError` on an OS error that is no longer raised.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
- `tests/mcp_servers/file/test_read_security.py::TestValidateFileDirBranch::test_validates_existing_directory`: raises `mcp_servers.file.common.FileValidationError: File size exceeds the limit (1024 bytes): 4096 bytes` — a directory-validation-branch test unexpectedly triggers a file-size check, suggesting the directory-vs-file branch logic (or the test's fixture file size / configured limit) is off.
- `tests/mcp_servers/file/test_read_service.py::TestGetFileInfo::test_get_file_info_os_error_raises_file_validation_error`: `Failed: DID NOT RAISE <class 'mcp_servers.file.common.FileValidationError'>` — an OS-error-on-stat scenario no longer converts to the expected `FileValidationError`.

These are two distinct, unrelated small bugs grouped here only because they are both single-test failures in the same file-server read-path area; treat as two independent fixes within one review.

## Reason for Change
Both concern the file MCP server's read-path validation/error-handling, which gates file-size and file-vs-directory access control — correctness here has security relevance (file access boundary enforcement).

## Implementation Intent
For the first: read `validate_file_dir_branch`'s current logic to see why a directory-existence check path applies the file-size limit against a 4096-byte value against a 1024-byte configured limit — determine if the test fixture or the branch logic is wrong. For the second: read `get_file_info`'s current OS-error handling to see whether the `except OSError` (or similar) branch was removed/changed to no longer wrap into `FileValidationError`.

## Target Files or Areas
- `scripts/mcp_servers/file/common.py` (confirm exact path for `FileValidationError`, size-limit check, `get_file_info`)
- `tests/mcp_servers/file/test_read_security.py`
- `tests/mcp_servers/file/test_read_service.py`

## Required Changes
- Fix the directory-branch validation so it does not apply the file-size limit incorrectly (or fix the test if its fixture setup was wrong).
- Restore or fix the OS-error-to-`FileValidationError` conversion in `get_file_info`.

## Constraints
Preserve the file-size limit enforcement for actual file reads — do not remove it, only fix its incorrect application to the directory-check branch.

## Acceptance Criteria
- Both listed tests pass.

## Testing Expectations
Run `tests/mcp_servers/file/test_read_security.py` and `tests/mcp_servers/file/test_read_service.py`; run full suite once after the fix.

## Documentation Impact
N/A: internal error-handling correction, no documented-contract change expected unless investigation shows otherwise.

## Out of Scope
Other unrelated failing tests from the same full-suite run.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: whether the size-limit-on-directory-branch issue is a test fixture problem or a production logic problem — requires reading `validate_file_dir_branch`'s current implementation.

## AI Implementation Instruction
Treat these as two independent fixes. Read the relevant function for each before changing anything; do not assume both share a cause.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/mcp_servers/file/test_read_security.py, tests/mcp_servers/file/test_read_service.py
