# Plan: Verify the reduced `agent.toml` end to end and document the migration

## Goal
- Prove the reduced standard `config/agent.toml` is the deployment contract through integration tests against the real file, and complete the operability layer: a single-source migration mapping, fatal validation errors that name each removed key's replacement, and a documented key reference with the explicit-default policy.

## Priority
Medium

## Scope
- **In-Scope**:
  - Integration tests that start the agent with the real reduced `config/agent.toml` (startup, MCP discovery, approval, plan mode, reload, Memory, database maintenance).
  - A migration mapping (old key → new key or owning file) as a single source in the production validator, emitted as a generated reference-table block and used verbatim by the fatal validation error.
  - Per-key configuration reference documentation (owner process, type, unit, default, reloadability, restart requirement) and the explicit-values-equal-code-defaults policy statement.
  - A long-TOML-comment lint tool and its CI wiring.
- **Out-of-Scope**: The individual reductions of agentcfg001 through agentcfg005 (already landed; this Plan only verifies and documents the result).
- **Dependencies**: All five earlier issues must land before this Plan is implemented. Adversarial verification confirms agentcfg003, agentcfg004, and agentcfg005 are Completed, and agentcfg001/agentcfg002 code behavior is present in current source; their Plans still carry non-`Completed` rows (documentation/test/gate steps), recorded as Unknown UNK-04.
  - **Depends on**: plans/done/20261120-123941_agentcfg001_tool-policy-mode.md | phase all | the mode-aware runtime policy and typed fields must land before the end-to-end check is meaningful
  - **Depends on**: plans/done/20261120-151418_agentcfg002_tool-catalog-registry.md | phase all | the tool-catalog ownership split must land before the ownership-uniqueness acceptance criterion is verifiable
  - **Depends on**: plans/done/20261121-105007_agentcfg003_runtime-tool-metadata.md | phase all | producer-declared metadata must land before schema/inventory sources can be called unique
  - **Depends on**: plans/done/20261121-140444_agentcfg004_config-ownership-split.md | phase all | the config ownership split must land before the RAG Pipeline MCP starts from its own file
  - **Depends on**: plans/done/20261122-162618_agentcfg005_system-prompt-snapshot.md | phase all | the prompt-source snapshot must land before reload-path verification is valid

## Background
Source: consolidated `agent.toml` reduction backlog (memo-issue.md, Issue 6). The reduction changed tool visibility, schema discovery, approval, plan mode, required capabilities, Memory embedding, database maintenance, and reload together, so unit tests alone may not expose a mismatch in a real deployment. The Issue's open question about integration-test coverage is now resolved: no test under `tests/integration/` reads the real `config/agent.toml`; the existing tests that load it (`tests/agent/test_production_config_validator.py`, `tests/shared/test_config_validator.py`, `tests/agent/test_config_effective_snapshot.py`, `tests/docs/test_github_config_consistency.py`) are unit-level single-point checks, not a startup-path verification (checked in Step 2).

## Problem
Without an end-to-end check and a migration reference, an operator with an old configuration gets an unknown-key failure with no guidance — the current validator emits a generic `Unknown config keys: ...` error that names keys but never the replacement (`scripts/agent/production_config_validator.py` lines 263-274, checked in Step 2) — and the meaning of retained explicit defaults is undocumented. The migration table does not exist under `docs/23_agent/` (checked in Step 2), and no tool polices long TOML comments (checked in Step 2).

## Reason for Change
Verification and operability of the whole reduction; it can only be done after the earlier issues land. All five landed as code; the remaining gaps are the verification harness, the migration reference, the migration error message, and the comment lint.

## Implementation Intent
Quality is measured by the number of duplicated sources and ownership violations, not by TOML line count. The real standard file is validated strictly (already true today — the existing tests pass against the live file, checked in Step 2), an old key produces a specific migration message at startup, and the reference lists owner process, type, unit, default, reloadability, and restart requirement for each key.

