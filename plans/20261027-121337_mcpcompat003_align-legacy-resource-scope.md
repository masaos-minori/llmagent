# Align the legacy resource_scope statement and the schema-2.0 validator contract

## Goal
- Make the document, the validator, and the discovery path state the same contract:
  a legacy singular `resource_scope` on a tool entry is explicitly rejected as a schema
  error, and presence of all four mandatory schema-2.0 fields is enforced in exactly one
  place — `shared/resource_scope.py::validate_tool_schema_v2()`.

## Priority
Medium

## Scope
- **In-Scope**:
  - Legacy policy (owner-decided 2026-10-27: **explicit rejection**): the validator
    returns a problem string for any entry carrying a singular `resource_scope` key.
  - Presence-check single-sourcing (owner-decided 2026-10-27: **move all four presence
    checks into the validator**): the validator rejects a missing
    `resource_scope_kind` / `resource_scope_keys` instead of defaulting `""` / `[]`; the
    fetch layer's `_REQUIRED_SCHEMA_V2_FIELDS` pre-check is retired and the fetch layer
    relies on the validator's result.
  - Test updates: rewrite the synthetic ignore-test as a rejection test; add validator
    tests for the two missing-field rejections and the legacy-key rejection.
  - Rewrite the one document sentence in `docs/22_mcp/mcp_03_02_tool-registry.md`.
- **Out-of-Scope**:
  - Changing `_KNOWN_SCOPE_KINDS` membership or scope-conflict logic.
  - Posture gating and the Health re-export (mcpcompat001).
  - Registry building (`mcp_tool_discovery_registry.py` direct indexing stays; its
    guarantee now comes from the validator instead of the fetch pre-check).
  - Finding severity handling (WARNING/FATAL escalation unchanged).
  - Other schema fields.
- **Dependencies**: No fix-order dependency. The Issue's optional
  `tools/check_compat_shims.py` guard is dropped (not requested by the owner). Shared
  docs directory with mcpcompat001 but different files; shared-file overlap with the
  mcpcompat001 Plan is read-only on the fetch/registry modules (recorded in
  `Assumptions`).

## Background
Source: `memo-issue.md` items H-03 and M-03 (responsibility part). Verified against
current source on 2026-10-27; the Issue's claims all confirmed:

- `docs/22_mcp/mcp_03_02_tool-registry.md` line 70 states "`status`, legacy singular
  `resource_scope`, and `enabled` are validated only if present" — no code validates a
  singular `resource_scope` on a tool entry.
- `scripts/agent/services/mcp_tool_discovery_fetch.py`:
  `_REQUIRED_SCHEMA_V2_FIELDS` (lines 44-48) pre-checks all four mandatory fields
  (consolidated "missing required schema-2.0 field(s)" message), then
  `_entry_schema_error()` (lines 212-238) calls `validate_tool_schema_v2()`.
  `_entry_optional_field_error()` (lines 240-261) validates `status` (str), `enabled`
  (bool), `capabilities` (list) only if present.
- `scripts/shared/resource_scope.py::validate_tool_schema_v2()` (lines 126-177) requires
  `is_write`/`requires_serial` but defaults `resource_scope_kind` to `""` (a legal member
  of `_KNOWN_SCOPE_KINDS`) and `resource_scope_keys` to `[]` — contradicting its own
  docstring "Never coerces or defaults a missing/mistyped field".
- `scripts/agent/services/mcp_tool_discovery_registry.py` (lines 86-89, 109-110) indexes
  the four fields directly, relying on the fetch-layer guarantee.
- Existing tests pin the current split behavior:
  `tests/agent/services/test_mcp_tool_discovery.py::test_resource_scope_field_ignored_after_removal_synthetic`
  asserts an entry with `resource_scope: 123` passes through into the registry unchanged.
- Verification of the Issue's unknowns:
  - UNK-02 resolved: every deployed MCP server is an in-tree module under
    `scripts/mcp_servers/` (confirmed against `/opt/llm/config/agent.toml`); none emits a
    singular `resource_scope` (repo-wide grep: only audit/scheduler/test hits, no server
    tool lists).
  - UNK-03 resolved: `tests/mcp_servers/test_tool_schema_contract.py` validates all 13
    in-tree `TOOL_LIST` modules through `validate_tool_schema_v2()`; every entry declares
    all four fields, so the validator hardening cannot break the contract test.
  - No test asserts the exact consolidated "missing required schema-2.0 field(s)" message
    text; `test_runtime_tool_routing_integration.py::test_incomplete_tool_declaration_excluded_from_routing`
    asserts exclusion only, not wording. Message consolidation therefore only touches
    message format, not assertions.
