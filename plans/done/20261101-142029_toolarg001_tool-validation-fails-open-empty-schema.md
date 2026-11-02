## Goal
- Make `validate_tool_arguments()` reject a tool call whose tool has a missing or empty `input_schema` (fail closed) instead of returning success, while keeping every non-empty schema, including a well-formed zero-argument schema, validated exactly as today.

## Priority
Low

## Scope
- **In-Scope**:
  - Replace the `if not input_schema` success branch in `validate_tool_arguments()` (`scripts/agent/tool_arg_validator.py`) with a failed `ValidationResult` whose reason names the tool and the missing schema.
  - Remove the "lenient mode" sentence from that function's docstring and document the fail-closed rule.
  - Flip the three existing tests that assert the lenient behavior and add tests for: `None` schema rejected, `{}` rejected, `allow_extra_fields=True` does not bypass the rejection, a well-formed zero-argument schema accepted (`tests/agent/test_tool_arg_validator.py`).
  - Add one preparation-level test that a registry tool with an empty schema is rejected by `prepare_tool_calls()` with kind `schema` (`tests/agent/test_tool_preparation.py`).
  - Give the five mock-registry fixtures that currently set `input_schema = {}` (to make validation pass) a well-formed zero-argument schema so their non-validation tests keep passing.
- **Out-of-Scope**:
  - `validate_tool_schema_v2()` in `scripts/shared/resource_scope.py` and the discovery gate in `scripts/agent/services/mcp_tool_discovery_fetch.py` (the Issue's Out of Scope).
  - The jsonschema, required-field, extra-field and custom-validator logic that runs for a present schema (Issue Constraint).
  - `build_runtime_tool()` in `scripts/shared/runtime_tool.py`: its default schema `{}` is left unchanged (see Design and UNK-01).
  - The separate "lenient fallback" in `_check_extra_fields()` for a non-empty schema without `properties`; the Issue does not name it.
- **Dependencies**: Issue Dependencies are `N/A: none`. Ordering against other Plans that edit `tests/agent/test_tool_runner.py` is recorded in Assumptions (Step 8b): none is a conflict; whichever lands later rebases its edits.

## Background
Found during an adversarial review of the REPL tool-execution and approval-gating subsystem, against the project rule "fail-fast for unknown tool names, tiers, or metadata, never fail-open". `validate_tool_arguments()` is the argument-injection gate that `prepare_tool_calls()` runs for every registered tool before approval and execution. The module docstring says the module exists to prevent argument injection, yet the first branch of the function skips all checks when the schema is falsy.

## Problem
`validate_tool_arguments()` returns `ValidationResult(success=True)` when `input_schema` is missing or `{}`, skipping the required-field, extra-field, jsonschema type and custom-validator checks. Its docstring documents this as "lenient mode". This is a structural fail-open. It is defense-in-depth only: discovery rejects an empty-schema tool before it reaches the registry (see Repository Evidence), so today only a non-discovery construction can reach the branch.

## Reason for Change
The branch contradicts the project's fail-fast policy and the stance of `validate_tool_schema_v2()` ("reject rather than silently accept") for the same data. Closing it makes the argument gate independent of the discovery gate, so a future registry construction path that skips discovery cannot silently disable argument validation.

## Implementation Intent
Change the falsy-schema branch to return a failed result and log a warning, using the existing `if not input_schema` truthiness test so the rule is exactly "missing or empty". Keep a well-formed zero-argument schema (non-empty, for example `{"type": "object", "properties": {}}`) accepted, because it is truthy and takes the normal path. Update the docstring. Migrate the test fixtures that relied on `{}` meaning "accept everything" to a non-empty zero-argument schema with `allow_extra_fields=True`, which preserves their previous pass behavior.

## Requirements
- `REQ-001`: `validate_tool_arguments()` returns `success=False` when `input_schema` is missing (`None`) or `{}`, with a reason that names the tool and says the input schema is missing; neither `allow_extra_fields` nor a registered custom validator changes this outcome.
- `REQ-002`: The "lenient mode" sentence in the `validate_tool_arguments()` docstring is removed and the docstring states that a missing or empty schema is rejected.
- `REQ-003`: Unit tests cover: `None` schema rejected; `{}` rejected; `{}` rejected even with `allow_extra_fields=True`; a well-formed zero-argument schema accepted; the three existing lenient-mode tests are changed to assert rejection.
- `REQ-004`: Every test fixture that stubs a registry tool with `input_schema = {}` is changed to a well-formed non-empty schema (keeping `allow_extra_fields = True`), so tests that are not about argument validation behave as before.
- `REQ-005`: A preparation-level test shows `prepare_tool_calls()` rejects a call to a registered tool with an empty schema with failure kind `schema`, so the Issue's acceptance ("a tool call targeting a tool whose `input_schema` is missing or `{}` is rejected") holds end to end.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/tool_arg_validator.py | Fail-closed branch and docstring in `validate_tool_arguments()` | The `if not input_schema` branch returns `ValidationResult(success=True)` and the function docstring says "falls back to lenient mode" | REQ-001, REQ-002 / AC-1, AC-2 | `validate_tool_arguments` first branch logs "No input schema ... skipping validation" and returns success; docstring paragraph "When the schema is missing or malformed, falls back to lenient mode" (checked in Step 2) | `tests/agent/test_tool_arg_validator.py` | Verified |
| tests/agent/test_tool_arg_validator.py | Flip lenient tests, add new tests | `TestValidateToolArgumentsEmptySchema` asserts `success is True` for `{}` in three tests; no test passes `None` and none covers `allow_extra_fields=True` with an empty schema | REQ-003 / AC-3 | `TestValidateToolArgumentsEmptySchema` (`test_none_schema_skips_validation`, `test_empty_dict_schema_skips_validation`, `test_missing_required_with_empty_schema`); the first of these passes `{}`, not `None` (checked in Step 2) | itself | Verified |
| tests/agent/test_tool_preparation.py | Fixture schema and one new rejection test | `TestPrepareToolCallsBatchOrdering._valid_registry` sets `runtime_tool.input_schema = {}`; no test covers an empty-schema registry tool | REQ-004, REQ-005 / AC-4, AC-5 | `_valid_registry` in `TestPrepareToolCallsBatchOrdering`; failure injection run (fail-closed wrapper) failed `test_mixed_valid_invalid_batch_preserves_order` and `test_approval_never_called_for_failed_prep_call` (checked in Step 3) | itself | Verified |
| tests/agent/test_tool_runner.py | Fixture schema in three registry helpers | `_default_runtime_tools`, `_runtime_tools` and `_write_registry` each build `tool.input_schema = {}`; 20 tests in this file failed under the fail-closed injection run | REQ-004 / AC-4 | The three `_get` helpers set `tool.input_schema = {}` with `allow_extra_fields = True`; `_write_registry`'s comment describes the empty schema as the way validation is made to pass (checked in Step 3) | itself; tests/agent/test_tool_loop_guard_wiring.py reuses `_make_ctx` from this file | Verified |
| tests/agent/test_agent_repl_tool_exec.py | Fixture schema in `_runtime_tools_for_dag` | `_runtime_tools_for_dag` sets `tool.input_schema = {}`; 3 tests failed under the injection run | REQ-004 / AC-4 | `_runtime_tools_for_dag` docstring "Provides a permissive empty schema (so argument validation ..."; failing tests `test_dag_serial_tool_calls_overrides_dag`, `test_dag_write_executed_before_read`, `test_parallel_execution_without_side_effects` (checked in Step 3) | itself | Verified |
| tests/integration/test_rag_turn_integration.py | Fixture schema in `_default_runtime_tools` | `_default_runtime_tools._get` sets `tool.input_schema = {}`; 5 tests (`test_f01` to `test_f05`) failed under the injection run | REQ-004 / AC-4 | `_default_runtime_tools` and its docstring about the fail-closed preparation phase (checked in Step 3) | itself | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/tool_preparation.py | Only production caller of `validate_tool_arguments()`; maps a failure to kind `schema` and answers the call | REQ-001, REQ-005 |
| scripts/shared/runtime_tool.py | `build_runtime_tool()` defaults a missing schema to `{}`; the only non-discovery construction path (UNK-01) | REQ-001 |
| scripts/shared/resource_scope.py | `validate_tool_schema_v2()` rejects a missing or empty `inputSchema` and requires `properties` to be a dict: the stance to mirror | REQ-001 |
| scripts/agent/services/mcp_tool_discovery_fetch.py | `_entry_schema_error()` calls `validate_tool_schema_v2()` as a hard gate (returns an error string) | REQ-001 |
| scripts/agent/services/mcp_tool_discovery_registry.py | The only production `build_runtime_tool()` call; passes `entry.get("inputSchema")` that discovery already validated | REQ-001 |
| tests/agent/test_tool_argument_injection_security.py | Existing tests with a non-empty schema and an empty `properties` dict that must stay green | REQ-003 |
| tests/agent/test_tool_loop_guard_wiring.py | Reuses `_make_ctx` from `test_tool_runner.py`; its 4 failures under the injection run are fixed by the `test_tool_runner.py` change | REQ-004 |
| tests/shared/runtime_tool_factory.py | `build_fixture_runtime_tool` builds real tools without a schema; confirmed none of its users reaches the validator | REQ-004 |
| docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Describes argument validation as fail-closed; no mention of lenient mode | Documentation Impact |
| docs/91_security/security_02_high-risk-tool-common-policy.md | Says "All tool arguments are validated before execution"; consistent with the change | Documentation Impact |

## Acceptance Criteria
- AC-1 (REQ-001): `validate_tool_arguments("t", {...}, {})` and `validate_tool_arguments("t", {...}, None)` return `success=False`, the reason contains the tool name and the words "input schema", and the result is the same with `allow_extra_fields=True`.
- AC-2 (REQ-002): The `validate_tool_arguments()` docstring no longer contains "lenient mode" and states that a missing or empty schema is rejected; the first docstring line is unchanged so the generated API reference stays in sync.
- AC-3 (REQ-003): `uv run pytest tests/agent/test_tool_arg_validator.py tests/agent/test_tool_argument_injection_security.py` passes; the zero-argument schema `{"type": "object", "properties": {}}` is accepted for empty args.
- AC-4 (REQ-004): With the fixtures migrated, `tests/agent/test_tool_preparation.py`, `tests/agent/test_tool_runner.py`, `tests/agent/test_agent_repl_tool_exec.py`, `tests/agent/test_tool_loop_guard_wiring.py` and `tests/integration/test_rag_turn_integration.py` pass, and no remaining fixture sets `input_schema = {}` for a tool reaching `prepare_tool_calls()`.
- AC-5 (REQ-005): A `prepare_tool_calls()` test with an empty-schema registry tool yields one failure of kind `schema` and no prepared call.

## Tests
- REQ-001, REQ-003: in `tests/agent/test_tool_arg_validator.py`, change `test_none_schema_skips_validation`, `test_empty_dict_schema_skips_validation` and `test_missing_required_with_empty_schema` to assert rejection (renamed to say "rejected"), add a `None` case, an `allow_extra_fields=True` case, and a zero-argument schema acceptance case.
- REQ-004: update the six `input_schema = {}` sites in the five fixture files; no new test is needed there.
- REQ-005: add one test to `tests/agent/test_tool_preparation.py` using a registry tool with `input_schema = {}`, asserting `failures` has one entry with kind `schema` and `prepared == []`.

## Documentation Impact
N/A: no `docs/*.md` file names the lenient-mode branch (`rg -i "lenient|no input schema|empty schema"` over `docs/` finds only generic governance glossary text), and `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` and `docs/91_security/security_02_high-risk-tool-common-policy.md` already describe validation as fail-closed. `docs/23_agent/agent_13_reference-api-generated.md` and `registry/manifests/agent_api.yaml` carry only the first docstring line, which stays unchanged (REQ-002).

## Assumptions
- A falsy `input_schema` (`None` or `{}`) is the rule for "missing or empty". Non-dict, non-falsy values (for example a `MagicMock` schema in other tests) keep their current behavior, because tightening to an `isinstance` check is not asked for by the Issue and would change unrelated test doubles. Falsifiable by AC-4 (`test_tool_loop_guard_wiring.py` style doubles still pass).
- A zero-argument tool already has a non-empty schema (`{"type": "object", "properties": {}}`): `validate_tool_schema_v2()` rejects an empty dict and a schema without a `properties` dict at discovery, and the existing test `test_empty_properties_allows_any_field` in `tests/agent/test_tool_argument_injection_security.py` shows that shape is accepted. So the Issue's "explicit, narrow allowance" is not needed: truthiness already separates the two cases.
- `build_runtime_tool()` keeps defaulting a missing schema to `{}`. Rejection happens at the argument gate, which is the single place every call passes through; rejecting at construction would also break the real-registry fixtures in `tests/shared/` that never reach the validator (see UNK-01).
- Real-registry tests built with `build_fixture_runtime_tool` do not reach the validator. Callers of `prepare_tool_calls()` / `execute_all_tool_calls()` in `tests/` are `test_tool_preparation.py`, `test_tool_runner.py`, `test_agent_repl_tool_exec.py`, `test_tool_loop_guard_wiring.py`, `test_llm_turn_runner.py`, `test_orchestrator.py`, `test_rag_llm_integration.py`, `test_orchestrator_integration.py` and `test_rag_turn_integration.py` (`rg -l` re-check, 20261102 Step 3); only the five fixture files named above supply an empty-schema stub — the other four callers set no `input_schema` at all (registries are `MagicMock`-based, so their truthy schema attribute keeps the normal path). Falsifiable by the broader test run in Phase 1.
- Step 8b (overlap re-check, 20261102 Step 3): `tools/check_plan_target_overlaps.py` names this Plan for one file, `tests/agent/test_tool_runner.py`, also targeted by `plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md` (adds new responsiveness test functions only) and `plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md` (adds a cancellation test only); blockio001's own Assumptions already record a sequencing dependency on this Plan for that file. Judged compatible: this Plan edits only the bodies of the three registry-stub helpers (`input_schema` value), the other two add tests; no source file overlaps and the stubs keep their pass behavior, so any order works and the later Plan rebases its additions. `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` and `plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md`, named at freeze time, are now archived under `plans/done/`. No finding names the other five target files.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner also wants `build_runtime_tool()` to stop defaulting a missing schema to `{}`. The Issue lists it as a target area but its Required Changes ask only for the validator change. Needs confirmation. | Owner intent; this cycle found the validator change sufficient and the default's only non-test construction path is discovery, which validates first | Owner decision at `plan-to-implementation-procedure`; if yes, amend this Plan with a new target row and migrate the `tests/shared/` fixtures | False |
| UNK-02 | Whether any test outside the target files reaches `prepare_tool_calls()` with an empty-schema stub. Static re-check (20261102 Step 3) found only two such stubs outside the target files (`tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py`) and neither file calls `prepare_tool_calls()` or `validate_tool_arguments()`, so no additional target file is statically indicated. | Runtime confirmation of the static result (a full-suite run was not performed) | Run `uv run pytest tests/agent tests/integration` after the fixture migration (Phase 1) and before the validator change (Phase 2); a failure means an additional target file, which stops per `rules/workflow-lifecycle.md` | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/tool_arg_validator.py | Modify | Low: one production caller (`tool_preparation._prepare_one`); only the missing/empty-schema case changes and no registered production tool takes that path | 1 commit | 2 authors in the last year | not applicable (rsynced) |
| tests/agent/test_tool_arg_validator.py | Modify | Low: validator unit tests only | 1 commit | 2 authors | not applicable (rsynced) |
| tests/agent/test_tool_preparation.py | Modify | Low: one fixture and one added test | 1 commit | 2 authors | not applicable (rsynced) |
| tests/agent/test_tool_runner.py | Modify | Medium: three shared helpers, and `test_tool_loop_guard_wiring.py` imports `_make_ctx` from this file; also targeted by other Plans (Assumptions) | 12 commits | 2 authors | not applicable (rsynced) |
| tests/agent/test_agent_repl_tool_exec.py | Modify | Low: one helper | 4 commits | 2 authors | not applicable (rsynced) |
| tests/integration/test_rag_turn_integration.py | Modify | Low: one helper | 5 commits | 2 authors | not applicable (rsynced) |

## Design
Path B (reclassified by file count: six target files exceeds the Path A limit of three; the behavior change is runtime-facing but no signature, schema or config key changes).

Architecture: `agent.tool_preparation._prepare_one` calls `validate_tool_arguments(tool_name, args, runtime_tool.input_schema, runtime_tool.allow_extra_fields)` and maps a failure to `_reject(..., "schema", reason)`; the rejected call is answered with a tool message, so the new rejection needs no change in the caller. `lint-imports` reports 6 contracts kept; the change adds no import. `tool_arg_validator.py` is imported only by `tool_preparation.py` in production.

Evidence on the claim "an empty-schema tool cannot reach the registry through discovery": `mcp_tool_discovery_fetch._entry_schema_error` requires `inputSchema` to be a dict and then calls `validate_tool_schema_v2()`, which rejects a non-dict or empty schema and a schema whose `properties` is not a dict; the error string is returned and the entry is dropped. The only production `build_runtime_tool()` call is in `mcp_tool_discovery_registry`, fed from those validated entries. So the branch is reachable in production only through a registry built outside discovery. Test doubles do reach it: six `input_schema = {}` stubs in the five fixture files, which the failure-injection run showed matter (34 tests fail across five files: 2 in `test_tool_preparation.py`, 20 in `test_tool_runner.py`, 3 in `test_agent_repl_tool_exec.py`, 4 in `test_tool_loop_guard_wiring.py`, 5 in `test_rag_turn_integration.py`). Re-check (20261102 Step 3): `rg 'input_schema\s*=\s*\{\}' tests/` finds eight single-line sites in total; the two outside the fixture files (`tests/agent/test_tool_policy.py` and `tests/agent/test_tool_policy_comprehensive.py`) build registries only for `classify_risk` / `classify_operation_type` tests that call neither `prepare_tool_calls()` nor `validate_tool_arguments()`, so they are evidence, not targets.

Design decisions:
- Rule: keep `if not input_schema` (falsy). Alternative: `not isinstance(input_schema, dict) or not input_schema`, mirroring `validate_tool_schema_v2`. Rejected for now because the `isinstance` form would also reject `MagicMock` schemas used by other test doubles, with no production benefit (the registry always holds a dict); recorded as a falsifiable assumption.
- Where to reject: at the validator, not in `build_runtime_tool()` (UNK-01). Alternative rejected: constructing-time rejection would break `tests/shared/` real-registry fixtures that never reach the validator and is not in the Issue's Required Changes.
- Log level: log a warning (not debug) because a reachable branch now means a registry construction bug. The reason string must name the tool so the answered tool message is actionable.
- Fixture schema: `{"type": "object", "properties": {}}` with `allow_extra_fields = True` keeps the same pass behavior (required: none; extra-field check skipped by the flag; jsonschema accepts any extra property).
- Compatibility: behavior changes only for a missing or empty schema; the `validate_tool_arguments()` signature, `ValidationResult` and the registered-hook ordering are unchanged.

Validation quality baseline: `radon cc` for `validate_tool_arguments` is B (7), and replacing the early return with another early return does not change it; `vulture scripts/ --min-confidence 80` reports three unrelated 100% items in `scripts/rag/ingestion/document_manager.py` and `scripts/shared/runtime_paths.py`; `bandit` on `scripts/` reports 8 Medium and 43 High findings repo-wide, none in `tool_arg_validator.py`; diff-cover must reach the `rules/toolchain.md` threshold (90%) on the changed lines.

## Implementation steps
1. **Phase 1: Migrate the stub schemas (no behavior change; safe to land first)**
   - [ ] In `tests/agent/test_tool_preparation.py`, `_valid_registry` uses `{"type": "object", "properties": {}}` (REQ-004).
   - [ ] In `tests/agent/test_tool_runner.py`, the `_get` helpers of `_default_runtime_tools`, `_runtime_tools` and `_write_registry` use that schema and the `_write_registry` comment is reworded (REQ-004).
   - [ ] In `tests/agent/test_agent_repl_tool_exec.py` (`_runtime_tools_for_dag`) and `tests/integration/test_rag_turn_integration.py` (`_default_runtime_tools`), same change (REQ-004).
   - [ ] Run `uv run pytest tests/agent tests/integration`; any new failure is an additional target file (UNK-02) and stops the work.
2. **Phase 2: Fail-closed validator**
   - [ ] In `scripts/agent/tool_arg_validator.py`, change the falsy-schema branch to a failed `ValidationResult` with a warning log, and replace the "lenient mode" docstring paragraph (REQ-001, REQ-002).
3. **Phase 3: Tests for the new behavior**
   - [ ] In `tests/agent/test_tool_arg_validator.py`, flip the three lenient tests and add the `None`, `allow_extra_fields=True` and zero-argument cases (REQ-003).
   - [ ] In `tests/agent/test_tool_preparation.py`, add the empty-schema rejection test (REQ-005).
4. **Phase 4: Deployment & verification**
   - [ ] Run the Validation plan commands below, including the checks for a changed `scripts/agent/` file (REQ-001 to REQ-005).
   - [ ] Deploy is a hand-off to `skills/deploy/SKILL.md`: the change must be committed and pushed first, and deploying is the user's decision (approval gate); `scripts/agent/tool_arg_validator.py` ships through the normal rsync, with no new file, config key or service change.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/tool_arg_validator.py | Unit | `uv run pytest tests/agent/test_tool_arg_validator.py tests/agent/test_tool_argument_injection_security.py` | All pass, including the flipped and new cases (AC-1, AC-3) |
| tests/agent/test_tool_preparation.py | Unit | `uv run pytest tests/agent/test_tool_preparation.py` | All pass; empty-schema call fails with kind `schema` (AC-5) |
| tests/agent/test_tool_runner.py, tests/agent/test_agent_repl_tool_exec.py, tests/agent/test_tool_loop_guard_wiring.py, tests/integration/test_rag_turn_integration.py | Integration (regression) | `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_agent_repl_tool_exec.py tests/agent/test_tool_loop_guard_wiring.py tests/integration/test_rag_turn_integration.py` | Pass with migrated fixtures (AC-4) |
| Whole agent and integration suites | Regression for UNK-02 | `uv run pytest tests/agent tests/integration` | No failure caused by an empty-schema stub |
| scripts/agent/tool_arg_validator.py | Lint, type, docs-sync | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_module_size.py`, `uv run python tools/check_docstrings.py` | Clean; generated API reference unchanged (AC-2) |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (sequence in `rules/toolchain.md` section 7) | At least 90% |

## Risks
- **Risk**: A test not run in this cycle builds a stub with an empty schema and fails after Phase 2 (likelihood: low) → **Mitigation**: Phase 1 migrates the known six sites and runs `tests/agent` and `tests/integration` before the validator change; a failure is handled as an additional target file discovery (UNK-02).
- **Risk**: A registry constructed outside discovery in a deployed path carries an empty schema and every call to that tool starts failing (likelihood: very low: the only production construction goes through discovery's hard gate) → **Mitigation**: the rejection reason names the tool and the schema problem and is answered as a normal `schema` rejection, not a crash; the change ships through the normal reviewed deploy.
- **Risk**: Edits to `tests/agent/test_tool_runner.py` collide with other Plans that touch the same file (likelihood: medium, file churn is 12 in 30 days) → **Mitigation**: this Plan edits three disjoint helper bodies only; Step 8b judged every overlap compatible (Assumptions).
- **Risk**: Fixture schema `{"type": "object", "properties": {}}` with `allow_extra_fields = True` changes a stubbed test's outcome (likelihood: low) → **Mitigation**: the failure-injection run reproduced the pass behavior requirement; Phase 1 runs the five fixture files before any production change, so a difference shows while the validator is still lenient.
- **Risk**: The reason text is relied on by an operator or a test elsewhere (likelihood: low) → **Mitigation**: the string is new and asserted only by the new tests (AC-1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate the five stub-registry fixtures (six sites) to a non-empty schema; run `tests/agent` and `tests/integration` | Completed | 20261102-201257 | 20261102-201257 |  |
| 2 | Fail-closed branch and docstring in `scripts/agent/tool_arg_validator.py` | Completed | 20261102-201257 | 20261102-201257 |  |
| 3 | Flip and add validator tests; add preparation rejection test | Completed | 20261102-201257 | 20261102-201257 |  |
| 4 | Validation commands and deploy hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-192710_01_scripts_agent_tool_arg_validator.py.md | 2, 3 | Procedure | Completed | — | — |
| implementations/20261102-192710_03_tests_agent_test_tool_preparation.py.md | 1, 3 | Procedure | Completed | — | — |
| implementations/20261102-192710_04_tests_agent_test_tool_runner.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261102-192710_05_tests_agent_test_agent_repl_tool_exec.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261102-192710_06_tests_integration_test_rag_turn_integration.py.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180328_toolarg001_tool-validation-fails-open-empty-schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-142029
- **Related target files**: scripts/agent/tool_arg_validator.py, tests/agent/test_tool_arg_validator.py, tests/agent/test_tool_preparation.py, tests/agent/test_tool_runner.py, tests/agent/test_agent_repl_tool_exec.py, tests/integration/test_rag_turn_integration.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Problem, Required Changes; `validate_tool_arguments` first branch | scripts/agent/tool_arg_validator.py | Step 2 | AC-1 | `tests/agent/test_tool_arg_validator.py` rejection cases | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (docstring); function docstring paragraph | scripts/agent/tool_arg_validator.py | Step 2 | AC-2 | `uv run python tools/generate_reference_table.py --check`; docstring inspection | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (add tests), Testing Expectations | tests/agent/test_tool_arg_validator.py | Step 3 | AC-3 | `uv run pytest tests/agent/test_tool_arg_validator.py tests/agent/test_tool_argument_injection_security.py` | Explicit in issue |
| REQ-004 | Issue Target Files (tests that build tools without a schema); failure-injection run showing 34 failing tests | tests/agent/test_tool_preparation.py | Step 1 | AC-4 | `uv run pytest tests/agent/test_tool_preparation.py` | Derived from confirmed evidence |
| REQ-004 | Same | tests/agent/test_tool_runner.py | Step 1 | AC-4 | `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_loop_guard_wiring.py` | Derived from confirmed evidence |
| REQ-004 | Same | tests/agent/test_agent_repl_tool_exec.py | Step 1 | AC-4 | `uv run pytest tests/agent/test_agent_repl_tool_exec.py` | Derived from confirmed evidence |
| REQ-004 | Same | tests/integration/test_rag_turn_integration.py | Step 1 | AC-4 | `uv run pytest tests/integration/test_rag_turn_integration.py` | Derived from confirmed evidence |
| REQ-005 | Issue Acceptance Criteria (tool call rejected); `prepare_tool_calls` maps a validation failure to kind `schema` | tests/agent/test_tool_preparation.py | Step 3 | AC-5 | `uv run pytest tests/agent/test_tool_preparation.py` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-192710 -->