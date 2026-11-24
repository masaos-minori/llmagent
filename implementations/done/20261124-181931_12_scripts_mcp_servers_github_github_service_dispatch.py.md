## Goal
Make the read-path dispatch build its request models from the whole argument dict
(`Model.model_validate(args)`) so the runtime rejects exactly what the published schema advertises,
and report failures as `GitHubValidationError` (REQ-008, discovery-time and runtime agree).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/mcp_servers/github/github_service_dispatch.py` (Plan Phase 6): the 12
  read-domain `fmt_*` methods.
- The write-domain half of the same phase is seq 13; the conversion helper is provided there and
  consumed here.

## Assumptions
- Implementation order inside Phase 6: seq 13 lands first (it defines `_validate_request` (new)), then this
  row. Both are one commit per the Plan's per-phase commit rule; the seq numbers reflect the frozen
  table order, not the landing order.
- Verified today: each `fmt_*` builds its model by picking `args[...]` keys, so unknown keys never
  reach the model (they are dropped) and a missing required key raises `KeyError` rather than a
  validation error.
- `pydantic.ValidationError` is a `ValueError` subclass, so `scripts/mcp_servers/dispatch.py:457-470`
  already converts it into `DispatchResult(is_error=True, error_type="validation_error")` on the
  `/v1/call_tool` path (HTTP 200 envelope); `exception_handlers.py:42-47` maps `GitHubValidationError`
  to HTTP 400 for paths that do not go through `dispatch_tool`. There is no 422 contract in this
  repository (Plan REQ-008 correction, Step 3a).
- `per_page` defaults: this row drops the `args.get("per_page", 30)` overrides at lines 47, 62, 78,
  105 because seq 06 sets those four repository-domain models' declared default to 30 (owner-confirmed
  2026-11-24 decision recorded in the Plan Assumptions), so the effective default is unchanged and the
  published `default: 30` now matches runtime behaviour.

## Design decisions
- Use one shared helper (`_validate_request` (new) from `github_service_dispatch_writes.py`, seq 13) rather
  than a per-method `try/except`, so the exception taxonomy is defined once for both dispatch files.
  The helper lives in `github_service_dispatch_writes.py` because `github_service_dispatch.py` already
  imports that module (line 33); the reverse direction would create an import cycle.
- `GitHubValidationError` is re-raised (not replaced) so `exception_handlers.py` and the posture/audit
  paths keep seeing the domain exception type the Plan Design requires.

## Alternatives considered
- Letting `pydantic.ValidationError` propagate: rejected in the Plan Design — the domain taxonomy would
  leak a library type into `exception_handlers.py` and into every later consumer.
- Keeping `args[...]` key-picking and validating separately: rejected — that is the drift pattern the
  Issue removes (two definitions of the same contract).

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_dispatch.py`

### Procedure
1. Add `from mcp_servers.github.github_service_dispatch_writes import _validate_request` to the existing
   import from that module (line 33 site); keep the model imports (lines 19-32).
2. In each of the 12 `fmt_*` methods (`fmt_search_repositories` 42, `fmt_list_branches` 56,
   `fmt_list_commits` 71, `fmt_get_commit` 84, `fmt_search_code` 100, `fmt_get_file_contents` 111,
   `fmt_list_issues` 123, `fmt_get_issue` 136, `fmt_search_issues` 148, `fmt_list_pull_requests` 159,
   `fmt_get_pull_request` 172, `fmt_search_pull_requests` 188) replace the inline
   `Model(owner=args["owner"], ...)` construction with
   `req = _validate_request(Model, args)` and pass `req` to the service method.
3. Remove the `per_page=args.get("per_page", 30)` and `args.get("per_page", 10)` arguments: the model
   declares the default.
4. Keep every formatting body, `fmt_md_link` usage, and empty-result string unchanged.

### Method
- The model instance replaces the inline construction; the surrounding async call shape does not
  change, so no method signature or service method is touched.

### Details
- Where a method used the value twice (for example `req.sha[:8]`), bind the validated model to a local
  `req` and read attributes from it.

## Compatibility considerations
- Newly rejected inputs (recorded in seq 18, tested by seq 17): any key not in the published
  `properties`; missing required keys (now a `validation_error` result instead of a `KeyError`);
  `per_page > 100`; `per_page < 1`; empty identifiers/queries; values outside a declared `pattern`.
- No default page-size change: 30 for the four repository-domain tools (now declared by the models)
  and 10 for the issues/PR-domain tools, matching the published `default`.
- `_clamp_per_page` (`github_service_security.py:66-69`) stays as defense-in-depth for configs whose
  `max_per_page` is below 100.
- `tests/mcp_servers/github/test_service_dispatch.py` pins the tool count (`== 21` at line 698) and
  must keep passing; its model-construction expectations are updated with the seq 17 document.
