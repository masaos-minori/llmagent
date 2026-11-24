## Goal
Make the repository-domain request models the strict contract and publish an honest pagination bound
(`per_page le=100`) plus query/identifier bounds (REQ-004 non-empty text; REQ-005 upper bounds;
REQ-008 strict base).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies `scripts/mcp_servers/github/github_models_repository.py` (Plan Phase 5), plus the two
  repository-domain request constructions in `github_service_dispatch.py` / `github_service_dispatch_writes.py`
  that the branch sentinels invalidate, and one clamp test (Step 3a findings, see Compatibility).
- Response models (`SearchRepositoriesResponse`, `ListCommitsResponse`, `SearchCodeResponse`,
  `ListBranchesResponse`, `GetCommitResponse`, `CreateBranchResponse`) and the info models
  (`RepositoryInfo`, `CommitInfo`, `CodeSearchResult`, `BranchInfo`, `CommitDetail`) stay plain
  `BaseModel`.

## Assumptions
- `StrictRequestModel` exists from seq 01; `DEFAULT_PER_PAGE` is already imported from
  `github_models_config.py` (line 24 of that file).
- `le=100` matches `config/github_mcp_server.toml` `max_per_page = 100` and the GitHub API cap
  (owner-confirmed, Plan Assumptions / UNK-02). A future config with a higher `max_per_page` is a
  documented conflict, not a model change (Plan Risks).
- `ListCommitsRequest.branch` (line 54, `default=""`) and `CreateBranchRequest.from_branch` (153,
  `default=""`) are empty-string sentinels meaning "default branch", handled the same way as seq 05.

## Design decisions
- `per_page` bounds are declared on the model (`ge=1, le=100`) rather than relying on
  `_clamp_per_page` (`github_service_security.py:66-69`): the published schema becomes truthful about
  the current cap, and the clamp stays as defense-in-depth for a lower configured `max_per_page`
  (Plan Design decision, per_page bound entry).
- `per_page` default changes from `DEFAULT_PER_PAGE` (10) to `30` on the four paginated repository
  models (`SearchRepositoriesRequest`, `ListCommitsRequest`, `SearchCodeRequest`,
  `ListBranchesRequest`), matching the value `github_service_dispatch.py` hard-codes today
  (`args.get("per_page", 30)` at lines 47, 62, 78, 105). Owner decision 2026-11-24 recorded in the
  Plan Assumptions: moving the default to the model keeps those four tools' effective page size at 30
  when seq 12 switches dispatch to `model_validate(args)`, and the published `default` then equals
  runtime behaviour. Issues/PR-domain models keep `DEFAULT_PER_PAGE` (10); their dispatch call sites
  already pass 10.
- Same sentinel rule as seq 05: a local `model_validator(mode="after")` rejects an explicitly
  supplied empty `branch`/`from_branch` while keeping the `default=""` semantics, because changing
  the defaults would require touching service files outside the frozen table.
- `sha` in `GetCommitRequest` (127) gets `min_length=1` only: it is a required identifier, not a
  sentinel, in that model.

## Alternatives considered
- `le` taken from config at import time: rejected — the model would depend on config state, making
  the published `/v1/tools` payload start-order dependent and the seq 14 drift gate non-deterministic.
