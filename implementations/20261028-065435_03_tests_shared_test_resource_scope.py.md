# Procedure: add validator tests for missing scope fields and the legacy key

## Goal

Extend `TestValidateToolSchemaV2` in `tests/shared/test_resource_scope.py` with tests for a
missing `resource_scope_kind`, a missing `resource_scope_keys`, and the legacy singular
`resource_scope` under the approved rejection policy (Plan REQ-004, REQ-005; AC-4, AC-5).

## Scope

- Modify only `tests/shared/test_resource_scope.py`.
- In scope: new test methods inside the existing `TestValidateToolSchemaV2` class.
- Out of scope: `TestResolveResourceScopes`, `TestScopesConflict` (unchanged behavior), all
  source files, discovery tests (procedure 04).

## Assumptions

- Procedure 01 supplies the validator behavior; write these tests first (Plan Phase 2 order:
  validator tests before the validator change) and expect them to fail until procedure 01 lands.
- `_valid_entry()` already carries all four fields (lines 157-165), so each new test deletes or
  adds one key on a copy.

## Design decisions

- Follow the file's existing pattern: build an entry via `_valid_entry()`, mutate it, call
  `validate_tool_schema_v2()`, assert with `any(<substring> in p for p in problems)` — matching
  `test_rejects_missing_is_write` (lines 182-186).
- Wording assertions use the bare field names (`"resource_scope_kind"`, `"resource_scope_keys"`,
  `"resource_scope"`) so they hold for any finding wording the validator adopts.

## Alternatives considered

- Parametrize the four missing-field cases into one test — rejected to keep one-failure-per-case
  diagnostics consistent with the existing class.

## Implementation

### Target file

`tests/shared/test_resource_scope.py`

### Procedure

1. Add `test_rejects_missing_resource_scope_kind` (new): `del entry["resource_scope_kind"]`;
   assert any problem contains `resource_scope_kind`.
2. Add `test_rejects_missing_resource_scope_keys` (new): `del entry["resource_scope_keys"]`;
   assert any problem contains `resource_scope_keys`.
3. Add `test_rejects_legacy_singular_resource_scope` (new): keep the valid entry unchanged and
   add `entry["resource_scope"] = "filesystem"`; assert any problem contains `resource_scope`
   and assert the entry would not validate (`validate_tool_schema_v2(entry) != []`).
4. Keep `test_accepts_empty_resource_scope_kind_and_keys` (lines 220-224) unchanged: it sets the
   values explicitly, so it remains the regression guard that empty values are still valid.
5. Do not touch the existing `_valid_entry()` helper signature.

### Method

Three new methods appended after `test_accepts_empty_resource_scope_kind_and_keys` inside the
class; no new imports.

### Details

- Note the substring trap in step 3: `"resource_scope"` is a substring of
  `"resource_scope_kind"`/`"resource_scope_keys"`, so the legacy test asserts against a fully
  valid entry plus the legacy key only — the only way a problem can appear is the legacy check.
- The acceptance test for empty values is the counter-guard for AC-2 (presence enforced, empties
  valid).

## Compatibility considerations

- These tests fail against the current validator (missing keys are silently defaulted today);
  they must be introduced together with procedure 01 in the same commit or the suite goes red.
- `tests/mcp_servers/test_tool_schema_contract.py` (reference file) must keep passing after
  procedure 01; no edit here.

## Security considerations

Not applicable (test-only change).

## Rollback considerations

Delete the three added test methods; no source dependency.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Unit | `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/test_tool_schema_contract.py -v` | Pass once procedure 01 is applied |
| Lint | `uv run ruff check tests/shared/test_resource_scope.py` | No finding |

## Completion criteria

- AC-4: the legacy key is covered by a test.
- AC-5: missing-kind, missing-keys, empty-values and legacy tests pass together with the
  contract test.

## Out of Scope

- Discovery-level tests (procedure 04).
- Validator implementation (procedure 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004, REQ-005 (AC-4, AC-5)
- **Source issue**: issues/20261027-104324_mcpcompat003_align-legacy-resource-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-111522_mcpcompat003_align-legacy-resource-scope.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-065435
- **Related target files**: tests/shared/test_resource_scope.py
