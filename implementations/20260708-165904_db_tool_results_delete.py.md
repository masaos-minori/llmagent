# Implementation: H-9 — Delete scripts/db/tool_results.py entirely

## Goal

Delete `db/tool_results.py` (the `ToolResultStore` class) entirely. Every runtime caller has
been removed by the H-1/H-2/H-4/H-5/H-6/H-7/H-8 companion docs, so nothing constructs or calls
this class anymore.

## Scope

**Target**: `scripts/db/tool_results.py` (deletion)

**Depends on**: land AFTER all of the following have been applied, since they remove every
caller of `ToolResultStore`:
- `implementations/20260708-163935_context.py.md` (H-7: `AgentContext` stops owning an instance)
- `implementations/20260708-162541_tool_runner_h2.py.md` (H-2: `.store()` call removed from
  `tool_runner.py`)
- `implementations/20260708-163427_llm_transport_errors.py.md` (H-4: `.store()` call removed)
- `implementations/20260708-164010_error_injection_service.py.md` (H-7/H-5: `.store()` call
  removed)
- `implementations/20260708-165242_undo_service_h6.py.md` (H-6: `.mark_turn_undone()` call
  removed)
- `implementations/20260708-164900_cmd_tooling_h8.py.md` (H-8: `.list_recent()`/`.get()` calls
  removed, along with the `ToolResultStore` import H-7 had added)
- `implementations/20260708-165725_repl_h9.py.md` (H-9: the direct SQL query and
  `ctx.tool_result_store` read removed)

**Depends on / land together with**: `implementations/*_db_models_h9.py.md` (the `ToolResultRow`
class this file imports, also being deleted) and
`implementations/*_db_init_h9.py.md` (the `db/__init__.py` export removal).

## Assumptions

1. `grep -rln "from db.tool_results import\|db\.tool_results"` across `scripts/` and `tests/`
   shows zero remaining references once all the dependency docs above are applied (verify this
   explicitly in Procedure Step 1 before deleting — do not delete speculatively).

## Implementation

### Target file

`scripts/db/tool_results.py` (to be deleted)

### Procedure

#### Step 1: Confirm zero remaining references

```bash
grep -rln "from db.tool_results import\|ToolResultStore" scripts/ tests/ --include="*.py"
```

Expected: no matches at all (once every dependency doc above has landed).

#### Step 2: Delete the file

```bash
rm scripts/db/tool_results.py
```

### Method

- File deletion — `git rm scripts/db/tool_results.py` at implementation time.

### Details

- `db/helper.py`'s `SQLiteHelper` class (imported by `tool_results.py` as
  `from db.helper import SQLiteHelper`) is unaffected — it is used by many other db-layer
  modules and stays.
- `db.models.ToolResultRow` (imported by `tool_results.py`) is deleted by its own companion doc
  in the same rollout — no orphaned import concern since both are removed together.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Grep (file gone) | `ls scripts/db/tool_results.py 2>&1` | "No such file or directory" |
| Grep (no dangling references) | `grep -rn "db.tool_results\|ToolResultStore" scripts/ tests/` | no matches |
| Type check | `mypy scripts/` | no new errors (confirms no remaining import references this deleted module) |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 broken contracts |
| Tests (full) | `uv run pytest -v` | no new failures once every H-9 doc lands together |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- Deleting this file before ALL of its callers have been removed will break the build
  (`ImportError`) wherever a stale caller remains. This is the LAST file to delete in the whole
  H-1 through H-9 rollout — sequence it last.
