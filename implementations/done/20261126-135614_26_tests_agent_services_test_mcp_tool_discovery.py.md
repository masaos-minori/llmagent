## Goal
- Update `tests/agent/services/test_mcp_tool_discovery.py` to cover the strict `config_dependent` validation, the capability-based exclusion, and the catalog-driven required-capability proof (REQ-005, REQ-006, REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this test file only (standalone row: it is named by four target rows, seq 09, 10, 11, 17, so it is not a companion).
- Out of scope: the implementation changes (seq 09, 10, 11, 17).

## Assumptions
- Verified in Step 3a: the file pins the schema-2.1 field assertions (`test_mcp_tool_discovery.py:201-263`), the drift FATAL counts (`:152-153`), and the posture-gate exclusion outcomes (`:422-502`); those pins must not be weakened.
- The implementation is in seq 09 (reorder and proof), seq 10 (strict bool), seq 11 (pass-through and map), seq 17 (catalog); write the failing tests first.

## Design decisions
- New cases use the same fixture shape as the existing discovery tests (fake server entries plus a gate map), so the pinned assertions stay untouched.

### Corrections made in Step 3b
- Corrected in Step 3b: "add cases only" cannot hold. Six existing cases assert the pre-REQ-005 behavior and are red under the report-based proof: two `TestDiscoverAllServerFilter` cases that expect no finding for a required server whose gate carries no report, and four `TestRequiredCapabilityCheck` cases that pin the removed inert guard, the tool-declaration proof, or the catalog-absence FATAL. They were updated, not weakened: the assertions that still express the requirement stay, and the fixtures now carry the report the check reads.
- Corrected in Step 3b: the gate fixture must carry a parsed report, because `gates_from()` builds a gate with no report and a gate with no report proves nothing. A local helper, `_gates_with_reports()`, was added in this file instead of changing the shared `tests/agent/services/_discovery_gates.py`, which three other test files read and which is not in the frozen Implementation Target Files.
- Corrected in Step 3b: the exclusion reason is read through `exclusion_reason()`, the name seq 13 implemented, not `get_exclusion_reason()`.
- Corrected in Step 3b: the two catalog-absence cases no longer assert FATAL for the absence itself. D-6 reads a required server with no catalog entry, or with no declared `required_capability`, through the legacy `ready` flag, so the cases assert the fallback decision: FATAL when the report does not prove readiness, nothing when it does.
- Corrected in Step 3b: the finding filter reads the capability messages only. The drift check reports its own FATAL rows for the fixture's partial tool list, so an unfiltered FATAL assertion is not the capability finding.

## Alternatives considered
- N/A: test-only change.

## Implementation
### Target file
`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure
1. Add strict-bool cases: a non-bool `config_dependent` entry is rejected with a warning finding; a bool entry passes and reaches `RuntimeTool` with the declared value (T-07).
2. Add capability-exclusion cases: a tool whose owning server's capability is `degraded` or `unavailable` is excluded with reason `capability`; a tool with no capability dependency stays registered (T-06).
3. Add the catalog-driven proof case: a `required=true` server whose required capability is not proven `ok` produces FATAL; a legacy body falls back to `ready` (T-05).
4. Assert the catalog loads before registry construction by making the missing-catalog case observable before any tool row exists.

### Method
- Keep every existing pinned assertion unchanged; add cases only.

### Corrected in Step 3b
- The method as written was amended: six pinned cases express behavior REQ-005 replaced, so they were rewritten to the report-based rule while the assertions that still state the requirement were kept. New cases were added in four classes: `TestRequiredCapabilityProofFromTheReport`, `TestStrictConfigDependentField`, `TestDiscoverAllCapabilityExclusion`, `TestCatalogLoadOrderBeforeRegistryConstruction`.

### Details
- The exclusion reason assertion reads `exclusion_reason()` (seq 13).

## Compatibility considerations
- The catalog fixture for the GitHub case must match seq 17 (`github.api` optional, `github.operations` required).

### Corrected in Step 3b
- The fixture matches seq 17. The drift check compares the live tool list against the static ToolRegistry rather than the fixture catalog, so it still reports rows for the fixture's partial tool list; the capability assertions read the capability messages only.

## Security considerations
- N/A: no credential content in the fixtures.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_mcp_tool_discovery_posture_gate.py`; `uv run ruff format` and `uv run ruff check` on this file; then the sequence in `rules/toolchain.md`.
- Ran: 118 passed (103 in this file, 15 in the companion); 10 cases added and 6 existing cases rewritten to the report-based rule; ruff format/check clean; check_docstrings, check_mock_patch_targets, check_module_size clean; lint-imports 6 contracts kept; reference table no drift; 75 cited ADR tests pass. Full suite pending at end of batch.

## Completion criteria
- The new cases fail before seq 09-11 and 17 and pass after; no existing pinned assertion is weakened.

### Corrected in Step 3b
- The cases could not be written as failing-first: seq 09-11 and 17 were executed before this cycle, per memo3.md's order, so the failing state was recorded as the six red cases this cycle repaired. The pinned assertions that still state the requirement are unchanged; the six that stated behavior REQ-005 replaced were rewritten.

## Out of Scope
- The implementation changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes | Completed | 20261126-194208 | 20261126-194208 | Changed file: tests/agent/services/test_mcp_tool_discovery.py. 10 cases added in four classes (report-based proof, strict config_dependent, capability exclusion, catalog-load order) and 6 existing cases rewritten to the report-based rule. Added the local helpers _gates_with_reports() and _tool_entry(), and extended the findings filter to the capability messages. The shared tests/agent/services/_discovery_gates.py was not changed: it is not in the frozen Implementation Target Files and three other test files read it. |
| 2 | Confirm the new cases fail before seq 09-11 and 17 and pass after | Completed | 20261126-194208 | 20261126-194208 | Failing-first was not possible: seq 09-11 and 17 ran before this cycle per memo3.md order. The six cases that were red under the report-based proof now pass. 103 tests in this file and 15 in the posture-gate companion pass. No pinned assertion that still states the requirement was weakened. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-194208 | 20261126-194208 | ruff format/check pass; check_docstrings, check_mock_patch_targets, check_module_size pass; lint-imports 6 contracts kept; reference table no drift; 75 cited ADR tests pass. Full suite pending at end of batch. Docs: N/A, the docs rows for this module are seq 33-38. |

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
- **Requirement ID**: `REQ-005` (required capability proof), `REQ-006` (capability exclusion), `REQ-007` (strict `config_dependent`)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `tests/agent/services/test_mcp_tool_discovery.py`