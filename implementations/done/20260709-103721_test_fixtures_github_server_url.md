# Implementation: H-10 — remove github_server_url from 11 test fixture dicts

Source plan: `plans/20260709-100244_plan.md` (H-10, Implementation step 7, part 1).

## Goal

Remove the `"github_server_url": "http://127.0.0.1:8006",` fixture line
from every test config dict that gets passed through `build_agent_config()`
— otherwise, once `implementations/20260709-103717_config_builders.py.md`
lands (rejecting this key), all 11 files below fail with `ConfigLoadError`.

## Scope

**Targets** (11 files, identical one-line edit in each — grouped into a
single implementation doc because the change is mechanically identical
across all of them):

| File | Line |
|---|---|
| `tests/test_tool_runner.py` | 60 |
| `tests/test_tool_result_formatter.py` | 50 |
| `tests/test_tool_loop_guard.py` | 49 |
| `tests/test_tool_approval_paths.py` | 60 |
| `tests/test_tool_approval_preflight.py` | 68 |
| `tests/test_plugin_ci_strict.py` | 50 |
| `tests/test_tool_policy_comprehensive.py` | 56 |
| `tests/test_tool_policy.py` | 54 |
| `tests/test_tool_audit.py` | 57 |
| `tests/test_tool_approval_repos.py` | 60 |
| `tests/test_tool_approval_risk.py` | 60 |

**Out of scope**: `tests/test_mcp_config.py:137` — verified while planning
H-10 that this occurrence passes its dict to `_build_mcp_servers()`
directly (not `build_agent_config()`), so it is inert test data unaffected
by the new rejection check; do not edit it.

## Assumptions

1. Each of the 11 files' fixture dict is passed to `build_agent_config()`,
   directly or via a local helper (`_cfg()` / `base = build_agent_config(...)`)
   — individually verified for each file by
   `grep -n "build_agent_config" tests/<file>.py` while planning H-10.
2. Line numbers above are as of the plan's research pass; re-verify each
   with `grep -n "github_server_url" tests/<file>.py` immediately before
   editing, since unrelated changes to these files between planning and
   implementation could shift line numbers.

## Implementation

### Target file

11 files (see table above) — same one-line deletion in each:

```python
        "github_server_url": "http://127.0.0.1:8006",
```

(Exact indentation varies slightly per file — match the surrounding dict's
existing indentation, do not reformat.)

### Procedure

For each file in the table:
1. `grep -n "github_server_url" tests/<file>.py` — confirm exactly one match.
2. Delete that line.
3. Confirm the dict's trailing comma structure is still valid (deleting a
   middle line from a Python dict literal never breaks syntax as long as
   the line itself ended in `,`).

### Method

- 11 independent, textually identical one-line deletions — no shared code
  path between the files, so there is no ordering dependency between them.
- Can be done as 11 separate small edits or one batched sweep; either way,
  re-run the grep in Assumption 2 per file first since these are test
  fixture files that may have drifted since planning.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All removed | `grep -rn "github_server_url" tests/test_tool_runner.py tests/test_tool_result_formatter.py tests/test_tool_loop_guard.py tests/test_tool_approval_paths.py tests/test_tool_approval_preflight.py tests/test_plugin_ci_strict.py tests/test_tool_policy_comprehensive.py tests/test_tool_policy.py tests/test_tool_audit.py tests/test_tool_approval_repos.py tests/test_tool_approval_risk.py` | no matches |
| `test_mcp_config.py` untouched | `grep -n "github_server_url" tests/test_mcp_config.py` | 1 match (unchanged, out of scope) |
| Full-suite regression (after config_builders.py rejection lands) | `uv run pytest tests/test_tool_runner.py tests/test_tool_result_formatter.py tests/test_tool_loop_guard.py tests/test_tool_approval_paths.py tests/test_tool_approval_preflight.py tests/test_plugin_ci_strict.py tests/test_tool_policy_comprehensive.py tests/test_tool_policy.py tests/test_tool_audit.py tests/test_tool_approval_repos.py tests/test_tool_approval_risk.py -v` | all pass |
