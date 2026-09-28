## Goal

Remove CI-010 entry from Known Issues Part 1 in governance_03 and update the batching note to reflect one fewer remaining member.

## Scope

- **In-Scope**: Removing CI-010 from Known Issues Part 1; updating the batching note on line 213 to reflect one fewer remaining member; dropping CI-010 from any `Related` cross-references
- **Out-of-Scope**: Changes to `scripts/shared/route_resolver.py`; additions to `tests/shared/test_route_resolver.py`; updates to `docs/10_adr/adr-index.md`

## Assumptions

- The test coverage added in the companion implementation procedure document (for `tests/shared/test_route_resolver.py`) will be validated before this documentation update
- CI-010 is listed in Known Issues Part 1 of `governance_03`

## Design decisions

- Remove the entire CI-010 section (lines 133-135) rather than marking it as resolved — the issue is closed once test coverage exists
- Update the batching note to remove CI-010 from the list of remaining members
- Drop CI-010 from any `Related` cross-references in the same document

## Alternatives considered

- Marking CI-010 as "resolved" instead of removing it — rejected because Known Issues Part 1 is for open issues, not resolved ones
- Creating a separate "Resolved Issues" section — rejected because the document structure does not support this

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Remove the CI-010 section (lines 133-135) from Known Issues Part 1
2. Update the batching note on line 213 to remove CI-010 from the list of remaining members
3. Drop CI-010 from any `Related` cross-references in the document

### Method

1. Delete lines 133-135 (the CI-010 section header through its last bullet point)
2. Edit the batching note to change:
   - From: "CI-009, CI-010, CI-012, CI-014, CI-016"
   - To: "CI-009, CI-012, CI-014, CI-016"
3. Search for any `Related: CI-010` references and remove them

### Details

**Step 1: Remove CI-010 section**

Delete the following block (approximately lines 133-135):
```markdown
#### CI-010

- **ID**: CI-010
- **Title**: ADR-003 RuntimeToolRegistry routing authority relies on a safe default, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: operational-gap
- **Source**: `scripts/shared/route_resolver.py` (`resolve()`), `scripts/shared/tool_registry.py`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`
- **Related**: ADR-003
- **Summary**: ADR-003 requires that `RuntimeToolRegistry` is the sole routing authority in `ToolRouteResolver.resolve()`.
- **Current Description**: `scripts/shared/route_resolver.py::resolve()` only looks up in `_runtime_registry`, never falling back to `ToolRegistry` — confirmed correct via code inspection — but no automated test covers this routing-authority invariant.
- **Observed Implementation**: Verified by code inspection only; no automated test.
- **Impact**: Without test coverage, a future change to `resolve()` could silently reintroduce a fallback to `ToolRegistry`, violating ADR-003, with no automated signal.
- **Recommended Action**: Add a unit test asserting `resolve()` never falls back to `ToolRegistry` when `RuntimeToolRegistry` is available, following existing test conventions for MCP routing tests.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below
```

**Step 2: Update batching note**

Change the batching note from:
```
Note on CI-009, CI-010, CI-012, CI-014, CI-016 batching: These five structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative (originally nine members; CI-008, CI-011, CI-013, and CI-015 were removed once test coverage was added). Their Area fields span Shared/DB (CI-009), MCP (CI-010), EventBus (CI-012), RAG (CI-014), and Agent (CI-016) — one member per area — and no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership.
```

To:
```
Note on CI-009, CI-012, CI-014, CI-016 batching: These four structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative (originally nine members; CI-008, CI-010, CI-011, CI-013, and CI-015 were removed once test coverage was added). Their Area fields span Shared/DB (CI-009), EventBus (CI-012), RAG (CI-014), and Agent (CI-016) — one member per area — and no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership.
```

**Step 3: Drop CI-010 from Related cross-references**

Search for any `Related: CI-010` references and remove them. If found, also update the count in the sentence above (e.g., "one member per area" → "one member per area" — no change needed since CI-010's area was MCP which is already mentioned).

## Compatibility considerations

- No compatibility impact — updating documentation does not change behavior
- Other documents referencing CI-010 may need similar updates (e.g., adr-index.md)

## Security considerations

- This update reflects improved security verification (automated test coverage for routing authority)
- Does not introduce any new security surface

## Rollback considerations

- If the test coverage is later removed, this row should be restored to Known Issues Part 1
- Document the reason for restoring in the commit message

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual verification | Read file content | CI-010 removed from Known Issues Part 1; batching note updated |

## Completion criteria

- [ ] CI-010 section removed from Known Issues Part 1
- [ ] Batching note updated to remove CI-010 from the list of remaining members
- [ ] CI-010 dropped from any `Related` cross-references

## Out of scope

- Production code changes (`scripts/shared/route_resolver.py`)
- Test additions (`tests/shared/test_route_resolver.py`)
- Updates to other INV rows or CI entries

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260928-171648 | 20260928-171648 | Removed CI-010 section (actual L113-131, not proc-doc stale L133-135) and updated batching note (four->three remaining: CI-012/014/016; CI-010 added to removed list; MCP(CI-010) area dropped). Step 4b: proc doc line numbers, CI-010 field text, and batching from/to described the pre-CI-009-removal state; implemented against actual current file. |
| 2 | Add or update tests per Validation plan | Completed | 20260928-171648 | 20260928-171648 | N/A - documentation-only update; no tests per Validation plan. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260928-171648 | 20260928-171648 | Doc checkers: 0 errors. Pre-existing/unrelated - structure size 28593B>24576B (reduced from 30897B by this edit), Lifecycle self-similarity warnings x3, content-policy code-fallback comparison at L317. removal-placeholder policy did not flag (CI-010 remains only in batching-note removed enumeration). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260928-171648 | 20260928-171648 | This workitem is the documentation update (CI-010 removal + batching note). |

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
- **Requirement ID**: REQ-001 (ADR-003 routing-authority invariant test exists and passes)
- **Source issue**: issues/20260927-211338_ci010_add-unit-test-for-adr-003-runtimetoolregistry-routing-authority.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-091830_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-105557
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md