## Goal

Wire the read path of `github_get_file_contents` to the boundary added in row 4: apply the path denylist to reads (REQ-005: denied paths are rejected for reads as the documentation states), check the content metadata size against the read limit before decoding (REQ-006: `max_file_read_size_kb`, `0` = unlimited), and replace the silent lossy decoding with an explicit rejection (REQ-007: content that does not decode as UTF-8 is rejected).

## Scope
**Release unit**: boundary tests (the test cases that lock this behavior are written in Phase 2 and fail until Phase 3 lands)

## Assumptions

- `_assert_allowed_path()` and `_assert_max_read_file_size()` are provided by `scripts/mcp_servers/github/github_service_security.py` (row 4); this document calls them, it does not define them.
- "Binary content" is defined only as content that does not decode as strict UTF-8 (Plan D-5): no magic-byte or content-type sniffing, no new setting.
- With the shipped config (`path_denylist` empty, `max_file_read_size_kb` 0) only the decoding behavior changes; the two guards are pass-throughs at the shipped values (Plan Assumptions).
- `GetFileContentsResponse.encoding` stays `"utf-8"` and no new response field is added (`scripts/mcp_servers/github/github_models_file.py` is a Reference File, not a target).

## Design decisions

- Order of checks on the read path: the repository boundary runs inside `_get_repo()`, the path denylist is checked before the API call (matching the write paths at lines 71-72), and the size check uses the metadata size after the content is fetched but before any decoding — AC-6 requires rejection before decoding happens.
- The decode failure is raised as `GitHubValidationError` naming the path, consistent with the module's existing directory guard (line 50) and the repository's domain-exception style.

## Alternatives considered

- Keeping `errors="replace"` and reporting the substitution in the response — rejected by REQ-007: a silent substitution makes binary content look like text.
- Checking the decoded length instead of the metadata size — rejected by REQ-006: it would require decoding first, which is the step the limit exists to protect.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_file.py`

### Procedure
1. In `get_file_contents()` (line 36), call `_assert_allowed_path(req.path)` before the `_sync()` closure runs, at the same position the write methods use (lines 71, 118, 164).
2. Inside the `_sync()` closure, after the directory guard and before decoding, call `_assert_max_read_file_size(file_content.size, req.path)`.
3. Replace `decode("utf-8", errors="replace")` (line 53) with strict decoding, and wrap the `UnicodeDecodeError` in `GitHubValidationError` naming `req.path`.
4. Change nothing else in the file: the three write methods keep their existing guard calls and audit behavior.

### Method
- The guards are called through the inherited `GitHubSecurityGuards` mixin; no new import beyond the existing `GitHubValidationError` import is needed.
- The error text names the path, not the content, so the message stays identifier-only per the module's logging convention.

### Details
- File size 7247 B at baseline, well below the 24576 B gate.
- The existing `isinstance(file_content, list)` directory guard stays in the same position; its test case must not change (Plan Validation plan).

### Companion test files
- `tests/mcp_servers/github/test_service_file.py`
  - Procedure: extend `TestGetFileContents` with the denial cases — out-of-allowlist repository, a `path_denylist` match, an oversized metadata size with `max_file_read_size_kb` positive and with `0`, and non-decodable content; replace `test_decodes_with_replace_on_invalid_utf8` (line 107), which locks the behavior REQ-007 removes, with the explicit-error case.
  - Validation: `uv run pytest tests/mcp_servers/github/test_service_file.py` (AC-1, AC-5, AC-6, AC-7); the denial cases are written before this row lands, per the release unit.

## Compatibility considerations

- Behavior change for callers: reads of denied paths, oversized files, and non-UTF-8 content now fail instead of returning substituted text (Plan D-5, Risks). The characterization test that locks the current decoding behavior is updated in the same commit as this implementation.
- The response model is unchanged, so existing consumers of `GetFileContentsResponse` are unaffected apart from the new failure mode.

## Security considerations

- `path_denylist` and `max_file_read_size_kb` are presented as security controls in the documentation; this row is where the read path actually honors them, which is what REQ-009 and REQ-011 require the posture and docs to state.

## Rollback considerations

- High: reverting the three call sites restores the current read behavior with no config or data change (Plan D-5).

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/mcp_servers/github/github_service_file.py` | Unit (mocked GitHub client) | `uv run pytest tests/mcp_servers/github/test_service_file.py` | Denied path, oversized size, and non-decodable content are refused before decoding; the `errors="replace"` case is replaced; the directory case is unchanged |
| Same file | Quality gates | `uv run ruff check scripts/mcp_servers/github/github_service_file.py`, `uv run mypy scripts/mcp_servers/github/github_service_file.py`, `uv run bandit scripts/mcp_servers/github/github_service_file.py` | No finding |

## Completion criteria

- `github_get_file_contents` cannot return content for a repository, a path, or a size the configuration denies, and no U+FFFD substitution occurs (AC-1, AC-5, AC-6, AC-7).

## Out of Scope

- Defining `_assert_max_read_file_size()` (row 4) and the config fields (row 3).
- A base64 file-read tool (Plan Out of Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261124-152854 | 20261124-152854 |  |
| 2 | Add or update tests per Validation plan (companion `tests/mcp_servers/github/test_service_file.py`) | Completed | 20261124-152854 | 20261124-152854 | The replaced characterization case is updated in the same commit test_decodes_with_replace_on_invalid_utf8 replaced by the strict-decode refusal case: intentional behavior change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261124-152854 | 20261124-152854 |  |

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
- **Requirement ID**: REQ-005 (path denylist on the read path), REQ-006 (read-size check before decoding), REQ-007 (strict UTF-8 decoding)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `scripts/mcp_servers/github/github_service_file.py`, `tests/mcp_servers/github/test_service_file.py`