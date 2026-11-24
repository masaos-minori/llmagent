## Goal
Make the issues-domain request models the strict authoritative contract: inherit `StrictRequestModel`,
require non-empty identifiers and positive numbers, add the owner-confirmed upper bounds
(REQ-004 required text and numbers, REQ-005 upper bounds, REQ-008 strict base so
`model_validate(args)` can reject unknown fields at runtime).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies `scripts/mcp_servers/github/github_models_issues.py` (Plan Phase 2), plus one existing test
  assertion the new `per_page` bound invalidates (Step 3a finding, see Compatibility):
  `tests/mcp_servers/github/test_service_issues.py::test_per_page_clamped_to_config_max` constructs
  `ListIssuesRequest(per_page=999)`, which `le=100` rejects, so the case must pass a value inside the
  contract bound to keep exercising the config cap.
- Response models (`ListIssuesResponse`, `GetIssueResponse`, `CreateIssueResponse`,
  `AddIssueCommentResponse`, `SearchIssuesResponse`) and `IssueInfo` stay plain `BaseModel`:
  response models are explicitly untouched by the Plan (Reference file `github_models_base.py`).

## Assumptions
- `StrictRequestModel` and `build_input_schema` exist from seq 01.
- Upper-bound values are owner-confirmed 2026-11-24 (Plan Assumptions, UNK-02 resolved):
  `per_page le=100`, `title max_length=256`, `body max_length=65536`, labels/assignees 100 items.
- `ListIssuesRequest.state` already declares `pattern="^(open|closed|all)$"` (lines 21-24) and
  `CreateIssueRequest`/`AddIssueCommentRequest` already declare `dry_run` (lines 61, 79); neither
  reaches the published schema until seq 08 generates it.

## Design decisions
- Strictness comes from inheritance only; no per-model `model_config` is added to this file, so all
  five request models share one contract definition (REQ-001).
- Optional text keeps its empty default where the empty value is a meaningful sentinel:
  `CreateIssueRequest.body` (`default=""`, "no body") keeps no `min_length` and only gains
  `max_length=65536`. Making it non-empty would reject calls that today legitimately send no body.
- List length is expressed with `min_length`/`max_length` on the `list[...]` field (pydantic 2.13
  maps them to minItems/maxItems), not with the deprecated min_items/max_items kwargs.
- Label/assignee item strings are left unconstrained beyond the count: REQ-004 covers mandatory
  text, and these are optional collections.

## Alternatives considered
- `constr(min_length=1)` / `conlist(...)`: rejected — Annotated + `Field` bounds keep one style
  across all four model rows (seq 03-06) and are what `model_json_schema()` reports as keywords.
- Adding `pattern` to `owner`/`repo`: rejected for this row — repository identity is already enforced
  canonically by `shared.repo_identity` at the authorization guard (REQ-007, seq 07); a second
  pattern here would be a second contract definition, the drift pattern this Plan removes.

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_issues.py`

### Procedure
1. Add `from mcp_servers.request_contract import StrictRequestModel` to the import block.
2. Change the base of `ListIssuesRequest` (line 16), `GetIssueRequest` (35), `CreateIssueRequest`
   (49), `AddIssueCommentRequest` (72), `SearchIssuesRequest` (91) from `BaseModel` to
   `StrictRequestModel`; leave the response models on `BaseModel`.
3. `owner`, `repo` (lines 19-20, 38-39, 52-53, 75-76): add `min_length=1`.
4. `per_page` (26, 98): `Field(default=10, ge=1, le=100)`.
5. `issue_number` (40, 77): add `ge=1`.
6. `title` (54): `min_length=1, max_length=256`; `body` (55): `max_length=65536`;
   `labels` (56) and `assignees` (57): add `max_length=100`.
7. `query` (94): add `min_length=1`; comment `body` (78): `min_length=1, max_length=65536`.
8. Keep every `description=` string unchanged (they become the published schema descriptions at
   seq 08) and keep `dry_run` fields exactly as they are (REQ-003 publication is seq 08).

### Method
- Field-level `Field(...)` bounds only; no validators are needed in this domain.
- Do not reorder fields: pydantic emits `properties` in declaration order, and seq 14's drift gate
  compares the published dict with the generated one.

### Details
- `SearchIssuesRequest.query` is required text (line 94-97) so an empty search query becomes a
  model error instead of an upstream GitHub search error.
- No change to `github_models.py` (re-export shim) or to `github_service_read.py` call sites.

## Compatibility considerations
- Newly rejected inputs for this domain (must be listed in seq 18 docs and covered by seq 15/17
  tests): unknown/extra keys; `owner`/`repo`/`query` empty string; `issue_number < 1`;
  `per_page > 100`; `title` empty or over 256; `body` over 65536; more than 100 labels or assignees.
- `extra="forbid"` does not change the `/v1/call_tool` path until seq 12-13 switch dispatch to
  `model_validate(args)`; today `github_service_dispatch.py` picks `args[...]` keys, so extra keys
  are still dropped until then (Plan Problem statement).
- `_clamp_per_page` (`github_service_security.py:66-69`) stays as defense-in-depth for configs with
  a lower `max_per_page` (Plan Design decision).
- Step 3a finding: the clamp test above is the only existing call site that feeds a value the new
  bound rejects (`grep` over `scripts` and `tests` for the five request models found no other). Change
  its `per_page=999` to `per_page=50` and keep the assertion that the service caps the result at the
  configured `max_per_page=3`; the rejection of `per_page=101` is covered by the seq 15 T-03 cases.
- A client that sends `per_page` above 100 now gets a `validation_error` result instead of a clamped
  call: `pydantic.ValidationError` is a `ValueError`, and `mcp_servers/dispatch.py:457` maps
  `ValueError` from a handler to `error_type="validation_error"`, so no unhandled-exception path opens
  between this row and seq 12-13.

## Security considerations
- Rejecting empty `owner`/`repo` and `per_page > 100` before any GitHub call narrows oversized
  request and identity-confusion surfaces (Plan AC-04).

## Rollback considerations
- Revert this commit alone: Phase 2 is one commit and no other domain depends on it (Plan Risk
  mitigation: per-domain revertable phases).

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_request_validation.py` (T-03) — issues-domain
  cases are added by the seq 15 document; this row does not modify test files.
- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py` (T-02 drift gate, seq 14).
- `uv run pytest tests/mcp_servers/github/test_github_mcp_service.py` (existing well-typed
  `from_dict`/model tests must keep passing).
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/github/ -c pyproject.toml`,
  `uv run lint-imports` (T-06).

## Completion criteria
- All five issues request models reject an unknown key with `pydantic.ValidationError`.
- The generated schema for each model reports `additionalProperties: false`, `minimum`/`maximum`,
  minLength, maxLength, maxItems matching the values above.
- No previously valid issues call except the newly rejected inputs in Compatibility changes result.

## Out of Scope
- Publishing the generated schema (`scripts/mcp_servers/github/tools_issues.py`, seq 08).
- Tests (seq 14, seq 15, seq 17), docs (seq 18-19), dispatch alignment (seq 12-13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply strict base + bounds to the five issues request models | Completed | 20261124-211156 | 20261124-211156 | REQ-004, REQ-005 Changed: scripts/mcp_servers/github/github_models_issues.py, tests/mcp_servers/github/test_service_issues.py. Step 3a finding: test_per_page_clamped_to_config_max passed per_page=999, rejected by the new le=100; changed to per_page=50 so the config cap is still exercised. |
| 2 | Confirm coverage through the seq 15 issues cases and seq 14 drift gate | Completed | 20261124-211156 | 20261124-211156 | T-02, T-03 Targeted run: test_service_issues.py, test_github_mcp_service.py, test_service_dispatch.py = 133 passed. T-03/T-02 cases themselves land in seq 15/14. |
| 3 | Run the validation sequence (`rules/toolchain.md`) for this file | Completed | 20261124-225226 | 20261124-225226 | ruff format/check, mypy pass; bandit/lint-imports/module-size and the full-suite run are the end-of-batch run. End-of-batch run (rules/toolchain.md, Batch mode): full pytest 13959 passed / 5 skipped / 6 errors; all 6 errors are the pre-existing tests/tools/test_append_plan_work_items.py contract mismatch (issues/20261124-155017_qa001_append-plan-attr-mismatch.md), none in this batch's files. ruff format+check, mypy, lint-imports, check_module_size, bandit, check_docstrings (after adding the em-dash separator to scripts/mcp_servers/request_contract.py), and diff-cover --fail-under 90 Pass. pre-commit run --all-files fails only on 14 pre-existing procedure-length findings in implementations/20261124-122732_* (issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md); check_workitem_structure --file on this batch's documents reports no findings. |
| 4 | Update documentation | Completed | 20261124-211156 | 20261124-211156 | N/A: newly rejected inputs are recorded by seq 18 N/A: newly rejected inputs are recorded by seq 18. |

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
- **Requirement ID**: `REQ-004` (non-empty text, numbers >= 1), `REQ-005` (upper bounds), `REQ-008` (strict base for runtime rejection)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/github/github_models_issues.py`