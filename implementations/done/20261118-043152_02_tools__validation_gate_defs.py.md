## Goal

Remove the toolchain table and the bare-except rule from `tools/_validation_gate_defs.py` (they move to the new module in seq 01), then add the two manual routing mappings for the audit and the reconciliation tool (Plan REQ-001, REQ-002, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: deleting the moved blocks and updating the module docstring (Plan Phase 1); appending the two manual `Gate` entries after the last routing gate (Plan Phase 2).
- Out of scope: creating the new module (seq 01 document); the runner import (seq 03 document); test updates (seq 04 document); `routing.md` rows (seq 05 document).

## Assumptions

- After seq 01 copies the blocks, removing them from this module frees about 4.7 KB; the two mappings add about 600 B, so the net drop is well above the 2 KB AC-6 floor and the module lands near 20.4 KB (measured 20261118: 24526 B module, 3377 B table, 1363 B rule).
- `TOOLCHAIN_GATES` is imported only by `tools/run_validation_gates.py` and `_BARE_EXCEPT_RULE` is used only inside this module (Plan row 2 evidence, corrected at plan revalidation 20261118); seq 03 rewires the runner import before the removal commit lands.
- A patternless routing gate is never auto-selected in fast or full mode (`select_gates` skips `SOURCE_ROUTING` gates with no patterns; precedent: the ten existing patternless entries, among them `amend_plan` and `check_compat_shims`) (Plan Assumptions; count verified 20261118).
- `Gate.checker_id` derives the id from the first command's tool basename, and a positional token after the tool path appends a `:<positional>` suffix (precedent: `amend_plan`'s id is `amend_plan:<plan>`). A placeholder token must carry no space: the drift check compares the gate id with the id `_checker_id_from_cell` derives from the `routing.md` Run cell by splitting the cell on whitespace, so a space-containing cell token like `[plans/*.md ...]` would derive a different id on each side (corrected 20261118 by adversarial re-verification). With the `<plan>` placeholders below, the two new ids are `audit_plan_target_paths:<plan>` and `sync_plan_workitem_status:<plan>`; `--dry-run` is not in `_VALUE_FLAG_RE` and never reaches the id because the positional matches first. No existing gate carries either name (checked 20261118).

## Design decisions

- Manual mappings: `patterns=()`, placeholder arguments, `source=SOURCE_ROUTING`, `mode=MODE_FAST` (Plan Decision 2): a patternless gate is never selected and never prints a gate-output row, while `requires_context` is true because the argv carries placeholders.
- Mappings are appended after the last routing gate (Plan Phase 2 checklist), keeping the table's documented order intact.

## Alternatives considered

- Give the audit a path pattern so fast mode auto-runs it: rejected — making the audit a blocking gate is Out-of-Scope (Plan Scope).
- Reuse the toolchain table location instead of appending: rejected — the drift check maps only `ROUTING_GATES`, and the routing table's order mirrors `routing.md`'s rows (Plan Decision 1c reasoning).

## Implementation
### Target file
`tools/_validation_gate_defs.py`
### Procedure
1. After seq 01 lands (same commit), delete the `_BARE_EXCEPT_RULE` assignment with its comment block and the entire `TOOLCHAIN_GATES` assignment with its per-gate comments (the region between `MODE_FULL` and `_PLACEHOLDER_TOKEN_RE`, and the `TOOLCHAIN_GATES` assignment immediately before `ROUTING_GATES`).
2. Update the module docstring: it names "the toolchain and routing gate tables" — change it to the routing gate table, naming `tools/_validation_gate_toolchain.py` as the toolchain table's new home. Keep the "Embedded gate inventory" comment's routing sentence; drop its `rules/toolchain.md` sentence (moved to the new module).
3. Keep every helper and constant the routing table or the orchestrator uses (`_PLACEHOLDER_TOKEN_RE`, `_CHANGED_FILES_SENTINEL`, `_TOOL_PY_RE`, `_VALUE_FLAG_RE`, `Gate`, source and mode constants, `_checker_id_from_command`).
4. In Plan Phase 2, append after the last `Gate` of `ROUTING_GATES` (immediately before its closing `)`):
   ```python
   Gate(
       name="audit_plan_target_paths",
       command=(("uv", "run", "python", "tools/audit_plan_target_paths.py", "<plan>"),),
       source=SOURCE_ROUTING,
       mode=MODE_FAST,
       patterns=(),
   ),
   Gate(
       name="sync_plan_workitem_status",
       command=(("uv", "run", "python", "tools/sync_plan_workitem_status.py", "<plan>", "--dry-run"),),
       source=SOURCE_ROUTING,
       mode=MODE_FAST,
       patterns=(),
   ),
   ```
   The argv mirrors the two `routing.md` Run cells (seq 05 document) token for token — each placeholder is a single space-free token — so both sides derive the same checker id.

