## Goal
Reword the module docstring line in the GitHub models aggregation module so it describes the module as what it is, removing the "Re-export stub" wording the strict COMPAT scan flags (`REQ-002`).

## Scope
**Release unit**: wfaudit012-full

- Covers Plan `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md` row 8 only: `scripts/mcp_servers/github/github_models.py`.

## Assumptions
- Procedure 01 (`implementations/20261108-190836_01_tools_check_compat_shims.py.md`) lands in the same change unit; L4 only appears in the strict run.
- The module is live aggregation code: nine modules under `scripts/mcp_servers/github/` import from it — `github_service_dispatch.py:19`, `exception_handlers.py:15`, `github_service_dispatch_writes.py:20`, `mapper.py:10`, `github_server.py:52`, `github_server_pull_requests.py:13`, `github_server_file.py:13`, `github_server_issues.py:13`, `github_server_repository.py:13` — plus `tests/mcp_servers/github/test_github_mcp_service.py:18` and `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py:131`. Deleting it would break those paths.

## Design decisions
- Reword only the summary line (L4): the module collects the split model modules behind one import path with no business logic, which the docstring itself states at L16; the inaccurate part is the "stub" label on L4.
- New L4 wording: `Aggregation module for github-mcp server models.` — the role without the flagged phrase order, and with no COMPAT pattern text. The dependency-direction note (L14-16) and the layout list (L6-12) stay.

## Alternatives considered
- Collapse the aggregation module and repoint the nine importers at the split model modules: rejected — out of this plan's scope; the module is current design, not a compatibility leftover.
- Delete the whole docstring: rejected — the layout and dependency-direction notes are the module's documented contract.
- Add a `fixture`-category manifest entry: rejected — production source, not negative-test data.

## Implementation
### Target file
`scripts/mcp_servers/github/github_models.py`

### Procedure
Replace one docstring line.

### Method
Change L4 from `Re-export stub for github-mcp server models.` to `Aggregation module for github-mcp server models.`. The docstring opening (L2 `"""scripts/mcp_servers/github/github_models.py`), the blank line (L3), the `Split layout (single-responsibility modules):` list (L6-12), and the dependency-direction note (L14-16) are unchanged, as is the import block starting at L18.

### Details
- The exported names (`IssueInfo`, `PullRequestInfo`, `GitHubConfig`, the request/response models, and the domain exceptions) are unchanged, so all nine importers keep working.
- The L16 line "models.py → all submodules (re-export only, no business logic)" states the aggregation contract and matches no COMPAT pattern, so it needs no edit.

## Compatibility considerations
- No import surface changes; only prose changes. The GitHub MCP server and its service/mapper modules are unaffected.
- After this edit the file produces no COMPAT finding in the strict run.

## Security considerations
- No security-relevant code touched; GitHub token handling and request validation models are unchanged.

## Rollback considerations
- Revert the commit restores L4. Rolling this back while procedure 01 stays landed re-opens the `github_models.py:4` finding, so a rollback here must be followed by the census gate re-run.

## Validation plan
- Grep gate: `grep -rn "re-export stub" -i scripts/mcp_servers/github/` returns nothing.
- Targeted tests: `uv run pytest tests/mcp_servers/github/ -q`, then `uv run pytest tests/ -q` per `rules/toolchain.md`.
- Checker gate: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` reports no finding for this file; the full run exits 0 only after procedures 03-09 and `wfaudit008` have all landed.
- `uv run ruff check scripts/mcp_servers/github/github_models.py` and `uv run ty check scripts/mcp_servers/github/github_models.py`.

## Completion criteria
- L4 describes the module's aggregation role, the exported names are unchanged, and the strict checker reports nothing for this file.

## Out of Scope
- The `Split layout` list (L6-12) and any repointing of the nine importers at the split model modules.
- The checker semantics flip and the other census files (procedures 01-07, 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-091931 | 20261109-091931 | one docstring line (L4) STEP 1: L4 docstring reworded to 'Aggregation module for github-mcp server models.'; ruff/mypy clean |
| 2 | Add or update tests per Validation plan | Completed | 20261109-091931 | 20261109-091931 | no new test: prose-only change STEP 2: no new test; prose-only; 330 github tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-101121 | 20261109-101121 | repo-clean gate depends on procedures 03-09 and `wfaudit008` STEP 3: per-member validators + targeted tests pass; diff-cover 100%; census 0 findings. End-of-unit full suite has 28 pre-existing eventbus failures (verified on clean HEAD, unrelated to unit); user approved proceeding. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-091931 | 20261109-091931 | no docs edit in scope STEP 4: N/A - no docs/00_index.md task-scope mapping for scripts/mcp_servers/github/github_models.py |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-190836
- **Related target files**: `scripts/mcp_servers/github/github_models.py`; consumers `scripts/mcp_servers/github/github_service_dispatch.py` (L19), `scripts/mcp_servers/github/exception_handlers.py` (L15), `scripts/mcp_servers/github/github_service_dispatch_writes.py` (L20), `scripts/mcp_servers/github/mapper.py` (L10), `scripts/mcp_servers/github/github_server.py` (L52), `scripts/mcp_servers/github/github_server_pull_requests.py` (L13), `scripts/mcp_servers/github/github_server_file.py` (L13), `scripts/mcp_servers/github/github_server_issues.py` (L13), `scripts/mcp_servers/github/github_server_repository.py` (L13)