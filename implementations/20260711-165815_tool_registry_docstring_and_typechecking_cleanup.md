# Implementation: Clean up `tool_registry.py` docstring, no-op TYPE_CHECKING block, and comments

## Goal

Make `scripts/shared/tool_registry.py`'s module docstring and comments accurate and
unambiguous — remove references to non-existent drift-detection functions, state the
module's ownership/routing-only scope explicitly, remove a dead no-op code block, and
clarify the reserved/unused status of two `ToolDefinition` fields — with zero runtime
behavior change.

## Scope

**In-Scope:**
- Rewrite the module docstring's "Drift detection" section to name only functions that
  actually exist in `shared.tool_routing_validation`.
- Add an explicit statement to the module docstring that `ToolRegistry` owns
  tool-to-server ownership and routing only, and is not a schema/description registry.
- Remove the no-op `if TYPE_CHECKING: pass` block and the now-unused `TYPE_CHECKING`
  import.
- Add a "reserved for future use" clarification to `ToolDefinition.description` and
  `ToolDefinition.input_schema`.
- Strengthen the backward-compatibility comment on the validation re-exports, if a
  re-export block is present in the file (see Assumptions — current file state does not
  show one; verify before editing).

**Out-of-Scope:**
- Any change to `shared/tool_routing_validation.py` (function signatures or logic).
- Removing the backward-compat re-export block, if present.
- Removing `ToolDefinition.description`/`input_schema` fields.
- Any change to `docs/04_mcp_03_02_tool-registry.md` or
  `docs/04_mcp_07_tool_schema_export_policy.md` (covered by separate docs, see the two
  Phase 2 implementation documents for this plan).

## Assumptions

1. Per the plan's Assumption 1, the module docstring (originally cited as lines 19-22)
   names `compare_registry_vs_config()`, `compare_registry_vs_live()`, and
   `compare_config_vs_live()`, none of which exist as functions anywhere in the
   codebase. Direct read of the current file (as of this document's authoring)
   confirms this drift is present at the docstring's "Drift detection:" section (near
   the end of the module docstring, currently around lines 19-21).
2. Per the plan's Assumption 2, the `if TYPE_CHECKING: pass` block is a genuine no-op.
   Direct read confirms it is present at approximately lines 30-31, immediately
   following `from typing import TYPE_CHECKING`, with no other `TYPE_CHECKING` usage
   in the file.
3. Per the plan's Assumption 3, `ToolDefinition.description`/`input_schema` (current
   file: `class ToolDefinition` body) are never constructed with non-default values and
   never read anywhere in `scripts/` or `tests/`. Keeping them with a clarifying
   docstring/comment is the zero-risk choice.
4. **Discrepancy flag (verify before editing):** the plan's Assumption 4 and Design
   section describe a backward-compat re-export block (`from shared.tool_routing_validation
   import validate_all_routing, validate_routing_against_config,
   validate_routing_against_live`) at lines 190-196 of `tool_registry.py`. A direct read
   of the current file at design-doc-authoring time shows the file is only ~187 lines
   long and contains **no** such re-export block and no reference to
   `tool_routing_validation` anywhere. Before implementing this phase, re-check the
   current file contents:
   ```bash
   grep -n "tool_routing_validation\|validate_routing_against_config\|validate_all_routing" scripts/shared/tool_registry.py
   ```
   - If the re-export block **is** present (e.g. added by a concurrently-processed
     sibling plan since this doc was authored), apply the comment-strengthening edit
     described below.
   - If the re-export block is **absent**, skip the re-export-comment edit entirely for
     this phase — there is nothing to strengthen. Note the discrepancy in the commit/PR
     description rather than fabricating a block (creating the re-export block itself
     is out of scope for this docstring-cleanup plan; it belongs to a different,
     concurrently-processed plan per this task's context).
5. `docs/04_mcp_03_02_tool-registry.md` already documents the three existing validation
   functions (`validate_routing_against_config`, `validate_routing_against_live`,
   `validate_all_routing`) in its own drift-verification table, confirming these are the
   correct canonical names to use in the rewritten docstring.

## Implementation

### Target file

`scripts/shared/tool_registry.py`

### Procedure

1. Read the full current file to re-confirm exact current line numbers for the
   docstring's "Drift detection:" section, the `if TYPE_CHECKING: pass` block, the
   `ToolDefinition` class body, and (per Assumption 4) whether a re-export block exists.
2. Edit the module docstring:
   - Replace the "Drift detection:" section's three bullet lines (currently naming
     `compare_registry_vs_config()`, `compare_registry_vs_live()`,
     `compare_config_vs_live()`) with the three functions that actually exist:
     `validate_routing_against_config()`, `validate_routing_against_live()`,
     `validate_all_routing()`, each with a one-line description of what it validates,
     and a lead-in noting `shared.tool_routing_validation` as the canonical validation
     module.
   - Add a short statement (near the top of the docstring, alongside the existing
     "Ownership model:" section) that `ToolRegistry` owns tool-to-server
     ownership/routing only, is not a schema/description registry, and that
     LLM-visible tool schemas come from each server's own `tools.py` `TOOL_LIST`
     (cross-reference `docs/04_mcp_07_tool_schema_export_policy.md`).
