## Goal

Wire the four security-relevant registry entries to their validators so the reload path can run them (REQ-003: registry wiring; REQ-001: same rules as startup for tier/risk/root values).

## Scope
**Release unit**: hot-reload-validation

- In scope: the four entry rows and the `config_validators` import block in this file; `validate_allowed_root` (new) and `validate_allowed_tools` (new) are created by the seq 02 document — the (new) marks here cover only the import statements this document adds.

## Assumptions
- Entries are constructed positionally (`name`, `section_path`, `hot_reloadable`, `validator_fn`) — `ConfigFieldRegistry("allowed_tools", "tool", True)` at `config_field_registry.py:79` becomes the four-argument form; no entry-shape change (REQ-006).
- Wiring alone does not run the approval-side validators: the `approval` section reloads through the direct path until the seq 03 document moves it (`config_section_reload.py:115-119` "No validators run and no candidate is built"). Execution order within the release unit: seq 06 tests → seq 02 → this document → seq 03 → seq 04 → seq 07.
- `validate_tool_max_tool_turns` etc. already occupy the import block (`:12-25`, alphabetically sorted); the new names join it in isort order.

## Design decisions
- `gitops_push_blocked` (`:90`) and all other approval entries stay validator-less with unchanged `hot_reloadable` values (REQ-006: current apply-and-report semantics frozen).

## Alternatives considered
- N/A: the frozen row prescribes attaching the four callables; no alternative wiring mechanism (e.g. string lookups) is in scope.

## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`

### Procedure
1. Extend the `from agent.services.config_validators import (...)` block with `validate_allowed_root` (new), `validate_allowed_tools` (new), `validate_approval_risk_rules`, and `validate_tool_safety_tiers` (existing symbols), keeping the list alphabetically sorted.
2. `ConfigFieldRegistry("allowed_tools", "tool", True)` (`:79`) → append `, validate_allowed_tools`.
3. `ConfigFieldRegistry("approval_risk_rules", "approval", True)` (`:81`) → append `, validate_approval_risk_rules`.
4. `ConfigFieldRegistry("tool_safety_tiers", "approval", True)` (`:87`) → append `, validate_tool_safety_tiers`.
5. `ConfigFieldRegistry("allowed_root", "approval", True)` (`:88`) → append `, validate_allowed_root`.
6. Touch no other entry.

### Method
- `prepare_validated_section` invokes `field_entry.validator_fn(replaced)` for each changed entry (`config_section_reload.py:58-67`); all four callables take the section dataclass candidate, so no adapter or partial is needed.

### Details
- The registry-content tests at `tests/agent/services/test_config_reload.py:912-1031` assert section membership, callable-or-None validators, and name uniqueness — all stay green without edits (wiring only tightens `validator_fn` from `None` to a callable).
- `tools/generate_reference_table.py` reads this registry to generate the manifest; regenerate in the seq 05 document after this change.

## Compatibility considerations
- After this change `/reload` starts validating `allowed_tools` on the already-validated `tool` section immediately; approval-side effect requires seq 03. Both land in the same release unit.
- `config_dataclasses.py` imports the validators directly and is unaffected.

## Security considerations
- This wiring is what makes the reload gate effective for the four fields; leaving any entry unwired re-opens the defect (Plan Problem section).

## Rollback considerations
- N/A: revert the commit (single release-unit commit).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Registry assertions | `uv run pytest tests/agent/services/test_config_reload.py -q` | `:912-1031` tests pass unchanged |
| Manifest consistency (after seq 05) | `uv run python tools/generate_reference_table.py --check` | No drift |
| Static gates | `rules/toolchain.md` sequence | ruff / mypy clean |

## Completion criteria
- The four entries carry their validators (non-`None` `validator_fn` pointing at the four callables), every other entry is byte-unchanged, and the registry assertions and static gates pass.

## Out of Scope
- Adding validators for the remaining approval fields (Plan Out-of-Scope); changing `hot_reloadable` values or entry shape (REQ-006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the import block and wire the four entries | Pending | — | — | Requires the seq 02 functions to exist |
| 2 | Run the registry assertions and related suite | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (validator wiring), REQ-001 (startup-equal reload validation)
- **Source issue**: issues/20261117-123004_adrchk004_hot-reload-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-094759_adrchk004_hot-reload-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-101805
- **Related target files**: `scripts/agent/services/config_field_registry.py`
