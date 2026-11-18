## Goal

Create `tools/_validation_gate_toolchain.py` holding the toolchain gate table and the bare-except rule, moved verbatim from `tools/_validation_gate_defs.py`, so the definition module gains the room for two new manual routing mappings (Plan REQ-001: the move is content-identical; REQ-006: all three gate modules stay under the 24576 B size limit).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new module (moved `_BARE_EXCEPT_RULE` and `TOOLCHAIN_GATES`, unchanged) and the pre-move characterization capture of both gate tables.
- Out of scope: removing the blocks from `tools/_validation_gate_defs.py` and adding the mappings (seq 02 document); the runner import (seq 03 document); test updates (seq 04 document); `routing.md`, the issue-to-plan workflow, and the tool descriptions (seq 05-07 documents).

## Assumptions

- The definition module is 24526 B with 50 B of headroom under the 24576 B limit, and two new mappings need about 600 B (Plan re-measured 20261118 at plan revalidation).
- The moved region is about 4.7 KB: the `TOOLCHAIN_GATES` block measures 3377 B and `_BARE_EXCEPT_RULE` with its comment 1363 B; at module level the block references only `Gate`, `MODE_FULL`, `SOURCE_TOOLCHAIN`, and `_BARE_EXCEPT_RULE` — everything else in it is a string or field name (Plan row 1 evidence, re-checked 20261118).
- The move is behavior-neutral because the orchestrator composes `_ALL_GATES` as `(*ROUTING_GATES, *TOOLCHAIN_GATES)` and the contents and order are kept (Plan Assumptions).
- The new module is not listed in `tools/check_module_size_tools_baseline.txt`, so it must stay under the default limit (Plan Reference Files).

## Design decisions

- Move only the toolchain table, not the routing table (Plan Decision 1): moving the routing table would relocate the row the structure-gate Plan edits and create an ordering conflict.
- The new module imports from the definition module only (`Gate`, `MODE_FULL`, `SOURCE_TOOLCHAIN`); the definition module MUST NOT import the new module — no import cycle (Plan Design - Architecture; Risk 2).

## Alternatives considered

- Put the two mappings in the runner (880 B of headroom): rejected — the runner should not hold gate tables (Plan Decision 1b).
- Skip the routing rows and name the tools only in workflow steps: rejected — it fails the issue's Required Changes (Plan Decision 1a).

## Implementation
### Target file
`tools/_validation_gate_toolchain.py` (new)
### Procedure
1. Before any edit, capture both tables for the characterization comparison (Plan Phase 1, first checklist item):
   `uv run python -c "import json, tools._validation_gate_defs as d; print(json.dumps({'toolchain': [[g.name, [list(c) for c in g.command], g.mode, list(g.patterns), list(g.env), g.exclusive] for g in d.TOOLCHAIN_GATES], 'routing': [[g.name, [list(c) for c in g.command], g.mode, list(g.patterns), list(g.env), g.exclusive] for g in d.ROUTING_GATES]}, ensure_ascii=False))" > /tmp/opencode/gate_tables_before_move.json`
2. Create the module with a docstring naming it as the toolchain gate table of `tools/run_validation_gates.py`, transcribed from `rules/toolchain.md`, then `from __future__ import annotations` and `from tools._validation_gate_defs import Gate, MODE_FULL, SOURCE_TOOLCHAIN`.
3. Move the `_BARE_EXCEPT_RULE` assignment and the comment block above it verbatim (the region between `MODE_FULL` and `_PLACEHOLDER_TOKEN_RE` in the definition module).
4. Move the entire `TOOLCHAIN_GATES` assignment verbatim, all 11 `Gate` entries with their per-gate comments (the assignment from `TOOLCHAIN_GATES: tuple[Gate, ...] = (` down to the closing `)` immediately before `ROUTING_GATES`). Adapt only the "Embedded gate inventory" comment: the new module keeps the `rules/toolchain.md` sentence; the routing sentence stays in the definition module.

### Method
- Copy the source regions verbatim into the new module; no gate field, command token, order, mode, pattern, env pair, or exclusive flag is touched (AC-1). Ruff formatting already matches since the source was formatted.

### Details
- The module is data only: no CLI, no function definitions.
- Phase 1 coupling (Plan Phase 1): seq 02, 03, and 04 land in the same commit. Between this document and seq 03, `TOOLCHAIN_GATES` exists in both modules while the runner still imports the definition module's copy; the identity test stays green until seq 04. Do not run the full gate suite against the intermediate state alone.
- Do not add the new module to `tools/check_module_size_tools_baseline.txt`.

## Compatibility considerations

- Imported by the orchestrator only (Plan Affected areas: blast radius Low); no `scripts/` module imports it, so the import-linter contracts are unaffected (Plan Design - Dependency graphing).
- The definition module's docstring still naming the toolchain table until seq 02 lands is transient within the same commit.

## Security considerations

- N/A: a data module moved as-is; `bandit` runs over it per the Validation plan and it holds no executable logic beyond gate literals.

## Rollback considerations

- Revert the Phase 1 commit; the blocks return with the definition module. The capture file `/tmp/opencode/gate_tables_before_move.json` records the pre-move state for re-verification.

## Validation plan

- `uv run ruff format tools/_validation_gate_toolchain.py && uv run ruff check tools/_validation_gate_toolchain.py` → clean.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` → clean.
- `uv run bandit -r tools/_validation_gate_toolchain.py` → clean (Plan Validation plan).
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` → passes with the new module under 24576 B (AC-6).

## Completion criteria

- The module imports cleanly and `uv run python -c "import tools._validation_gate_defs, tools._validation_gate_toolchain"` exits 0; the seq 04 comparison against the captured tables reports them identical (AC-1); the size gate passes (AC-6).

## Out of Scope

- `tools/_validation_gate_defs.py`, `tools/run_validation_gates.py`, and `tests/tools/test_run_validation_gates.py` edits (seq 02-04 documents).
- `routing.md`, `skills/issue-to-plan/workflow.md`, and `tools/TOOL_DESCRIPTIONS.md` edits (seq 05-07 documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by the seq 04 document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Description row is the seq 07 document |

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
- **Requirement ID**: `REQ-001` (move the table unchanged), `REQ-006` (size gates)
- **Source issue**: issues/20261117-123333_wftool004_orphan-tool-routing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125207_wftool004_orphan-tool-routing.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-043152
- **Related target files**: `tools/_validation_gate_toolchain.py`
