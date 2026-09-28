## Goal

Remove CI-009 entry from Known Issues Part 1 in governance_03 and update the batching note to reflect one fewer remaining member.

## Scope

- **In-Scope**: Removing CI-009 from Known Issues Part 1; updating the batching note on line 213 to reflect one fewer remaining member; dropping CI-009 from any `Related` cross-references
- **Out-of-Scope**: Changes to `scripts/shared/config_loader.py`; additions to `tests/shared/test_config_loader.py`; updates to `docs/10_adr/adr-index.md`

## Assumptions

- The test coverage added in the companion implementation procedure document (for `tests/shared/test_config_loader.py`) will be validated before this documentation update
- CI-009 is listed in Known Issues Part 1 of `governance_03`

## Design decisions

- Remove the entire CI-009 section (lines 113-130) rather than marking it as resolved — the issue is closed once test coverage exists
- Update the batching note to remove CI-009 from the list of remaining members
- Drop CI-009 from any `Related` cross-references in the same document

## Alternatives considered

- Marking CI-009 as "resolved" instead of removing it — rejected because Known Issues Part 1 is for open issues, not resolved ones
- Creating a separate "Resolved Issues" section — rejected because the document structure does not support this

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Remove the CI-009 section (lines 113-130) from Known Issues Part 1
2. Update the batching note on line 213 to remove CI-009 from the list of remaining members
3. Drop CI-009 from any `Related` cross-references in the document

### Method

1. Delete lines 113-130 (the CI-009 section header through its last bullet point)
2. Edit the batching note to change:
   - From: "CI-009, CI-010, CI-012, CI-014, CI-016"
   - To: "CI-010, CI-012, CI-014, CI-016"
3. Search for any `Related: CI-009` references and remove them

### Details

**Step 1: Remove CI-009 section**

Delete the following block (approximately lines 113-130):
```markdown
#### CI-009

- **ID**: CI-009
- **Title**: ADR-002 config isolation enforcement relies on a safe default, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: Shared/DB
- **Type**: operational-gap
- **Source**: `scripts/shared/config_loader.py` (`restrict_to()`), `scripts/shared/config_errors.py`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/10_adr/ADR-002-config-isolation-policy.md`
- **Related**: ADR-002
- **Summary**: ADR-002 requires that config loading respects isolation boundaries enforced by `restrict_to()`.
- **Current Description**: `scripts/shared/config_loader.py::restrict_to()` enforces config isolation per ADR-002 — confirmed correct via code inspection — but no automated test exists, so a future regression of this invariant would not be caught.
- **Observed Implementation**: Verified by code inspection only; no automated test.
- **Impact**: Without test coverage, a future change to `restrict_to()` could silently violate ADR-002 with no automated signal, and CI-009 cannot be removed from the Known Issues inventory until coverage exists.
- **Recommended Action**: Add a unit test asserting `restrict_to()`'s isolation enforcement, following existing test conventions in `tests/shared/`.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below
```

**Step 2: Update batching note**

Change the batching note from:
```
Note on CI-009, CI-010, CI-012, CI-014, CI-016 batching: These five structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative (originally nine members; CI-008, CI-011, CI-013, and CI-015 were removed once test coverage was added). Their Area fields span Shared/DB (CI-009), MCP (CI-010), EventBus (CI-012), RAG (CI-014), and Agent (CI-016) — one member per area — and no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership.
```

To:
```
Note on CI-010, CI-012, CI-014, CI-016 batching: These four structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative (originally nine members; CI-008, CI-009, CI-011, CI-013, and CI-015 were removed once test coverage was added). Their Area fields span MCP (CI-010), EventBus (CI-012), RAG (CI-014), and Agent (CI-016) — one member per area — and no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership.
```

**Step 3: Drop CI-009 from Related cross-references**

Search for any `Related: CI-009` references and remove them. If found, also update the count in the sentence above (e.g., "one member per area" → "one member per area" — no change needed since CI-009's area was Shared/DB which is already mentioned).

## Compatibility considerations

- No compatibility impact — updating documentation does not change behavior
- Other documents referencing CI-009 may need similar updates (e.g., adr-index.md)

## Security considerations

- This update reflects improved security verification (automated test coverage for config isolation)
- Does not introduce any new security surface

## Rollback considerations

- If the test coverage is later removed, this row should be restored to Known Issues Part 1
- Document the reason for restoring in the commit message

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual verification | Read file content | CI-009 removed from Known Issues Part 1; batching note updated |

## Completion criteria

- [ ] CI-009 section removed from Known Issues Part 1
- [ ] Batching note updated to remove CI-009 from the list of remaining members
- [ ] CI-009 dropped from any `Related` cross-references

## Out of scope

- Production code changes (`scripts/shared/config_loader.py`)
- Test additions (`tests/shared/test_config_loader.py`)
- Updates to other INV rows or CI entries

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260928-160317 | Removed CI-009 section from Known Issues Part 1; updated batching note (five->four members, CI-009 moved to removed list). |
| 2 | Add or update tests per Validation plan | Completed | — | 20260928-160317 | N/A: doc-only change; manual verification per Validation plan. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260928-160317 | Doc checkers pass: quality 0 errors, content_policy exit 0, japanese exit 0. Pre-existing size violation (30897B>24576B committed) unchanged by this edit; out of scope. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260928-160317 |  |

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
- **Requirement ID**: REQ-001 (ADR-002 config isolation invariant test exists and passes)
- **Source issue**: issues/20260927-211337_ci009_add-unit-test-for-adr-002-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-085809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-105131
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md