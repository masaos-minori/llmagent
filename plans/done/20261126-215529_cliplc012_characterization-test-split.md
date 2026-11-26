# Plan: Separate characterization tests from authoritative security and lifecycle contracts

## Goal
- Give the suite two explicit test kinds — a characterization suite that records observed behavior and a contract suite that asserts behavior traceable to a requirement source — so an implementation issue can reverse a legacy expectation without contradicting a "requirement", and CI reports the two kinds separately.

## Priority
Medium

## Scope
- **In-Scope**: two pytest markers registered in `pyproject.toml`; a written classification rule grounded in the documentation authority model; a read-only checker that enforces the rule for classified modules and tracks the rest in a baseline; the first tranche of test modules named by the Issue (HTTP lifecycle, CLI input, approval, reload, persistence) classified and their contradictory docstrings corrected; CI reporting the two suites separately from a single run; the tool inventory, gate, and toolchain entries for the new checker.
- **Out-of-Scope**: fixing the underlying behavior (owned by the other issues of this backlog); classifying the 90 currently unclassified modules in `tests/agent` and `tests/shared` in one pass — they are classified incrementally as each contract changes, per the Issue's Implementation Intent; test modules outside the Issue's named areas except the single verified contradiction row; the final documentation rewrite (issue `20261119-145312_cliplc014_cli-docs-consolidation.md`, still active).
- **Dependencies**: the consolidated backlog issues (cliplc001 through cliplc011) are all closed under `issues/done/`; their plans are archived under `plans/done/` except cliplc010, whose plan is still open (gated by its blocking Unknown). This Plan changes no file that cliplc010's plan targets (`tools/check_plan_target_overlaps.py`: no findings), so it has no open ordering dependency. `N/A: none open`.

## Background
The Issue is Issue 12 of the consolidated CLI REPL and MCP lifecycle backlog. Its eight legacy-behavior claims (delayed-input handoff, process-record deletion before confirmed exit, restart after unconfirmed termination, permissive command confinement, shared credential inheritance, `filter_env(None)`, SIGINT absorption, rename-only log rotation) were recorded as backlog claims needing confirmation. Step 2 verified each against current source: seven are already corrected in the implementation, so the tests that assert them are not legacy locks but current contracts. Only the environment-filter pass-through is still a live contradiction between a test and a documented contract. The Issue's remaining substance is therefore the taxonomy itself: which tests are authoritative and which record history, and how CI reports them.

## Problem
The suite has no machine-readable distinction between a test that asserts a required behavior and a test that records observed behavior. Classification is currently inferable only from prose: 253 test modules in `tests/agent` and `tests/shared` hold 4,377 test functions, of which 128 cite a requirement number, 24 mix requirement-cited assertions with characterization-worded sections, 11 are characterization-only, and 90 carry neither signal. A characterization test can therefore read as a normative contract, and a correction to the contract it records conflicts with what looks like a requirement. One verified instance exists: `tests/mcp_servers/shell/test_shell_mcp_service.py:93-96` locks the empty-allowlist/empty-denylist pass-through in `scripts/mcp_servers/shell/shell_service.py:342-350`, which contradicts the documented default-deny filter (`docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:67`), while the module header presents it as a guard contract. No checker reads pytest markers or validates test structure, so nothing prevents this from recurring.

## Reason for Change
Each implementation issue must be able to reverse a legacy expectation in the same commit as its fix, without a test that records history being read as a requirement. The taxonomy also has to be machine-checkable, because the classification is currently carried only in docstrings that drift: `tests/shared/test_llm_client_characterization.py:1-8` already cites wrappers that were removed.

## Implementation Intent
Make the classification explicit at the test-module level with pytest markers, define the rule in the authority model where tests are already `verification-contract`, enforce it with a narrow read-only checker plus a baseline for the existing unclassified modules, and report the two suites separately in CI from the single existing run so coverage measurement is not fragmented. Migrate a module when its contract changes rather than re-marking the whole suite at once.

