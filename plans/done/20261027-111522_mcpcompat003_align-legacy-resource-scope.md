## Goal
- Make the schema-2.0 validator, the discovery fetch layer, the tests and the MCP tool-registry document state one contract: the validator itself enforces presence of the four mandatory fields, a legacy singular `resource_scope` field is handled by an owner-approved policy, and the document no longer claims that the legacy field is "validated only if present".

## Priority
Medium

## Scope
- **In-Scope**:
  - Record the owner-approved legacy `resource_scope` policy (explicit rejection recommended, or ignore and document as unsupported) before implementation.
  - Make `validate_tool_schema_v2()` enforce presence of `is_write`, `requires_serial`, `resource_scope_kind` and `resource_scope_keys` so that its docstring ("never coerces or defaults") is true, while keeping empty values (`""`, `[]`) valid.
  - Make the fetch layer report the validator's result once instead of running its own presence pre-check, so a missing field is not reported twice.
  - Implement the approved legacy policy with a test that uses an entry carrying a singular `resource_scope`.
  - Rewrite the document sentence that claims the legacy field is validated.
- **Out-of-Scope**:
  - Changing the set of known scope kinds or the scope-conflict logic.
  - Posture gating and the Health re-export (the `mcpcompat001` Plan).
  - Schema fields other than the four mandatory fields and the legacy `resource_scope`.
  - Registry building (`mcp_tool_discovery_registry.py`) and finding severity handling.
- **Dependencies**: Sequencing only, no hard ordering. `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md` also edits `tests/agent/services/test_mcp_tool_discovery.py` (it passes gates at 60 constructor calls); implement its test phase first or rebase, because both edit the same file in different places. Its document edit targets a different file of `docs/22_mcp/`.

## Background
- The document sentence is verbatim: "`status`, legacy singular `resource_scope`, and `enabled` are validated only if present." The code validates only `status`, `enabled` and `capabilities` in `_entry_optional_field_error()`; no code reads or validates a singular `resource_scope` key.
- The existing test `test_resource_scope_field_ignored_after_removal_synthetic` in `tests/agent/services/test_mcp_tool_discovery.py` records the current behavior on purpose: its docstring says "resource_scope is no longer a valid field; entries containing it should pass", it feeds `resource_scope` values `123` and `"filesystem"`, and it asserts the entries are registered and no finding mentions `resource_scope`. The issue's recommended explicit rejection therefore reverses a behavior that a test documents.
- The fetch layer checks all four mandatory fields for presence (`_REQUIRED_SCHEMA_V2_FIELDS`) and reports "missing required schema-2.0 field(s)" before calling the validator; the registry indexes the four fields directly. The validator requires `is_write` and `requires_serial` itself, but reads `resource_scope_kind` with default `""` and `resource_scope_keys` with default `[]`, although its docstring says it never defaults a missing field. The empty kind `""` is a member of the known kinds.
- The validator is called only by the fetch layer and by tests. The contract test `test_all_tools_pass_schema_v2_contract` calls the validator alone, so today it does not assert presence of the two scope fields; a runtime check of 56 in-tree tool entries found all four fields present and no legacy key. Two tool-list modules (`mcp_servers.github.tools_repository`, `mcp_servers.web_search.web_search_tools`) could not be imported outside the test environment.
- The existing validator test `test_accepts_empty_resource_scope_kind_and_keys` sets the values explicitly to `""` and `[]`, so it stays valid when presence becomes mandatory. No test asserts the fetch-layer wording "missing required schema-2.0 field".

## Problem
- The document states a validation of the legacy field that does not exist, and the code and a test record a different behavior (ignore).
- Required-field enforcement is split: two fields in the validator, all four in the fetch layer. A caller that uses the validator alone, such as the contract test, accepts entries that the Discovery path rejects, and the validator's documented contract is not its actual contract.

## Reason for Change
A documentation and code mismatch about a validation rule, and a validator whose documented contract is not its actual contract. It is non-critical because the production Discovery path is already strict, hence Medium, and it is not time-sensitive.

## Implementation Intent
Single-source the mandatory-field check in the validator, the last line of defense, and let the fetch layer report its result once. Put any legacy-field rejection in the validator too, so one module owns the schema-2.0 contract of a raw entry. Keep new checks in small helper functions because `validate_tool_schema_v2` is already rated C (17) for complexity. Treat the legacy-field policy as an owner sign-off gate before implementation; the Plan covers both outcomes (reject: the validator reports the legacy key and the test that expects acceptance is changed; ignore: no code change and the document and test wording state it as unsupported). Rewrite the document sentence to state the adopted policy and where presence is enforced.

