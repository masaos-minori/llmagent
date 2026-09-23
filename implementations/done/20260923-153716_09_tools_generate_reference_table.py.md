## Goal

Implement REQ-010 (`plans/20260923-152824_plan.md`) in
`tools/generate_reference_table.py`: update the 5 `REFERENCE_DOC_*`
constants' directory components for their new locations.

## Scope

Modify only `tools/generate_reference_table.py` to update:
1. `REFERENCE_DOC_MCP` → `docs/22_mcp/04_mcp_01_tool_ownership_matrix.md`.
2. `REFERENCE_DOC_DEPLOYMENT` → `docs/90_deployment/02_deployment-part2.md`
   (directory component only — the pre-existing, unrelated bug where this
   filename does not exist under any name is NOT fixed here, see Out of
   scope).
3. `REFERENCE_DOC_AGENT` → `docs/23_agent/05_agent_14_reference-api-generated.md`.
4. `REFERENCE_DOC_EVENTBUS` → `docs/24_eventbus/06_eventbus_06_reference-api.md`
   (this constant was omitted from the source Issue's Problem section —
   discovered during this Plan's drafting via Read).
5. `REFERENCE_DOC_MEMORY` → `docs/23_agent/05_agent_12_07_memory-module-reference-generated.md`.

## Assumptions

- All 5 constants are standalone output-path constants with no relationship
  to `discover_md_files()` — they are write-targets for generated reference
  tables, resolved directly by path, not discovered by glob. Unaffected by
  seq 01's recursive-glob change; this document has no dependency on any
  other document in this Plan.
- `tests/tools/test_generate_reference_table.py` is confirmed hermetic
  (tests the generator functions directly, no real `docs/` path dependency)
  — no test change needed.
- `REFERENCE_DOC_MEMORY`'s file moves to `docs/23_agent/` (not a separate
  memory-specific folder) since `05_agent_12_07_memory-module-reference-generated.md`
  is part of the `05_agent_*` prefix group per the folder classification —
  confirmed consistent with the source Plan's directory-component mapping.

## Design decisions

- Update all 5 constants together in one document since they are structurally
  identical (a `REPO_ROOT / "docs" / "<filename>"` literal each) and none
  depends on another landing first — the smallest coherent, independently
  testable unit for this file.
- Do not attempt to fix the pre-existing `docs/02_deployment-part2.md`
  non-existent-file bug — only the directory component of the constant
  changes, exactly as the source Issue's own Constraints required.

## Alternatives considered

- Splitting the 5 constant updates into 5 separate documents: rejected —
  they share the exact same file, the exact same mechanical pattern, and
  none has an inter-dependency; one document is the appropriately-scoped
  unit (still one target file per `templates/implementation-procedure.md`'s
  one-file-per-document rule).

## Implementation

### Target file

`tools/generate_reference_table.py`

### Procedure

1. Locate the 5 constants (lines 67-73).
2. Update each constant's path literal to insert the new directory segment
   between `"docs"` and the filename, per the mapping in Scope.

### Method

One `Edit` call covering all 5 lines (they are contiguous in the source).

### Details

Current (lines 67-73):
```python
REFERENCE_DOC_MCP = REPO_ROOT / "docs" / "04_mcp_01_tool_ownership_matrix.md"
REFERENCE_DOC_DEPLOYMENT = REPO_ROOT / "docs" / "02_deployment-part2.md"
REFERENCE_DOC_AGENT = REPO_ROOT / "docs" / "05_agent_14_reference-api-generated.md"
REFERENCE_DOC_EVENTBUS = REPO_ROOT / "docs" / "06_eventbus_06_reference-api.md"
REFERENCE_DOC_MEMORY = (
    REPO_ROOT / "docs" / "05_agent_12_07_memory-module-reference-generated.md"
)
```

After modification:
```python
REFERENCE_DOC_MCP = REPO_ROOT / "docs" / "22_mcp" / "04_mcp_01_tool_ownership_matrix.md"
REFERENCE_DOC_DEPLOYMENT = REPO_ROOT / "docs" / "90_deployment" / "02_deployment-part2.md"
REFERENCE_DOC_AGENT = REPO_ROOT / "docs" / "23_agent" / "05_agent_14_reference-api-generated.md"
REFERENCE_DOC_EVENTBUS = REPO_ROOT / "docs" / "24_eventbus" / "06_eventbus_06_reference-api.md"
REFERENCE_DOC_MEMORY = (
    REPO_ROOT / "docs" / "23_agent" / "05_agent_12_07_memory-module-reference-generated.md"
)
```

(Line-wrapping per `ruff format`'s line-length rule — confirm exact
formatting during implementation via `ruff format`.)

## Compatibility considerations

- Not wired into pre-commit or the CI workflows inspected for this Plan —
  invoked manually/on-demand only.
- `REFERENCE_DOC_DEPLOYMENT`'s pre-existing bug (file doesn't exist under
  any name) is unaffected either way — `--type deployment` without
  `--dry-run` will continue to fail the same way it does today, just
  reporting the new (still-nonexistent) path instead of the old one.
- Correctness for the other 4 constants against the real repository only
  lands once the corresponding physical-move issues land.

## Security considerations

No security impact.

## Rollback considerations

1. Revert all 5 constants to their original values.
2. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_generate_reference_table.py -q`
(confirmed hermetic — passes unchanged, since it tests the generator
functions directly rather than the module-level path constants). Manually
invoke `uv run python tools/generate_reference_table.py --type mcp --dry-run`
(and `agent`, `eventbus`, `memory` — skip `deployment` per the pre-existing
bug) against the current (pre-move) tree to confirm each reports the new
(currently nonexistent, pre-move) path rather than raising an unrelated
exception.

## Completion criteria

- All 5 `REFERENCE_DOC_*` constants include their new directory component,
  with the filename portion unchanged.
- `uv run pytest tests/tools/test_generate_reference_table.py -q` passes
  unchanged.
- `--dry-run` invocations for `mcp`/`agent`/`eventbus`/`memory` report the
  new path without a Python exception.

## Out of scope

- Fixing the pre-existing `docs/02_deployment-part2.md` non-existent-file
  bug.
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-162229 | 20260923-162229 | Step3 stale_detector false-positive (REFERENCE_DOC_MEMORY, exists in source) confirmed and bypassed. All 5 REFERENCE_DOC_* constants updated with new directory components. |
| 2 | Add or update tests per Validation plan | Completed | 20260923-162229 | 20260923-162229 | No test change needed; test_generate_reference_table.py confirmed hermetic, 7 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-162229 | 20260923-162229 | ruff/mypy/bandit pass. pytest: 7 passed. --dry-run for mcp/agent/eventbus/memory all ran without exception (deployment skipped per its own pre-existing, unrelated bug, per Out of scope). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-162229 | 20260923-162229 | N/A: no docs/00_index.md task-scope mapping for tools/generate_reference_table.py. |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tools/generate_reference_table.py