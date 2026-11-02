## Goal
- Make `tools/run_validation_gates.py` and `.pre-commit-config.yaml` agree on which checkers exist, so that a change that passes the gate runner cannot be rejected at commit time by a tool-backed hook the runner never ran.

## Priority
High

## Scope
- **In-Scope**:
  - Extend the `drift` subcommand to read `.pre-commit-config.yaml` and report each tool-backed hook that has no gate mapping and no reviewed allowlist entry.
  - Add gate mappings and `routing.md` "When to run which tool" rows for the seven checkers that only the hooks run today: `check_adr_invariant_matrix`, `check_adr_reference`, `check_adr_structure`, `check_known_deviation_sync`, `check_plan_target_overlaps`, `check_conftest_integrity`, and `check_workitem_traceability`. Gate triggers mirror each hook's own `files` or `types_or` filter.
  - Add a reviewed allowlist (hook id plus reason) for hooks that are intentionally commit-only.
  - Add a pre-commit hook that runs the drift check, so a new hook without a mapping fails the commit that adds it.
  - State the parity rule in one sentence in `rules/toolchain.md` and update the tool's entry in `tools/TOOL_DESCRIPTIONS.md`.
  - Measure and report the fast-mode run time the new gates add.
- **Out-of-Scope**:
  - Merging the gate runner and the hooks into one mechanism.
  - Changing CI workflows.
  - Changing what any existing checker verifies.
- **Dependencies**: N/A: none. Re-verified in Step 2 (2026-11-02): no open Issue or Plan lists these files in an `Implementation Target Files` table. Sequencing note: `tools/TOOL_DESCRIPTIONS.md` and `routing.md` are also edited by the sibling Plans filed from `flowimp001`, `flowimp003`, `flowimp008`, `flowimp010`, and `flowimp011`; each Plan adds its own rows, so the edits do not contradict each other and whichever lands later rebases.

## Background
- `Operationally observed` (2026-10-30, from the Issue): `uv run python tools/run_validation_gates.py` reported every gate `Pass`, then the commit was rejected by the `adr-invariant-matrix` hook because a test cited by `docs/10_adr/adr_01_index.md` had been removed. The failure surfaced only at commit time.
- `Explicit in code` (checked in Step 3): `drift_report()` in `tools/run_validation_gates.py` compares only the checkers named in the `routing.md` table with the mapping (`ROUTING_GATES`). `_run_drift()` reads `routing.md` only. It never reads `.pre-commit-config.yaml`.
- `Explicit in code` (checked in Step 3): `.pre-commit-config.yaml` defines the hooks `adr-invariant-matrix`, `adr-reference-scoped`, `adr-structure`, `known-deviation-sync`, `plan-target-overlaps`, `conftest-integrity`, and `workitem-traceability`, all invoked as `python -m tools.<name>`. None of those `tools/<name>.py` names appears in `tools/run_validation_gates.py`. In `routing.md`, only `check_adr_reference` appears, once, inside the note of the `check_adr_authority` row, not as a row of its own.
- `Explicit in code` (checked in Step 3): `drift_report()` treats a mapping entry that is not a `routing.md` checker as an error. Every new gate mapping therefore needs a matching `routing.md` row in the same change.
- `Explicit in code`: `skills/code-implementation/workflow.md` Step 3e and `skills/git-commit-and-sync/workflow.md` Phase 4 treat `run_validation_gates.py` as the single entry point, and `AGENTS.md` Global Rule 9 points to `routing.md`; both miss the seven checkers.
- `Explicit in code` (checked in plan-to-implementation-procedure Step 3a, 2026-11-02): applying the planned id rule to the live config gives eight unmapped tool-backed hooks, not seven. The eighth is `check-compat-shims`: its hook entry carries `--check-removed-names --check-doc-symbols`, so its id is `check_compat_shims:--check-removed-names`, while the existing gate `check_compat_shims` (patternless, manual) has id `check_compat_shims`. `check-compat-shims` is resolved with a reviewed allowlist entry (see Design). Likewise the hook `workitem-traceability` passes `--active-only`, so its id is `check_workitem_traceability:--active-only`; the new gate command and its `routing.md` Run cell must carry `--active-only` for the ids to match.
- `Explicit in code` (checked in Step 3a): hook entries use the module form `python -m tools.<name>`, which `_TOOL_PY_RE` (`tools/<name>.py`) does not match; the derivation must first rewrite a `tools.<name>` token to `tools/<name>.py`. The new drift hook itself (`python -m tools.run_validation_gates drift`) is a tool-backed hook whose id would be `run_validation_gates:drift`; it must be excluded by the same `_SELF_CHECKER_ID` rule the routing comparison uses, or the drift check would fail on itself.
- Measured in Step 2 (2026-11-02, one run each): six of the seven checkers finish in about 1 second or less. `check_workitem_traceability` took about 6.6 seconds when run without the hook's `--active-only` flag and exited 1 on archived items, so its fast-mode cost with `--active-only` is not yet known.

