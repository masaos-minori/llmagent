## Goal

Delete the four dead public lifecycle aliases and their section header comment from the adapter (`REQ-001`, removing the Backward-compatible grep target), collapse the `deactivate_workflow` wrapper pair into one real public method so the live orchestrator caller is untouched (`REQ-002`), and pin the resulting public surface with hasattr regression tests so the aliases cannot silently return (`REQ-005`).

## Scope
**Release unit**: wfaudit008-full

- Covers Plan `plans/20261108-084009_wfaudit008_dead-alias-test-patches.md` row 1 only: `scripts/agent/workflow_engine_adapter.py`.
- Also hosts the `REQ-005` pinning test file `tests/agent/workflow/test_adapter_alias_surface.py` (new) described in the Validation plan.
- Plan Phases 1-2 (test-patch retargeting in `tests/agent/test_orchestrator.py`) belong to sibling document `implementations/20261108-162804_02_tests_agent_test_orchestrator.py.md`.

## Assumptions
- Line numbers refer to HEAD `ad48bfa28`; no already-generated procedure of this batch edits this file. Draft siblings wfaudit013/wfaudit014 target disjoint adapter regions (L172/L407, L49-62/L255/L262-275) — if either executes first, re-verify line citations before this procedure.
- `deactivate_workflow` at `scripts/agent/orchestrator.py` L200 is the only production caller of the public aliases (caller census in plan Notes 2026-11-08: no CLI `task-init` path, no getattr-based callers).
- The `execute_turn` flow reaches the engine through the private methods; the wrappers are exercised only by the test patches listed in the sibling document.

## Design decisions
- Collapse direction: keep the public name `deactivate_workflow`, delete the private twin `_deactivate_workflow` (def L336-341), and carry the twin's body under the public name — the orchestrator call site and its (self, ctx) signature stay byte-identical (`REQ-002`, plan Design constraint "orchestrator untouched").
- Delete the L106 section header comment with the block; any replacement heading must avoid the word "Backward-compatible" (REQ-001 acceptance grep).

## Alternatives considered
- Keep `deactivate_workflow` as a wrapper over the private twin: rejected — the plan target row mandates "keep public name with the private body, delete twin"; the wrapper pair is itself the audit finding.
- Make `deactivate_workflow` private and rename the orchestrator call site: rejected — it modifies a live production caller for no gain and contradicts `REQ-002`'s "remains callable with its current signature".

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
Delete the alias block wholesale, rename the private deactivate twin to the public name in place, and update the module docstring's extracted-names list.

### Method
1. Delete L106-146: the "Backward-compatible public API" header comment (L106) plus the four wrappers — `init_workflow_task` (def L108, delegates at L124), `activate_workflow` (def L125, delegates at L130), `deactivate_workflow` (def L132, delegates at L137), `handle_workflow_halt` (def L139, signature (ctx, exc) but passes only exc, delegates at L146). Their docstrings carry "Backward-compatible alias for ..." lines at L121/L128/L135/L144.
2. Rename `_deactivate_workflow` (def L336, body L338-341 resetting the four ctx workflow fields) to `deactivate_workflow`, keeping the (self, ctx) signature and body unchanged. Order the edit so the wrapper deletion (step 1) precedes the rename (step 2): no duplicate `deactivate_workflow` definition ever exists mid-edit.
3. Update the module docstring: replace the `_deactivate_workflow` entry in the extracted-names list (L7-8) with the public name; the other private-name entries stay accurate.

### Details
- Untouched regions: private defs at L282 (`init_workflow_task`), L326 (`activate_workflow`), L343 (`handle_workflow_halt`), and `execute_turn` / `_record_exit_status` code after the block.
- The orchestrator call site `self._workflow_adapter.deactivate_workflow(self._ctx)` (`scripts/agent/orchestrator.py` L200) is not edited (`REQ-002`).
- The public halt wrapper accepted ctx and discarded it when delegating; deleting it removes the only public entry point that silently ignored an argument.