- Dropping `_clamp_per_page` once the model has `le`: rejected — configs with `max_per_page < 100`
  exist as a supported posture; the Plan documents the clamp instead of removing it.

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_repository.py`

### Procedure
1. Add `from mcp_servers.request_contract import StrictRequestModel` and
   `from pydantic import model_validator`.
2. Switch `SearchRepositoriesRequest` (16), `ListCommitsRequest` (49), `SearchCodeRequest` (74),
   `ListBranchesRequest` (100), `GetCommitRequest` (122), `CreateBranchRequest` (147) to
   `StrictRequestModel`.
3. `per_page` (23-27, 55, 81, 105): `default=30, ge=1, le=100` (see Design decisions; drop the
   `DEFAULT_PER_PAGE` import only if no other use remains in this file).
4. `owner`/`repo` (52-53, 76? query-only models aside): `min_length=1` on lines 52-53, 103-104,
   125-126, 150-151.
5. `query` (19, 77): `min_length=1`.
6. `sha` (127): `min_length=1`; `branch_name` (152): `min_length=1`.
7. Add the sentinel validator for `ListCommitsRequest.branch` and `CreateBranchRequest.from_branch`.
8. Keep `CreateBranchRequest.dry_run` (157) and all `description=` strings unchanged.

### Method
- Field bounds for required text and pagination; one after-validator for the two branch sentinels.

### Details
- `SearchRepositoriesRequest` and `SearchCodeRequest` have no `owner`/`repo` field; their only text
  bound is `query`, which the GitHub Search API rejects when empty today.

## Compatibility considerations
- Newly rejected inputs (recorded in seq 18, tested by seq 15/17): unknown/extra keys; `per_page > 100`
  (previously clamped silently to `max_per_page`); `per_page < 1`; empty `query`; empty `branch` or
  `from_branch` supplied explicitly; empty `sha`; empty `branch_name`.
- Silently clamped `per_page` values above the cap become an error result: this is the Plan's
  "advertised contract matches enforcement" goal and must be listed in seq 18.
- Effective default page size for `github_search_repositories`, `github_list_commits`,
  `github_search_code`, `github_list_branches` stays 30 (previously hard-coded in
  `github_service_dispatch.py`); the published schema now declares `default: 30` for them.
- Step 3a findings:
  - `DEFAULT_PER_PAGE` has no remaining use in this file after the four defaults move to 30, so its
    import is removed. Nothing imports it from here (`github_models.py` re-exports it from
    `github_models_config.py`, and `tests/mcp_servers/github/test_github_server_auth.py` imports it
    from `github_models_config`), so the removal breaks no caller.
  - The same interim dispatch problem seq 05 recorded applies to this domain:
    `github_service_dispatch.py` passed `branch=args.get("branch", "")` and
    `github_service_dispatch_writes.py` passed `from_branch=args.get("from_branch", "")`, so an absent
    key arrived as an explicitly empty value and was rejected by the new sentinels. Both call sites now
    pass an absent key as absent; seq 12-13 replace them with `model_validate(args)`.
  - `tests/mcp_servers/github/test_service_repository.py::test_per_page_clamped_to_config_max` passed
    `per_page=999`, which `le=100` rejects; changed to `per_page=50` so the config cap is still exercised.

## Security considerations
- The hard `le=100` caps page size before any GitHub API call, independent of config drift.

## Rollback considerations
- Revert this Phase 5 commit; `per_page` clamping behaviour returns with it.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_request_validation.py` (T-03; repository cases
  added by the seq 15 document).
- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py` (T-02, seq 14, all 21 tools
  gated after this row).
- `uv run pytest tests/mcp_servers/github/test_service_dispatch.py` (pins `== 21` at
  `tests/mcp_servers/github/test_service_dispatch.py:698`; the tool count must not change).
- `uv run ruff check`, `uv run mypy`, `uv run lint-imports` (T-06).

## Completion criteria
- Every repository request model's generated schema carries `maximum: 100` for `per_page` and
  `minLength: 1` for required text.
- `per_page=101` raises instead of being clamped.

## Out of Scope
- `scripts/mcp_servers/github/tools_repository.py` (seq 10), the config `> 0` rule (seq 07), tests
  (seq 14-15, 17), docs (seq 18-19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply strict base + bounds to the six repository request models | Completed | 20261124-212453 | 20261124-212453 | REQ-004, REQ-005 Changed: scripts/mcp_servers/github/github_models_repository.py, scripts/mcp_servers/github/github_service_dispatch.py, scripts/mcp_servers/github/github_service_dispatch_writes.py, tests/mcp_servers/github/test_service_repository.py. |
| 2 | Add the branch sentinel validators | Completed | 20261124-212453 | 20261124-212453 | REQ-004 _reject_empty_branch and _reject_empty_from_branch after-validators; DEFAULT_PER_PAGE import removed (no remaining use in this file). |
| 3 | Confirm coverage through the seq 15 repository cases and seq 14 drift gate | Completed | 20261124-212453 | 20261124-212453 | T-02, T-03 Targeted run: tests/mcp_servers/github/ = 358 passed. T-02/T-03 cases land in seq 14/15. |
| 4 | Run the validation sequence (`rules/toolchain.md`) for this file | Completed | 20261124-225226 | 20261124-225226 | ruff format/check, mypy pass; bandit/lint-imports/module-size and the full-suite run are the end-of-batch run. End-of-batch run (rules/toolchain.md, Batch mode): full pytest 13959 passed / 5 skipped / 6 errors; all 6 errors are the pre-existing tests/tools/test_append_plan_work_items.py contract mismatch (issues/20261124-155017_qa001_append-plan-attr-mismatch.md), none in this batch's files. ruff format+check, mypy, lint-imports, check_module_size, bandit, check_docstrings (after adding the em-dash separator to scripts/mcp_servers/request_contract.py), and diff-cover --fail-under 90 Pass. pre-commit run --all-files fails only on 14 pre-existing procedure-length findings in implementations/20261124-122732_* (issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md); check_workitem_structure --file on this batch's documents reports no findings. |

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
- **Requirement ID**: `REQ-004` (non-empty text), `REQ-005` (`per_page le=100`), `REQ-008` (strict base)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/github/github_models_repository.py`