## Requirements
- `REQ-001`: Add integration tests that start startup validation, MCP discovery, approval, plan mode, reload, Memory, and database maintenance against the real reduced `config/agent.toml`.
- `REQ-002`: Hold the old-key → new-key/owner mapping as a single source in the production validator, and emit the migration table from it as a guarded generated block in the Agent configuration reference.
- `REQ-003`: Make each removed key a fatal validation error that names its replacement, reading the mapping from REQ-002's single source.
- `REQ-004`: Document owner process, type, unit, default, reloadability, and restart requirement for each key, and state the policy of keeping explicit values equal to code defaults.
- `REQ-005`: Add a lint tool that flags long TOML comments in `config/`.
- `REQ-006`: Run the REQ-005 lint in CI. The unknown-key CI check already exists (CI runs the full pytest suite, which includes the real-file validator tests — `(.github/workflows/ci.yml)` line 83, checked in Step 2); no duplicate CI job is added.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed for all rows; the pre-freeze path audit `tools/audit_plan_target_paths.py` flagged only the rows marked `Create`, which state create, and the post-freeze overlap check reported no conflicts. See `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).
Amended 2026-11-22 (scope): added tools/_agent_config_migration.py — check_drift() resolves a doc-backed domain through _RENDER_MANIFEST, so a domain registered only in DOMAIN_GENERATORS is not covered by --check; and generate_reference_table.py's recorded baseline equals its current 50404 B, so any growth fails the check-module-size-tools gate
Amended 2026-11-22 (scope): added registry/manifests/agent_config_migration.yaml — check_drift() verifies a doc-backed domain against its committed manifest, so the generated migration table cannot be covered by --check without the manifest artifact
Amended 2026-11-22 (scope): added tools/_validation_gate_defs.py — drift_report() requires a mapping entry for every row of rules/tool-gates.md's 'When to run which tool' table, so the new tool cannot be registered as a gate row without a Gate entry here

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/integration/test_standard_config_integration.py` | Create | New integration test covering startup, MCP discovery, approval, plan mode, reload, Memory, and database maintenance against the real `config/agent.toml` | REQ-001 / AC-1, AC-2, AC-5 | No integration test references the real file today; `tests/integration/` contains only fixture-based tests (`test_production_security_regression.py` uses a hand-built config dict, checked in Step 2) | Self (its own test cases); runs in CI via full pytest | Verified |
| `scripts/agent/production_config_validator.py` | Modify | Emit a fatal error naming the replacement for each key in `_REMOVED_PRODUCTION_KEYS` (REQ-003); the mapping defined here is the single source consumed by the generator (REQ-002) | REQ-002, REQ-003 / AC-4 | Current message is `Unknown config keys: {list}` with no replacement guidance (lines 263-274, checked in Step 2); existing message-substring assertions in three test files constrain the format, including lines 467 and 494 which assert the prefix against mapped keys (see Design D3, corrected by Step 3a) | `tests/agent/test_production_config_validator.py` | Verified |
| `tests/agent/test_production_config_validator.py` | Modify | Add assertions that the error names the replacement for each removed key; keep existing message-substring assertions valid | REQ-003 / AC-4 | Existing assertions at lines 188-265 pin the `Unknown config keys` class name (checked in Step 3, predictable-fallout pinned-count hit) | Self | Verified |
| `tools/generate_reference_table.py` | Modify | Register the agent-config-key domain so `--check` covers it; the generator body and table renderer live in `tools/_agent_config_migration.py` | REQ-002 | `DOMAIN_GENERATORS` has no agent-config-key generator today; existing types (rag, deployment, mandatoriness) read live sources (checked in Step 2); `--check` runs in CI per `tools/TOOL_DESCRIPTIONS.md`. Implementation-cycle Step 3a (2026-11-22): `check_drift()` resolves a doc-backed domain through `_RENDER_MANIFEST[domain]` (line 1058), so the domain must go through the contract-manifest path, and the file's recorded baseline equals its current 50404 B, so any growth fails the `check-module-size-tools` gate → owner decision: register the domain through the manifest path and keep the generator in the new helper module | `tests/tools/test_generate_reference_table.py` | Verified |
| `tests/tools/test_generate_reference_table.py` | Modify | Cover the new generator type and its `--check` behavior | REQ-002 | File exists and tests the existing generator contract (checked in Step 3) | Self | Verified |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Modify | Destination of the generated migration table (REQ-002, AC-5 single place) and of the per-key reference plus the explicit-default policy statement (REQ-004) | REQ-002, REQ-004 / AC-5 | The document owns the Agent configuration-file-ownership and reload-classification tables (lines 38-39, checked in Step 2); no migration section exists in any `agent_08_*` file (checked in Step 2) | `tools/generate_reference_table.py --check` for the generated block; `tools/check_docs_consistency.py` for prose | Verified |
| `tools/check_config_comment_length.py` | Create | Long-TOML-comment lint for `config/` (REQ-005); no existing tool polices TOML comments, so it cannot be an extension | REQ-005 | The `tools/` inventory and `tools/TOOL_DESCRIPTIONS.md` contain no config-comment checker (checked in Step 2) | `tests/tools/test_check_config_comment_length.py` | Verified |
| `tests/tools/test_check_config_comment_length.py` | Create | Unit tests for the lint tool (finding codes, exit codes, allowlist behavior) | REQ-005 | Mirrors the existing `tests/tools/` test convention (e.g. `tests/tools/test_generate_reference_table.py` exists, checked in Step 3) | Self | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Register the new tool's row (predictable-fallout tool-inventory hit; `check_tool_descriptions_sync.py`) | REQ-005 | New `tools/*.py` requires a row in the same change (`routing.md` Tools, Adding a new tool) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |
| `.github/workflows/ci.yml` | Modify | Run the new lint tool in CI (REQ-006) | REQ-006 | CI already runs the full pytest suite (line 83, checked in Step 2), so only the new tool needs a CI step | N/A: CI job itself | Verified |
| `rules/tool-gates.md` | Modify | Add the new checker to "When to run which tool" per `routing.md` Tools step 5 | REQ-005 | `rules/tool-gates.md` exists and defines the path-keyed gate rows that `tools/run_validation_gates.py` executes (checked in Step 3); implementation-cycle Step 3a (2026-11-22) found that `drift_report()` requires a mapping entry for every row of that table (`run_validation_gates.py` lines 519-530), so `tools/_validation_gate_defs.py` needs a `Gate` entry for the new tool — recorded as an additional target file row below (owner-approved, class `scope`). The tool is CI-triggered, so no pre-commit hook is added | `uv run python tools/run_validation_gates.py drift` | Verified |
| `tools/_agent_config_migration.py` | New file: helper module that reads the validator's migration mapping and renders the agent-config migration table | check_drift() resolves a doc-backed domain through _RENDER_MANIFEST, so a domain registered only in DOMAIN_GENERATORS is not covered by --check; and generate_reference_table.py's recorded baseline equals its current 50404 B, so any growth fails the check-module-size-tools gate | REQ-002 / N/A: none cites REQ-002 | tools/generate_reference_table.py line 1058 (_RENDER_MANIFEST[domain]) and lines 1118-1131 (check_drift); tools/check_module_size_tools_baseline.txt records generate_reference_table.py at 50404 B; tools/_contract_manifests.py is the existing helper-module pattern | tests/tools/test_generate_reference_table.py | Verified |
| `registry/manifests/agent_config_migration.yaml` | New file: committed contract manifest for the agent-config migration domain | check_drift() verifies a doc-backed domain against its committed manifest, so the generated migration table cannot be covered by --check without the manifest artifact | REQ-002 / N/A: none cites REQ-002 | tools/generate_reference_table.py check_drift() lines 1118-1131 and _manifest_entries() line 1058 resolve a doc-backed domain through _RENDER_MANIFEST; registry/manifests/ holds the committed artifacts CI compares with 'git diff --exit-code registry/manifests/' (ci.yml line 37) | tests/tools/test_generate_reference_table.py | Verified |
| `tools/_validation_gate_defs.py` | Add the Gate mapping entry for the new comment-length checker | drift_report() requires a mapping entry for every row of rules/tool-gates.md's 'When to run which tool' table, so the new tool cannot be registered as a gate row without a Gate entry here | REQ-005 / N/A: none cites REQ-005 | tools/run_validation_gates.py drift_report() lines 519-530 compares the table rows against ROUTING_GATES; existing rows such as check_db_separation (line 154) and generate_reference_table_check (line 413) each have a Gate entry | uv run python tools/run_validation_gates.py drift | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `config/agent.toml` | The reduced standard file under test; its keys define the migration table content | REQ-001, REQ-002, REQ-004 |
| `config/rag_pipeline_mcp_server.toml` | Confirms the RAG Pipeline MCP starts from its own file (AC-2) | REQ-001 |
| `config/tool_catalog.toml` | The ownership/capability registry; required-capability check reads it (AC-5 ownership source) | REQ-001, REQ-004 |
| `tests/integration/test_production_security_regression.py` | Existing integration test asserting the unknown-key error; shows the fixture pattern and the message format that must not break | REQ-003; design D3 |
| `tests/shared/test_shared_boundary_conditions.py` | Line 179 pins the `Unknown config keys` message format for a removed key; the format design must keep it passing | REQ-003; design D3 |
| `tests/shared/test_config_validator.py` | Line 173 is the existing real-file validation test that already satisfies AC-1 at unit level | REQ-001 baseline |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | The ADR governing unknown-key rejection; any change to that behavior needs a maintainer approval record in the same change (Constraint) | REQ-003, ADR constraint |
| `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` | Documents that removed settings are rejected as unknown production keys; the migration message must stay consistent with it | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001): The standard `agent.toml` passes strict validation. Verified as already true today (the existing real-file tests pass, checked in Step 2); the new integration test must re-assert it through the startup path.
- `AC-2` (REQ-001): The Agent reads only the settings it needs, and the RAG Pipeline MCP starts from `config/rag_pipeline_mcp_server.toml`.
- `AC-3` (REQ-002, REQ-004): The sources of tool schema, inventory, and safety metadata are documented and unique — the migration table exists in exactly one place (the generated block) and the reference names the owner for each key.
- `AC-4` (REQ-003): An old key causes a startup error with specific migration guidance naming the replacement.
- `AC-5` (REQ-002): The reduction removed duplicated ownership; it did not merely omit values — the generated table shows each removed key's owner, and the validator reads the same single mapping.

