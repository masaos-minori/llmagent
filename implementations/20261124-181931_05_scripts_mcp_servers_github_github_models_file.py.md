## Goal
Make the file-domain request models the strict contract: strict base, the 1 MiB `content` upper
bound, and at least one file in `push_files` (REQ-004 non-empty text and `minItems=1`; REQ-005 upper
bounds; REQ-008 strict base). This row also produces the Plan's only nested model, so it is where
`$defs`/`$ref` first appear in a published schema (UNK-01).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/mcp_servers/github/github_models_file.py` (Plan Phase 4).
- Response models (`GetFileContentsResponse`, `CreateOrUpdateFileResponse`, `PushFilesResponse`,
  `DeleteRepoFileResponse`) stay plain `BaseModel`.

## Assumptions
- `StrictRequestModel` exists from seq 01.
- Owner-confirmed bounds (Plan Assumptions, UNK-02): `content le=1048576` characters (matches
  `config/github_mcp_server.toml` `max_file_size_kb = 1024`), `push_files` files 1..100.
- Empty-string defaults in this file (`GetFileContentsRequest.ref` line 23,
  `CreateOrUpdateFileRequest.branch` 47 and `.sha` 51, `DeleteRepoFileRequest.branch` 108) are
  meaningful sentinels today: `""` means "default branch", and for `sha` it means "new file".
- `github_service_read.py` / `github_service_dispatch_writes.py` pass those defaults through
  unchanged; both files are outside the frozen table for Phase 4.

## Design decisions
- Empty-string sentinels keep `default=""` and are instead guarded by one local
  `model_validator(mode="after")` per model class that rejects an explicitly supplied empty value
  (`field in self.model_fields_set and value == ""`). `min_length=1` alone would make the declared
  default invalid or silently allow the empty value, and a shared "optional sentinel" helper is not
  added: the Plan fixes the shared module's API at base model + generator function, so a reusable
  sentinel helper would be a follow-up Issue, not an improvised addition.
- `PushFile` (line 66) also inherits `StrictRequestModel`: `github_push_files` must reject unknown
  keys inside each file object, not only at the top level. This is what makes `build_input_schema()`
  emit `$defs`/`$ref` (`#/$defs/PushFile`) for that tool.
- `message` (required commit message) gets `min_length=1` (REQ-004 "mandatory text") but no upper
  bound: no owner-confirmed value exists for commit messages, and inventing one is out of scope.

## Alternatives considered
- `min_length=1` on `ref`/`branch`/`sha` with `validate_default=True`: rejected — it breaks the
  documented "default branch"/"new file" sentinel semantics of the existing defaults.
- Flattening `PushFile` inline in the schema: rejected — the Issue mandates keeping `$defs`/`$ref`
  unless provider rejection is proven (UNK-01 path: a live `github_push_files` call, run at seq 11).

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_file.py`

### Procedure
1. Add `from mcp_servers.request_contract import StrictRequestModel` and
   `from pydantic import model_validator`.
2. Switch `GetFileContentsRequest` (14), `CreateOrUpdateFileRequest` (39), `PushFile` (66),
   `PushFilesRequest` (73), `DeleteRepoFileRequest` (94) to `StrictRequestModel`.
3. `owner`/`repo`/`path` on every request model: `min_length=1` (lines 19-22, 42-44, 69, 76-78, 97-99).
4. `content` (45, and `PushFile.content` 70): `max_length=1048576`.
5. `message` (46, 80, 103): `min_length=1`.
6. `PushFilesRequest.files` (79): `min_length=1, max_length=100`.
7. `DeleteRepoFileRequest.sha` (104): `min_length=1` (required to prevent conflicts).
8. Add the sentinel validator described in Design decisions for `ref`, `CreateOrUpdateFileRequest.branch`/`.sha`,
   and `DeleteRepoFileRequest.branch`.
9. Keep the three `dry_run` fields (55, 81, 112) and all `description=` strings unchanged.

### Method
- Field bounds for every required identifier; one after-validator for the optional-sentinel trio;
  no service-layer changes.

### Details
- `PushFile.path`/`content` bounds must be declared on `PushFile` itself: the generated schema for
  `github_push_files` reads them from the `$defs` entry, and seq 11 publishes that schema verbatim.

## Compatibility considerations
- Newly rejected inputs (recorded in seq 18, tested by seq 15/17): unknown/extra keys at either
  level; empty `owner`/`repo`/`path`/`message`; empty `ref`/`branch`/`sha` supplied explicitly;
  `content` over 1048576 characters; `files` empty or with more than 100 entries;
  `github_delete_file` with an empty `sha`.
- Existing `_execute_with_dry_run` short-circuit (`Plan Risk` note) is untouched: publishing
  `dry_run` happens at seq 11.
- The 1 MiB bound is a second, independent guard to `max_file_size_kb = 1024`: the model rejects
  before any HTTP request, the guard still protects against a lower configured cap.

## Security considerations
- Rejecting an empty `sha` on delete removes the "delete without a confirmed blob" path; the
  `content` bound caps the payload the server will hand to the GitHub API.

## Rollback considerations
- Revert this Phase 4 commit; the sentinel validators are the only non-field-bound change.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_request_validation.py` (T-03; file cases added
  by the seq 15 document).
- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py` (T-02, seq 14) — includes the
  `github_push_files` `$defs`/`$ref` shape.
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/github/ -c pyproject.toml`,
  `uv run lint-imports` (T-06).

## Completion criteria
- `PushFilesRequest.model_validate({... "files": []})` raises; a file object with an unknown key
  raises; a 1048577-character `content` raises.
- `build_input_schema(PushFilesRequest)` contains `$defs` with a `PushFile` entry and
  `minItems: 1`, `maxItems: 100`, `maxLength: 1048576`.

## Out of Scope
- `scripts/mcp_servers/github/tools_file.py` (seq 11), tests (seq 14-15, 17), docs (seq 18-19),
  provider-side `$defs` verification run (seq 11 verification step).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply strict base + bounds to the five file request models and `PushFile` | Pending | — | — | REQ-004, REQ-005 |
| 2 | Add the empty-sentinel validators for `ref`/`branch`/`sha` | Pending | — | — | REQ-004 |
| 3 | Confirm coverage through the seq 15 file cases and seq 14 drift gate | Pending | — | — | T-02, T-03 |
| 4 | Run the validation sequence (`rules/toolchain.md`) for this file | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (non-empty text, `push_files` `minItems=1`), `REQ-005` (content upper bound), `REQ-008` (strict base, including nested models)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/github/github_models_file.py`
