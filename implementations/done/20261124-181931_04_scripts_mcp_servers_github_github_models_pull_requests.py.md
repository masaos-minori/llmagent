## Goal
Make the pull-requests-domain request models the strict contract and reject a no-op pull request
update at the model level (REQ-004 non-empty text, numbers >= 1, no-op update validator; REQ-005
upper bounds; REQ-008 strict base for runtime rejection).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies `scripts/mcp_servers/github/github_models_pull_requests.py` (Plan Phase 3), plus three
  existing tests the new contract invalidates (Step 3a findings, see Compatibility).
- Response models (`ListPullRequestsResponse`, `GetPullRequestResponse`, `CreatePullRequestResponse`,
  `UpdatePullRequestResponse`, `MergePullRequestResponse`, `SearchPullRequestsResponse`) stay plain
  `BaseModel`.

## Assumptions
- `StrictRequestModel` exists from seq 01; `min_length`/`max_length` on `str`/`list` map to
  minLength/maxLength/minItems/maxItems in pydantic 2.13.4 output.
- Owner-confirmed bounds (Plan Assumptions, UNK-02): `title max_length=256`, `body max_length=65536`,
  `per_page le=100`.
- `ListPullRequestsRequest.state` (line 21, `pattern="^(open|closed|all)$"`) and
  `UpdatePullRequestRequest.state` (71-75, `pattern="^(open|closed)$"`) and
  `MergePullRequestRequest.merge_method` (99-103, `pattern="^(merge|squash|rebase)$"`) already
  declare patterns; they reach the published schema only when seq 09 generates the schema.

## Design decisions
- No-op update rejection is a `model_validator(mode="after")` on `UpdatePullRequestRequest`
  (REQ-004 final clause): at least one of `title`, `body`, `state` must be present in
  `self.model_fields_set`, otherwise raise `ValueError("... no field to update")`. It rejects the
  no-op even when `dry_run=True`, because a preview of nothing is still a wasted call.
- `MergePullRequestRequest.commit_title`/`commit_message` keep their `default=""` sentinel
  ("GitHub default") but gain the same class of upper bound as `title`/`body`
  (`max_length=256` / `max_length=65536`): REQ-005 bounds text per request, and these are the merge
  commit's title and body.
- Optional `UpdatePullRequestRequest.title`/`body` keep `default=None` (omit to keep) and gain
  bounds that apply only when supplied (`title: min_length=1, max_length=256`;
  `body: max_length=65536`).

## Alternatives considered
- Rejecting the no-op update in `github_service_dispatch_writes.py` instead of the model: rejected —
  the Plan freezes the rejection as "model-level validator" (REQ-004) and a dispatch-side check
  would not appear in the published schema contract that seq 09 generates.
