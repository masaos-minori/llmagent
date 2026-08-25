## Goal
- `list_tools()` should accept `include_disabled`/`disabled_code` query parameters
  and pass them through to `build_tools_response()` (REQ-005).

## Scope
- In scope: `write_server.py::list_tools()` only. `availability_flags()`
  (`mcp_servers.file.common`)'s logic is unchanged.

## Assumptions
- `build_tools_response`'s import is not yet present in this file and must be added.

## Design decisions
- Keep the existing `_annotate_tool(t, enabled, disabled_reason)` list (a single
  shared `enabled`/`disabled_reason` pair applied to every tool) as the annotation
  step, and pass its result into `build_tools_response()`.

## Alternatives considered
- Writing a bespoke filter — rejected, same reasoning as the other five documents in
  this set.

## Implementation
### Target file
`scripts/mcp_servers/file/write_server.py`

### Procedure
1. Add `build_tools_response` to the `from mcp_servers.server import ...` line.
2. Add `include_disabled`/`disabled_code` `Query` parameters to `list_tools()`'s
   signature.
3. Replace the return value with the `_annotate_tool()`-built list passed into
   `build_tools_response(annotated, "file_write", include_disabled=include_disabled, disabled_code=disabled_code)`.

### Method
- Add `fastapi.Query` to the existing `from fastapi import FastAPI` line.

### Details
- The existing `availability_flags(_cfg.allowed_dirs)` call and `_annotate_tool()`
  loop are unchanged.

## Compatibility considerations
- Existing `GET /v1/tools` (no parameters) response is unchanged.

## Security considerations
- No change.

## Rollback considerations
- Single-file change; reverting `write_server.py` restores prior behavior.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_tools_endpoint.py -v` (the existing
  cross-file-server parametrized test) to confirm no regression.
- Add a new case for `include_disabled`/`disabled_code` filtering — this file is a
  candidate for the Plan's "one representative server" REQ-005 acceptance test.

## Out of scope
- `availability_flags()`'s decision logic.
- The equivalent change to the other five servers — each has its own document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-133000 | 20260825-133300 | Matches docs 04-09's pattern |
| 2 | Add or update tests per Validation plan | Completed | 20260825-133300 | 20260825-134500 | **Cross-cutting regression found and fixed**: `tests/mcp_servers/file/test_mcp_tools_validation.py::test_v1_tools_returns_expected_tools[mdq]` — an `@pytest.mark.integration` test in a different directory that spawns real subprocess servers — started FAILING (not just weakening) because docs 05/06 (mdq/shell) also switched to `build_tools_response()`'s default `include_disabled=False` filtering, and this environment's real mdq/shell/cicd config has empty allowlists. Fixed by adding `include_disabled=true` to that test's two functions (covers shell/cicd/mdq at once). Also fixed the same "vacuous pass" issue in `test_tools_endpoint.py::test_file_server_tools_disabled_when_allowed_dirs_empty` (parametrized across all 3 file servers) so it stays valid once docs 11/12 land. Added 0 new REQ-005-specific cases here since `tests/mcp_servers/git/test_tools_endpoint.py`'s existing file-server-parametrized tests already exercise `write_server.py`. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-134500 | 20260825-135000 | ruff/mypy/lint-imports/bandit clean; `write_server.py` is in the coverage `omit` list; 288/290 pass (excluding `-m integration`, verified separately: 4/4 relevant integration cases now pass for mdq/shell, cicd skipped for pre-existing missing-deps reasons) — the 2 non-integration failures confirmed pre-existing via `git stash` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Deferred | — | — | Same MCP-001 batching decision as doc 03 — see that document's Blocker Log |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Docs 05 (mdq) and 06 (shell), already moved to `implementations/done/`, shipped a real (not just test-quality) regression in `tests/mcp_servers/file/test_mcp_tools_validation.py`'s integration test that was never run during those cycles (different test directory). Fixed here since it was only discovered now; those documents' own Execution Status tables were not retroactively edited (already archived) — flagged here and in the final report instead. | Yes — fixed in this cycle | 20260825-134500 |
| 4 | `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-001 update deferred — see doc 03 Blocker Log | N/A: intentionally deferred | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/mcp_servers/file/write_server.py` change | 1 | Code Change | Completed | — | — |
| `tests/mcp_servers/git/test_tools_endpoint.py` fix | 2 | Test | Completed | — | — |
| `tests/mcp_servers/file/test_mcp_tools_validation.py` regression fix | 2 | Test | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/mcp_servers/file/write_server.py
