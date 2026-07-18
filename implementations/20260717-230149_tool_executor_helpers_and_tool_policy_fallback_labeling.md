# Implementation procedure: `tool_executor_helpers.py` / `tool_policy.py` fallback-comment verification

Source plan: `plans/20260717-130629_plan.md` (requirement `requires/done/20260717_10_require.md`),
Implementation step 5.

## Goal

Verify that requirements 06-07's migrations of `is_side_effect()`
(`scripts/shared/tool_executor_helpers.py`) and `classify_operation_type()`
(`scripts/agent/tool_policy.py`) to consult `RuntimeToolRegistry` primarily include an explicit code
comment marking the static-frozenset path as secondary/fallback — and add one if their landed
implementation didn't already include it.

## Scope

**In scope**
- Confirming/adding a fallback-labeling code comment adjacent to the frozenset-based branches inside
  `is_side_effect()` and `classify_operation_type()`, once requirements 06/07 land their
  production-code migration.

**Out of scope**
- Requirements 06/07's actual RuntimeToolRegistry-consulting logic itself (not this requirement's
  job — this requirement only confirms/adds the comment).
- Any change to the frozensets in `tool_constants.py` (covered by the separate
  `implementations/20260717-230059_tool_constants.py.md` doc).

## Assumptions

1. Per `implementations/20260717-225949_requirements_04_09_landing_check.md`, requirements 06 and 07
   have **not landed** their production-code migration — only `agent/tool_enums.py`'s
   `OperationType.UNKNOWN` addition (`implementations/20260717-220404_tool_enums.py.md`) and test-side
   scaffolding (`implementations/20260717-220433_test_tool_policy.py.md`,
   `implementations/20260717-220527_test_tool_approval_risk.py.md`) exist so far.
2. Confirmed by direct read of current real source:
   - `is_side_effect()` (`scripts/shared/tool_executor_helpers.py:47-50`):
     ```
     def is_side_effect(tool_name: str) -> bool:
         """Return True when the tool modifies state: file write/delete, shell,
         Git write operations, or GitHub write/dangerous operations."""
         return tool_name in _SIDE_EFFECT_TOOLS
     ```
     No `RuntimeToolRegistry` reference; no fallback comment exists (there is nothing to be a
     "fallback" from yet).
   - `classify_operation_type()` (`scripts/agent/tool_policy.py:52-60`):
     ```
     def classify_operation_type(tool_name: str) -> OperationType:
         """Return the operation type for a tool."""
         if tool_name in _ALL_WRITE_TOOLS:
             return OperationType.WRITE
         if tool_name in DELETE_TOOLS:
             return OperationType.DELETE
         if tool_name in _EXEC_TOOLS:
             return OperationType.EXECUTE
         if tool_name in _GITHUB_MUTATION_TOOLS:
             return OperationType.API_WRITE
         return OperationType.READ
     ```
     No `RuntimeToolRegistry` reference; falls back to `OperationType.READ` by default today (not yet
     `OperationType.UNKNOWN`, confirming the enum addition from
     `implementations/20260717-220404_tool_enums.py.md` is itself not yet wired into this function).
3. Consequently, there is nothing in current real source for this item to "confirm" yet — this
   item's Procedure step below is itself the gate that must be satisfied before there is anything
   concrete to check.

## Implementation

### Target files

- `scripts/shared/tool_executor_helpers.py` — `is_side_effect()`, lines 47-50 (plus the
  `_SIDE_EFFECT_TOOLS` frozenset definition immediately above, lines 30-40).
- `scripts/agent/tool_policy.py` — `classify_operation_type()`, lines 52-60 (plus `_ALL_WRITE_TOOLS`,
  `_EXEC_TOOLS`, `_GITHUB_MUTATION_TOOLS` definitions, lines 31-36).

### Procedure

1. Wait for requirements 06 and 07 to land their production-code doc + implementation (i.e., both
   functions gain a `RuntimeToolRegistry`-consulting branch, per each requirement's own plan).
2. Once landed, read the landed function bodies to check whether a comment already marks the
   remaining static-frozenset branch as fallback/secondary.
3. If present and worded consistently with this requirement's compatibility framing, no change
   needed — note this in the final report.
4. If absent, or worded ambiguously (e.g., doesn't clarify "used only when the tool is absent from
   `RuntimeToolRegistry`"), add/adjust the comment.

### Method

Code comment insertion adjacent to the frozenset-based branch in each function; no logic change from
this item itself (requirements 06/07 already own the logic change — this item only ensures the
comment exists and is worded correctly).

### Details

- For `is_side_effect()`: once migrated, the comment should convey: "The frozenset check below
  (`_SIDE_EFFECT_TOOLS`) is the fallback path, consulted only when `tool_name` is absent from
  `RuntimeToolRegistry`'s live-discovered side-effect metadata."
- For `classify_operation_type()`: the comment should convey the equivalent for the frozenset-based
  branches (`_ALL_WRITE_TOOLS`, `DELETE_TOOLS`, `_EXEC_TOOLS`, `_GITHUB_MUTATION_TOOLS`), and should
  additionally note that `OperationType.UNKNOWN` (landed via
  `implementations/20260717-220404_tool_enums.py.md`) is the fail-safe result once neither
  `RuntimeToolRegistry` nor the static sets can classify a tool — replacing today's silent
  `OperationType.READ` default (this is requirement 07's own stated purpose for adding `UNKNOWN`, per
  that doc's Goal).
- Because requirements 06/07 haven't landed, this doc cannot specify an exact line number for the new
  comment beyond "adjacent to whatever `RuntimeToolRegistry`-consulting branch requirement 06/07 adds"
  — that branch doesn't exist in source yet, so its insertion point is undetermined until then.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Requirements 06/07 gate | manual check of `implementations/` for landed production-code docs (not just enum/test scaffolding) | this item's edit not applied until gate passes |
| Comment presence/wording review | manual read of both functions once 06/07 land | fallback comment present in both, worded per this doc's Details |
| `ruff check` | `uv run ruff check scripts/shared/tool_executor_helpers.py scripts/agent/tool_policy.py` | pass (comment-only for this item) |
| Full suite | `uv run pytest` | no failures attributable to this item (comment-only) |