- Owner decisions recorded 2026-10-27: explicit rejection of the legacy field; presence
  checks single-sourced in the validator.

## Problem
Three artifacts disagree: the document promises validation of a field no code checks; the
validator's docstring forbids defaulting while it defaults two fields; and presence
enforcement is duplicated across fetch layer and validator, so a validator-only caller
accepts entries the Discovery path rejects.

## Reason for Change
A validation contract that differs per caller is a latent acceptance hole: any future
caller of the "last line of defense" would silently accept incomplete tool declarations.
Fixing the contract in one place also makes the document sentence true.

## Implementation Intent
Harden `validate_tool_schema_v2()` to be the single contract point: reject a singular
`resource_scope` key with an explicit problem string naming it as a removed legacy field,
and report missing `resource_scope_kind` / `resource_scope_keys` as required-field
problems (keeping `""` and `[]` as legal explicit values). Retire the fetch layer's
four-field pre-check constant and its branch so missing fields surface through the
validator's per-field strings exactly once. Update the three test files that pin the old
behavior, and rewrite the document sentence to state the adopted policy and where presence
is enforced.

## Requirements
- `REQ-001`: `validate_tool_schema_v2()` returns a problem string when the entry contains
  a singular `resource_scope` key (policy: legacy field rejected, migration mistakes
  visible).
- `REQ-002`: `validate_tool_schema_v2()` reports a missing `resource_scope_kind` or
  missing `resource_scope_keys` as a required-field problem; explicit `""` / `[]` remain
  valid; the docstring and implementation agree.