### Method
- Region deletion plus one append; no other line changes. The commands must equal the `routing.md` rows because the drift check compares derived ids in both directions.

### Details
- Do not reformat existing entries; the table's per-gate comments (e.g. hook names, `Not available` notes) stay as they are.
- Phase ordering (Plan Phases 1 and 2): the removal lands with seq 01/03/04 in the Phase 1 commit; the mappings land in the Phase 2 commit together with the two `routing.md` rows (seq 05) — landing one without the other fails the drift check (Risk 3).

## Compatibility considerations

- The orchestrator and its test module import this module (Plan Affected areas: blast radius Medium); their edits are seq 03 and seq 04 in the same commit, so no importer sees a missing `TOOLCHAIN_GATES`.
- `SOURCE_TOOLCHAIN` stays defined here; the new module imports it from here (Plan Design - Architecture).

## Security considerations

- N/A: gate data edits only; the bare-except rule moves unchanged and keeps applying through the moved table.

## Rollback considerations

- Revert the Phase 1 (and Phase 2) commits; the blocks return to this module. The captured tables (`/tmp/opencode/gate_tables_before_move.json`, seq 01 document) allow content re-verification.

## Validation plan

- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` → passes, and the module is at least 2 KB below its 24526 B pre-move size (AC-6).
- `uv run ruff check tools` and `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` → clean.
- After Phase 2: `uv run python tools/run_validation_gates.py drift` → parity with both rows present (AC-2, AC-3, run jointly with seq 05).

## Completion criteria

- The two blocks no longer appear here; the docstring names the new module; both mappings exist with `patterns == ()`, `requires_context` true, and ids `audit_plan_target_paths:<plan>` and `sync_plan_workitem_status:<plan>` (AC-1, AC-2); the size gate passes with the module at least 2 KB below 24526 B (AC-6).

## Out of Scope

- `tools/_validation_gate_toolchain.py` creation (seq 01), `tools/run_validation_gates.py` import (seq 03), `tests/tools/test_run_validation_gates.py` (seq 04), `routing.md` (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-101946 | 20261118-103121 | TOOLCHAIN_GATES and _BARE_EXCEPT_RULE removed (lines 107-122, 145-283), module docstring and inventory comment updated, two manual Gate entries appended after ruff_format_check_changed |
| 2 | Add or update tests per Validation plan | Completed | — | 20261118-103121 | Covered by the seq 04 document N/A: covered by the seq 04 document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261118-103121 | module 24526->21484 B (net drop 3042 B, above the 2 KB AC-6 floor); file-level ruff format/check, mypy, bandit -c pyproject.toml (low-only, pre-existing): clean; drift: 47 routing.md checkers all mapped; 102 tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261118-103121 | Description rows are the seq 07 document N/A: description rows are the seq 07 document |

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
- **Requirement ID**: `REQ-001` (move), `REQ-002` (manual mappings), `REQ-006` (size gates)
- **Source issue**: issues/20261117-123333_wftool004_orphan-tool-routing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125207_wftool004_orphan-tool-routing.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-043152
- **Related target files**: `tools/_validation_gate_defs.py`