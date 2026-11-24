## Goal
Make the write-path dispatch build its request models from the whole argument dict and define the one
shared conversion helper that turns `pydantic.ValidationError` into `GitHubValidationError`, so no write
request reaches the business layer with unknown or malformed fields (REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/mcp_servers/github/github_service_dispatch_writes.py` (Plan Phase 6): the 9
  write-domain `fmt_*` methods plus the new `_validate_request()` helper consumed by seq 12.

## Assumptions
- The strict file/issue/PR models exist from seq 03-05, including nested `PushFile` and the
  `UpdatePullRequestRequest` no-op validator from seq 04.
- This row lands before seq 12 in Phase 6 because seq 12 imports the helper defined here (the import
  direction `github_service_dispatch.py` -> `github_service_dispatch_writes.py` already exists at line
  33, and the reverse would create a cycle).
- Verified today: every `fmt_*` here picks `args[...]` keys and `dry_run=args.get("dry_run", False)`;
  `fmt_push_files` (143) hands `args["files"]` (raw dicts) to `PushFilesRequest`, which coerces them
  without rejecting extra keys today.
- `GitHubValidationError` is defined in `scripts/mcp_servers/github/github_models_config.py` (line 110)
  and is not yet imported in this file.

## Design decisions
- `_validate_request(model_cls: type[BaseModel], args: ToolArgs) -> Any` (new) is module-level in this
  file: it calls `model_cls.model_validate(args)`, catches `pydantic.ValidationError`, and re-raises
  `GitHubValidationError` with the model name and the pydantic error count/messages so the caller sees
  an actionable message. Keeping the domain type preserves `exception_handlers.py:42-47` (HTTP 400) and
  the `dispatch_tool` classification (`scripts/mcp_servers/dispatch.py:457-470`, `error_type="validation_error"`,
  HTTP 200 envelope).
- The helper does not log the payload: argument text can contain file content, and the audit layer owns
  request recording.
- No `args.get(...)` fallbacks remain: every default comes from the model, which is what the published
  schema advertises.

## Alternatives considered
- Registering per-tool validators in `tool_validators.py`: rejected in the Plan Design (second
  definition of the same contract).
- Defining the helper in `scripts/mcp_servers/request_contract.py`: rejected — the Plan fixes that
  module's public API at base model + generator function (Plan Risks mitigation), and the helper is
  GitHub-domain exception taxonomy, not a shared contract.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_dispatch_writes.py`

### Procedure
1. Add `import pydantic` (or `from pydantic import BaseModel, ValidationError`),
   `from mcp_servers.github.github_models_config import GitHubValidationError`, and typing for the
   helper.
2. Define `_validate_request()` (new) after `_fmt_body_field` (line 53) and before `WriteDispatchOps`.
3. Replace the model construction in each of the 9 methods: `fmt_create_branch` (89),
   `fmt_create_or_update_file` (113), `fmt_push_files` (143), `fmt_delete_file` (169),
   `fmt_create_issue` (195), `fmt_add_issue_comment` (222), `fmt_create_pull_request` (245),
   `fmt_update_pull_request` (271), `fmt_merge_pull_request` (309) with
   `req = _validate_request(<Model>, args)`.
4. Remove the `dry_run=args.get("dry_run", False)` arguments (the models default to `False`) and the
   per-key `args.get(...)` arguments for optional fields.
5. Keep `_DryRunRequest` (line 36), `_dry_run_preview`, `_execute_with_dry_run`, `_fmt_body_field`, the
   nested `_execute` closures, and every preview/return string unchanged.

### Method
- Authorization still happens inside `_execute_with_dry_run` (`self._assert_allowed_repo(req.owner,
  req.repo)`), i.e. after validation, so a rejected payload never reaches the allowlist check or the
  GitHub API.

### Details
- `_validate_request` (new) must accept the raw `ToolArgs` dict unchanged (no copying, no key injection) so
  `extra="forbid"` sees exactly what the caller sent.
- The helper's error message names the model and lists pydantic's `errors()` field paths, not the values.

## Compatibility considerations
- Newly rejected inputs (recorded in seq 18, tested by seq 15/17): unknown keys at either level of
  `github_push_files`; empty `files`; more than 100 files; `content` over 1048576 characters; empty
  `owner`/`repo`/`path`/`message`/`sha`/`head`/`base`/`title`; `pr_number`/`issue_number < 1`; `body`
  over 65536; `github_update_pull_request` with no update field (seq 04 rule); explicitly empty
  `branch`/`ref`/`sha`; a `merge_method` or `state` outside the declared pattern.
- Missing required keys now produce a `validation_error` result instead of a `KeyError`.
- The 9 `dry_run` preview paths behave as before (`_execute_with_dry_run` short-circuit) now that
  `dry_run` is a published property (seq 08-11).

## Security considerations
- Write payloads are validated before the allowlist check and before any GitHub write; nested batch
  items are validated with the same strictness as the top level.

## Rollback considerations
- Revert the Phase 6 commit (this row + seq 12): key-picking construction returns and the helper is
  removed with it.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_server_endpoints.py` (T-05, seq 17).
- `uv run pytest tests/mcp_servers/github/test_github_request_validation.py` (T-03, seq 15) for the
  model-level cases the helper surfaces.
- `uv run pytest tests/mcp_servers/github/test_github_dry_run*.py tests/mcp_servers/github/` (existing
  dry-run behaviour must not change).
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/github/ -c pyproject.toml`,
  `uv run lint-imports`, `uv run diff-cover coverage.xml --compare-branch=master` (T-06).

## Completion criteria
- `_validate_request()` exists here and is the only place that converts `pydantic.ValidationError` to
  `GitHubValidationError` for GitHub dispatch.
- All 9 write builders use it, and no `args.get(...)` default remains in this file.
- Invalid write payloads produce `is_error=True` / `error_type="validation_error"` and no GitHub service
  method is invoked (asserted in seq 17).

## Out of Scope
- Read-domain builders (seq 12), model bounds and validators (seq 03-06), config strictness (seq 07),
  tests (seq 17), docs (seq 18-19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define `_validate_request()` with the `ValidationError` -> `GitHubValidationError` conversion | Pending | — | — | REQ-008; consumed by seq 12 |
| 2 | Replace the 9 write-domain model constructions with the helper | Pending | — | — | REQ-008 |
| 3 | Confirm dry-run behaviour is unchanged | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) for this file | Pending | — | — | T-05, T-06 |

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
- **Requirement ID**: `REQ-008` (runtime validation aligned with the published schema, domain exception taxonomy)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/github/github_service_dispatch_writes.py`