- `min_length=1` on `state` instead of the existing `pattern`: rejected — the pattern is already the
  narrower contract and is carried into the schema verbatim.

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_pull_requests.py`

### Procedure
1. Add `from mcp_servers.request_contract import StrictRequestModel` and
   `from pydantic import model_validator` to the import block.
2. Switch `ListPullRequestsRequest` (16), `GetPullRequestRequest` (31), `CreatePullRequestRequest`
   (45), `UpdatePullRequestRequest` (63), `MergePullRequestRequest` (85), `SearchPullRequestsRequest`
   (116) to `StrictRequestModel`.
3. `owner`/`repo` on every request model: `min_length=1`.
4. `per_page` (22, 123): `ge=1, le=100`. `pr_number` (36, 68, 90): `ge=1`.
5. `CreatePullRequestRequest`: `title min_length=1, max_length=256`; `body max_length=65536`;
   `head min_length=1`; `base min_length=1` (REQ-004 branch names).
6. `UpdatePullRequestRequest`: `title min_length=1, max_length=256`; `body max_length=65536`.
7. `MergePullRequestRequest`: `commit_title max_length=256`; `commit_message max_length=65536`.
8. `SearchPullRequestsRequest.query` (119): `min_length=1`.
9. Add the no-op `model_validator(mode="after")` described in Design decisions.
10. Keep all four `dry_run` fields (54, 76, 104) and all `description=` strings unchanged.

### Method
- One validator, no cross-field dependencies beyond presence checking; the message names the three
  update fields so the rejected call is actionable without reading the source.

### Details
- model_fields_set is the authoritative "explicitly supplied" signal: `title=None` supplied
  explicitly is still not an update, so the validator tests membership in model_fields_set for a
  non-`None` value rather than truthiness.

## Compatibility considerations
- Newly rejected inputs (recorded in seq 18, tested by seq 15/17): unknown/extra keys; `github_update_pull_request`
  with only `owner`/`repo`/`pr_number`; `title` empty or over 256; `body` over 65536; empty `head` or
  `base`; `pr_number < 1`; `per_page > 100`; empty `query`; `commit_message` over 65536.
- `github_service_dispatch_writes.py` still key-picks `args.get(...)` until seq 13 lands, so extra
  keys keep being dropped in this phase.
- Step 3a findings (three existing tests invalidated by the new contract, all adjusted in this row):
  - `tests/mcp_servers/github/test_service_dispatch.py::test_dry_run_preview_no_changes_placeholder`
    asserted the `"(no changes)"` dry-run preview for an update with no field to change. The model
    validator rejects that request, so the case is now
    `test_update_with_no_field_to_change_is_rejected`, asserting `pydantic.ValidationError` and no
    service call. The `or "(no changes)"` fallback it covered (`github_service_dispatch_writes.py:298`)
    is unreachable from this row on and is removed by seq 13.
  - `tests/mcp_servers/github/test_service_pull_requests.py::test_skips_edit_call_when_no_fields_set`
    built a no-op request through the constructor. It now builds it with `model_construct` so the
    service-side `if kwargs:` guard (`github_service_pull_requests.py:141`) keeps its coverage as
    defense-in-depth behind the contract.
  - `tests/mcp_servers/github/test_service_pull_requests.py:137` passed `per_page=999` to the config-cap
    clamp test; changed to `per_page=50`, inside the new `le=100` bound.

## Security considerations
- Rejecting empty branch names (`head`, `base`) prevents a write path from receiving an ambiguous
  target branch before the protected-branch guard runs.

## Rollback considerations
- Revert this single Phase 3 commit; the no-op validator is the only behavior change that is not a
  field bound.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_request_validation.py` (T-03; PR cases added by
  the seq 15 document).
- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py` (T-02, seq 14).
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/github/ -c pyproject.toml`,
  `uv run lint-imports` (T-06).

## Completion criteria
- `UpdatePullRequestRequest.model_validate({"owner": "o", "repo": "r", "pr_number": 1})` raises.
- Every PR request model rejects an unknown key and reports the declared `pattern`s plus
  `minimum`/`maximum`/`minLength`/`maxLength` in its generated schema.
- No previously valid PR call except the listed inputs changes result.

## Out of Scope
- `scripts/mcp_servers/github/tools_pull_requests.py` (seq 09), tests (seq 14-15, 17), docs (seq 18-19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply strict base + bounds to the six PR request models | Completed | 20261124-211658 | 20261124-211658 | REQ-004, REQ-005 Changed: scripts/mcp_servers/github/github_models_pull_requests.py, tests/mcp_servers/github/test_service_dispatch.py, tests/mcp_servers/github/test_service_pull_requests.py. |
| 2 | Add the no-op `UpdatePullRequestRequest` model validator | Completed | 20261124-211658 | 20261124-211658 | REQ-004 _require_a_change model_validator added; message names title/body/state. |
| 3 | Confirm coverage through the seq 15 PR cases and seq 14 drift gate | Completed | 20261124-211658 | 20261124-211658 | T-02, T-03 Targeted run: tests/mcp_servers/github/ = 358 passed. Two existing tests invalidated by the contract were adjusted (see Compatibility); T-03/T-02 cases land in seq 15/14. |
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
- **Requirement ID**: `REQ-004` (non-empty text, numbers >= 1, no-op PR update rejection), `REQ-005` (upper bounds), `REQ-008` (strict base)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/github/github_models_pull_requests.py`