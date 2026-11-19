## Goal

Move `"approval"` from the direct-section loop to the validated-section loop in `apply_config_dict` so approval candidates are built and validated before commit (REQ-001: invalid approval reloads abort; REQ-006: existing non-defect semantics unchanged).

## Scope
**Release unit**: hot-reload-validation

- In scope: the two section-path tuples in `apply_config_dict` (`config_reload.py:111` validated loop, `:126` direct loop) and the method docstring's wording if it names the section split.

## Assumptions
- `prepare_validated_section` returns `({}, None)` when nothing changed (`config_section_reload.py:52-53`), so an approval-only-unchanged reload stays a no-op.
- `dataclasses.replace` on the live `ApprovalConfig` runs `ApprovalConfig.__post_init__` tier/risk checks on the candidate (`config_dataclasses.py:316-319`), and `prepare_validated_section` wraps any `ValueError` as `ConfigReloadValidationError` (`config_section_reload.py:54-67`).
- `hot_reloadable` stays report-only: neither prepare helper filters by it, and `classify_startup_only_fields` (`config_outcome_classification.py:48-65`) keeps reporting `gitops_push_blocked` as `startup_only` while it still applies — the Plan freezes this as REQ-006 (UNK-01 is out of scope).
- Every consumer reads `ctx.cfg.approval` through `ctx` per call (Plan Assumptions, consumer inspection), so replacing the section object on commit is safe.

## Design decisions
- Plan DT-01 Option A: reuse the existing validated path rather than building a parallel per-field validation path (Option B) or enforcing `hot_reloadable=False` (Option C, rejected in the Plan).

## Alternatives considered
- Keep `approval` direct and validate inside `prepare_direct_section`: rejected in the Plan — it would put two argument shapes into one registry contract and duplicate the candidate machinery.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`

### Procedure
1. `for section_path in ("llm", "rag", "tool"):` (`:111`) → `("llm", "rag", "tool", "approval")`.
2. `for section_path in ("approval", "memory", "mcp"):` (`:126`) → `("memory", "mcp")`.
3. Update the `apply_config_dict` docstring only where it names the section split; the two-phase description (`:91-104`) already describes the candidate-phase abort and stays.

### Method
- No other code changes: `extra_changed_fields` stays keyed to `section_path == "tool"` (`:113-119`); the commit phase's `apply_validated_section(ctx, "approval", candidate)` (`:145-147`) does the `setattr`; `outcome.applied` still receives the section name from the loop that applied it (`:146-150`).
- `mcp_servers` classification (`:131-134`) and `pending_conv_updates` (`:136-141`) stay untouched.

### Details
- `apply_config_dict` is C(16) (radon baseline); this edit adds no branch — just one tuple entry move (Plan Risks).
- `_sync_services` keeps re-applying `RuntimeToolRegistry.apply_policy` with `ctx.cfg.approval.tool_safety_tiers` (`config_service_sync.py:78`) after commit; the replaced candidate is read through `ctx` there.

## Compatibility considerations
- After this move, `ctx.cfg.approval` must be a real `ApprovalConfig` in tests that send approval fields (candidate construction calls `dataclasses.replace`); the fixture conversions are the seq 06 and seq 07 documents.
- Operators can no longer apply previously-accepted invalid approval values via `/reload`; `_cmd_reload` already surfaces the `ValueError` subclass as "Reload failed: ..." (`cmd_config.py:105-107`).

## Security considerations
- This is the move that makes the seq 01 wiring live: tier/risk/root values are validated before any live mutation, and a rejection leaves the previous approval section in force.

## Rollback considerations
- N/A: revert the commit (single release-unit commit; behavior reverts to the unvalidated direct path).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Two-phase abort | `uv run pytest tests/agent/services/ -q` | Rejected reload leaves `ctx.cfg.approval` / `ctx.cfg.tool` unchanged |
| Approval still applies | `uv run pytest tests/agent/services/test_config_reload.py -q` | `gitops_push_blocked` apply-and-report test (`:715-786`) passes through the validated path |
| Static gates | `rules/toolchain.md` sequence; radon re-run | Clean; complexity unchanged |

## Completion criteria
- `"approval"` appears only in the validated loop; an invalid approval candidate aborts in the candidate phase with the live config untouched; the `gitops_push_blocked` semantics (apply + `startup_only` report) are observably unchanged.

## Out of Scope
- `ConfigFieldRegistry` entry shape, validator signatures, `classify_startup_only_fields` behavior (REQ-006); docstring updates in `config_section_reload.py` (seq 04 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Move `"approval"` between the section loops and adjust the docstring | Completed | 20261119-105020 | 20261119-105156 | Land together with seq 02/01 wiring Step 2 stale check clean; Step 3a: loop tuples and apply_config_dict docstring verified (docstring does not name the section split); consumers read ctx.cfg.approval per call; file clean at baseline Changed: scripts/agent/services/config_reload.py (approval moved to the validated loop; apply_config_dict docstring does not name the section split, so unchanged) |
| 2 | Run the services suite after the seq 06/07 fixture conversions | Completed | 20261119-105156 | 20261119-112102 | services suite 325 passed after seq 06 fixture conversion; test_agent_cmd_config awaits seq 07 services + commands suites 769 passed after seq 06/07 fixture conversions |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-112102 | 20261119-112102 | End of unit: full suite 12907 passed, 7 skipped, 1 unrelated failure (test_check_repo_path_equivalence: Hypothesis property test on PurePosixPath, passes alone 9/9 and in the git MCP module under xdist 418/418); diff-cover 100%; ADR-cited tests 52 passed; validation gates pass; ruff/mypy/lint-imports/bandit clean; radon apply_config_dict still C(16) |

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
- **Requirement ID**: REQ-001 (validated approval reload), REQ-006 (existing semantics and shapes unchanged)
- **Source issue**: issues/20261117-123004_adrchk004_hot-reload-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-094759_adrchk004_hot-reload-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-101805
- **Related target files**: `scripts/agent/services/config_reload.py`