- `REQ-003`: The fetch layer no longer duplicates presence checks:
  `_REQUIRED_SCHEMA_V2_FIELDS` and its missing-fields branch are removed; a missing field
  produces exactly one finding per entry via the validator's `failed schema-2.0
  validation` message.
- `REQ-004`: Registry building is untouched; its docstring note (lines 109-110) remains
  true because the validator now guarantees presence.
- `REQ-005`: Tests cover the new behavior: legacy-key rejection, missing scope-field
  rejection, and a discovery-path test showing an entry with a singular
  `resource_scope` is excluded with a finding.
- `REQ-006`: `docs/22_mcp/mcp_03_02_tool-registry.md` states: the four fields are
  mandatory and their presence is enforced by `validate_tool_schema_v2()`; a singular
  `resource_scope` is rejected as a removed legacy field; `status` and `enabled` remain
  validated only if present.
- `REQ-007`: Severity behavior is unchanged: the rejection finding routes through the
  existing per-entry WARNING/FATAL escalation (FATAL under strict), and duplicate-name
  handling is untouched.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/resource_scope.py | Legacy singular `resource_scope` rejection; presence checks for all four fields; docstring becomes literally true | REQ-001, REQ-002 | REQ-001, REQ-002 / AC-01, AC-02 | lines 126-177 (verified) | tests/shared/test_resource_scope.py | Verified |
| scripts/agent/services/mcp_tool_discovery_fetch.py | Remove `_REQUIRED_SCHEMA_V2_FIELDS` pre-check and branch; validator is the single presence gate | REQ-003 | REQ-003 / AC-03 | lines 44-48, 222-228 (verified) | tests/agent/services/test_mcp_tool_discovery.py | Verified |
| tests/shared/test_resource_scope.py | Add `TestValidateToolSchemaV2` cases: missing scope fields rejected, legacy key rejected | REQ-001, REQ-002, REQ-005 | REQ-005 / AC-05 | class lines 155-224 (verified, no such cases today) | itself | Verified |
| tests/agent/services/test_mcp_tool_discovery.py | Rewrite `test_resource_scope_field_ignored_after_removal_synthetic` into a rejection/exclusion test | REQ-005, REQ-007 | REQ-005 / AC-05 | lines 1173-1250 (verified) | itself | Verified |
| tests/agent/services/test_runtime_tool_routing_integration.py | Verify the incomplete-declaration test still passes under validator-sourced messages; adjust message expectations only if any (none found) | REQ-003, REQ-007 | REQ-003 / AC-03 | lines 322-340 (verified) | itself | Verified |
| docs/22_mcp/mcp_03_02_tool-registry.md | Rewrite the line-70 sentence: legacy-field policy + enforcement point | REQ-006 | REQ-006 / AC-06 | line 70 (verified) | check_docs_consistency.py | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/services/mcp_tool_discovery_registry.py | Confirms direct indexing (lines 86-89) and the guarantee note (lines 109-110) stay valid; not modified | REQ-004 |
| scripts/agent/services/mcp_tool_discovery.py | Entry findings flow and severity escalation unchanged | REQ-007 |
| tests/mcp_servers/test_tool_schema_contract.py | Contract re-run proves all 13 in-tree TOOL_LISTs pass the hardened validator; not modified | REQ-002 |
| tests/agent/services/test_mcp_tool_discovery.py (lines 1150-1171) | TOOL_LIST sanity check referencing singular `resource_scope` as a guard; reviewed for consistency with rejection policy | REQ-005 |
| scripts/shared/runtime_tool.py | `build_runtime_tool` defaults remain untouched (defaults belong to the builder, not the validator) | REQ-004 |
| docs/00_index.md | Task-scope mapping for the doc edit | REQ-006 |

## Acceptance Criteria
- `AC-01` (REQ-001): `validate_tool_schema_v2({..., "resource_scope": "filesystem"})`
  returns a problem string naming `resource_scope` as removed/legacy; covered by a unit
  test and a discovery-path exclusion test.
- `AC-02` (REQ-002): an entry missing `resource_scope_kind` or `resource_scope_keys`
  returns a required-field problem string; explicit `""`/`[]` still validate clean; the
  docstring's "never defaults" claim matches the code.
- `AC-03` (REQ-003): `_REQUIRED_SCHEMA_V2_FIELDS` no longer exists in
  `mcp_tool_discovery_fetch.py`; a missing field yields exactly one finding string per
  entry (no double reporting).
- `AC-04` (REQ-004): `git diff` shows no change to the registry module or
  `build_runtime_tool`.
- `AC-05` (REQ-005): new tests exist in `tests/shared/test_resource_scope.py` and the
  rewritten synthetic discovery test asserts exclusion + finding, including the
  `resource_scope: 123` (non-string) case now rejected by key presence, not type.
- `AC-06` (REQ-006): the document no longer says the legacy field is "validated only if
  present"; it states rejection and the validator as the enforcement point.
- `AC-07` (REQ-007): severity outcomes for missing/invalid fields are unchanged
  (WARNING non-strict, FATAL strict) and duplicate-name FATAL behavior is unchanged.

## Tests
- `REQ-001`/`REQ-002`/`REQ-005`: new `TestValidateToolSchemaV2` cases in
  `tests/shared/test_resource_scope.py` (legacy key present → problem; each scope field
  missing → problem; explicit `""`/`[]` → clean).
- `REQ-005`/`REQ-007`: rewritten discovery test in
  `tests/agent/services/test_mcp_tool_discovery.py`: entry with singular
  `resource_scope` → excluded from `result.registry`, one finding under
  `result.findings`.
- `REQ-003`: `tests/agent/services/test_runtime_tool_routing_integration.py`'s
  incomplete-declaration test re-run as the regression for the removed pre-check.
- Regression run: `uv run pytest tests/shared/test_resource_scope.py
  tests/mcp_servers/test_tool_schema_contract.py tests/agent/services -q`, then the full
  suite.

## Documentation Impact
Yes: `docs/22_mcp/mcp_03_02_tool-registry.md` (REQ-006), named via `docs/00_index.md`
task scope for MCP tool registry/discovery. Rewrite the validation-rule sentence only:
legacy-field policy, enforcement point, unchanged four-field requirement. Responsibility
boundaries (fetch module owns `/v1/tools` fetch and entry validation; registry module owns
duplicate exclusion and build) are already stated at line 70 of the same sentence group —
verified, so no additional boundary sentences are needed.

## Assumptions
- Owner decisions (2026-10-27): explicit rejection; presence single-sourced in the
  validator. This closes the Issue's UNK-01.
- `""` (unscoped) and `[]` remain legal explicit values — the rejection is for absence of
  the key, not for empty values (preserves `test_accepts_empty_resource_scope_kind_and_keys`).
- No deployed server emits the legacy field (verified in Background), so rejection cannot
  turn a working production server's tools into findings.
- Cross-plan overlap: the mcpcompat001 Plan lists
  `scripts/agent/services/mcp_tool_discovery_registry.py` as a read-only Reference File
  and edits `mcp_tool_discovery.py` (service) — no edit collision with this Plan's fetch/
  registry targets. `docs/22_mcp/` is shared with mcpcompat001 but the files differ
  (`mcp_03_02` vs `mcp_03_03`). This doc has 20 commits in 30d — rebase before editing.
- No checker rule in `tools/check_compat_shims.py` is added (owner did not request the
  optional guard), so no overlap with ebcompat002 (retention branch, checker untouched) or
  mcpcompat001 (no checker edit) exists there.
- Overlap adjudication (2026-10-27 overlap-tool run): `tests/agent/services/test_runtime_tool_routing_integration.py`
  is also edited by the mcpcompat001 Plan (gate maps at the discovery constructions,
  lines 313/347); this Plan touches only the incomplete-declaration test. Compatible;
  rebase between edits.
- Overlap adjudication with the mcpcompat001 Plan: `scripts/agent/services/mcp_tool_discovery_registry.py`
  is a read-only Reference File in mcpcompat001 and a no-edit reference here — Compatible.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | The Issue's three unresolved questions are resolved: legacy policy = explicit rejection (owner, 2026-10-27); external/deployed emitters = none (all servers in-tree, verified); contract test coverage = confirmed (13 modules validated through the validator) | — | — | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/resource_scope.py | Validator hardening | discovery path + contract test (13 TOOL_LISTs) | 0 | low | No deploy.sh change; agent + MCP server file sync and restart not required (validator runs agent-side only) — restart of agent service after deploy |
| scripts/agent/services/mcp_tool_discovery_fetch.py | Pre-check removal | startup discovery | 1 | medium | No deploy.sh change; agent restart |
| tests (3 files) | Behavior re-pinning | test suite | 0-6 | n/a | None |
| docs/22_mcp/mcp_03_02_tool-registry.md | One sentence rewrite | docs | 20 | medium | None |

## Design
- Single enforcement point: `validate_tool_schema_v2()` becomes the whole entry contract —
  presence, types, known kinds, key/inputSchema coherence, and legacy-field rejection. The
  fetch layer keeps response-shape checks (list, schema_version, name/description/
  inputSchema basic types) and optional-field checks (`status`, `enabled`,
  `capabilities`), which are genuinely "only if present" concerns.
- Failure surfacing is unchanged: validator problem strings flow through
  `_entry_schema_error`'s "failed schema-2.0 validation" finding into the existing
  severity escalation; the consolidated missing-fields message is retired, so missing-field
  findings change wording but not status or count-per-entry (one finding per bad entry is
  preserved because `_validate_entry` returns at the first error).
- Registry and builder defaults (`build_runtime_tool`'s optional parameters) are left
  as-is: defaults there serve non-discovery callers (local tool registration), not the
  discovery contract.

## Implementation steps
1. **Phase 1: Validator hardening**
   - [ ] Add legacy `resource_scope` key rejection and the two missing-field presence checks; keep docstring accurate (REQ-001, REQ-002; scripts/shared/resource_scope.py)
   - [ ] Add the corresponding `TestValidateToolSchemaV2` cases (REQ-005; tests/shared/test_resource_scope.py)
2. **Phase 2: Fetch-layer single-sourcing**
   - [ ] Remove `_REQUIRED_SCHEMA_V2_FIELDS` and its branch in `_entry_schema_error` (REQ-003; scripts/agent/services/mcp_tool_discovery_fetch.py)
   - [ ] Rewrite the synthetic legacy-field test as an exclusion+finding test (REQ-005, REQ-007; tests/agent/services/test_mcp_tool_discovery.py)
   - [ ] Re-run the incomplete-declaration routing test and adjust only if message-dependent (REQ-003; tests/agent/services/test_runtime_tool_routing_integration.py)
3. **Phase 3: Verification & docs**
   - [ ] `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/test_tool_schema_contract.py tests/agent/services -q` then full suite; mypy, ruff, lint-imports (REQ-002, REQ-003)
   - [ ] Rewrite the document sentence (REQ-006; docs/22_mcp/mcp_03_02_tool-registry.md)
   - [ ] `check_docs_consistency.py --domain mcp` + docs quality/structure checkers (REQ-006)
   - [ ] Deployment check: sync changed scripts to /opt/llm, restart agent service, confirm startup log shows `mcp_tool_discovery` OK (operational check; no deploy.sh change)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/resource_scope.py | Unit | `uv run pytest tests/shared/test_resource_scope.py -q` | legacy-key and missing-field rejections pass; explicit `""`/`[]` clean |
| tests/mcp_servers/test_tool_schema_contract.py | Contract regression | `uv run pytest tests/mcp_servers/test_tool_schema_contract.py -q` | all 13 in-tree TOOL_LISTs pass the hardened validator |
| scripts/agent/services/mcp_tool_discovery_fetch.py | Integration (discovery tests) | `uv run pytest tests/agent/services -q` | exclusion behavior preserved, one finding per bad entry, severity unchanged |
| whole repo | Static | `uv run ruff check scripts tests`; `uv run mypy --no-namespace-packages scripts`; `PYTHONPATH=scripts uv run lint-imports` | clean; `eventbus`/layer contracts unaffected |
| docs/22_mcp/mcp_03_02_tool-registry.md | Docs checkers | `uv run python tools/check_docs_consistency.py --domain mcp` plus quality/structure checkers | pass |

## Risks
- **Risk**: an out-of-tree server emitting the legacy field starts failing discovery →
  **Mitigation**: verified all deployed servers are in-tree (Background); the rejection
  produces a per-tool finding, not a crash, and is visible in the startup pipeline.
- **Risk**: retiring the consolidated missing-field message hides which field was missing →
  **Mitigation**: the validator's per-field strings name each field explicitly
  ("is_write is required", "resource_scope_keys is required"); per-entry finding count is
  unchanged.
- **Risk**: `docs/22_mcp/mcp_03_02_tool-registry.md` is high-churn (20 commits/30d) and
  shared with parallel Plans → **Mitigation**: rebase onto latest master immediately
  before the doc edit; sentence-scoped change only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: validator hardening | Pending | — | — | |
| 2 | Phase 2: fetch-layer single-sourcing | Pending | — | — | |
| 3 | Phase 3: verification & docs | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-104324_mcpcompat003_align-legacy-resource-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-121337
- **Related target files**: scripts/shared/resource_scope.py, scripts/agent/services/mcp_tool_discovery_fetch.py, tests/shared/test_resource_scope.py, tests/agent/services/test_mcp_tool_discovery.py, tests/agent/services/test_runtime_tool_routing_integration.py, docs/22_mcp/mcp_03_02_tool-registry.md

### Requirement Traceability
| Requirement | Source | Plan Section | Target File | Test / Validation | Status |
|---|---|---|---|---|---|
| REQ-001 | issues/20261027-104324 (Implementation Intent, owner decision) | Design, Target Files row 1 | scripts/shared/resource_scope.py | unit + discovery tests, AC-01 | Planned |
| REQ-002 | issues/20261027-104324 (Problem, owner decision) | Target Files rows 1, 3 | scripts/shared/resource_scope.py, tests/shared/test_resource_scope.py | AC-02 | Planned |
| REQ-003 | issues/20261027-104324 (Required Changes) | Target Files rows 2, 5 | scripts/agent/services/mcp_tool_discovery_fetch.py | discovery + routing tests, AC-03 | Planned |
| REQ-004 | issues/20261027-104324 (AI Implementation Instruction) | Reference Files | N/A (no edit) | AC-04 git-diff pin | Planned |
| REQ-005 | issues/20261027-104324 (Required Changes) | Tests | test files rows 3-5 | AC-05 | Planned |
| REQ-006 | issues/20261027-104324 (Documentation Impact) | Documentation Impact | docs/22_mcp/mcp_03_02_tool-registry.md | docs checkers, AC-06 | Planned |
| REQ-007 | issues/20261027-104324 (Constraints) | Design | scripts/agent/services/mcp_tool_discovery_fetch.py | severity assertions, AC-07 | Planned |