## Requirements
- `REQ-001`: Register the `characterization` and `contract` markers in `pyproject.toml`'s `[tool.pytest.ini_options] markers`, selectable with `-m` under the existing parallel run (`-n logical`) and the `tests/conftest.py` autouse fixtures.
- `REQ-002`: Define the classification rule in the documentation authority model: a test module is `contract` when its assertions are traceable to a requirement source (an Accepted ADR, a Canonical Source Registry entry, or the recorded requirement of an archived backlog issue under `issues/done/`, consistent with the Resolution Matrix's `verification-contract` row, whose canonical source kind is `tests/` plus the requirement source) and carries that citation; otherwise it is `characterization`, asserting observed behavior with no requirement source. A characterization module MUST NOT present its assertions as normative. (Requirement source definition extended 2026-11-26 in Step 3a: rows 13 and 14 have no ADR or Registry entry for their contract, so the archived issue's recorded requirement is the only available source; owner decision.)
- `REQ-003`: Every test module in the classified areas carries exactly one taxonomy marker through `pytestmark`; a module that mixes both kinds marks individual tests; a module that is not yet classified is tracked in a baseline and must be classified when it is next modified.
- `REQ-004`: A read-only checker enforces the rule — a marker is present, a `contract` marker is justified by a requirement citation, no module claims both kinds at module level, and no module outside the baseline is unclassified — and runs as a local fast gate and a CI lint step, registered in the tool inventory.
- `REQ-005`: CI reports the characterization suite and the contract suite separately from one pytest run, using JUnit XML grouped by module, with the existing coverage measurement and `diff-cover` step unchanged.
- `REQ-006`: A failure in the characterization suite is reported in its own section and does not fail the CI job; a failure in the contract suite does. A baseline entry for a characterization failure must name the owning issue.
- `REQ-007`: Remove docstrings that present characterization assertions as normative contracts or that cite symbols that no longer exist, in the modules of the first tranche.
- `REQ-008`: Confirm that every High-priority issue of this backlog has authoritative acceptance tests and mark those modules `contract`; record the Issue's disconfirmed legacy claims as corrected findings.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `pyproject.toml` | Modify | Add `characterization` and `contract` to the `markers` list | REQ-001 / AC-1 | `pyproject.toml:145-148` registers only `integration` and `repo_scan` (checked in Step 3) | `tests/tools/test_check_test_taxonomy.py` | Verified |
| `tools/check_test_taxonomy.py` | Create (new file) | Read-only checker for the classification rule and the per-suite report mode | REQ-003, REQ-004, REQ-005 / AC-2, AC-4 | No checker reads pytest markers: `grep -rln "tool.pytest.ini_options" tools/ tests/` returns no match (checked in Step 3); `tools/check_conftest_integrity.py:1-30` is the narrow read-only precedent | `tests/tools/test_check_test_taxonomy.py` | Verified |
| `tools/test_taxonomy_baseline.txt` | Create (new file) | Baseline of the modules that are not yet classified | REQ-003 / AC-3 | 90 unclassified modules under `tests/agent` and `tests/shared` counted in Step 3; header format precedent `tools/known_test_failures_baseline.txt` | `tests/tools/test_check_test_taxonomy.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Register the new checker in the tool inventory | REQ-004 / AC-2 | `rules/tool-gates.md` requires every `tools/` script to be registered in `tools/TOOL_DESCRIPTIONS.md`; the file is the tool inventory (checked in Step 3) | `tests/tools/test_check_test_taxonomy.py` | Verified |
| `tools/_validation_gate_defs.py` | Modify | Add the gate and its `tests/` patterns | REQ-004 / AC-2 | `tools/_validation_gate_defs.py:650-655` shows the gate shape and pattern convention (`check_conftest_integrity`) (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `rules/toolchain.md` | Modify | Add the taxonomy check to the standard validation sequence and the marker selection commands | REQ-004, REQ-005 / AC-2, AC-4 | `rules/toolchain.md:107` full-suite command, `:118` coverage command, `:125` CI note (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `.github/workflows/ci.yml` | Modify | Add the checker to the `lint` job and the per-suite report step to the test job | REQ-005, REQ-006 / AC-4, AC-5 | `.github/workflows/ci.yml:87` runs all tests in one run with coverage; the `lint` job steps are at `:23-31` (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tests/tools/test_check_test_taxonomy.py` | Create (new file) | Tests for the checker: rule enforcement, baseline behavior, report grouping | REQ-003, REQ-004, REQ-005 / AC-2, AC-3, AC-4 | `tests/tools/` holds one test module per checker, e.g. `tests/tools/test_check_conftest_integrity.py` (checked in Step 3) | itself | Verified |
| `docs/00_governance/governance_01_documentation-policy.md` | Modify | Record the taxonomy definition against the `verification-contract` row of the Resolution Matrix | REQ-002 / AC-6 | `docs/00_governance/governance_01_documentation-policy.md:125` defines `verification-contract` and states tests cannot silently redefine requirements (checked in Step 3) | `tests/tools/test_check_docs_quality.py` | Verified |
| `docs/00_index.md` | Modify | Add the test-taxonomy task-scope row that the Documentation Impact section must name | REQ-002 / AC-6 | `docs/00_index.md:117-126` has no test-taxonomy row (checked in Step 3) | `tests/tools/test_check_docs_structure.py` | Verified |
| `skills/python-test-and-fix/workflow.md` | Modify | Record the classification rule in the Test structure section | REQ-002, REQ-003 / AC-6 | `skills/python-test-and-fix/workflow.md:24-26` is where the `tests/` mirrors `scripts/` convention is documented (checked in Step 3) | `tests/tools/test_check_skill_size.py` | Verified |
| `tests/agent/test_stdin_reader.py` | Modify | Add `pytestmark = pytest.mark.characterization` | REQ-003 / AC-3 | No `pytestmark` and no requirement citation; asserts post-cancellation delivery is discarded (`tests/agent/test_stdin_reader.py:89,124,136`) matching `scripts/agent/stdin_reader.py:39-43` (checked in Step 3) | itself | Verified |
| `tests/agent/test_repl_input_controller.py` | Modify | Add `pytestmark = pytest.mark.contract` and the requirement-source citation the checker requires | REQ-003, REQ-008 / AC-3, AC-7 | No `pytestmark` and no citation; its contract is the archived cliplc001 acceptance tests, so the citation must name `issues/done/20261119-145259_cliplc001_repl-input-controller.md` as the requirement source (Step 3a, per the extended REQ-002) | itself | Verified |
| `tests/agent/test_repl_shutdown_machine.py` | Modify | Add `pytestmark = pytest.mark.contract` and the requirement-source citation the checker requires | REQ-003, REQ-008 / AC-3, AC-7 | No `pytestmark` and no citation; its contract is the archived cliplc004 acceptance tests, so the citation must name `issues/done/20261119-145302_cliplc004_bounded-shutdown-machine.md` as the requirement source (Step 3a, per the extended REQ-002) | itself | Verified |
| `tests/agent/test_http_lifecycle.py` | Modify | Per-test markers: the module mixes requirement-cited assertions with a characterization section | REQ-003 / AC-3 | Module docstring cites REQ-001/REQ-002; characterization section begins at `tests/agent/test_http_lifecycle.py:223` (checked in Step 3) | itself | Verified |
| `tests/agent/test_http_lifecycle_command_validator.py` | Modify | Add `pytestmark = pytest.mark.contract` | REQ-003, REQ-008 / AC-3, AC-7 | `tests/agent/test_http_lifecycle_command_validator.py:5-6` states trusted-directory confinement is the default and permissive is an explicit `LLMAGENT_COMMAND_MODE=permissive` opt-in; `:463`, `:534` assert REQ-004 (checked in Step 3) | itself | Verified |
| `tests/agent/test_http_lifecycle_launch_spec.py` | Modify | Add `pytestmark = pytest.mark.contract` | REQ-003, REQ-008 / AC-3, AC-7 | Asserts the REQ-006 fixed inheritable environment set; secrets are stripped in `scripts/mcp_servers/shell/shell_service_static_helpers.py:266-283` (checked in Step 3) | itself | Verified |
| `tests/agent/test_http_lifecycle_env_allowlist_integration.py` | Modify | Add `pytestmark = pytest.mark.contract` | REQ-003, REQ-008 / AC-3, AC-7 | Its module docstring cites cliplc006 REQ-006/REQ-007 (`tests/agent/test_http_lifecycle_env_allowlist_integration.py:3`) and the gates at `:262-464` assert the per-server environment boundary; `:128-138` are helpers, not assertions (reverified in Step 3a) | itself | Verified |
| `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Modify | Per-test markers: module-level `contract` for the requirement-cited assertion, `characterization` for the rotation tests | REQ-003 / AC-3 | Asserts rename-only rotation (`tests/agent/test_http_lifecycle_stderr_log_manager.py:145-160`) matching `scripts/agent/http_lifecycle_stderr_log_manager.py:111-129`; no requirement source defines rotation semantics, while `:221` cites REQ-005 for `open_log` key validation, so the module mixes kinds (reverified in Step 3a) | itself | Verified |
| `tests/agent/test_signal_handler.py` | Modify | Add `pytestmark = pytest.mark.contract` | REQ-003, REQ-008 / AC-3, AC-7 | Asserts SIGINT acts through the REPL input state (`tests/agent/test_signal_handler.py:171,235,246`), not absorption (checked in Step 3) | itself | Verified |
| `tests/agent/test_config_builders.py` | Modify | Per-test markers: requirement-cited assertions plus a characterization section | REQ-003 / AC-3 | Characterization section at `tests/agent/test_config_builders.py:658-737` alongside REQ-cited assertions (checked in Step 3) | itself | Verified |
| `tests/agent/memory/test_memory_store.py` | Modify | Per-test markers: requirement-cited assertions plus a characterization section | REQ-003 / AC-3 | Characterization section at `tests/agent/memory/test_memory_store.py:598` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | Per-test markers: requirement-cited assertions plus a characterization section | REQ-003 / AC-3 | Characterization section at `tests/agent/workflow/test_workflow_state_store.py:323` (checked in Step 3) | itself | Verified |
| `tests/shared/test_llm_client_characterization.py` | Modify | Add `pytestmark = pytest.mark.characterization` and correct the stale module docstring | REQ-003, REQ-007 / AC-3, AC-5 | `tests/shared/test_llm_client_characterization.py:1-8` cites the removed `LLMClient.build_payload` and `request_with_retry` wrappers and carries a truncated sentence (line 4 ends with a dangling clause continued by the parenthetical at line 5) (reverified in Step 3a) | itself | Verified |
| `tests/mcp_servers/shell/test_shell_mcp_service.py` | Modify | Per-test markers: module-level `contract` for the requirement-cited assertions, `characterization` for the pass-through case; correct the header that presents the pass-through as a guard contract | REQ-003, REQ-007 / AC-3, AC-5 | `tests/mcp_servers/shell/test_shell_mcp_service.py:93-96` locks the empty-allowlist/empty-denylist pass-through in `scripts/mcp_servers/shell/shell_service.py:342-350`, contradicting the documented default-deny filter at `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:67`; the module's only requirement citation is REQ-004 at `:318` (audit record), so it mixes kinds (reverified in Step 3a) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tests/conftest.py` | Marker registration precedent (`pytest_configure`, `:298-304`) and the autouse fixtures and production-path guard the markers must not disturb; this Plan registers markers only in `pyproject.toml`, so the file is not modified | REQ-001 |
| `tests/tools/test_run_validation_gates.py` | `test_every_ci_lint_command_has_a_gate_or_a_reviewed_exception` (`:948-970`) fails when the new CI lint step has no gate | REQ-004 |
| `tools/check_adr_invariant_matrix.py` | Fails when a test path cited by the ADR index no longer exists; this is the reason the taxonomy uses markers rather than a directory | REQ-002 |
| `docs/10_adr/adr_01_index.md` | 46 lines cite test paths; a directory move would break those citations | REQ-002 |
| `tools/compare_test_baseline.py` | JUnit XML input format and the baseline policy the CI report step reuses | REQ-005, REQ-006 |
| `tools/known_test_failures_baseline.txt` | Header policy: a reason must name an issue; nothing is skipped, xfailed, or deselected | REQ-006 |
| `scripts/agent/stdin_reader.py` | Current behavior the stdin test records (`:39-43`) | REQ-003 |
| `scripts/agent/http_lifecycle.py` | Current behavior: the process record is released only after a confirmed exit (`:411-444`) | REQ-008 |
| `scripts/agent/signal_handler.py` | Current behavior: SIGINT acts through the REPL input controller | REQ-008 |
| `scripts/agent/http_lifecycle_launch_spec.py` | Current behavior: the fixed inheritable environment set (REQ-006) | REQ-008 |
| `scripts/agent/http_lifecycle_stderr_log_manager.py` | Current behavior: rename-only rotation (`:111-129`) | REQ-003 |
| `scripts/mcp_servers/shell/shell_service.py` | The pass-through the shell test records (`:342-350`) | REQ-007 |
| `scripts/mcp_servers/shell/shell_service_static_helpers.py` | `build_command_env` (`:266-283`) shows the documented contract is implemented, so only the `req.env` filter is affected | REQ-007 |
| `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` | The documented default-deny filter the shell test contradicts (`:67`, `:114`) | REQ-007 |
| `rules/tool-gates.md` | Checker mapping for a new `tools/` script and for `tests/**/conftest*` | REQ-004 |
| `deploy/deploy.sh` | Confirms `tests/` and `docs/` are rsynced and no `cp` line is affected | Affected areas |