## Requirements
- `REQ-001`: Record the repository owner's decision on the legacy singular `resource_scope` policy (explicit rejection or ignore as unsupported) on this Plan before any code change.
- `REQ-002`: Make `validate_tool_schema_v2()` report a missing `resource_scope_kind` or `resource_scope_keys` (in addition to the two it already requires), keep empty values valid, and make its docstring and behavior agree.
- `REQ-003`: Make the fetch layer use the validator's result for field presence and remove its separate presence pre-check, so each missing field is reported once, with the exclusion and severity behavior unchanged.
- `REQ-004`: Implement the approved legacy policy and cover it with a test that uses an entry carrying a singular `resource_scope`, changing `test_resource_scope_field_ignored_after_removal_synthetic` together with the code if rejection is approved.
- `REQ-005`: Add validator tests for a missing `resource_scope_kind`, a missing `resource_scope_keys` and accepted empty values, a discovery test that a missing field is reported once, and confirm that the contract test passes for every in-tree tool list.
- `REQ-006`: Rewrite the document sentence so that it no longer says the legacy field is "validated only if present", states the adopted policy and the unchanged four-field requirement, and names where presence is enforced.
- `REQ-007`: Keep a tool with a missing or invalid field excluded from the registry, keep finding severity unchanged, and leave the type check, the import-layer check, the test suite and the documentation checkers passing.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8's
Implementation Target Files Validation — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/resource_scope.py` | Schema-2.0 entry validator | Enforce presence of the four mandatory fields, apply the legacy policy, align docstring and behavior | REQ-002, REQ-004; AC-2, AC-4 | `validate_tool_schema_v2` requires `is_write` and `requires_serial`, reads the kind with default `""` and the keys with default `[]`, and its docstring says it never defaults a missing field; cyclomatic complexity C (17) (checked in Step 3) | `tests/shared/test_resource_scope.py` | Verified |
| `scripts/agent/services/mcp_tool_discovery_fetch.py` | Discovery fetch and entry validation | Remove the separate presence pre-check and report the validator's result once | REQ-003; AC-3 | `_entry_schema_error` lists missing fields from `_REQUIRED_SCHEMA_V2_FIELDS` before calling the validator; `_entry_optional_field_error` validates only `status`, `enabled` and `capabilities` (checked in Step 3) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `tests/shared/test_resource_scope.py` | Validator tests | Add tests for missing kind, missing keys and accepted empty values, and for the legacy key under the approved policy | REQ-004, REQ-005; AC-4, AC-5 | `_valid_entry()` carries all four fields; existing tests cover a missing `is_write` and `requires_serial` and the explicit empty values (checked in Step 3) | `tests/shared/test_resource_scope.py` | Verified |
| `tests/agent/services/test_mcp_tool_discovery.py` | Discovery service tests | Change `test_resource_scope_field_ignored_after_removal_synthetic` if rejection is approved, add a single-report test for a missing field | REQ-004, REQ-005; AC-4, AC-5 | The test feeds `resource_scope` `123` and `"filesystem"` and asserts the entries are registered and no finding mentions the field; a live-server helper in the same file asserts that a present `resource_scope` is a string (checked in Step 3) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `docs/22_mcp/mcp_03_02_tool-registry.md` | MCP tool registry document | Rewrite the sentence that claims the legacy field is validated | REQ-006; AC-6 | The `RuntimeToolRegistry` and Live Discovery paragraph ends with "`status`, legacy singular `resource_scope`, and `enabled` are validated only if present." (checked in Step 3) | N/A: documentation-only; `tools/check_docs_consistency.py --domain mcp` | Verified |

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
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/services/mcp_tool_discovery_registry.py` | Indexes the four fields directly after validation; must stay consistent | REQ-002, REQ-003 |
| `tests/mcp_servers/test_tool_schema_contract.py` | Contract test that calls the validator on every in-tree tool list; no change expected once the validator enforces presence | REQ-005 |
| `tests/mcp_servers/test_tool_schema.py` | Narrower pre-schema-2.0 presence check of file and git modules | REQ-005 |
| `docs/22_mcp/mcp_06_11_new-tool-registration-procedure.md` | States the four mandatory fields for new tools; must stay consistent with the adopted policy | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001): The owner's legacy-policy decision is recorded on this Plan before any code change.
- AC-2 (REQ-002): `validate_tool_schema_v2()` on an entry that lacks `resource_scope_kind` or `resource_scope_keys` reports that field as required, an entry with `""` and `[]` is still valid, and the docstring and implementation agree.
- AC-3 (REQ-003): A tool that lacks a mandatory field is excluded and the finding names the field once; finding severity is unchanged.
- AC-4 (REQ-004): An entry carrying a singular `resource_scope` behaves as the approved policy states and a test covers it.
- AC-5 (REQ-005): The validator and discovery tests described under REQ-005 pass, and the contract test passes for every in-tree tool list.
- AC-6 (REQ-006): The document no longer says the legacy singular `resource_scope` is "validated only if present", and states the adopted policy and the four-field requirement.
- AC-7 (REQ-007): The checks listed under Tests pass.

