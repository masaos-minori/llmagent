## Goal
Collapse the `notify_bg_failure_threshold` / `_notify_threshold_breach` wrapper pair in the background-task monitor into one method named as the documentation names it, removing the "Backward-compatible alias" sentence the strict COMPAT scan flags (`REQ-002`).

## Scope
**Release unit**: wfaudit012-full

- Covers Plan `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md` row 4 only: `scripts/agent/bg_task_monitor.py`.

## Assumptions
- Procedure 01 (`implementations/20261108-190836_01_tools_check_compat_shims.py.md`) lands in the same change unit; the flagged docstring line L150 only appears in the strict run.
- The public name is the contract: `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` L90-91 describe `BgTaskMonitor.notify_bg_failure_threshold()` as the notification guarantee, so the collapse keeps that name and retires the private one.
- No test or script calls either method directly: the 2026-11-08 grep over `scripts/` and `tests/` finds call sites only at `scripts/agent/bg_task_monitor.py:138` and `:152` (both `self._notify_threshold_breach(...)`). `tests/agent/test_orchestrator.py` L2574, L2582, L2593, L2632, L2661 mention the older name `_notify_bg_failure_threshold` in docstrings and comments only, and `tests/agent/test_orchestrator_bg_failure_threshold.py` drives the behavior through `on_task_done`, so no test edit is needed.

## Design decisions
- Collapse (delete the wrapper, rename the real method to the public name) rather than delete the public wrapper: the documented public surface must stay callable, and the internal caller becomes the only caller of the surviving method. This mirrors the `wfaudit008` collapse pattern in `scripts/agent/workflow_engine_adapter.py` (`implementations/20261108-162804_01_scripts_agent_workflow_engine_adapter.py.md`).
- No `# noqa` or comment rewording: the pair itself is the leftover, so removing it is the fix.

## Alternatives considered
- Keep the private method and reword the wrapper docstring: rejected — the wrapper adds an extra call frame whose only purpose was name compatibility.
- Rename callers to the private name and delete the public method: rejected — the docs name the public method, and `--check-doc-symbols` validates docs references against definitions under `scripts/`.
- Add a `fixture`-category manifest entry for this file: rejected — production source, not negative-test data.

## Implementation
### Target file
`scripts/agent/bg_task_monitor.py`

### Procedure
Delete the wrapper method, rename the real method to the public name, and update the one internal call site.

### Method
- Delete L147-152: `def notify_bg_failure_threshold(self, task_name: str, count: int) -> None:` (L147), its docstring L148-151 including the flagged sentence "Backward-compatible alias for _notify_threshold_breach." (L150), and its forwarding body `self._notify_threshold_breach(task_name, count)` (L152).
- Rename the definition at L154: `def _notify_threshold_breach(self, task_name: str, count: int) -> None:` becomes `def notify_bg_failure_threshold(self, task_name: str, count: int) -> None:`. Its single-line docstring (L155) already states the guarantee and stays as the method's documentation.
- Update the call site at L138 (inside the threshold branch of the failure counter) to `self.notify_bg_failure_threshold(task_name, count)`.

### Details
- Everything after the rename is unchanged: the `RuntimeError` message construction (L156 onward), the `_on_error` callback path with its catch-all, and the `logger.critical` fallback.
- The module docstring's history sentence at L7 ("Extracted from orchestrator.py (`_discard_and_log`, `_notify_bg_failure_threshold`)") stays: it names the pre-extraction name in `orchestrator.py` and matches no COMPAT pattern.
- `docs/23_agent/agent_13_reference-api-generated.md:38` lists only the class row for this module, so no reference-table regeneration is required.

## Compatibility considerations
- Public surface preserved: `BgTaskMonitor.notify_bg_failure_threshold(task_name, count)` keeps its exact signature and behavior, which is what `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` L90-91 documents.
- The private name `_notify_threshold_breach` disappears; nothing outside this file referenced it.
- After this edit the file produces no COMPAT finding in the strict run.

## Security considerations
- Notification path unchanged, including the catch-all that keeps a failing `on_error` callback from crashing the turn (`logger.critical` fallback).

## Rollback considerations
- Revert the commit restores the wrapper and the private name with no state to unwind. Rolling this back while procedure 01 stays landed re-opens the `bg_task_monitor.py:150` finding, so a rollback here must be followed by the census gate re-run.

## Validation plan
- Grep gate: `grep -rn "_notify_threshold_breach" scripts/ tests/ docs/` returns nothing after the change.
- Targeted tests: `uv run pytest tests/agent/test_orchestrator_bg_failure_threshold.py -q` (threshold-notification characterization suite: `on_error` fires exactly once at the threshold, exception path falls back to `logger.critical`, pause state on repeated failures) and `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py -q`, then `uv run pytest tests/agent/ -q`.
- Checker gate: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` reports no finding for this file and the `--check-doc-symbols` stage still resolves the `BgTaskMonitor.notify_bg_failure_threshold()` references in `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`; the full run exits 0 only after procedures 03-09 and `wfaudit008` have all landed.
- `uv run ruff check scripts/agent/bg_task_monitor.py`, `uv run ty check scripts/agent/bg_task_monitor.py`, and `uv run python tools/check_module_size.py` per `rules/toolchain.md`.

## Completion criteria
- One method named `notify_bg_failure_threshold` with the guarantee docstring, one internal caller at the threshold branch, no `_notify_threshold_breach` left in the repository, and no finding for this file in the strict checker run.

## Out of Scope
- `tests/agent/test_orchestrator.py` comment wording that still narrates the pre-extraction name `_notify_bg_failure_threshold`.
- `scripts/agent/bg_task_monitor.py` L7 module-docstring history.
- The checker semantics flip and the other census files (procedures 01-03, 05-09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | delete L147-152, rename L154, update L138 |
| 2 | Add or update tests per Validation plan | Pending | — | — | no new test: existing characterization suite plus the grep gate |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | repo-clean gate depends on procedures 03-09 and `wfaudit008` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | no doc edit in scope; docs already name the public method |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-190836
- **Related target files**: `scripts/agent/bg_task_monitor.py`; consumers `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` (L90-91), `tests/agent/test_orchestrator_bg_failure_threshold.py`, `tests/agent/test_orchestrator.py`, `tests/integration/test_orchestrator_integration.py`
