# Procedure: rewrite the legacy-field discovery test and add a single-report test

## Goal

Change `test_resource_scope_field_ignored_after_removal_synthetic` in
`tests/agent/services/test_mcp_tool_discovery.py` to the approved rejection policy and add one
test asserting a missing field is reported exactly once (Plan REQ-004, REQ-005; AC-3, AC-4, AC-5).

## Scope

- Modify only `tests/agent/services/test_mcp_tool_discovery.py`.
- In scope: the synthetic legacy-field test (currently lines 1174-1256) and one new
  single-report test.
- Out of scope: the validator and fetch source (procedures 01, 02), validator tests (procedure
  03), the posture-gate edits owned by the mcpcompat001 procedures
  (`implementations/20261028-013216_12.md`), all other tests in this file.

## Assumptions

- Apply after the mcpcompat001 test-phase procedures (Plan UNK-04 and Scope Dependencies): that
  procedure adds posture gates to the `McpToolDiscoveryService(...)` construction call sites in
  this file. Locate targets by test function name, never by line number, and keep whatever gated
  call form those procedures produced.
- Procedures 01 and 02 supply the behavior; this test fails until both are applied.

## Design decisions

- Rename the synthetic test to `test_legacy_singular_resource_scope_rejected_synthetic` (new):
  the old name documents "ignored" behavior the owner reversed; a renamed test makes the policy
  change visible in the suite (Plan Risk mitigation: cite the owner decision in the commit).
- Keep the synthetic two-entry shape (bad-value `123` and plausible `"filesystem"`) so the
  rejection is proven independent of the legacy key's value.

## Alternatives considered

- Keep the test name and only flip assertions — rejected: the name would then contradict the
  behavior it asserts, which is exactly the documentation/code mismatch this Plan removes.
- Delete the test and rely on procedure 03's validator test — rejected: the Plan table row
  requires discovery-level coverage (an entry is rejected through the full discovery path).

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

1. Rename `test_resource_scope_field_ignored_after_removal_synthetic` to
   `test_legacy_singular_resource_scope_rejected_synthetic` (new) and rewrite its docstring to:
   "legacy singular `resource_scope` is rejected as a schema error (owner decision
   2026-10-28)".
2. First half (entry with `"resource_scope": 123`): replace the expected `RuntimeTool` equality
   block with (a) `result.registry.all_tools() == []` (or `result.registry.get("test_tool") is
   None` matching the file's prevailing exclusion-assertion style) and (b) `any("resource_scope"
   in f.message for f in result.findings)`. Keep the mocked response payload unchanged.
3. Second half (entry with `"resource_scope": "filesystem"`): replace
   `assert result2.registry.get("test_tool_ok") is not None` and
   `assert not any("resource_scope" in f.message ...)` with a registered-None assertion and a
   findings-contains-`resource_scope` assertion.
4. Add `test_missing_scope_field_reported_once_synthetic` (new): one mocked entry lacking
   `resource_scope_keys` (all other fields valid); after `discover_all()`, assert the tool is
   excluded and `sum(1 for f in result.findings if "resource_scope_keys" in f.message) == 1` —
   guarding against a missing field being named twice after procedure 02 removes the pre-check.
5. Leave untouched: `test_missing_resource_scope_kind_produces_warning_and_is_excluded` and
   `test_missing_resource_scope_keys_produces_warning_and_is_excluded` (substring assertions on
   finding messages, which still hold under the validator wording), and the live-server helper
   check that asserts a present `resource_scope` is a string (it inspects raw live responses;
   no in-tree server emits the key — Plan Background 56-entry check).

### Method

Edit in place by test-function name; reuse the file's existing `_make_ctx`, `_server`, `_resp`
and `_async_result` helpers exactly as the current test uses them.

### Details

- The new single-report test is the AC-3 regression guard: today the pre-check reports the
  field, and after procedure 02 only the validator's joined message names it; either way the
  count must be exactly one.
- If the mcpcompat001 gate procedure has already wrapped the construction call sites in this
  file, the new test's service construction must copy the gated form from a neighboring test
  rather than the ungated form shown here.

## Compatibility considerations

- Sequencing (Plan UNK-04): mcpcompat001 procedures 11-15 (test phase) first, then this
  procedure; both edit disjoint regions of the same file but overlapping call-site lines.
- The old test asserted the full `RuntimeTool(...raw_definition={... "resource_scope": 123 ...})`
  equality; removing that block also removes the only test-side expectation that raw entries
  with the legacy key reach the registry — which is intended under the rejection policy.

## Security considerations

Not applicable (test-only change).

## Rollback considerations

Restore the original test name/body from the parent commit and delete the new test function.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Targeted | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` | Pass once procedures 01 and 02 are applied |
| Integration | `uv run pytest tests/agent/services -q` | Pass; a missing field is reported once; exclusion and severity unchanged |
| Lint | `uv run ruff check tests/agent/services/test_mcp_tool_discovery.py` | No finding |

## Completion criteria

- AC-3: single-report test proves the field is named once.
- AC-4: an entry carrying a singular `resource_scope` is excluded with a finding naming the key.
- AC-5: the discovery tests pass.

## Out of Scope

- Posture-gate insertion at the constructor call sites (owned by `implementations/20261028-013216_12.md`).
- Source changes (procedures 01, 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-111006 | 20261028-111006 | Changed: tests/agent/services/test_mcp_tool_discovery.py (renamed/rewrote legacy test, added single-report test, removed now-unused RuntimeTool import); stale check clean |
| 2 | Add or update tests per Validation plan | Completed | 20261028-111006 | 20261028-111618 | tests/agent/services: 308 passed full suite 10265 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-111006 | 20261028-111618 | ruff pass; full suite running joint full-suite run after procedures 01-05 applied: 10265 passed, 8 skipped; diff-cover 95% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-111618 | 20261028-111618 | N/A: no docs/00_index.md mapping needed; docs handled by procedure 05 |

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
- **Requirement ID**: REQ-004, REQ-005 (AC-3, AC-4, AC-5)
- **Source issue**: issues/20261027-104324_mcpcompat003_align-legacy-resource-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-111522_mcpcompat003_align-legacy-resource-scope.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-065435
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py