## Compatibility considerations
- `REQ-005`: deleted public names raise `AttributeError` for any hypothetical external user — no shims, no deprecation wrappers; obsolete-symbol tracking follows the compat policy of `issues/done/20261020-123232_compat007_track-compatibility-exceptions-and-obsolete-symbols-in-a-manifest-with-owner-and-expiry.md` and `wfaudit012`'s manifest context.
- Coordination: procedure `implementations/20261108-155554_01_scripts_agent_workflow_engine_adapter.py.md` (wfaudit006) hosts `tests/agent/workflow/test_adapter_store_ownership.py` (new) calling the public `init_workflow_task`; after this procedure lands, that test must call the private method instead. The wfaudit006 document's Details claim "public alias stays unchanged" is superseded by this plan (recorded in plan Notes 2026-11-08).

## Security considerations
- No new attack surface: the change deletes delegation wrappers; no I/O, trust boundary, or persistence change.

## Rollback considerations
- Revert the commit: the aliases return and the new pinning tests fail again on HEAD behavior. Single-commit revert, no persisted state to unwind.

## Validation plan
- New pinning file `tests/agent/workflow/test_adapter_alias_surface.py` (new), reusing the fixture pattern of `tests/agent/workflow/test_workflow_engine.py` (sqlite-vec availability guard, adapter built over a tmp_path `StateStore`):
  - `test_adapter_public_surface` (new) — on the class and an instance: `deactivate_workflow` present; `init_workflow_task`, `activate_workflow`, `handle_workflow_halt` absent (`REQ-005` AttributeError contract).
  - `test_deactivate_workflow_resets_workflow_state` (new) — pass a MagicMock ctx whose workflow fields start non-default, call the public method, assert active False and the other three fields None (`REQ-002` behavior pin).
  - `test_deactivate_workflow_takes_ctx` (new) — signature check via the inspect module on the method: one parameter besides self (`REQ-002` contract with the L200 call site).
  - `test_private_deactivate_twin_removed` (new) — `_deactivate_workflow` absent from the class after the collapse.
- Grep gates (post-change): `grep -i "Backward-compatible" scripts/agent/workflow_engine_adapter.py` returns nothing (`REQ-001`); `grep -rn "init_workflow_task(\|activate_workflow(\|handle_workflow_halt(" scripts/ tests/` shows only private-underscore usages (`REQ-005` acceptance grep from the plan).
- `uv run pytest tests/agent/ -q` after the change with the sibling procedure's retargeting applied, then full `uv run pytest tests/ -q`; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- `grep -i "Backward-compatible"` over the adapter returns nothing and the adapter defines exactly one method per lifecycle action (private trio plus the public `deactivate_workflow`, no `_deactivate_workflow`).
- Orchestrator flow tests are green without editing `scripts/agent/orchestrator.py` (`REQ-002`).
- All four pinning tests pass; the public-surface test fails on HEAD (it pins the post-change contract).

## Out of Scope
- The `tests/agent/test_orchestrator.py` retargeting (row 2 procedure, same release unit, sibling document).
- `scripts/agent/orchestrator.py` (verified no-change Reference row).
- Docs: plan Documentation Impact verified no-change (only private-name mentions exist, e.g. `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-022546 | 20261109-022546 | implementation complete; validation gates green; suite 4216 passed; REQ-005 grep clean |
| 2 | Add `tests/agent/workflow/test_adapter_alias_surface.py` (new) per Validation plan | Completed | 20261109-022546 | 20261109-022546 | implementation complete; validation gates green; suite 4216 passed; REQ-005 grep clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-022546 | 20261109-022546 | implementation complete; validation gates green; suite 4216 passed; REQ-005 grep clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-022546 | 20261109-022546 | implementation complete; validation gates green; suite 4216 passed; REQ-005 grep clean |

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
- **Requirement ID**: `REQ-001` (alias block gone), `REQ-002` (live caller unaffected), `REQ-005` (names removed loudly)
- **Source issue**: `issues/20261107-203221_wfaudit008_dead-alias-test-patches.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084009_wfaudit008_dead-alias-test-patches.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-162804
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-162804 -->