## Tests
- `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/test_tool_schema_contract.py tests/mcp_servers/test_tool_schema.py tests/agent/services -q` (REQ-002 to REQ-005).
- `uv run pytest` (full suite), `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run ruff format` and `uv run ruff check` on changed files, `uv run bandit` on changed scripts (REQ-007).
- `uv run python tools/check_docs_consistency.py --domain mcp`, `check_docs_quality.py`, `check_docs_structure.py` on the changed document, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` (REQ-006).
- A diff-cover run per `rules/toolchain.md` (REQ-007).

## Documentation Impact
Yes. The MCP tool-registry document (located through `docs/00_index.md` "Document References by Task") changes: the stated validation rule, the legacy-field policy and where mandatory-field presence is enforced (responsibility boundary only); REQ-006 drives it. Optionally one sentence each on the fetch module and the registry module, only if the current text lacks them (not verified; the text beyond the edited paragraph was not read). Do not copy implementation detail into the document (`skills/DESIGN.md` Docs content policy). All text is written in English.

## Assumptions
- Presence enforcement in the validator is safe for production: the fetch layer already rejects entries that lack any of the four fields, so the Discovery path does not become stricter, only the validator-only callers do.
- All in-tree tool lists satisfy the four-field contract; this was verified at runtime for 56 entries and is confirmed for the two environment-dependent modules by the contract test (UNK-03).
- No test asserts the current fetch-layer wording for a missing field, so the wording may follow the validator's.
- Step 8b overlap judgment: `tests/agent/services/test_mcp_tool_discovery.py` is also targeted by `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`; the designs are compatible (that Plan changes the constructor calls to pass gates at 60 call sites, this Plan changes one legacy-field test and adds a single-report test) and the edits only need sequencing, recorded in Scope Dependencies and UNK-04.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which legacy `resource_scope` policy does the owner approve: explicit rejection (recommended by the issue) or ignore as unsupported (the behavior the existing test records)? | No owner decision | Record the repository owner's decision as a comment on this Plan before implementation, per the sign-off channel of `rules/coding.md` Explicit sign-off gates; the Plan covers both outcomes | False |
| UNK-02 | Does an external or deployed MCP server still emit a singular `resource_scope`? Only in-tree definitions were searched | Deployed servers are outside the repository | The repository owner confirms before approving rejection; ignore needs no such confirmation | False |
| UNK-03 | Do the two environment-dependent tool-list modules satisfy the four-field contract? | They could not be imported outside the test environment | Run `tests/mcp_servers/test_tool_schema_contract.py` in Phase 1 before and after the validator change | False |
| UNK-04 | Implementation order against the `mcpcompat001` Plan, which also edits `tests/agent/services/test_mcp_tool_discovery.py` | The sibling Plan is not yet implemented | Implement its test phase first or rebase; the implementation-procedure phase reads this Plan's Scope Dependencies | False |

## Decision record
- 2026-10-28 (procedure-generation session, owner-approved): UNK-01 resolved — the legacy singular
  `resource_scope` policy is explicit rejection: `validate_tool_schema_v2()` reports an entry carrying
  the key as a schema error. UNK-02 is covered by the same approval: the owner accepts the exclusion
  risk for external or deployed emitters. The ignore alternative is not adopted. REQ-001 and AC-1 are
  satisfied by this record.

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/resource_scope.py` | Modify | Medium | 0 | 1 author (1y), flagged as high | not applicable (rsynced) |
| `scripts/agent/services/mcp_tool_discovery_fetch.py` | Modify | Medium | 1 | 1 author (1y), flagged as high | not applicable (rsynced) |
| `tests/shared/test_resource_scope.py` | Modify | Low | 0 | 1 author (1y), flagged as high | not applicable (rsynced) |
| `tests/agent/services/test_mcp_tool_discovery.py` | Modify | Medium | 6 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_02_tool-registry.md` | Modify | Low | 20 | 2 authors (1y), share not measured | not applicable (rsynced) |

## Design
- Path B: five target files and a stricter validator contract. Architecture: `shared.resource_scope` is a shared-layer module imported by the agent fetch layer, so the dependency direction stays agent to shared; six import-layer contracts were kept before the change. Dependency graphing: `validate_tool_schema_v2` is called only by the fetch layer and by tests, and the registry indexes the four fields directly after validation, so the stricter validator affects no production caller beyond the fetch layer. Historical analysis: churn in 30 days is 0 and 1 for the two source files and 20 for the document, so the document edit is one sentence and is rebased carefully. Operational dependency inspection: not applicable (no process, port or database change).
- Validation baseline: `radon cc` rates `validate_tool_schema_v2` C (17) and `resolve_resource_scope` C (11), and several fetch functions B, so the new presence and legacy checks go into small helper functions and must not raise the validator's rating; `vulture scripts/ --min-confidence 80` reports 17 findings, none in the target files; `bandit` reports no issue on the two scripts; `lint-imports` reports six contracts kept; the MCP documentation consistency check passes. The diff-cover baseline was not run in planning (a full coverage run is too costly); the implementation phase runs it against the threshold of `rules/toolchain.md`.
- Decision (single source): the validator owns all schema-2.0 presence checks, as the issue prefers, because it is documented as the last line of defense. Alternative rejected: keeping the fetch pre-check and documenting presence as the caller's responsibility, which leaves validator-only callers such as the contract test unprotected.
- Decision (legacy field location): if rejection is approved it lives in the validator, so one module owns the entry contract. Alternative rejected: rejecting in the fetch layer only, which would again leave validator-only callers unprotected.
- Open decision (legacy policy): an owner sign-off gate (UNK-01) before implementation; the existing test is the recorded evidence for "ignore", and the issue's recommendation is "reject".
- Finding wording for a missing field follows the validator's wording; no test depends on the old fetch-layer wording.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Sign-off and baseline**
   - [ ] Record the owner's legacy-policy decision on this Plan (UNK-01, UNK-02) (REQ-001; read-only)
   - [ ] Run the contract test and the validator and discovery tests before any change (UNK-03) (REQ-005; read-only)
2. **Phase 2: Validator contract**
   - [ ] Add the validator tests first: missing kind, missing keys, accepted empty values, and the legacy key under the approved policy (REQ-002, REQ-004, REQ-005; `tests/shared/test_resource_scope.py`)
   - [ ] Enforce presence of all four fields in the validator, apply the legacy policy, and align the docstring, using small helper functions (REQ-002, REQ-004; `scripts/shared/resource_scope.py`)
3. **Phase 3: Fetch layer and discovery tests**
   - [ ] Remove the separate presence pre-check and use the validator's result once (REQ-003; `scripts/agent/services/mcp_tool_discovery_fetch.py`)
   - [ ] Change `test_resource_scope_field_ignored_after_removal_synthetic` if rejection is approved, and add a single-report test for a missing field (REQ-004, REQ-005; `tests/agent/services/test_mcp_tool_discovery.py`)
4. **Phase 4: Document, deployment and verification**
   - [ ] Rewrite the document sentence (REQ-006; `docs/22_mcp/mcp_03_02_tool-registry.md`)
   - [ ] Run the checks listed under Tests and measure diff-cover (REQ-007; the Phase 2 and 3 files)
   - [ ] Deploy hand-off: because `scripts/` changes, hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision and has an approval gate (REQ-007; `scripts/shared/resource_scope.py`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/resource_scope.py` | Unit tests of the validator and the contract test | `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/test_tool_schema_contract.py -v` | Pass; missing fields rejected; empty values accepted |