## Acceptance Criteria
- AC-1 (REQ-001): `uv run pytest -m characterization tests/` and `uv run pytest -m contract tests/` select without an unknown-marker warning, and the selection works with `-n logical` and the `tests/conftest.py` fixtures.
- AC-2 (REQ-004): the checker reports a module with no marker outside the baseline, a `contract` module without a requirement citation, and a module claiming both kinds at module level; it runs as a gate and in the CI `lint` job.
- AC-3 (REQ-003): every module in the first tranche carries exactly one marker, and mixed modules carry per-test markers; the baseline holds only modules outside the tranche.
- AC-4 (REQ-005): CI prints a characterization section and a contract section from one run, and the coverage and `diff-cover` steps are unchanged.
- AC-5 (REQ-007): no first-tranche docstring presents a characterization assertion as normative or cites a removed symbol.
- AC-6 (REQ-002): the authority model states the rule and `docs/00_index.md` maps the test-taxonomy task to it.
- AC-7 (REQ-008): each High-priority backlog issue (cliplc001 through cliplc007) has its acceptance-test module marked `contract`; the seven disconfirmed legacy claims are recorded as corrected findings, not as tests to change.
- AC-8 (REQ-006): a characterization failure is reported in its own section and does not fail the CI job; a contract failure fails it.