3. Remove the `if TYPE_CHECKING: pass` block and the `from typing import TYPE_CHECKING`
   import line. Confirm no other symbol in the file depends on `TYPE_CHECKING`.
4. Add a docstring to `ToolDefinition` (or extend its existing one-line docstring)
   stating that `description`/`input_schema` are reserved for future use, are never
   populated by `_populate_default_registry()` (or equivalent default-population
   function), and are not read by any caller today; add short inline `# reserved for
   future use; not populated today` comments on the two field declarations themselves.
5. Conditionally (per Assumption 4): if a validation re-export block exists in the
   file, replace its leading comment with a strengthened version stating it exists
   ONLY for backward compatibility with external callers, that no internal caller uses
   this path today (all internal imports go directly to
   `shared.tool_routing_validation`), and that new code should import from
   `shared.tool_routing_validation` directly.

### Method

- Use targeted `Edit`-style string replacements (in the actual implementation step, not
  in this design step) — one replacement per logical change (docstring, TYPE_CHECKING
  block + import, ToolDefinition comments, optional re-export comment).
- No function signatures, class definitions, or runtime logic change anywhere in this
  file.
- Preserve all surrounding docstring sections ("Ownership model:", any existing
  "Routing authority:" section) verbatim except for the specific edits above.

### Details

- The docstring rewrite must not introduce any function name that does not exist under
  `shared.tool_routing_validation` — cross-check with
  `grep -n "^def " scripts/shared/tool_routing_validation.py` before finalizing wording.
- Removing the `TYPE_CHECKING` import must not leave an unused-import lint error (ruff
  `F401`); confirm no other code path in the file references `TYPE_CHECKING`.
- The `ToolDefinition` field comments must stay accurate: do not claim the fields are
  used anywhere, since Assumption 3 confirms zero internal readers/writers today.
- This is a comments/docstring-only change; no import of new modules, no change to
  `ToolRegistry`'s or `ToolDefinition`'s public shape (field types/order unchanged).

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/tool_registry.py` | 0 errors (confirms unused `TYPE_CHECKING` import removal doesn't leave an F401) |
| Type check | `uv run mypy scripts/shared/tool_registry.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes beyond removing the unused one) |
| Tests (no behavior change expected) | `uv run pytest tests/test_tool_registry.py tests/test_tool_registry_counts.py tests/test_tool_registry_reset_protection.py tests/test_routing_duplicate_ownership.py tests/test_startup_routing_drift.py tests/test_github_tool_registry.py -q` | All pass, identical results to pre-change baseline |
| Manual grep | `grep -n "compare_registry_vs_config\|compare_registry_vs_live\|compare_config_vs_live" scripts/shared/tool_registry.py` | No matches |
| Manual grep (TYPE_CHECKING) | `grep -n "TYPE_CHECKING" scripts/shared/tool_registry.py` | No matches |