| `scripts/agent/services/mcp_tool_discovery_fetch.py` | Discovery tests | `uv run pytest tests/agent/services -v` | Pass; a missing field is reported once; exclusion and severity unchanged |
| All changed scripts | Type, import-layer, lint, security | `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`; `uv run ruff check`; `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new finding; six contracts kept; validator complexity not above C (17) |
| `docs/22_mcp/mcp_03_02_tool-registry.md` | Documentation checks | `check_docs_consistency.py --domain mcp`; `check_docs_quality.py`; `check_docs_structure.py`; `check_docs_content_policy.py --strict` | No finding |
| Whole change | Full suite and coverage | `uv run pytest`; diff-cover per `rules/toolchain.md` | Pass; at least 90 percent on changed lines |

## Risks
- **Risk**: Explicit rejection excludes tools from a deployed MCP server that still emits a singular `resource_scope` → **Mitigation**: Treat the policy as an owner sign-off gate and confirm external emitters (UNK-02) before approving rejection; the ignore policy avoids the risk.
- **Risk**: Changing the test that records the "ignored after removal" behavior silently reverses a documented decision → **Mitigation**: Change it only together with the approved policy, and cite the owner's decision in the commit.
- **Risk**: Presence enforcement in the validator makes a validator-only caller stricter → **Mitigation**: The only callers are the fetch layer, which already rejects such entries, and tests; the contract test and the in-tree tool-list check confirm that no in-tree entry is affected.
- **Risk**: Moving the presence check changes the finding wording → **Mitigation**: No test asserts the old wording; severity and exclusion stay unchanged, and the single-report test guards against double reporting.
- **Risk**: The validator's complexity grows beyond its current C (17) rating → **Mitigation**: Add the checks as small helper functions and compare `radon cc` before and after.
- **Risk**: `tests/agent/services/test_mcp_tool_discovery.py` is also edited by the `mcpcompat001` Plan and the document changes often (20 commits in 30 days) → **Mitigation**: Sequence the test edits after that Plan's test phase, keep each edit small, and re-run the checks after any sync.
- **Risk**: The change is deployed without the user's approval → **Mitigation**: Phase 4 only hands off to the deploy skill after commit and push; the deploy skill's approval gate decides.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the legacy-policy sign-off and run the baseline | In Progress | — | — |  |
| 2 | Validator contract (tests first, then the validator) | In Progress | — | — |  |
| 3 | Fetch layer and discovery tests | In Progress | — | — |  |
| 4 | Document, deployment hand-off and verification | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-065435_01_scripts_shared_resource_scope.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-065435_02_scripts_agent_services_mcp_tool_discovery_fetch.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-065435_03_tests_shared_test_resource_scope.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-065435_04_tests_agent_services_test_mcp_tool_discovery.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-065435_05_docs_22_mcp_mcp_03_02_tool-registry.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-104324_mcpcompat003_align-legacy-resource-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-111522
- **Related target files**: `scripts/shared/resource_scope.py`, `scripts/agent/services/mcp_tool_discovery_fetch.py`, `tests/shared/test_resource_scope.py`, `tests/agent/services/test_mcp_tool_discovery.py`, `docs/22_mcp/mcp_03_02_tool-registry.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (decide and record the policy); Unresolved Questions | `scripts/shared/resource_scope.py` | Phase 1 | AC-1 | Owner decision recorded on this Plan | Needs confirmation |
| REQ-002 | Required Changes (validator enforces all four); Background | `scripts/shared/resource_scope.py` | Phase 2 | AC-2 | `uv run pytest tests/shared/test_resource_scope.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes (avoid double reporting); Constraints | `scripts/agent/services/mcp_tool_discovery_fetch.py` | Phase 3 | AC-3 | `uv run pytest tests/agent/services -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes (implement the policy with a test) | `scripts/shared/resource_scope.py` | Phase 2 | AC-4 | `uv run pytest tests/shared/test_resource_scope.py -v` | Needs confirmation |
| REQ-004 | Required Changes (implement the policy with a test) | `tests/agent/services/test_mcp_tool_discovery.py` | Phase 3 | AC-4 | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes (implement the policy with a test) | `tests/shared/test_resource_scope.py` | Phase 2 | AC-4 | `uv run pytest tests/shared/test_resource_scope.py -v` | Needs confirmation |
| REQ-005 | Required Changes (tests; contract test) | `tests/shared/test_resource_scope.py` | Phase 2 | AC-5 | `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/test_tool_schema_contract.py -v` | Confirmed by repository evidence |
| REQ-005 | Required Changes (confirm by test) | `tests/agent/services/test_mcp_tool_discovery.py` | Phase 3 | AC-5 | `uv run pytest tests/agent/services -v` | Confirmed by repository evidence |
| REQ-006 | Required Changes (rewrite the document sentence) | `docs/22_mcp/mcp_03_02_tool-registry.md` | Phase 4 | AC-6 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-007 | Constraints; Acceptance Criteria; Testing Expectations | `scripts/agent/services/mcp_tool_discovery_fetch.py` | Phase 4 | AC-7 | Full suite; `lint-imports`; `mypy`; diff-cover | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261028-065435 -->