## Tests
- T-1 (REQ-001, AC-1): `uv run pytest -m characterization tests/ -q` and `uv run pytest -m contract tests/ -q` — both selections run; the union equals the full suite for the classified areas.
- T-2 (REQ-003, AC-3): `uv run pytest tests/tools/test_check_test_taxonomy.py -v` — rule enforcement, baseline exemption, mixed-module detection.
- T-3 (REQ-004, AC-2): `uv run python tools/check_test_taxonomy.py` on the repository — reports only the baseline modules as unclassified; `uv run python tools/run_validation_gates.py` runs it as a gate.
- T-4 (REQ-005, AC-4): `uv run pytest tests/ -n logical --cov=scripts --cov-report= --junitxml=report.xml -q` then `uv run python tools/check_test_taxonomy.py --junit-xml report.xml` — two suite sections with counts matching the run.
- T-5 (REQ-006, AC-8): `uv run pytest tests/tools/test_run_validation_gates.py -v` — the CI lint step has a gate; the report step's exit behavior is asserted by `tests/tools/test_check_test_taxonomy.py`.
- T-6 (REQ-002, AC-6): `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py` on the changed docs.
- T-7 (REQ-008, AC-7): `uv run pytest tests/agent tests/shared -q` — the full suite passes with the markers applied and no assertion changed.

## Documentation Impact
Yes. `docs/00_governance/governance_01_documentation-policy.md` carries the taxonomy definition against its `verification-contract` Resolution Matrix row (REQ-002), and `docs/00_index.md`'s "Document References by Task" table needs a test-taxonomy row pointing to it (REQ-002) — the table has no such row today, so the Documentation Impact section names the doc by adding that row rather than hardcoding a new filename. `rules/toolchain.md` and `skills/python-test-and-fix/workflow.md` carry the operational convention (REQ-004, REQ-003).