## Problem
Three lists describe the checkers: the pre-commit hooks, the `routing.md` table, and the gate mapping. Only the pair `routing.md` and gate mapping is compared. A checker that exists only as a hook runs for the first time at commit, where a failure costs the most.

## Reason for Change
Test removal, ADR edits, and Plan target changes are routine in this workflow. Each miss repeats a validation round at commit time, after the full validation sequence and a multi-minute test run.

## Implementation Intent
Add the missing parity check instead of relying on memory. The drift check compares the tool-backed hooks with the gate mapping, with a small reviewed allowlist for hooks that are intentionally commit-only. The seven unmapped checkers get mapping entries whose triggers mirror the hooks' own filters, plus the matching `routing.md` rows so the manual path (`AGENTS.md` Global Rule 9) stays consistent. The drift check also runs in pre-commit, so a new hook without a mapping fails the commit that adds it.

## Requirements
- `REQ-001`: `drift` MUST read `.pre-commit-config.yaml`, derive the checker id of every tool-backed hook, and report each hook that has neither a gate mapping nor an allowlist entry. A malformed or unreadable config MUST produce a non-zero exit with a message.
- `REQ-002`: The seven checkers MUST each get a gate mapping whose `patterns` mirror the hook's `files` or `types_or` filter, and a `routing.md` row whose `Run` cell yields the same checker id. A checker that must stay commit-only MUST be recorded in the allowlist with a reason instead.
- `REQ-003`: The drift check MUST run as a pre-commit hook so that a new tool-backed hook without a mapping fails the commit that adds it.
- `REQ-004`: The run time the new gates add in fast mode MUST be measured and reported; a checker that is slow in fast mode MUST be mapped to full mode only, with the reason recorded.
- `REQ-005`: `rules/toolchain.md` MUST state that gates and hooks must stay in parity, and `tools/TOOL_DESCRIPTIONS.md` MUST describe the extended `drift` behavior.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/run_validation_gates.py` | Hook parity in `drift`, allowlist, seven new mapping entries | `drift_report()` compares only `routing.md`; add a hook-vs-mapping comparison, an allowlist constant, and gates for the seven checkers | REQ-001, REQ-002, REQ-004 / AC-1, AC-2, AC-3 | `drift_report`, `_run_drift`, `ROUTING_GATES`, `Gate` dataclass (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tests/tools/test_run_validation_gates.py` | Tests for the new drift behavior and trigger selection | Existing drift tests cover only `routing.md`; add unmapped-hook, allowlisted-hook, malformed-config, and trigger-selection cases | REQ-001, REQ-002 / AC-1, AC-2, AC-3 | `test_drift_all_routing_checkers_mapped`, `test_drift_reports_unmapped_checker`, `test_selection_*` (checked in Step 3) | itself | Verified |
| `.pre-commit-config.yaml` | New hook that runs the drift check | No hook compares hooks with gates; add one with a `files` filter covering the hook config, `routing.md`, and the gate runner | REQ-003 / AC-4 | existing hook shape (`entry: python -m tools.<name>`, `language: system`, `pass_filenames: false`) (checked in Step 3) | `tools/check_tool_descriptions_sync.py` run, hook run | Verified |
| `routing.md` | Rows for the seven checkers | The "When to run which tool" table has no row for six of them and only a passing mention of the seventh | REQ-002 / AC-1 | table in "When to run which tool"; `check_adr_reference` appears only in the `check_adr_authority` note (checked in Step 3) | `drift` run, `check_skills_references.py` | Verified |
| `rules/toolchain.md` | One sentence naming the parity rule | The validation-sequence text does not say that gates and hooks must stay in parity | REQ-005 / AC-5 | "Standard validation sequence" paragraph on `run_validation_gates.py` (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Update the `run_validation_gates.py` entries | The two existing entries describe `drift` as a `routing.md` comparison only | REQ-005 / AC-5 | rows for `run_validation_gates.py` in both tables (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Confirm the checker's invocation and exit behavior for the gate command | REQ-002 |
| `tools/check_plan_target_overlaps.py` | Confirm it is report-only (exit 0) and what it scans | REQ-002 |
| `tools/check_workitem_traceability.py` | Confirm the `--active-only` flag the hook passes and measure its fast-mode cost | REQ-002, REQ-004 |
| `tools/check_tool_descriptions_sync.py` | Registered-tool and CI/hook reference check that runs after the edits | REQ-005 |
| `AGENTS.md` | Global Rule 9 wording that relies on `routing.md` | REQ-002 |
| `skills/code-implementation/workflow.md` | Step 3e treats the gate runner as the single entry point | REQ-005 |
| `skills/git-commit-and-sync/workflow.md` | Phase 4 treats the gate runner as the single entry point | REQ-005 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-002`): Before the change, `uv run python tools/run_validation_gates.py drift` extended with the hook comparison names the seven checkers plus `check-compat-shims` (resolved by allowlist); after the change it reports none unmapped, and the drift check passes on the live repository.
- AC-2 (`REQ-001`): A fixture pre-commit config with an added tool-backed hook and no mapping makes `drift` exit non-zero; an allowlisted hook does not; a malformed config exits non-zero with a message.
- AC-3 (`REQ-002`): On a fixture where changed files include a removed test cited by an ADR, `select_gates` selects the ADR invariant gate in fast mode and the gate reports `Fail` when the checker fails.
- AC-4 (`REQ-003`): The pre-commit configuration contains a hook that runs the drift check, and `uv run pre-commit run <hook id> --all-files` passes.
- AC-5 (`REQ-004`, `REQ-005`): The measured fast-mode time added by the new gates is recorded in the implementing change; `rules/toolchain.md` states the parity rule; `check_tool_descriptions_sync.py`, `check_skills_references.py`, and `check_skills_heading_cycles.py` pass.

## Tests
- `REQ-001`: unit tests for unmapped hook, allowlisted hook, and malformed or missing config.
- `REQ-002`: unit tests for trigger selection of each newly mapped gate against its hook filter (`files` regex and `types_or`), and a test that every routing row of the seven yields a mapped checker id.
- `REQ-003`: a live `pre-commit run` of the new hook.
- `REQ-004`: a timed live run of the default mode on a representative diff.

## Documentation Impact
- Yes. `routing.md` (Tools table rows), `rules/toolchain.md` (parity sentence), and `tools/TOOL_DESCRIPTIONS.md` (drift behavior). Driven by REQ-002 and REQ-005. No `docs/*.md` change: this Plan changes workflow tooling, not system design documentation.

## Assumptions
- A1: The hooks' `files` and `types_or` filters can be transcribed as gate `patterns` without loss. A `types_or: [python, markdown]` filter becomes the two globs for `.py` and `.md` files. Falsifiable by the AC-3 trigger tests.
- A2: PyYAML is available to the tools (`uv run python -c "import yaml"` succeeded in Step 2), so the drift check parses the config with `yaml.safe_load` rather than a regex. Falsifiable by a failing import in the dev environment.
- A3: Hooks that call `uv run python -m tools.<name>` and `python -m tools.<name>` reduce to the same checker id as the `tools/<name>.py` argv form used by gates once the `tools.<name>` token is rewritten to `tools/<name>.py`. Corrected in Step 3a: this holds only when the hook passes no extra flag; a hook flag (`--active-only`, `--check-removed-names`) becomes part of the id, so the mapped command must carry the same flag or the hook is allowlisted.
- A4: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository; `git shortlog` shows one dominant author, Step 3).
- A5: Overlap judgment (Step 8b, `check_plan_target_overlaps.py`): `routing.md` is also a target of `plans/20261102-075753_flowimp004_schema-change-checklist.md`. Judged compatible: this Plan adds rows to the "When to run which tool" table, that Plan adds an entry to the "Conditional load" list, so the two edits touch different sections.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any of the seven checkers is intentionally commit-only | No statement in the hook config or docs; each runs in about 1 second except one | Decide per checker at implementation: map to fast mode unless the measured time is slow, then allowlist with a reason | False |
| UNK-03 | Whether `check-compat-shims` should be allowlisted or its gate command changed to carry the hook flags | Hook flags differ from the manual gate; changing the gate changes an existing mapping and `routing.md` row, which is outside this Plan's intent | Allowlist it with a reason at implementation (no existing mapping is renamed); revisit only if the user asks | False |
| UNK-02 | Fast-mode time of `check_workitem_traceability --active-only` | Measured only without `--active-only` (about 6.6 seconds, exit 1) | Time it with the hook's exact arguments at implementation; map to full mode only if slow | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/run_validation_gates.py` | Modify | Medium (every gate selection and the drift check; used by `AGENTS.md` Rule 9 and two skills) | 8 | N/A | not applicable (rsynced) |
| `tests/tools/test_run_validation_gates.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `.pre-commit-config.yaml` | Modify | Medium (runs on every commit) | 10 | N/A | not applicable (rsynced) |
| `routing.md` | Modify | Medium (loaded by every task) | 28 | N/A | not applicable (rsynced) |
| `rules/toolchain.md` | Modify | Low | 11 | N/A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | N/A | not applicable (rsynced) |

## Design
- Parity check: `drift_report()` gains a second input, the parsed hook list. A hook is tool-backed when its `entry` names `tools.<name>` or `tools/<name>.py`. Its checker id is computed with the same rule as `Gate.checker_id`. A hook whose checker id is in neither the mapping nor the allowlist is a drift error. `_run_drift()` reads both files and exits non-zero on any error. Alternatives: a regex scan of the YAML (rejected: PyYAML is available, and the regex form hides malformed config); comparing hooks with `routing.md` only (rejected: the drift check already requires mapping and `routing.md` to agree, so mapping covers both).
- Id derivation (corrected in Step 3a): the entry is split on whitespace, each `tools.<name>` token is rewritten to `tools/<name>.py`, and `_checker_id_from_command` computes the id. A hook whose base tool is `run_validation_gates` is skipped (self-exclusion, same rule as `_SELF_CHECKER_ID`). `check-compat-shims` is allowlisted with the reason that its hook runs stricter flags than the manual gate; `workitem-traceability` is mapped with `--active-only` in the gate command.
- Allowlist: a reviewed constant in `tools/run_validation_gates.py`, a tuple of hook id and reason. An entry without a reason is rejected by a test. It is not a silent default.
- Triggers: each new gate's `patterns` mirror the hook filter. The ADR gates (`types_or: [python, markdown]`) select on any `.py` or `.md` change; if measured cost in fast mode is high, they move to full mode only and the reason is recorded (REQ-004).
- Self-check: the new hook runs the drift check through `python -m tools.run_validation_gates drift`, consistent with the other hooks, filtered to `.pre-commit-config.yaml`, `routing.md`, and `tools/run_validation_gates.py`.
- Compatibility: no checker changes behavior; no existing mapping entry is renamed; the default gate run only gains gates.

## Implementation steps
1. **Phase 1: Drift check reads the hooks**
   - [ ] Add hook parsing, checker-id derivation, and the allowlist constant to `tools/run_validation_gates.py` and extend `drift_report()` and `_run_drift()` (`REQ-001`; `tools/run_validation_gates.py`)
   - [ ] Add unmapped-hook, allowlisted-hook, malformed-config, and missing-reason tests (`REQ-001`; `tests/tools/test_run_validation_gates.py`)
2. **Phase 2: Map the seven checkers**
   - [ ] Add the seven gate entries with filter-mirroring patterns and the matching `routing.md` rows; allowlist any commit-only checker with a reason (`REQ-002`; `tools/run_validation_gates.py`, `routing.md`)
   - [ ] Add trigger-selection tests including the removed-ADR-cited-test fixture (`REQ-002`; `tests/tools/test_run_validation_gates.py`)
   - [ ] Time the new gates in fast mode and record the result; move a slow gate to full mode with the reason (`REQ-004`; `tools/run_validation_gates.py`)
3. **Phase 3: Hook and documentation**
   - [ ] Add the drift-check hook (`REQ-003`; `.pre-commit-config.yaml`)
   - [ ] Add the parity sentence and update the tool description (`REQ-005`; `rules/toolchain.md`, `tools/TOOL_DESCRIPTIONS.md`)
4. **Phase 4: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run `uv run python tools/run_validation_gates.py drift`, the default mode on a representative diff, `check_tool_descriptions_sync.py`, `check_skills_references.py`, `check_skills_heading_cycles.py`, `check_workitem_structure.py`, and the tool lint sequence of `routing.md` "Adding a new tool" on the changed tool (`REQ-001` to `REQ-005`; all rows above)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/run_validation_gates.py` | Unit (drift, selection) and live run | `uv run pytest tests/tools/test_run_validation_gates.py -v`; `uv run python tools/run_validation_gates.py drift` | all pass; drift reports none unmapped |
| `tools/run_validation_gates.py` | Lint, type, security on the changed tool | `uv run ruff format tools/run_validation_gates.py`; `uv run ruff check tools/run_validation_gates.py`; `uv run mypy tools/run_validation_gates.py`; `uv run bandit tools/run_validation_gates.py` | clean (pre-existing bandit findings, if any, recorded) |
| `.pre-commit-config.yaml` | Live hook run | `uv run pre-commit run <new hook id> --all-files` | passes |
| `routing.md`, `rules/toolchain.md` | Reference and heading checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | no findings |
| `tools/TOOL_DESCRIPTIONS.md` | Sync check | `uv run python tools/check_tool_descriptions_sync.py` | passes |

## Risks
- **Risk**: Mapping the ADR gates to every `.py` and `.md` change slows fast mode. → **Mitigation**: REQ-004 measures it; a slow gate moves to full mode only with a recorded reason (UNK-02).
- **Risk**: The new drift hook fails on a legitimate commit-only hook that has no reason recorded. → **Mitigation**: the allowlist is reviewed text; the implementation records each exception with a reason, and a test rejects an entry without one.
- **Risk**: Checker-id derivation from hook `entry` strings misses a hook form (for example `uv run python -m tools.x` or arguments after the module). → **Mitigation**: unit tests cover each entry form present in the live config; the drift check reports an unparseable tool-backed entry as an error rather than ignoring it.
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` and `routing.md` are edited by several sibling Plans, so a late rebase conflicts. → **Mitigation**: edits are row-additive; `tools/check_plan_target_overlaps.py` reports the overlap, judged compatible in Assumptions A1 of the sibling Plans.
- **Risk**: Pre-existing `bandit` findings in `scripts/` (High 43, Medium 8, measured in Step 5) and `vulture` findings are unrelated and could be mistaken for regressions. → **Mitigation**: baseline recorded here; only new findings on the changed tool count.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drift check reads the hooks: `tools/run_validation_gates.py`, `tests/tools/test_run_validation_gates.py` | Completed | — | 20261102-093315 |  |
| 2 | Map the seven checkers: `tools/run_validation_gates.py`, `routing.md`, `tests/tools/test_run_validation_gates.py` | Completed | — | 20261102-093315 |  |
| 3 | Hook and documentation: `.pre-commit-config.yaml`, `rules/toolchain.md`, `tools/TOOL_DESCRIPTIONS.md` | Completed | — | 20261102-093315 |  |
| 4 | Verification of all changed files | Completed | 20261102-153320 | 20261102-153320 | Audit 20261102: drift OK (42 checkers mapped, hooks in parity); targeted gates/conftest/isolation/deploy tests 87 passed; full suite 11262 passed, 8 skipped, 0 failed after the close_procedures_batch fixture identity fix. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261102-084648_01_tools_run_validation_gates.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261102-084648_02_tests_tools_test_run_validation_gates.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261102-084648_03_.pre-commit-config.yaml.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261102-084648_04_routing.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261102-084648_05_rules_toolchain.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261102-084648_06_tools_TOOL_DESCRIPTIONS.md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191302_flowimp005_gates-hook-parity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-075445
- **Related target files**: `tools/run_validation_gates.py`, `tests/tools/test_run_validation_gates.py`, `.pre-commit-config.yaml`, `routing.md`, `rules/toolchain.md`, `tools/TOOL_DESCRIPTIONS.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (extend drift); Background (`drift_report` reads `routing.md` only) | `tools/run_validation_gates.py` | Phase 1 | AC-1, AC-2 | drift unit tests | Confirmed by repository evidence |
| REQ-001 | Testing Expectations (drift behavior tests) | `tests/tools/test_run_validation_gates.py` | Phase 1 | AC-2 | unmapped, allowlisted, malformed-config tests | Confirmed by repository evidence |
| REQ-002 | Required Changes (seven mapping entries); Background (seven checkers) | `tools/run_validation_gates.py` | Phase 2 | AC-1, AC-3 | trigger-selection tests | Confirmed by repository evidence |
| REQ-002 | Required Changes (`routing.md` rows) | `routing.md` | Phase 2 | AC-1 | `drift` run | Confirmed by repository evidence |
| REQ-002 | Acceptance Criteria (removed ADR-cited test selects the ADR gate) | `tests/tools/test_run_validation_gates.py` | Phase 2 | AC-3 | selection fixture test | Explicit in issue |
| REQ-003 | Required Changes (drift as pre-commit hook) | `.pre-commit-config.yaml` | Phase 3 | AC-4 | live hook run | Explicit in issue |
| REQ-004 | Required Changes (measure fast-mode time); Constraints (slow checker maps to full mode) | `tools/run_validation_gates.py` | Phase 2 | AC-5 | timed live run | Explicit in issue |
| REQ-005 | Documentation Impact (`rules/toolchain.md` sentence) | `rules/toolchain.md` | Phase 3 | AC-5 | `check_skills_references.py` | Explicit in issue |
| REQ-005 | Target Files (`tools/TOOL_DESCRIPTIONS.md` if behavior changes); Required Changes | `tools/TOOL_DESCRIPTIONS.md` | Phase 3 | AC-5 | `check_tool_descriptions_sync.py` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-084648 -->