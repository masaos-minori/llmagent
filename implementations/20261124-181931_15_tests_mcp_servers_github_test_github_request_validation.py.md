## Goal
Add the model-level regression suite for the strict GitHub request contract: every bound, pattern,
sentinel rule, and cross-field rule introduced in seq 03-06 rejects exactly the inputs the Plan lists
and accepts everything else (T-03, REQ-004/REQ-005 model coverage).

## Scope
**Release unit**: N/A: not part of a release unit

- Creates `tests/mcp_servers/github/test_github_request_validation.py` (new) (Plan Phases 2-5).
- No production file is modified by this document; it is the test owner for all four model rows
  (seq 03-06), which explicitly delegate test authoring here.

## Assumptions
- The strict models exist per domain as each phase lands; the file grows per phase (one test class per
  domain) so each Plan phase stays individually verifiable, matching the Plan's per-phase commits.
- Tests call `Model.model_validate(dict)` directly: the contract under test is the model, not the
  dispatch path (HTTP-level behavior is seq 17).
- `pydantic.ValidationError` is the raised type at model level; `GitHubValidationError` conversion is
  tested by seq 17, not here.

## Design decisions
- One test class per domain (`TestIssuesModel` (new), `TestPullRequestsModel` (new), `TestFileModel` (new),
  `TestRepositoryModel` (new)), each with three test shapes: a parametrized reject table (invalid
  args -> `pytest.raises(ValidationError)`), a parametrized accept table (boundary-valid args), and
  one explicit test for the domain's cross-field rule.
- Boundary values are tested at the edge (`per_page=100` accepted, `101` rejected; `content` at
  1048576 accepted, 1048577 rejected; `title` at 256 accepted, 257 rejected), not just far-inside or
  far-outside values: the owner-confirmed numbers (Plan Assumptions, UNK-02) become the pinned
  contract.
- Sentinel rules are tested as "explicitly supplied empty rejected, default omitted accepted"
  (model_fields_set semantics from seq 05/06), e.g. `{"ref": ""}` rejects but `{}` (no `ref`) passes.
- Accept tables include every field default so a future tightening of an unrelated field fails the
  suite loudly rather than silently.

## Alternatives considered
- Extending `tests/mcp_servers/github/test_github_mcp_service.py` (which already has model
  construction tests): rejected — that file is the service-behavior suite with mocked `Github`; mixing
  a large reject/accept matrix into it obscures both roles, and the Plan reserves this dedicated file
  (target-file row 15).
- Snapshot/golden-file schema tests: rejected — schema shape equality is seq 14's drift gate; this file
  tests acceptance and rejection behavior.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_request_validation.py` (new)

### Procedure
1. Create the file with a module docstring naming the Plan requirement IDs and imports for the four
   domain model modules plus `pydantic`.
2. `TestIssuesModel` (new) (with seq 03): reject extra keys; empty `owner`/`repo`/`query`/`title`;
   `issue_number=0`; `per_page` 0 and 101; `title` 257 chars; `body` 65537 chars; 101 `labels` or
   `assignees`; accept the boundary values and the `state` pattern (`"open"|"closed"|"all"` accepted,
   `"merged"` rejected).
3. `TestPullRequestsModel` (new) (with seq 04): the same shapes for `pr_number`, `head`, `base`, `query`,
   `commit_title`, `commit_message`; plus `test_update_pull_request_requires_a_field` (new) —
   `{"owner","repo","pr_number"}` only rejects, `{"state": "open"}` alone accepts
   (`CreatePullRequestRequest` `head`/`base` empty rejected; `merge_method` pattern).
4. `TestFileModel` (new) (with seq 05): unknown key at top level and inside a `files` item; empty
   `owner`/`repo`/`path`/`message`; explicitly empty `ref`/`branch`/`sha` rejected while omitted
   defaults pass; `content` at 1048576 accepted and 1048577 rejected; `files` `[]` rejected and one
   valid item accepted; `DeleteRepoFileRequest.sha=""` rejected.
5. `TestRepositoryModel` (new) (with seq 06): `per_page` 0/100/101 for all four paginated models; default
   `per_page` equals 30 for `SearchRepositoriesRequest`, `ListCommitsRequest`, `SearchCodeRequest`,
   `ListBranchesRequest` (owner decision recorded in seq 06); empty `query`/`sha`/`branch_name`;
   explicitly empty `branch`/`from_branch` rejected while omitted pass.

### Method
- Parametrize reject tables as `(model, payload, expected_field)` tuples and assert the error's
  `errors()` list names the expected field, so a rejection caused by an unrelated rule fails the test
  rather than passing by accident.

### Details
- The default-value tests (step 5) pin the 30 vs 10 split between the repository and issues/PR domains;
  a change to either default is a documented behavior change and must edit this file.
- Long-string cases build `"x" * n` once via a module helper to keep the file small and readable.

## Compatibility considerations
- Purely additive test file; it changes no production behavior and no existing test file.
- Until the matching model row lands, its class is not added — each domain class arrives in the same
  commit as its model row (seq 03 -> issues class, seq 04 -> PR, seq 05 -> file, seq 06 -> repository).

## Security considerations
- The boundary tests are what keep AC-04 (oversized/empty inputs rejected before any GitHub call)
  provable in CI.

## Rollback considerations
- Each domain class reverts with its domain commit; nothing else references this file.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_request_validation.py` (T-03).
- Mutation sanity check while developing: temporarily remove one bound (for example `le=100`), confirm
  the matching case fails, revert (do not commit).
- `uv run pytest tests/mcp_servers/github/` and `uv run ruff check`, `uv run mypy` (T-06).

## Completion criteria
- Every input listed in the Compatibility considerations of seq 03-06 has a reject case here, and each
  has a passing counterpart at the accepted boundary.
- The four domain classes exist and pass together with the rest of the GitHub suite.

## Out of Scope
- Schema-equality and `dry_run` publication tests (seq 14), HTTP endpoint tests (seq 17), shared
  request_contract unit tests (companion of seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the file and `TestIssuesModel` (new) with seq 03 | Pending | — | — | T-03 |
| 2 | Add `TestPullRequestsModel` (new) with seq 04 (incl. no-op update case) | Pending | — | — | T-03 |
| 3 | Add `TestFileModel` (new) with seq 05 (incl. nested `PushFile` and sentinel cases) | Pending | — | — | T-03 |
| 4 | Add `TestRepositoryModel` (new) with seq 06 (incl. default 30 pin) | Pending | — | — | T-03 |
| 5 | Run the validation sequence (`rules/toolchain.md`) for this file | Pending | — | — | T-06 |

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
- **Requirement ID**: `REQ-004` (non-empty text, numbers >= 1, no-op update rule), `REQ-005` (upper bounds), `REQ-008` (model contract)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `tests/mcp_servers/github/test_github_request_validation.py`