## Assumptions
- The classification unit is the test module (`pytestmark`), with per-test markers only where a module mixes both kinds; grouping the CI report by module rather than by test avoids parametrized-ID mismatches in JUnit XML.
- Bulk classification is incremental, not a single pass: the Issue's Implementation Intent says "migrate as each contract changes", so the 90 unclassified modules are tracked in the baseline and classified when touched. Classifying all 152 signal-bearing modules now would require 152 target rows and is not assumed.
- `tests/mcp_servers/shell/test_shell_mcp_service.py` is outside the Issue's stated areas (`tests/agent`, `tests/shared`) but is the only verified test that locks a behavior contradicting a documented contract; its row is a scope extension and needs approval per `rules/workflow-lifecycle.md` Plan Amendment Approval Classes.
- The Issue's "maintenance tests" area is not in the target rows: maintenance tests live under `tests/db/` (`tests/db/test_db_maintenance.py`), not under `tests/agent/`.
- Markers are registered only in `pyproject.toml`; `tests/conftest.py`'s `pytest_configure` is left unchanged to avoid two registration sources.
- Step 3a corrections (2026-11-26, adversarial verification): `pyproject.toml`'s `markers` list is at `:145-148`, not `:144-147`; the env-allowlist row's cited lines `:128-138` are helpers, not assertions, and its requirement citation is at `:3` with gates at `:262-464`; the llm-client docstring defect is a truncated sentence at `:4-5`, not an unclosed parenthetical; cliplc010's plan is still open (only its issue is archived); REQ-002's requirement-source definition was extended to include an archived backlog issue's recorded requirement (owner decision), which is the source that makes rows 13 and 14 `contract` and requires a citation to be added in those modules; rows 19 and 25 carry one requirement-cited assertion each, so they mix kinds and take per-test markers under REQ-003.
- Phase 2's "record the seven disconfirmed legacy claims as corrected findings in the plan's Problem section" names this Plan file, which is not a row of the `Implementation Target Files` table, so no procedure document covers it; the seven claims are recorded in Background and the Problem-section record stays an implementation-phase action on the Plan itself.
- Step 8b overlap judgement: `tests/agent/test_http_lifecycle.py` and `tests/agent/test_http_lifecycle_stderr_log_manager.py` are also targeted by the cliplc009 plan — judged compatible, because that plan changes assertions there while this Plan adds markers and corrects docstrings only. The characterization classification of the rotation tests holds until cliplc009's copy-and-truncate rotation lands; after that the module becomes `contract` under the incremental rule.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Marker versus directory for the characterization suite | None — resolved by repository evidence | Markers: `pyproject.toml:145-148` already registers markers, `skills/python-test-and-fix/workflow.md:26` requires `tests/` to mirror `scripts/`, and `tools/check_adr_invariant_matrix.py` fails when a test path cited by `docs/10_adr/adr_01_index.md` (46 lines) moves. A directory split breaks all three. | False |
| UNK-02 | Whether the CI job may treat a characterization failure as non-blocking | Governance approval for weakening the CI gate | The Issue's acceptance criterion states it; the plan limits the exemption to the characterization marker and keeps the baseline entry naming the owning issue. Confirm with the governance owner before the CI step is written. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `pyproject.toml` | Modify | High — pytest configuration read by every local run, tox, pre-commit, and CI | 5 | 2 | not applicable (not rsynced) |
| `tools/check_test_taxonomy.py` | Create | Medium — new gate; consumed by `tools/run_validation_gates.py`, CI, and its own test | new | new | not applicable (not rsynced) |
| `tools/test_taxonomy_baseline.txt` | Create | Low — data file read only by the checker | new | new | not applicable (not rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low — inventory drift check | 81 | 2 | not applicable (not rsynced) |
| `tools/_validation_gate_defs.py` | Modify | Medium — consumed by `tools/run_validation_gates.py`, the pre-commit hooks, and `tests/tools/test_run_validation_gates.py` | 11 | 2 | not applicable (not rsynced) |
| `rules/toolchain.md` | Modify | Medium — the documented sequence the gate definitions are transcribed from | 16 | 2 | not applicable (not rsynced) |
| `.github/workflows/ci.yml` | Modify | High — parsed by `tests/tools/test_run_validation_gates.py`; changes the CI gate semantics | 10 | 2 | not applicable (not rsynced) |
| `tests/tools/test_check_test_taxonomy.py` | Create | Low | new | new | not applicable (rsynced) |
| `docs/00_governance/governance_01_documentation-policy.md` | Modify | Medium — authority model read by the docs checkers and the ADR authority check | 4 | 2 | not applicable (rsynced) |
| `docs/00_index.md` | Modify | Low — task-scope mapping | 0 | 0 | not applicable (rsynced) |
| `skills/python-test-and-fix/workflow.md` | Modify | Low — skill size check | 6 | 2 | not applicable (not rsynced) |
| `tests/agent/test_stdin_reader.py` | Modify | Low | 2 | 1 | not applicable (rsynced) |
| `tests/agent/test_repl_input_controller.py` | Modify | Low | 1 | 1 | not applicable (rsynced) |
| `tests/agent/test_repl_shutdown_machine.py` | Modify | Low | 1 | 1 | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle.py` | Modify | Medium — cited by the ADR index | 4 | 2 | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle_command_validator.py` | Modify | Medium | 2 | 2 | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle_launch_spec.py` | Modify | Low | 1 | 1 | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle_env_allowlist_integration.py` | Modify | Medium — cited by an archived plan's REQ-008 boundary | 5 | 2 | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Modify | Low | 2 | 2 | not applicable (rsynced) |
| `tests/agent/test_signal_handler.py` | Modify | Low | 2 | 1 | not applicable (rsynced) |
| `tests/agent/test_config_builders.py` | Modify | Medium | 12 | 2 | not applicable (rsynced) |
| `tests/agent/memory/test_memory_store.py` | Modify | Low | 4 | 1 | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | Medium | 16 | 2 | not applicable (rsynced) |
| `tests/shared/test_llm_client_characterization.py` | Modify | Low | 0 | 0 | not applicable (rsynced) |
| `tests/mcp_servers/shell/test_shell_mcp_service.py` | Modify | Medium — the only verified test-contract contradiction | 1 | 1 | not applicable (rsynced) |

## Design
Path B. The taxonomy is expressed as pytest markers rather than a directory: markers are already the repository's mechanism for test classification (`integration`, `repo_scan`, `production_paths_allowed`), the `tests/` tree mirrors `scripts/` by rule, and moving test files would break the ADR index citations that `tools/check_adr_invariant_matrix.py` guards. The classification rule is derived from the existing authority model: a `verification-contract` needs a requirement source, so a module whose assertions cite one is `contract` and one that records observed behavior is `characterization`. Enforcement is a narrow read-only checker plus a baseline, following the `check_conftest_integrity.py` and `known_test_failures_baseline.txt` precedents, so the existing 90 unclassified modules do not have to be re-marked in one pass.

CI reporting keeps a single pytest run. Splitting the run into two `-m` selections would fragment coverage: `pytest-cov` measures and combines xdist workers within one run, and `diff-cover --fail-under=90` reads one data file. The report is produced from the JUnit XML of the single run, grouped by module, which is the same input `tools/compare_test_baseline.py` already consumes.

Validation quality baseline (Step 5): `vulture scripts/ --min-confidence 80` reports 5 unused variables, none in a target file; `bandit -r scripts/ -c pyproject.toml -ll` reports 0 Medium and 0 High findings; `diff-cover coverage.xml --compare-branch=master` reports no lines with coverage information because no `scripts/` file is a target. `radon cc` is not run: no `Implementation Target Files` row is a Python file under `scripts/`; the new `tools/` checker is created by the implementation phase and must be kept under the module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`). The `diff-cover` threshold in `rules/toolchain.md`'s Completion checklist (90) is unchanged by this Plan.

## Implementation steps
1. **Phase 1: Mechanism**
   - [ ] Register `characterization` and `contract` in `pyproject.toml`'s `markers` list (REQ-001; `pyproject.toml`)
   - [ ] Write `tools/check_test_taxonomy.py`: read the registered markers, classify each test module by `pytestmark`, require a requirement citation for a `contract` module, exempt the baseline, and add a `--junit-xml` report mode that groups results by module (REQ-003, REQ-004, REQ-005; `tools/check_test_taxonomy.py`)
   - [ ] Generate `tools/test_taxonomy_baseline.txt` from the current unclassified modules (REQ-003; `tools/test_taxonomy_baseline.txt`)
   - [ ] Register the checker in `tools/TOOL_DESCRIPTIONS.md` and add its gate and `tests/` patterns (REQ-004; `tools/TOOL_DESCRIPTIONS.md`, `tools/_validation_gate_defs.py`)
2. **Phase 2: First tranche classification**
   - [ ] Add `pytestmark` to the contract modules named in the target table (REQ-003, REQ-008; `tests/agent/test_repl_input_controller.py`, `tests/agent/test_repl_shutdown_machine.py`, `tests/agent/test_http_lifecycle_command_validator.py`, `tests/agent/test_http_lifecycle_launch_spec.py`, `tests/agent/test_http_lifecycle_env_allowlist_integration.py`, `tests/agent/test_signal_handler.py`)
   - [ ] Add `pytestmark` to the characterization modules (REQ-003; `tests/agent/test_stdin_reader.py`, `tests/agent/test_http_lifecycle_stderr_log_manager.py`, `tests/shared/test_llm_client_characterization.py`, `tests/mcp_servers/shell/test_shell_mcp_service.py`)
   - [ ] Add per-test markers to the mixed modules (REQ-003; `tests/agent/test_http_lifecycle.py`, `tests/agent/test_config_builders.py`, `tests/agent/memory/test_memory_store.py`, `tests/agent/workflow/test_workflow_state_store.py`)
   - [ ] Correct the contradictory docstrings without changing any assertion (REQ-007; `tests/shared/test_llm_client_characterization.py`, `tests/mcp_servers/shell/test_shell_mcp_service.py`)
   - [ ] Record the seven disconfirmed legacy claims as corrected findings in the plan's Problem section (REQ-008; `plans/20261126-215529_cliplc012_characterization-test-split.md`)
3. **Phase 3: CI reporting and failure policy**
   - [ ] Add the checker to the CI `lint` job and the `--junitxml` plus per-suite report step to the test job (REQ-005; `.github/workflows/ci.yml`)
   - [ ] Make a characterization failure report-only and a contract failure blocking, with the baseline entry naming the owning issue (REQ-006; `.github/workflows/ci.yml`, `tools/check_test_taxonomy.py`)
   - [ ] Add the marker selection commands and the taxonomy check to the documented validation sequence (REQ-004, REQ-005; `rules/toolchain.md`)
4. **Phase 4: Documentation and convention**
   - [ ] Record the classification rule against the `verification-contract` row and add the test-taxonomy task-scope row (REQ-002; `docs/00_governance/governance_01_documentation-policy.md`, `docs/00_index.md`)
   - [ ] Record the rule in the Test structure section (REQ-002, REQ-003; `skills/python-test-and-fix/workflow.md`)
5. **Phase 5: Validation and hand-off**
   - [ ] Run T-1 through T-7 (all Requirements); `N/A: no deploy step — no `scripts/` or `config/` file is a target; `tests/` and `docs/` are rsynced by `deploy/deploy.sh` and deploying remains the user's decision after the commit is pushed`
   - [ ] Run the tool gates for the changed `tools/` and `docs/` files (REQ-004; `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_01_documentation-policy.md`, `docs/00_index.md`)

### Release units
**Unit**: taxonomy mechanism | **Phases**: 1, 3 | **Reason**: the CI lint step is validated by `tests/tools/test_run_validation_gates.py`, which fails when a CI lint command has no gate, so the checker, its gate definition, and the CI step cannot be validated independently of one another.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `pyproject.toml` | Configuration | `uv run pytest -m characterization tests/ -q` and `uv run pytest -m contract tests/ -q` | Both selections run with no unknown-marker warning |
| `tools/check_test_taxonomy.py` | Unit | `uv run pytest tests/tools/test_check_test_taxonomy.py -v` | Rule enforcement, baseline exemption, mixed-module detection pass |
| `tools/check_test_taxonomy.py` | Gate | `uv run python tools/check_test_taxonomy.py` | Reports only baseline modules as unclassified; exit 0 |
| `tools/_validation_gate_defs.py` | Unit | `uv run pytest tests/tools/test_run_validation_gates.py -v` | The new CI lint command has a gate |
| `.github/workflows/ci.yml` | Integration | `uv run pytest tests/ -n logical --cov=scripts --cov-report= --junitxml=report.xml -q` then `uv run python tools/check_test_taxonomy.py --junit-xml report.xml` | Two suite sections; coverage file unchanged and `diff-cover` still passes at 90 |
| `tests/agent/`, `tests/shared/` tranche modules | Unit | `uv run pytest tests/agent tests/shared -q` | Full suite passes with no assertion changed |
| `docs/00_governance/governance_01_documentation-policy.md`, `docs/00_index.md` | Static | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py` | No findings |
| `skills/python-test-and-fix/workflow.md` | Static | `uv run python tools/check_skill_size.py` | No finding |

## Risks
- **Risk**: a directory-based split would break the `tests/` mirrors `scripts/` rule and the ADR index test citations guarded by `tools/check_adr_invariant_matrix.py` → **Mitigation**: markers only; the decision is recorded in Unknowns as resolved (UNK-01).
- **Risk**: making characterization failures non-blocking weakens the CI gate, and `tools/compare_test_baseline.py` currently exits 1 on any new failure → **Mitigation**: limit the exemption to the characterization marker, require the baseline entry to name the owning issue, keep contract failures blocking, and obtain governance approval before the CI step is written (UNK-02).
- **Risk**: splitting the CI run would fragment coverage measurement, since `pytest-cov` combines xdist workers only within one run → **Mitigation**: single run plus JUnit XML grouping; the coverage and `diff-cover` steps are unchanged.
- **Risk**: the baseline could keep 90 modules unclassified indefinitely → **Mitigation**: the gate fails on any changed module that is not classified, and the baseline shrinks as modules are classified, following the `compare_test_baseline.py` policy.
- **Risk**: JUnit testcase ids for parametrized tests do not match AST-derived ids, so per-test grouping could misreport → **Mitigation**: group by module classname, which is the classification unit.
- **Risk**: two sources of marker registration (`pyproject.toml` and `tests/conftest.py`'s `pytest_configure`) could drift → **Mitigation**: register only in `pyproject.toml`; `tests/conftest.py` is a reference file.
- **Risk**: the new checker itself is subject to the module-size gate and the tool-inventory drift check → **Mitigation**: keep it narrow, and update `tools/TOOL_DESCRIPTIONS.md` in the same commit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: markers, checker, baseline, tool inventory, gate | In Progress | — | — | Release unit with Phase 3 |
| 2 | Phase 2: first tranche classification and docstring corrections | In Progress | — | — | No assertion changes |
| 3 | Phase 3: CI reporting and failure policy | In Progress | — | — | Needs governance approval (UNK-02) |
| 4 | Phase 4: documentation and convention updates | In Progress | — | — | Docs checkers required |
| 5 | Phase 5: validation and hand-off | In Progress | — | — | No deploy step; no `scripts/` target |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261126-232726_01_pyproject.toml.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-232726_02_tools_check_test_taxonomy.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-232726_03_tools_test_taxonomy_baseline.txt.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-232726_04_tools_TOOL_DESCRIPTIONS.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-232726_05_tools__validation_gate_defs.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-232726_06_rules_toolchain.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-232726_07_.github_workflows_ci.yml.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-232726_08_tests_tools_test_check_test_taxonomy.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-232726_09_docs_00_governance_governance_01_documentation-policy.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261126-232726_10_docs_00_index.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261126-232726_11_skills_python-test-and-fix_workflow.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261126-232726_12_tests_agent_test_stdin_reader.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_13_tests_agent_test_repl_input_controller.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_14_tests_agent_test_repl_shutdown_machine.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_15_tests_agent_test_http_lifecycle.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_16_tests_agent_test_http_lifecycle_command_validator.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_17_tests_agent_test_http_lifecycle_launch_spec.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_18_tests_agent_test_http_lifecycle_env_allowlist_integration.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_19_tests_agent_test_http_lifecycle_stderr_log_manager.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_20_tests_agent_test_signal_handler.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_21_tests_agent_test_config_builders.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_22_tests_agent_memory_test_memory_store.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_23_tests_agent_workflow_test_workflow_state_store.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_24_tests_shared_test_llm_client_characterization.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-232726_25_tests_mcp_servers_shell_test_shell_mcp_service.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-215529
- **Evidence revision**: 72c08b1c2ab9fe5c789c5cb539661d75e8073f2b
- **Related target files**: `pyproject.toml`, `tools/check_test_taxonomy.py`, `tools/test_taxonomy_baseline.txt`, `tools/TOOL_DESCRIPTIONS.md`, `tools/_validation_gate_defs.py`, `rules/toolchain.md`, `.github/workflows/ci.yml`, `tests/tools/test_check_test_taxonomy.py`, `docs/00_governance/governance_01_documentation-policy.md`, `docs/00_index.md`, `skills/python-test-and-fix/workflow.md`, `tests/agent/test_stdin_reader.py`, `tests/agent/test_repl_input_controller.py`, `tests/agent/test_repl_shutdown_machine.py`, `tests/agent/test_http_lifecycle.py`, `tests/agent/test_http_lifecycle_command_validator.py`, `tests/agent/test_http_lifecycle_launch_spec.py`, `tests/agent/test_http_lifecycle_env_allowlist_integration.py`, `tests/agent/test_http_lifecycle_stderr_log_manager.py`, `tests/agent/test_signal_handler.py`, `tests/agent/test_config_builders.py`, `tests/agent/memory/test_memory_store.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/shared/test_llm_client_characterization.py`, `tests/mcp_servers/shell/test_shell_mcp_service.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `pyproject.toml:145-148` | `pyproject.toml` | Phase 1 | AC-1 | T-1 | Confirmed by repository evidence |
| REQ-002 | Problem; `docs/00_governance/governance_01_documentation-policy.md:125` | `docs/00_governance/governance_01_documentation-policy.md` | Phase 4 | AC-6 | T-6 | Confirmed by repository evidence |
| REQ-002 | `docs/00_index.md:117-126` has no test-taxonomy row | `docs/00_index.md` | Phase 4 | AC-6 | T-6 | Confirmed by repository evidence |
| REQ-002 | `skills/python-test-and-fix/workflow.md:24-26` | `skills/python-test-and-fix/workflow.md` | Phase 4 | AC-6 | T-6 | Confirmed by repository evidence |
| REQ-003 | Required Changes; 90 unclassified modules (Step 3 count) | `tools/test_taxonomy_baseline.txt` | Phase 1 | AC-3 | T-2 | Confirmed by repository evidence |
| REQ-003 | Required Changes | `tools/check_test_taxonomy.py` | Phase 1 | AC-2, AC-3 | T-2, T-3 | Confirmed by repository evidence |
| REQ-003 | `tests/agent/test_stdin_reader.py:89,124,136` | `tests/agent/test_stdin_reader.py` | Phase 2 | AC-3 | T-7 | Confirmed by repository evidence |
| REQ-003 | `tests/agent/test_http_lifecycle.py:223` | `tests/agent/test_http_lifecycle.py` | Phase 2 | AC-3 | T-7 | Confirmed by repository evidence |
| REQ-003 | `tests/agent/test_config_builders.py:658-737` | `tests/agent/test_config_builders.py` | Phase 2 | AC-3 | T-7 | Confirmed by repository evidence |
| REQ-003 | `tests/agent/memory/test_memory_store.py:598` | `tests/agent/memory/test_memory_store.py` | Phase 2 | AC-3 | T-7 | Confirmed by repository evidence |
| REQ-003 | `tests/agent/workflow/test_workflow_state_store.py:323` | `tests/agent/workflow/test_workflow_state_store.py` | Phase 2 | AC-3 | T-7 | Confirmed by repository evidence |
| REQ-003 | `tests/agent/test_http_lifecycle_stderr_log_manager.py:145-160` | `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Phase 2 | AC-3 | T-7 | Confirmed by repository evidence |
| REQ-003 | `tests/shared/test_llm_client_characterization.py:1-8` | `tests/shared/test_llm_client_characterization.py` | Phase 2 | AC-3 | T-7 | Confirmed by repository evidence |
| REQ-003 | `tests/mcp_servers/shell/test_shell_mcp_service.py:93-96` | `tests/mcp_servers/shell/test_shell_mcp_service.py` | Phase 2 | AC-3 | T-7 | Confirmed by repository evidence |
| REQ-003 | Archived cliplc001 acceptance tests | `tests/agent/test_repl_input_controller.py` | Phase 2 | AC-3, AC-7 | T-7 | Confirmed by repository evidence |
| REQ-003 | Archived cliplc004 acceptance tests | `tests/agent/test_repl_shutdown_machine.py` | Phase 2 | AC-3, AC-7 | T-7 | Confirmed by repository evidence |
| REQ-004 | No checker reads pytest markers (Step 3 grep) | `tools/check_test_taxonomy.py` | Phase 1 | AC-2 | T-3 | Confirmed by repository evidence |
| REQ-004 | `rules/tool-gates.md` tool registration | `tools/TOOL_DESCRIPTIONS.md` | Phase 1 | AC-2 | T-3 | Confirmed by repository evidence |
| REQ-004 | `tools/_validation_gate_defs.py:650-655` | `tools/_validation_gate_defs.py` | Phase 1 | AC-2 | T-5 | Confirmed by repository evidence |
| REQ-004 | `rules/toolchain.md:107,118,125` | `rules/toolchain.md` | Phase 3 | AC-2, AC-4 | T-3, T-4 | Confirmed by repository evidence |
| REQ-005 | `.github/workflows/ci.yml:87` | `.github/workflows/ci.yml` | Phase 3 | AC-4, AC-8 | T-4, T-5 | Confirmed by repository evidence |
| REQ-005 | Report mode of the checker | `tools/check_test_taxonomy.py` | Phase 1 | AC-4 | T-4 | Derived from confirmed evidence |
| REQ-006 | Acceptance Criteria; `tools/known_test_failures_baseline.txt` header | `.github/workflows/ci.yml` | Phase 3 | AC-8 | T-5 | Explicit in issue |
| REQ-007 | Problem; `tests/shared/test_llm_client_characterization.py:1-8` | `tests/shared/test_llm_client_characterization.py` | Phase 2 | AC-5 | T-7 | Confirmed by repository evidence |
| REQ-007 | `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:67` vs `scripts/mcp_servers/shell/shell_service.py:342-350` | `tests/mcp_servers/shell/test_shell_mcp_service.py` | Phase 2 | AC-5 | T-7 | Confirmed by repository evidence |
| REQ-008 | Acceptance Criteria; seven legacy claims disconfirmed in Step 2 | `tests/agent/test_http_lifecycle_command_validator.py` | Phase 2 | AC-7 | T-7 | Confirmed by repository evidence |
| REQ-008 | `scripts/agent/http_lifecycle.py:411-444` | `tests/agent/test_http_lifecycle_launch_spec.py` | Phase 2 | AC-7 | T-7 | Confirmed by repository evidence |
| REQ-008 | `tests/agent/test_http_lifecycle_env_allowlist_integration.py:3` (docstring citation) and `:262-464` (gates) | `tests/agent/test_http_lifecycle_env_allowlist_integration.py` | Phase 2 | AC-7 | T-7 | Confirmed by repository evidence |
| REQ-008 | `tests/agent/test_signal_handler.py:171,235,246` | `tests/agent/test_signal_handler.py` | Phase 2 | AC-7 | T-7 | Confirmed by repository evidence |
| REQ-008 | Step 2 findings recorded as corrected findings | `plans/20261126-215529_cliplc012_characterization-test-split.md` | Phase 2 | AC-7 | N/A: documentation record, no test | Confirmed by repository evidence |
| REQ-003 | Test module for the checker | `tests/tools/test_check_test_taxonomy.py` | Phase 1 | AC-2, AC-3 | T-2 | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261126-232726 -->