## Goal

Create a new test file, `tests/mcp_servers/test_tool_schema_contract.py`, that
parametrizes over every one of the 10 MCP server `TOOL_LIST` modules and asserts each
exported tool entry satisfies the schema-2.0 contract (`is_write`, `requires_serial`,
`resource_scope_kind`, `resource_scope_keys` all present, well-typed, and valid), plus
a full-coverage check that every name in `shared.tool_constants.get_all_mcp_tool_names()`
is present and schema-2.0-valid in its owning server's `TOOL_LIST` — so a future tool
addition without complete metadata fails CI immediately, per the plan's Phase 2 and
Risk-mitigation instructions.

## Scope

In scope: creation of the new file `tests/mcp_servers/test_tool_schema_contract.py`
only. Out of scope: the shared contract validator function itself
(`scripts/shared/resource_scope.py`'s `validate_tool_schema_v2()` or equivalent — a
different agent's assigned file per this task's brief); any change to
`scripts/shared/tool_constants.py`; any change to the 10 `TOOL_LIST` modules
themselves (each has its own document in this batch/sibling batches).

## Assumptions

- `tests/mcp_servers/test_tool_schema_contract.py` does not exist today (confirmed:
  `ls tests/mcp_servers/*test_tool_schema_contract*` → no match); this is a wholly
  new file, not an edit.
