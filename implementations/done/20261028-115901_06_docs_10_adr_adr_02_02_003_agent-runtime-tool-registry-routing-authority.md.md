# Procedure: fill the six empty Implementation cells of the ADR-003 Automated Tests table

## Goal

Cite an existing test or record `Not verified` in each empty `Implementation` cell (INV-01, 02, 03, 04, 06, 07) (Plan REQ-001).

## Scope

- Modify only `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- Candidate tests were identified in the planning phase; re-verify each by reading the test body before citing it.
- Edit verification text only; Decisions and Invariants stay unchanged.
- Overlap (compatible): `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` edits only the ADR-006 Implementation Notes, while this Plan edits ADR-006's Verification table. Any citation added by that Plan must resolve to an existing test node once the node validation of this Plan is in force.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure

- INV-01 (startup fails on duplicate Tool name ownership): cite `tests/agent/services/test_mcp_tool_discovery.py::<class>::test_dedupe_and_build_excludes_a_duplicated_name_and_reports_it_fatal` (find the class with `rg -n "^class " tests/agent/services/test_mcp_tool_discovery.py`).
- INV-02 (unregistered Tools are not executed): cite `tests/shared/test_route_resolver.py::TestRegistryRouting::test_unknown_tool_raises` (correction after adversarial verification: the index row for ADR-003 INV-02 already cites `tests/shared/test_route_resolver.py`, and the checker's body/index rule compares cited files, so citing `tests/shared/test_tool_executor_routing.py` created a new disagreement).
- INV-03 (routing, approval and auditing reference the same Safety Tier): record `Not verified` (correction after adversarial verification: the candidate `tests/agent/test_startup_severity_classification.py::TestCheckServicesSeverityClassification::test_routing_safety_tiers_warning_on_messages` mocks `check_routing_safety_tiers` and only asserts that its messages become a WARNING outcome; it does not check that routing, approval and auditing use the same tier). Do not change the Blocking column.
- INV-06 (a statically disabled Tool is not in `llm_tool_definitions()`): cite `tests/shared/test_runtime_tool_registry.py::TestRuntimeToolRegistry::test_llm_tool_definitions_filters_enabled_and_rekeys_parameters` (correction after adversarial verification: the `llm_tool_definitions` calls inside `TestDisabledServerExclusion` are posture-gate tests, not static-disable tests; this test builds a tool with `enabled_for_llm=False` and asserts it is absent).
- INV-04 (no fallback to the static ToolRegistry) and INV-07 (Circuit-Open server tools stay in `llm_tool_definitions()`): no existing test was found; write `Not verified` and do not change the Blocking column (UNK-03; a follow-up Issue adds the tests).
- Verify every cited node with the new node validation (`uv run python tools/check_adr_invariant_matrix.py`) and update the matching index rows only if the checker reports a body/index disagreement.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The index says a `Not verified` row is non-blocking, which conflicts with a Blocking `Yes` column for INV-04 and INV-07; the Constraint forbids lowering a gate here, so only the evidence text is written and the conflict is reported.

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py --strict`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_docs_consistency.py --domain governance` | No finding |

## Completion criteria

- The document states the behavior described in Details.
- All listed documentation checkers report no finding.

## Out of Scope

- Every other document.
- Code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-162007 | 20261028-162007 | Step 3b: INV-03 Not verified; INV-02 cites test_route_resolver; ADR-003 size gate (26602 B) forces file/class-level citations for INV-01, INV-02, INV-06 |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261028-162007 | 20261028-162007 |  |

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
- **Requirement ID**: REQ-001 (empty evidence cells)
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115901
- **Related target files**: docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md