## Tests
- `REQ-001`: `tests/integration/test_standard_config_integration.py` — startup validation, MCP discovery, approval, plan mode, reload, Memory, and database maintenance against the real files; `integration` marker.
- `REQ-002`: `tests/tools/test_generate_reference_table.py` — the new generator type and `--check` drift detection.
- `REQ-003`: `tests/agent/test_production_config_validator.py` — per-removed-key error naming the replacement; existing assertions must keep passing.
- `REQ-004`: N/A: documentation-only requirement; verified by the doc checkers in the Validation plan.
- `REQ-005`: `tests/tools/test_check_config_comment_length.py` — unit tests for the lint.
- `REQ-006`: N/A: the CI job itself; the lint tool's own tests cover its logic, and CI executes the tool.

## Documentation Impact
Yes. The Agent configuration reference is `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` (located via `docs/00_index.md` → Agent spec / configuration docs); it receives the generated migration table (REQ-002), the per-key reference, and the explicit-default policy statement (REQ-004). The migration table lives in one place only, per `skills/DESIGN.md` Docs content policy, and the reference does not copy values that the generator already owns. `rules/tool-gates.md` receives the new checker row (REQ-005). Run the doc checkers listed in `routing.md` Tools after the edits.

## Assumptions
- The reduced standard file remains as it is today: no `config/agent.toml` change is planned; the file already passes strict validation (falsifiable by re-running the existing real-file tests).
- The migration error format emits a per-key message naming the replacement for mapped keys, so the existing message-substring assertions stay passing. Corrected by Step 3a adversarial verification (2026-11-22): the earlier claim that those assertions pass only unmapped fixtures through the generic path is false — `tests/agent/test_production_config_validator.py` lines 188-265 and lines 467, 494 pass mapped keys (`tool_safety_tiers` and the other `_REMOVED_PRODUCTION_KEYS`) through the validation path and assert the `Unknown config keys` prefix plus the key name, and `tests/shared/test_shared_boundary_conditions.py` line 179 and `tests/integration/test_production_security_regression.py` line 50 assert the prefix against `tool_safety_tiers`. Therefore the per-key message must keep the `Unknown config keys` prefix AND name the replacement (design D3, corrected).
- The single source of the migration mapping is a module-level mapping in `scripts/agent/production_config_validator.py`; the generator and the error message read the same mapping, satisfying the Current-Specification-Only policy.
- The unknown-key CI check is satisfied by the existing full-pytest CI job; no duplicate CI check is added (only the new comment lint is wired).
- Overlap note (Step 8b): `scripts/agent/production_config_validator.py` and `tests/agent/test_production_config_validator.py` are also targeted by the Frozen plan mcpdl003 (dedup-config-isolation). Judged compatible: that plan extends the valid-key table for the new Agent key and per-server `[dedup]` tables, while this Plan adds the removed-key migration message and its tests; the two designs do not contradict each other on the shared files. No sequencing dependency is required; the implementation order between them is free.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Location and generator of the configuration reference (Issue's open question) | None remaining — resolved: the Agent configuration reference exists as `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` (checked in Step 2); `tools/generate_reference_table.py` has no agent-config-key generator type (checked in Step 2), so the plan extends the existing generator (Design D1) | Resolved by repository evidence (Step 2); decision recorded in Design D1 | False |
| UNK-02 | Whether the long-comment lint is a new tool or an extension of an existing check | None remaining — resolved: no existing tool polices `config/` TOML comments (TOOL_DESCRIPTIONS inventory and `tools/` listing, checked in Step 2), so it is a new `tools/` script | Resolved by repository evidence (Step 2); the Issue's "prefer extending existing tools" instruction cannot apply when nothing exists to extend | False |
| UNK-03 | Which integration tests already cover startup with the real `config/agent.toml` | None remaining — resolved: none do; existing real-file coverage is unit-level only (checked in Step 2), which is the gap REQ-001 closes | Resolved by repository evidence (Step 2) | False |
| UNK-04 | agentcfg001 and agentcfg002 Plans still have non-`Completed` Execution Status rows | Rows for their documentation/test/validation steps are open, while their code behavior is present in current source (`tool_policy_mode` field at `scripts/agent/config_dataclasses.py` line 198; `config/tool_catalog.toml` exists; required-capability FATAL gate at `scripts/agent/services/mcp_tool_discovery.py` lines 266-271; `tool_names` absent from `scripts/shared/mcp_config.py`; checked in Step 2), and the full suite passes 13315 / 5 skipped | Complete those Plans' remaining steps; this Plan is not gated on them because its targets do not read those Plans' outputs as unfinished behavior | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here is a subset of `Implementation Target Files`' rows. `Bus Factor`: `git-fame` is not installed on this host, so all rows are `N/A`.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/integration/test_standard_config_integration.py` | Create | Low | N/A (new file) | N/A | not applicable (rsynced) |
| `scripts/agent/production_config_validator.py` | Modify | Medium — called by `scripts/agent/config_builders.py` and `scripts/agent/startup_validation.py` and by 8 test modules (dependency graphing, Step 5) | 15 | N/A | not applicable (rsynced) |
| `tests/agent/test_production_config_validator.py` | Modify | Low | N/A (not in top churn list; message-format assertions pin the target) | N/A | not applicable (rsynced) |
| `tools/generate_reference_table.py` | Modify | Medium — runs in CI with `--check`; writes guarded blocks into docs | 9 | N/A | not applicable (rsynced) |
| `tests/tools/test_generate_reference_table.py` | Modify | Low | N/A (not in top churn list) | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Modify | Low — guarded generated block plus prose sections | 2 | N/A | not applicable (rsynced) |
| `tools/check_config_comment_length.py` | Create | Low | N/A (new file) | N/A | not applicable (rsynced) |
| `tests/tools/test_check_config_comment_length.py` | Create | Low | N/A (new file) | N/A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low (registry file; checked by `check_tool_descriptions_sync.py`) | 74 | N/A | not applicable (rsynced) |
| `.github/workflows/ci.yml` | Modify | Low | 9 | N/A | not applicable (rsynced) |
| `rules/tool-gates.md` | Modify | Low | N/A (not in top churn list) | N/A | not applicable (rsynced) |
| `tools/_agent_config_migration.py` | Create | Not assessed (amendment 2026-11-22) | N/A | N/A | Not assessed (amendment 2026-11-22) |
| `registry/manifests/agent_config_migration.yaml` | Create | Not assessed (amendment 2026-11-22) | N/A | N/A | Not assessed (amendment 2026-11-22) |
| `tools/_validation_gate_defs.py` | Modify | Not assessed (amendment 2026-11-22) | N/A | N/A | Not assessed (amendment 2026-11-22) |

## Design

### Architecture analysis
- `scripts/agent/production_config_validator.py` imports only `agent.services.config_validators`, `shared.component_mandatoriness`, `shared.config_validator`, stdlib, and typing (Step 5). Adding a module-level mapping constant keeps it within the `agent` layer; no import-cycle risk: `tools/` is not part of the `.importlinter` contract graph, and `tests/conftest.py` puts both `scripts/` and `tools/` on `sys.path`, so `tools/generate_reference_table.py` can import the mapping the way it already reads `scripts/db/config.py`.
- No module-boundary, interface, or data-model change beyond the error-message content; no persisted-schema change (`rules/persisted-schema-change.md` not applicable).

### Dependency graphing
- Consumers of the changed symbol `_check_unknown_production_keys`: only `scripts/agent/production_config_validator.py` itself (its own `validate()` path) plus ADR test citations; callers of `ProductionConfigValidator` are `scripts/agent/config_builders.py` and `scripts/agent/startup_validation.py` and 8 test modules (`tools/scan_change_consumers.py`, Step 3). None of them asserts the exact full message text beyond the `Unknown config keys` prefix, so the prefix-preserving format in Assumptions keeps all consumers valid.
- Predictable fallout check (Step 3): module size — `scripts/agent/production_config_validator.py` is 14050 B, below the 24576 B gate, so a message addition does not trigger a split row; `tools/generate_reference_table.py` (50404 B) is already under the `check_module_size_tools_baseline.txt` exemption, and no new code is added to it beyond the generator entry. Pinned counts — the three message-substring tests listed in Assumptions. Tool inventory — the new tool requires the `tools/TOOL_DESCRIPTIONS.md` row. Generated blocks — the new generator type must be included in `generate_reference_table.py --check`, already wired in CI.
- Consumer scan candidates recorded above: ADR docs citations (`docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`) and `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` are reference rows, not affected as targets (documentation text describes existing behavior that stays true).

### Historical analysis
Churn (30d) per target is in the `Affected areas` table (Step 5 command). The validator is the highest-churn real target (15); the new files carry no history. No regression is described, so `git bisect` is not used.

### Operational dependency inspection
The change runs offline only; no service port or DB lock is involved in the planning path, and the Issue's constraint forbids production-affecting checks against `/opt/llm`, so no `ss`/`fuser` check was run against production. CI execution of the new lint tool is a workflow-file addition, not a running-process change.

### Validation quality baseline (Step 5)
- `radon cc scripts/agent/production_config_validator.py -s`: highest complexity A(3) on `_check_unknown_production_keys`; no existing grade above A for the touched paths.
- `vulture` on the target: no findings. `bandit` on the target (`-c pyproject.toml`): no findings.
- Full suite baseline: 13315 passed, 5 skipped, 0 failures (run this cycle). diff-cover: no changed Python lines yet, so no current percentage to record; the plan's validation steps must keep diff-cover at the `rules/toolchain.md` threshold (90) as new code lands.

### Design decisions
- D1 — Migration table location and generator (resolves UNK-01): the single normative source is a module-level mapping in `scripts/agent/production_config_validator.py`; `tools/generate_reference_table.py` gains one generator type that renders that mapping into a guarded block in `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`. Alternatives considered: a hand-maintained table in the doc (rejected: duplicates the source the error message already reads, violating the single-place policy); a new standalone tool (rejected: the existing generator infrastructure already owns config tables and `--check`).
- D2 — Long-comment lint (resolves UNK-02): a new `tools/check_config_comment_length.py`; no existing checker polices `config/` comments. It reports findings as warnings (exit 0) or errors by a single threshold constant, follows the existing `tools/` checker shape, and needs the `tools/TOOL_DESCRIPTIONS.md` row and a `rules/tool-gates.md` row.
- D3 — Error format (keeps consumers valid): every removed key produces a per-key fatal error that keeps the `Unknown config keys` prefix and names the replacement, e.g. `Unknown config keys: <key> — replaced by <new key or owning file>`; unmapped keys keep the existing generic message unchanged. The single-message variant listing all keys plus a migration suffix was rejected because AC-4 requires a specific per-key message. Corrected by Step 3a (2026-11-22): the earlier form (`Removed config key '<key>': replaced by ...` without the prefix) was rejected as infeasible because the pinned assertions listed in Assumptions pass mapped keys through the validation path and assert the prefix plus the key name; the prefix-preserving per-key form satisfies AC-4 and keeps all three test files passing. `tests/agent/test_production_config_validator.py` gains per-key replacement assertions.

## Implementation steps

1. **Phase 1: Single-source migration mapping and fatal migration error**
   - [ ] Define the old-key → replacement mapping as a module-level constant in `scripts/agent/production_config_validator.py` (REQ-002 single source; REQ-003).
   - [ ] Change the removed-key path to emit the per-key fatal message naming the replacement; keep the generic `Unknown config keys` path for unmapped keys (REQ-003; design D3).
   - [ ] Add per-removed-key assertions in `tests/agent/test_production_config_validator.py` without altering existing passing assertions (REQ-003, AC-4).
2. **Phase 2: End-to-end integration tests against the real standard file**
   - [ ] Create `tests/integration/test_standard_config_integration.py` covering startup validation, MCP discovery, approval, plan mode, reload, Memory, and database maintenance against `config/agent.toml` and `config/rag_pipeline_mcp_server.toml` (REQ-001, AC-1, AC-2); the file must not touch `/opt/llm` (Constraint).
3. **Phase 3: Long-comment lint tool and CI wiring**
   - [ ] Create `tools/check_config_comment_length.py` per design D2 (REQ-005).
   - [ ] Create `tests/tools/test_check_config_comment_length.py` (REQ-005).
   - [ ] Add the tool row to `tools/TOOL_DESCRIPTIONS.md` and the gate row to `rules/tool-gates.md` in the same change (REQ-005); run `check_tool_descriptions_sync.py` and `run_validation_gates.py drift`.
   - [ ] Add the CI step to `.github/workflows/ci.yml` (REQ-006). Do not add a duplicate unknown-key CI job (already covered, REQ-006).
   - [ ] Add the Gate mapping entry for the new comment-length checker (REQ-005; `tools/_validation_gate_defs.py`) — amendment 2026-11-22
4. **Phase 4: Generated migration table and key reference documentation** (release unit RU-1 with Phase 5)
   - [ ] Add the generator type and its `--check` coverage in `tools/generate_reference_table.py` reading the Phase 1 mapping (REQ-002).
   - [ ] Add tests to `tests/tools/test_generate_reference_table.py` (REQ-002).
   - [ ] New file: helper module that reads the validator's migration mapping and renders the agent-config migration table (REQ-002; `tools/_agent_config_migration.py`) — amendment 2026-11-22
   - [ ] New file: committed contract manifest for the agent-config migration domain (REQ-002; `registry/manifests/agent_config_migration.yaml`) — amendment 2026-11-22
5. **Phase 5: Documentation content** (release unit RU-1 with Phase 4)
   - [ ] Insert the guarded generated migration-table block in `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` (REQ-002, AC-5).
   - [ ] Write the per-key reference (owner process, type, unit, default, reloadability, restart requirement) and the explicit-values-equal-code-defaults policy statement in the same document (REQ-004, AC-3). The reference does not copy values that the generator already owns (`skills/DESIGN.md` Docs content policy).
6. **Phase 6: Validation and deployment hand-off**
   - [ ] Run the full validation sequence (`rules/toolchain.md` order) including `tools/generate_reference_table.py --check`, `check_tool_descriptions_sync.py`, the Agent-domain doc checker, and diff-cover at the threshold (all REQs).
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md`: prerequisite — the change is committed and pushed first; deploying is the user's decision (approval gate). No `deploy.sh` cp line changes (all rows are rsynced).

### Release units
**Unit**: RU-1 generator-and-generated-block | **Phases**: 4, 5 | **Reason**: `generate_reference_table.py --check` fails until both the generator type and the guarded block in the target doc exist; the phases cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/production_config_validator.py` | Unit | `uv run ruff format`, `ruff check --fix`, `uv run mypy`, `uv run bandit`, then `uv run pytest tests/agent/test_production_config_validator.py` | Clean; new per-key replacement assertions pass; existing message assertions pass |
| `tests/integration/test_standard_config_integration.py` | Integration | `uv run pytest tests/integration/ -m integration` | All startup/discovery/approval/plan-mode/reload/Memory/maintenance tests pass against the real files |
| `tools/generate_reference_table.py` | Unit + generated-block check | `uv run pytest tests/tools/test_generate_reference_table.py`; `uv run python tools/generate_reference_table.py --check` | New generator tests pass; `--check` exits 0 with the block present |
| `tools/check_config_comment_length.py` | Unit + tool sequence | `routing.md` Tools sequence (ruff, mypy, bandit, manual smoke run on live `config/`) | Clean on the live files only through the allowlist. Step 3a (implementation cycle, 2026-11-22): the zero-findings premise did not hold — 8 `config/` files already carry comment blocks over 5 consecutive comment lines (max 23, `config/tool_catalog.toml`). Owner decision: threshold = 5 consecutive comment lines, and the 8 existing blocks are recorded as allowlist exceptions; the CI step gates only after the allowlist makes the live run clean. |
| `tools/TOOL_DESCRIPTIONS.md`, `rules/tool-gates.md` | Sync gate | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/run_validation_gates.py drift` | No drift |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Doc checkers | Agent-domain doc checker per `rules/tool-gates.md` | No findings |
| Whole suite | Regression | `uv run pytest` full sequence per `rules/toolchain.md`, diff-cover ≥ 90 | No failures beyond the recorded baseline (13315 passed, 5 skipped) |

## Risks
- **Risk**: Changing the unknown-key error text breaks the existing message-substring assertions → **Mitigation**: design D3 (corrected) keeps the `Unknown config keys` prefix for every removed key while naming the replacement per key; run `tests/agent/test_production_config_validator.py` (lines 188-265, 467, 494), `tests/shared/test_shared_boundary_conditions.py`, and `tests/integration/test_production_security_regression.py` before the message change is finalized.
- **Risk**: The migration-error behavior touches the unknown-key rejection governed by ADR-002 (platform config isolation); a change to that decision or invariant needs a maintainer approval record in the same change → **Mitigation**: the plan only adds guidance to the existing fatal path, not a policy change; if the implementer finds the message change to be an ADR decision change, stop and request the approval record. Do not write or simulate an ADR approval.
- **Risk**: agentcfg001/agentcfg002 carry open Plan rows (their doc/test/gate steps); a later change from those Plans could alter the behavior this Plan verifies → **Mitigation**: this Plan targets only its own frozen rows; the open dependencies are recorded (UNK-04, Scope). If a test fails because of an unfinished earlier issue, stop and report per the Issue's AI Implementation Instruction.
- **Risk**: The new generator type adds a CI `--check` domain that can drift against live config → **Mitigation**: it reads the validator mapping as the single source, so the error message and the table cannot diverge; `--check` runs in CI.
- **Risk**: Long-comment lint false positives on intentional denylist comments (e.g. `plan_blocked_tools`) → **Mitigation**: give the tool a documented allowlist following the `tools/compat_exceptions.toml` pattern, tuned to zero findings on live `config/` before it gates CI. Implementation-cycle Step 3a found the live `config/` already exceeds the threshold in 8 files, so the allowlist is the mechanism that keeps the gate green; it is not a hypothetical false-positive guard.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migration mapping constant and per-key fatal message in the validator; tests | Completed | 2026-11-22 | 2026-11-22 | `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py` mapping constant + per-key message; per-key assertions added; pinned files pass |
| 2 | Integration test against the real standard files | Completed | 2026-11-22 | 2026-11-22 | `tests/integration/test_standard_config_integration.py` integration module implemented and passing against the real config/ files |
| 3 | Long-comment lint tool, its tests, tool/gate registration, CI wiring | Completed | 2026-11-22 | 2026-11-23 | `tools/check_config_comment_length.py`, `tests/tools/test_check_config_comment_length.py`, `tools/TOOL_DESCRIPTIONS.md`, `rules/tool-gates.md`, `.github/workflows/ci.yml`, `tools/_validation_gate_defs.py`. Live run reports 8 warnings (the blocks present at plan freeze) and exits 0; `run_validation_gates.py drift` reports all rows mapped |
| 4 | Generator type and `--check` coverage (RU-1) | Completed | 2026-11-22 | 2026-11-23 | `tools/generate_reference_table.py`, `tests/tools/test_generate_reference_table.py`, `tools/_agent_config_migration.py`, `registry/manifests/agent_config_migration.yaml`. `--check` reports no drift. **Additional target file discovered**: `schemas/contract_manifest.json` needed the `agent_config_migration` name and entry shape; it is not a row of the frozen table, so the change is recorded in procedure seq 13 and is pending the owner's decision on adding the row |
| 5 | Generated block, per-key reference, explicit-default policy in the doc (RU-1) | Completed | 2026-11-23 | 2026-11-23 | `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`: guarded block regenerated, per-key reference for all 130 key lines, and the explicit-values-equal-code-defaults policy statement. Four doc checkers clean. **Conflict recorded**: REQ-004's per-key table is a mechanical field/type/default table, which `check_docs_content_policy.py` `check_field_type_table` flags as a WARNING under `--strict` |
| 6 | Validation sequence and deployment hand-off | In Progress | 2026-11-23 | — | `rules/toolchain.md` gates pass (mypy, ruff, format, bandit, import contracts, full pytest 95% TOTAL, diff-cover on the changed lines, pre-commit). Deployment hand-off per `skills/deploy/SKILL.md` not performed: no production access was used in this cycle |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261122-192217_01_tests_integration_test_standard_config_integration_py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261122-192217_02_scripts_agent_production_config_validator_py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261122-192217_04_tools_generate_reference_table_py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261122-192217_06_docs_23_agent_agent_08_01_configuration-loading-agent-config.md.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261122-192217_07_tools_check_config_comment_length_py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261122-192217_09_tools_TOOL_DESCRIPTIONS_md.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261122-192217_10_.github_workflows_ci_yml.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261122-192217_11_rules_tool-gates_md.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261122-201558_12_tools__agent_config_migration.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261122-201558_13_registry_manifests_agent_config_migration.yaml.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261122-201558_14_tools__validation_gate_defs.py.md` | 3 | Procedure | Completed | — | — |

## Traceability
- **Source issue**: issues/done/20261120-114214_agentcfg006_reduction-integration-verification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261122-190238
- **Related target files**: `tests/integration/test_standard_config_integration.py`, `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`, `tools/generate_reference_table.py`, `tests/tools/test_generate_reference_table.py`, `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`, `tools/check_config_comment_length.py`, `tests/tools/test_check_config_comment_length.py`, `tools/TOOL_DESCRIPTIONS.md`, `.github/workflows/ci.yml`, `rules/tool-gates.md`, `tools/_agent_config_migration.py`, `registry/manifests/agent_config_migration.yaml`, `tools/_validation_gate_defs.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes / Acceptance Criteria; Step 2 confirmed no integration test reads the real file | `tests/integration/test_standard_config_integration.py` | 2 | AC-1, AC-2 | Self + full suite | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes; Step 2 confirmed no migration table in `docs/23_agent/` and no agent-config generator type | `scripts/agent/production_config_validator.py` | 1 | AC-5 | `tests/agent/test_production_config_validator.py` | Confirmed by repository evidence |
| REQ-002 | Design D1 decision (generator extension); Issue Testing Expectations | `tools/generate_reference_table.py` | 4 | AC-5 | `tests/tools/test_generate_reference_table.py` | Confirmed by repository evidence |
| REQ-002 | Generator test coverage for the new type | `tests/tools/test_generate_reference_table.py` | 4 | AC-5 | Self + `--check` | Confirmed by repository evidence |
| REQ-002 | Single-place policy (`skills/DESIGN.md` Docs content policy) | `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | 5 | AC-5 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes; Step 2 confirmed the generic message names no replacement (validator lines 263-274) | `scripts/agent/production_config_validator.py` | 1 | AC-4 | `tests/agent/test_production_config_validator.py` | Confirmed by repository evidence |
| REQ-003 | New per-key assertions; existing passing assertions preserved | `tests/agent/test_production_config_validator.py` | 1 | AC-4 | Self | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes; the doc is the Agent configuration reference located via `docs/00_index.md` | `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | 5 | AC-3 | Agent-domain doc checker | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes; Step 2 confirmed no existing comment-lint tool (new tool, resolving UNK-02) | `tools/check_config_comment_length.py` | 3 | N/A: verified through the tool's tests and CI | `tests/tools/test_check_config_comment_length.py` | Confirmed by repository evidence |
| REQ-005 | Tool inventory row required by `routing.md` Tools step 5 | `tools/TOOL_DESCRIPTIONS.md` | 3 | N/A | `check_tool_descriptions_sync.py` | Confirmed by repository evidence |
| REQ-005 | Gate registration required by `routing.md` Tools step 5 | `rules/tool-gates.md` | 3 | N/A | `run_validation_gates.py drift` | Confirmed by repository evidence |
| REQ-006 | Issue Required Changes; Step 2 resolved the unknown-key CI check as already covered by CI's full pytest job (line 83); only the new lint is wired | `.github/workflows/ci.yml` | 3 | N/A | CI execution | Confirmed by repository evidence |
| REQ-006 | New tool tests executed by CI | `tests/tools/test_check_config_comment_length.py` | 3 | N/A | Self | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-22: check_drift() resolves a doc-backed domain through _RENDER_MANIFEST, so a domain registered only in DOMAIN_GENERATORS is not covered by --check; and generate_reference_table.py's recorded baseline equals its current 50404 B, so any growth fails the check-module-size-tools gate | tools/_agent_config_migration.py | Phase 4 | N/A: none cites REQ-002 | tests/tools/test_generate_reference_table.py | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-22: check_drift() verifies a doc-backed domain against its committed manifest, so the generated migration table cannot be covered by --check without the manifest artifact | registry/manifests/agent_config_migration.yaml | Phase 4 | N/A: none cites REQ-002 | tests/tools/test_generate_reference_table.py | Confirmed by repository evidence |
| REQ-005 | Amendment 2026-11-22: drift_report() requires a mapping entry for every row of rules/tool-gates.md's 'When to run which tool' table, so the new tool cannot be registered as a gate row without a Gate entry here | tools/_validation_gate_defs.py | Phase 3 | N/A: none cites REQ-005 | uv run python tools/run_validation_gates.py drift | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261122-201558 -->