- This test depends on a shared contract validator that the plan places in
  `scripts/shared/resource_scope.py` (Phase 1, "Add a shared contract validator...
  enforcing: name non-empty; `inputSchema` valid; `is_write`/`requires_serial` present
  and `bool`; `resource_scope_kind` in the known kind set (or `""`);
  `resource_scope_keys` a `list[str]` each present in `inputSchema["properties"]`").
  That module does not exist yet either (confirmed: `ls scripts/shared/resource_scope.py`
  → not found) and is out of scope for this document per the task brief ("a different
  agent's assigned file — you do not write that file, just reference it as a
  dependency"). This test file's implementation therefore cannot literally run green
  until that validator lands; this document specifies the test assuming the
  validator's function signature will be `validate_tool_schema_v2(entry: dict) -> list[str]`
  (returning a list of human-readable violation strings, empty when valid) per the
  plan's own phrasing.
- `shared.tool_constants.get_all_mcp_tool_names()` (lines 169-186, confirmed by
  reading it) returns the union of 10 module-level frozensets (`READ_TOOLS`,
  `WRITE_TOOLS`, `DELETE_TOOLS`, `RAG_TOOLS`, `CICD_TOOLS`, `MDQ_TOOLS`, `GIT_TOOLS`,
  `SHELL_TOOLS`, `WEB_SEARCH_TOOLS`, `GITHUB_TOOLS`) — this is the authoritative
  name-set the new test's coverage check reconciles against the 10 actual `TOOL_LIST`
  modules' tool names.
- The existing `tests/mcp_servers/test_tool_schema.py` (read in full) establishes the
  project's convention for this kind of test: `importlib.import_module()` +
  `getattr(mod, "TOOL_LIST")`, a module-level `_SCHEM_MODULES: list[tuple[str, str]]`
  of `(module_path, attr_name)` pairs, and `@pytest.mark.parametrize`. The new file
  follows the same convention but expands `_SCHEM_MODULES` (or an equivalently named
  constant) to all 10 modules instead of the 4 covered there.

## Design decisions

- Name the parametrization list `_TOOL_LIST_MODULES` (distinct from
  `test_tool_schema.py`'s `_SCHEM_MODULES`, to avoid implying this file supersedes
  that one — both files coexist, this one adds the schema-2.0-specific fields while
  `test_tool_schema.py` remains the "authoritative full-field-set check for the 4
  file+git modules only" per its own docstring).
- Two top-level test functions: (1) a parametrized per-module test asserting every
  entry in each of the 10 `TOOL_LIST`s passes the shared validator; (2) a single
  non-parametrized coverage test asserting the union of all 10 modules' tool names
  equals `get_all_mcp_tool_names()` exactly (catches a tool present in one but absent
  from the other, in either direction).
- Import the validator lazily inside each test function (not at module top-level)
  only if it is not yet guaranteed to exist at collection time in a partially-applied
  plan state — but since this document assumes the validator lands together with (or
  before) this test per the plan's Phase 2 ordering, a normal top-level import is
  used; note this in Compatibility considerations as a phase-ordering dependency.

## Alternatives considered

Considered writing one enormous test iterating a hand-maintained dict of
`{module_path: expected_tool_count}` — rejected in favor of reusing
`get_all_mcp_tool_names()` as the single source of truth for full coverage, per the
plan's own Risk-mitigation text ("asserting every name in
`shared.tool_constants.get_all_mcp_tool_names()` is present and schema-2.0-valid in
its owning server's `TOOL_LIST`"), avoiding a second, driftable source of truth.

## Implementation

### Target file: `tests/mcp_servers/test_tool_schema_contract.py` (new)

### Procedure

1. Create the file with a module docstring stating its purpose (schema-2.0 contract
   coverage across all 10 `TOOL_LIST` modules) and cross-referencing
   `tests/mcp_servers/test_tool_schema.py` as the pre-existing, narrower-scope sibling
   test (mirroring how that file's own docstring cross-references
   `test_mcp_tools_validation.py`).
2. Import `importlib`, `pytest`, `shared.tool_constants.get_all_mcp_tool_names`, and
   the shared validator from `scripts/shared/resource_scope.py` (exact import path to
   be confirmed once that module lands — placeholder:
   `from shared.resource_scope import validate_tool_schema_v2`).
3. Define `_TOOL_LIST_MODULES: list[tuple[str, str]]` listing all 10
   `(module_path, "TOOL_LIST")` pairs: `mcp_servers.file.read_tools`,
   `mcp_servers.file.write_tools`, `mcp_servers.file.delete_tools`,
   `mcp_servers.git.git_tools`, `mcp_servers.github.tools_repository`,
   `mcp_servers.github.tools_file`, `mcp_servers.github.tools_issues`,
   `mcp_servers.github.tools_pull_requests`, `mcp_servers.cicd.cicd_tools`,
   `mcp_servers.rag_pipeline.rag_pipeline_tools`, `mcp_servers.mdq.mdq_tools`,
   `mcp_servers.shell.shell_tools`, `mcp_servers.web_search.web_search_tools` — note:
   this is actually 13 entries once RAG/MDQ/shell/web-search are included per the
   plan's full In-Scope module list, even though this document's own assigned
   `target_file_name` batch only covers 10 of the 13 producer files; the test file
   itself must cover all 13 to match `get_all_mcp_tool_names()`'s 10 *name-set*
   constants (`READ_TOOLS` etc.) which map onto exactly these 13 modules (file
   read/write/delete = 3 modules for one server's worth of `READ_TOOLS`+`WRITE_TOOLS`+
   `DELETE_TOOLS`, GitHub = 4 modules for `GITHUB_TOOLS`).
4. Add `test_all_tools_pass_schema_v2_contract` parametrized over
   `_TOOL_LIST_MODULES`, importing each module, iterating its `TOOL_LIST`, and
   asserting `validate_tool_schema_v2(entry) == []` for every entry (with the
   violation list included in the assertion failure message for diagnosability).
5. Add `test_tool_name_coverage_matches_tool_constants`, non-parametrized: collect the
   union of `t["name"]` across all 13 modules' `TOOL_LIST`s, and assert it equals
   `get_all_mcp_tool_names()` exactly (`==` on sets, with a diff-friendly failure
   message showing `symmetric_difference` when unequal).

### Method

New pytest module following the existing project convention
(`importlib.import_module()` + `getattr` + `@pytest.mark.parametrize`), added as a
sibling to `tests/mcp_servers/test_tool_schema.py` rather than replacing it.

### Details

- Skeleton content (illustrative; exact validator import path depends on the
  sibling implementation procedure for `scripts/shared/resource_scope.py`):
  ```python
  """tests/mcp_servers/test_tool_schema_contract.py

  Schema-2.0 contract coverage across all MCP server TOOL_LIST modules.

  Validates every tool dict exported by every MCP server's TOOL_LIST against the
  schema-2.0 per-tool metadata contract (is_write, requires_serial,
  resource_scope_kind, resource_scope_keys) via
  scripts/shared/resource_scope.py::validate_tool_schema_v2(), and cross-checks full
  tool-name coverage against shared.tool_constants.get_all_mcp_tool_names().

  See also tests/mcp_servers/test_tool_schema.py for the narrower, pre-schema-2.0
  field-presence check limited to the 4 file+git modules.
  """

  from __future__ import annotations

  import importlib
  from typing import Any

  import pytest
  from shared.resource_scope import validate_tool_schema_v2
  from shared.tool_constants import get_all_mcp_tool_names

  _TOOL_LIST_MODULES: list[tuple[str, str]] = [
      ("mcp_servers.file.read_tools", "TOOL_LIST"),
      ("mcp_servers.file.write_tools", "TOOL_LIST"),
      ("mcp_servers.file.delete_tools", "TOOL_LIST"),
      ("mcp_servers.git.git_tools", "TOOL_LIST"),
      ("mcp_servers.github.tools_repository", "TOOL_LIST"),
      ("mcp_servers.github.tools_file", "TOOL_LIST"),
      ("mcp_servers.github.tools_issues", "TOOL_LIST"),
      ("mcp_servers.github.tools_pull_requests", "TOOL_LIST"),
      ("mcp_servers.cicd.cicd_tools", "TOOL_LIST"),
      ("mcp_servers.rag_pipeline.rag_pipeline_tools", "TOOL_LIST"),
      ("mcp_servers.mdq.mdq_tools", "TOOL_LIST"),
      ("mcp_servers.shell.shell_tools", "TOOL_LIST"),
      ("mcp_servers.web_search.web_search_tools", "TOOL_LIST"),
  ]


  @pytest.mark.parametrize("module_path, attr_name", _TOOL_LIST_MODULES)
  def test_all_tools_pass_schema_v2_contract(module_path: str, attr_name: str) -> None:
      mod = importlib.import_module(module_path)
      tool_list: list[dict[str, Any]] = getattr(mod, attr_name)
      for tool in tool_list:
          violations = validate_tool_schema_v2(tool)
          assert violations == [], f"{module_path}::{tool['name']}: {violations}"


  def test_tool_name_coverage_matches_tool_constants() -> None:
      found: set[str] = set()
      for module_path, attr_name in _TOOL_LIST_MODULES:
          mod = importlib.import_module(module_path)
          found |= {t["name"] for t in getattr(mod, attr_name)}
      expected = get_all_mcp_tool_names()
      assert found == expected, (
          f"mismatch: {found.symmetric_difference(expected)}"
      )
  ```
- The `mcp_servers.rag_pipeline.rag_pipeline_tools`, `mcp_servers.mdq.mdq_tools`,
  `mcp_servers.shell.shell_tools`, `mcp_servers.web_search.web_search_tools` module
  paths are included in `_TOOL_LIST_MODULES` above for the coverage test to succeed
  even though their own field-population is out of scope for this task's assigned
  11-file batch (they are covered by a separate batch/agent per the plan's full Scope
  list) — omitting them here would make
  `test_tool_name_coverage_matches_tool_constants` fail spuriously (missing names) as
  soon as this test file is added, before those other files' own docs are
  implemented. This is flagged explicitly since it means this test file's list must
  stay synchronized with all 13 producer modules across both batches, not only the
  10 named in this task's target list plus 1 test file.

## Compatibility considerations

This is a new file; it adds no risk to existing tests. It has a hard phase-ordering
dependency: it will fail to import (`ImportError` on
`from shared.resource_scope import validate_tool_schema_v2`) until
`scripts/shared/resource_scope.py` exists with that function, and it will fail its
assertions until all 13 `TOOL_LIST` modules (10 in this task's batch + 3 in the
sibling RAG/MDQ/shell/web-search batch) have their schema-2.0 fields populated. This
matches the plan's own Phase ordering (Phase 1 adds the validator, Phase 2 populates
`TOOL_LIST`s and adds this test) — the test is expected to be red until both
predecessor steps land, which is normal for a plan executed phase-by-phase rather than
file-by-file.

## Security considerations

None directly — this is a test-only file with no production code path. Indirectly,
it is the CI gate the plan's Risk section relies on to prevent a future tool addition
from silently shipping without complete write/scope metadata (which the plan
identifies as a risk to fail-closed discovery-time enforcement in
`mcp_tool_discovery.py`, a different target file).

## Rollback considerations

Trivial: delete the new file. No production code imports it; no other test file
depends on it existing.

## Validation plan

- `uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v` — per the plan's
  own Validation-plan row for this exact file: "Every exported tool passes the
  schema-2.0 validator." Expected to fail until
  `scripts/shared/resource_scope.py::validate_tool_schema_v2()` exists and all 13
  `TOOL_LIST` modules are populated; expected to pass once both land.
- `uv run pytest tests/mcp_servers/ -v` — confirm no collection error is introduced
  and no pre-existing test in this directory regresses.

## Out of scope

- `scripts/shared/resource_scope.py` and its `validate_tool_schema_v2()` function
  (or equivalent name) — a different agent's assigned file.
- Populating the schema-2.0 fields on `rag_pipeline_tools.py`, `mdq_tools.py`,
  `shell_tools.py`, `web_search_tools.py` — a different batch's target files, though
  this test file's `_TOOL_LIST_MODULES` list must include them for the coverage
  check to be meaningful.
- Any change to `shared.tool_constants.get_all_mcp_tool_names()` itself.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-195328
- Related target files: tests/mcp_servers/test_tool_schema_contract.py