- Step 3a verification: the pinned count and every read-path test in `test_service_dispatch.py` pass
  unchanged; no read-domain test needed editing in this row (the seq 13 row edited one write-path test).
- Step 3a finding: the `state=args.get("state", "open")` overrides in `fmt_list_issues` and
  `fmt_list_pull_requests` were dropped along with the `per_page` overrides — `ListIssuesRequest.state`
  and `ListPullRequestsRequest.state` declare `default="open"`, so the effective default is unchanged and
  the published `default: "open"` now matches runtime behaviour.
- Step 3a verification: dropping `per_page=args.get("per_page", 30)` / `(…, 10)` keeps the effective
  defaults identical because seq 06 and seq 03/04 declare `default=30` (four repository-domain models) and
  `default=10` (issues/PR-domain models).

## Security considerations
- Unknown-field rejection closes the silent-drop path before any GitHub read call, and page size is
  capped by the model rather than by a clamp applied after validation.

## Rollback considerations
- Revert the Phase 6 commit (this row and seq 13 land as one commit); key-picking and the local
  `per_page` overrides return with it.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_server_endpoints.py` (T-05, seq 17): unknown
  fields, bad types, and empty identifiers produce `is_error=True` / `error_type="validation_error"`
  with no GitHub service method called.
- `uv run pytest tests/mcp_servers/github/test_service_dispatch.py` and
  `uv run pytest tests/mcp_servers/github/test_github_mcp_service.py`.
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/github/ -c pyproject.toml`,
  `uv run lint-imports`, `uv run diff-cover coverage.xml --compare-branch=master` (T-06, >= 90% on
  changed lines).

## Completion criteria
- No `args[...]` model construction remains in this file; every read tool builds its model through
  `_validate_request` (new).
- An unknown key, a missing required key, and `per_page: 0` each produce a `validation_error` result
  and never reach a `GitHubService` method (asserted in seq 17).
- Default page sizes are unchanged (30 / 10) and equal the published `default` values.

## Out of Scope
- Write-domain builders (seq 13), the helper definition (seq 13), tests (seq 17), docs (seq 18-19),
  `exception_handlers.py` (unchanged contract).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the 12 read-domain model constructions with `_validate_request(...)` | Completed | 20261124-215221 | 20261124-215221 | REQ-008; needs seq 13 first Changed: scripts/mcp_servers/github/github_service_dispatch.py. All 12 read-domain fmt_* build req = _validate_request(Model, args); no args[...] construction remains. seq 13 landed first as this row's Assumptions require. |
| 2 | Drop the local `per_page` overrides and confirm defaults match the models | Completed | 20261124-215221 | 20261124-215221 | seq 06 defaults per_page and state overrides dropped; effective defaults unchanged (30 repo-domain, 10 issues/PR-domain, open) and now equal the published defaults. |
| 3 | Confirm the seq 17 HTTP tests prove no service call on invalid input | Completed | 20261124-225226 | 20261124-225226 | T-05 Read-path tests in test_service_dispatch.py pass unchanged (396 in tests/mcp_servers/github/). The HTTP-level no-service-call assertions are seq 17's row. End-of-batch run (rules/toolchain.md, Batch mode): full pytest 13959 passed / 5 skipped / 6 errors; all 6 errors are the pre-existing tests/tools/test_append_plan_work_items.py contract mismatch (issues/20261124-155017_qa001_append-plan-attr-mismatch.md), none in this batch's files. ruff format+check, mypy, lint-imports, check_module_size, bandit, check_docstrings (after adding the em-dash separator to scripts/mcp_servers/request_contract.py), and diff-cover --fail-under 90 Pass. pre-commit run --all-files fails only on 14 pre-existing procedure-length findings in implementations/20261124-122732_* (issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md); check_workitem_structure --file on this batch's documents reports no findings. |
| 4 | Run the validation sequence (`rules/toolchain.md`) for this file | Completed | 20261124-225226 | 20261124-225226 | T-06 ruff format/check, mypy pass on this file. bandit/lint-imports/module-size/diff-cover and the full-suite run are the end-of-batch run. End-of-batch run (rules/toolchain.md, Batch mode): full pytest 13959 passed / 5 skipped / 6 errors; all 6 errors are the pre-existing tests/tools/test_append_plan_work_items.py contract mismatch (issues/20261124-155017_qa001_append-plan-attr-mismatch.md), none in this batch's files. ruff format+check, mypy, lint-imports, check_module_size, bandit, check_docstrings (after adding the em-dash separator to scripts/mcp_servers/request_contract.py), and diff-cover --fail-under 90 Pass. pre-commit run --all-files fails only on 14 pre-existing procedure-length findings in implementations/20261124-122732_* (issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md); check_workitem_structure --file on this batch's documents reports no findings. |

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
- **Requirement ID**: `REQ-008` (runtime validation aligned with the published schema)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/github/github_service_dispatch.py`