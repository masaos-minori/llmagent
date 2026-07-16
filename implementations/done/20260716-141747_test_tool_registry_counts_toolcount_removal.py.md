# Implementation: tests/test_tool_registry_counts.py (remove `TestRegistryTotalCounts` and one count method)

Source plan: `plans/20260716-135355_plan.md`

Note: distinct from the two earlier `test_tool_registry_counts.py` docs
(`implementations/done/20260711-170008_...md`,
`implementations/done/20260711-170647_...md`), which respectively *added*
per-server snapshot tests and *marked* fixed-count tests as intentional
drift guards. This doc *removes* the total-count class and one per-server
count method entirely — the opposite direction, per the updated
requirement's disambiguation rule (keep cross-source comparisons, remove
literal-count/literal-name-set comparisons).

## Goal

Remove `TestRegistryTotalCounts` (3 methods, all literal-count assertions
against `ToolRegistry`) and
`TestRegistryRagPipelineCounts.test_registry_rag_pipeline_tool_count` (a
literal per-server count), while keeping every cross-source drift check in
the same file intact.

## Scope

**In:**
- Delete `TestRegistryTotalCounts` in full (current lines 55-92 area:
  `test_registry_total_tool_count`, `test_github_tools_count`,
  `test_mcp_tools_module_count`).
- Delete `TestRegistryRagPipelineCounts.test_registry_rag_pipeline_tool_count`
  (current lines 16-24) — a single method inside a class that has 3 other
  methods which must remain.

**Out:**
- `TestRegistryRagPipelineCounts.test_rag_tools_all_in_registry`,
  `.test_rag_list_documents_registered`, `.test_rag_delete_document_registered`
  — these compare `RAG_TOOLS` (an independent implementation source) against
  the live `ToolRegistry` (another independent source); explicitly retained
  per the source plan's Out-of-scope list.
- Any other file.

## Assumptions

1. Every assertion inside `TestRegistryTotalCounts`'s 3 methods and the one
   removed `TestRegistryRagPipelineCounts` method is a literal
   count/name-set comparison with no unique behavioral coverage — matches
   the source plan's Assumption 5 (confirmed during planning by reading
   each test body; re-confirm during implementation before deleting, since
   this doc's author has not independently re-read the method bodies).
2. After removing `test_registry_rag_pipeline_tool_count`,
   `TestRegistryRagPipelineCounts` still has 3 methods
   (`test_rag_tools_all_in_registry`, `test_rag_list_documents_registered`,
   `test_rag_delete_document_registered`) — the class itself is not
   removed, only the one method.

## Implementation

### Target file

`tests/test_tool_registry_counts.py`

### Procedure

1. Open `tests/test_tool_registry_counts.py`.
2. Read the full file to confirm current line numbers (they may have
   shifted since the source plan's analysis) and the exact body of each
   target method, per Assumption 1.
3. Delete `test_registry_rag_pipeline_tool_count` (the method, its
   docstring, and its full body) from inside `TestRegistryRagPipelineCounts`
   — leave the class declaration and its 3 remaining methods untouched.
4. Delete `TestRegistryTotalCounts` in full — the class declaration line,
   its docstring (if any), and all 3 methods
   (`test_registry_total_tool_count`, `test_github_tools_count`,
   `test_mcp_tools_module_count`).
5. Confirm no blank-line/whitespace residue is left where the deleted
   class used to sit (match the file's existing between-class spacing
   convention).

### Method

Two deletions: one method removed from an otherwise-retained class, one
class removed in full — no renaming, no weakened replacement assertions
(per the source plan's explicit instruction not to replace count checks
with `>= 1`-style checks).

### Details

- Do not replace the removed count assertions with any weakened numeric
  check — the requirement's intent is that no count-shaped assertion
  remains at all.
- Do not touch imports at the top of the file unless a name used only by
  the deleted tests becomes unused after removal — check via
  `uv run ruff check tests/test_tool_registry_counts.py` after the edit
  and remove any now-unused import it flags.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| `TestRegistryTotalCounts` gone | `grep -n "TestRegistryTotalCounts" tests/test_tool_registry_counts.py` | 0 matches |
| Removed method gone | `grep -n "test_registry_rag_pipeline_tool_count" tests/test_tool_registry_counts.py` | 0 matches |
| Remaining 3 methods intact | `grep -n "def test_rag_tools_all_in_registry\|def test_rag_list_documents_registered\|def test_rag_delete_document_registered" tests/test_tool_registry_counts.py` | 3 matches |
| Targeted tests pass | `uv run pytest tests/test_tool_registry_counts.py -v` | remaining tests pass; `TestRegistryTotalCounts` no longer collected |
| Lint | `uv run ruff check tests/test_tool_registry_counts.py` | 0 errors |
| Type check | `uv run mypy tests/test_tool_registry_counts.py` | no new errors |
