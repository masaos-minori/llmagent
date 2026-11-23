## Goal
- Pin the existing protected-HEAD protection of `git_add` and `git_commit` with regression tests, and record in ADR-012 and the governance inventory that the tests now exist while the Invariant decision stays with the maintainer, so MCP-005 describes the current state accurately.

## Priority
Medium

## Scope
- **In-Scope**: characterization tests for `git_add` and `git_commit` against a protected HEAD in `tests/mcp_servers/git/test_repository_state.py` (state-level and pipeline-level); updating the MCP-005 bullet in ADR-012 `## Known Deviations`; updating the MCP-005 entry in the governance inventory to match. No production code changes.
- **Out-of-Scope**: adding or approving an ADR-012 Invariant for the HEAD-destination check (the Invariant text and its approval are the maintainer's); any `AAL` ledger entry, `adr_01_index.md` matrix row, or change to the pinned citation count; changing `verify_authorization()` or any other authorization behavior; the postcondition work of mcpai008; other git tools' authorization rules.
- **Dependencies**: None blocking. mcpai008 edits the same server source file and reads the same test directory; the two changes are independent and either may land first. The ledger issue (gov005) lists AAL-014, AAL-015, and AAL-036 for ADR-012; this Plan does not add or change any entry.

## Background
Source Issue: `gov002`, from governance Known Issue MCP-005 (Medium). Verified in Step 2 (adversarial verification against code, tests, and the ADR):
- The enforcement exists: `RepositoryState.verify_authorization()` takes the current HEAD (`self.active_branch`) as the destination for `git_add` and `git_commit` and rejects a protected one (`scripts/mcp_servers/git/repository_state.py:144-155`); `WriteProtectionPipeline.run()` calls it as Stage 3 before Stage 5 (`scripts/mcp_servers/git/write_protection_pipeline.py:155-185`). A run against a real repository on `main` with protected `["main"]` returned `[DENIED] 'main' is a protected branch` for both tools, including for `Main` and `refs/heads/main`, and allowed `["develop"]` and no list.
- No protected-branch test exists for these two tools: `rg` over `tests/mcp_servers/git/*.py` finds none combining protected with `git_add` or `git_commit`; `test_protected_branch_rejected` in `test_repository_state.py` only asserts a `MagicMock` return value, and the live-call class `TestLiveCallToolAuthorization` covers checkout, pull, and push.
- ADR-012 INV-03 names only `git_checkout`, `git_pull`, `git_push`; its `## Known Deviations` carries the MCP-005 bullet, and the Invariant is outside this Plan.
- New finding, not in the Issue: on a detached HEAD, `active_branch` is None, `ref_valid` is False for an empty ref, and `verify_authorization("git_commit", ...)` returns `[DENIED] Ref None looks like a CLI option` at Stage 3, before Stage 5 could honor `allow_detached_head`. So `git_add` and `git_commit` are denied on a detached HEAD with a misleading message and `allow_detached_head` has no effect at Stage 3. Whether that is intended is `Needs confirmation` (UNK-02); the Issue's request to test the detached-HEAD policy therefore pins the denial itself and not its message.
- The Issue proposed an Invariant plus a pending ledger entry. That path touches `adr_01_index.md` and the citation-count pin in `tests/test_run_cited_adr_tests.py` (70), so this Plan leaves the Invariant to the maintainer and records the decision as open.

## Problem
A safety-relevant enforcement (a write on a protected branch is refused) has no regression test, so a refactor could drop it without a failing test; the inventory entry also says "no test" and will be wrong once tests exist.

## Reason for Change
Tests are valuable whichever way the Invariant decision goes, and they make the inventory accurate; they change no behavior.

## Implementation Intent
Add tests that pin the current rejection and allow cases at the state level and through the Stage 3 pipeline entry, then update the ADR deviation note and the inventory entry to say tests exist and only the Invariant decision remains open.

## Requirements
- `REQ-001`: Tests pin that `git_add` and `git_commit` are rejected when the current HEAD matches a protected branch (exact, case-insensitive, and `refs/heads/` forms), allowed on a non-protected HEAD and with no protected list, and denied on a detached HEAD (message not asserted); through `WriteProtectionPipeline.run` the operation callable is never invoked on a rejection.
- `REQ-002`: The ADR-012 MCP-005 `## Known Deviations` bullet states that the tests now exist (citing the new test class) and that the Invariant decision remains pending with the maintainer; the Known Issue stays open.
- `REQ-003`: The governance inventory MCP-005 entry matches (Observed Implementation, Impact, Recommended Action, Resolution Target); status stays `open`; no approval text is written.
- `REQ-004`: No file under `scripts/` changes and no Invariant, ledger entry, or index row is added.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/mcp_servers/git/test_repository_state.py | modify: add a test class for the HEAD-destination protection of `git_add` and `git_commit` | No protected-branch test exists for these tools | REQ-001; AC-1 | `test_repository_state.py:38-44,218-228` (`working_repo`, `detached_repo` fixtures); `repository_state.py:144-155`; `write_protection_pipeline.py:155-185` (checked in Step 2) | itself | Verified |
| docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md | modify: update the MCP-005 `## Known Deviations` bullet | The bullet says there is no dedicated test | REQ-002; AC-2 | `adr_02_03_012...md:183` (checked in Step 2) | N/A: documentation | Verified |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | modify: update the MCP-005 inventory entry | The entry says there is no test | REQ-003; AC-2 | `governance_03...md:194-212` (checked in Step 2) | N/A: documentation | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/mcp_servers/git/repository_state.py | Behavior under test: `verify_authorization`, `verify_preconditions`, `_validate_ref` | REQ-001 |
| scripts/mcp_servers/git/write_protection_pipeline.py | Stage order and the `run` signature used by the pipeline-level test | REQ-001 |
| tests/mcp_servers/git/test_git_security_compliance.py | Existing live-call and dirty-worktree tests for the two tools (not to be duplicated) | REQ-001 |
| docs/10_adr/adr_01_index.md | Invariant matrix that this Plan deliberately leaves unchanged | REQ-004 |
| tests/test_run_cited_adr_tests.py | Pins the matrix citation count, which this Plan leaves unchanged | REQ-004 |
| tools/check_known_deviation_sync.py | Known Issue and Known Deviation citation sync | REQ-002, REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001): The new tests pass and fail when the protected-HEAD check is removed from `verify_authorization()` (verified once by a local mutation, then restored); they cover both tools, the protected and non-protected cases, the normalized forms, the detached HEAD denial, and the pipeline never invoking the operation on rejection.
- `AC-2` (REQ-002, REQ-003): The ADR-012 MCP-005 bullet and the inventory entry say the tests exist and cite the test class, state that the Invariant decision remains with the maintainer, and MCP-005 stays `open`.
- `AC-3` (REQ-004): `git diff` shows no change under `scripts/`, no new Invariant, no ledger entry, and no change to `adr_01_index.md` or the citation-count pin.
- `AC-4` (REQ-001 to REQ-004): The git server test suite, ruff, mypy, the known-deviation sync and ADR structure checkers, and the documentation gates pass.

## Tests
- State level: real repositories from the existing fixtures with an explicit branch name; `verify_authorization` for `git_add` and `git_commit` against protected lists that match, do not match, are case-differing, are `refs/heads/`-qualified, or are absent (REQ-001).
- Feature-branch HEAD with protected `["main"]` is allowed (REQ-001).
- Detached HEAD: both tools denied, with and without `allow_detached_head` (pinning today's Stage 3 behavior; the message is not asserted, UNK-02) (REQ-001).
- Pipeline level: `WriteProtectionPipeline.run` with a stub operation proves the operation is not invoked when Stage 3 rejects (REQ-001).
- One-time mutation check that the new tests fail without the HEAD-destination branch (AC-1).

## Documentation Impact
Yes. ADR-012 `## Known Deviations` and the governance inventory entry for MCP-005 (state of evidence only, no new policy and no Invariant).

## Assumptions
- Characterization tests are appropriate before the Invariant decision because they pin existing, intended behavior (`verify_authorization` documents destination-based protection) whichever way the decision goes.
- The test module is `tests/mcp_servers/git/test_repository_state.py` because it already provides the `working_repo` and `detached_repo` fixtures; the large `test_git_security_compliance.py` is not extended.
- `git.Repo.init` may create `master` instead of `main`, so the tests create or name the branch explicitly instead of relying on the default.
- Path A: three files, no public interface or schema change; the Python baseline commands apply only to the test file and no source target exists (`vulture` and `bandit` baseline: `N/A: no scripts/ or tools/ target`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the maintainer adds an ADR-012 Invariant for the HEAD-destination check or declares it out of scope | No maintainer decision; the Invariant text and approval are the maintainer's | Maintainer decides after this change; the Invariant, pending ledger entry, index row, and citation-count update would then be a separate Plan | False |
| UNK-02 | Whether denying `git_add` and `git_commit` on a detached HEAD at Stage 3 with `Ref None looks like a CLI option`, and `allow_detached_head` having no effect there, is intended | The ADR's Detached HEAD policy (Decision Detail 5) names only checkout and pull | The tests pin the denial without its message; the maintainer decides whether a follow-up Issue should fix the message or the policy | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/mcp_servers/git/test_repository_state.py | Modify | Low | 1 | N/A | none (tests) |
| docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md | Modify | Low | 6 | N/A | none (documentation) |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Modify | Medium | 19 | N/A | none (documentation) |

## Design
- New class `TestHeadDestinationProtection` in `test_repository_state.py`: parametrized over `git_add` and `git_commit`; builds the protected list from the repository's actual current branch name so the test does not depend on the git default branch; uses `detached_repo` for the detached cases; the pipeline test passes `lambda` operations that record a call and asserts none happened on rejection.
- ADR-012 bullet: replace the "no dedicated test" wording with a statement that the HEAD-destination protection for `git_add` and `git_commit` is covered by the new test class and that the Invariant decision remains pending with the maintainer; keep the Known Issue citation so `check_known_deviation_sync.py` still resolves it.
- Inventory entry: update Observed Implementation (tests exist), Impact (regression protection exists, the mandate does not), Recommended Action (the maintainer decides on the Invariant; a separate Plan applies it), and Resolution Target; Status stays `open`.
- Alternatives: proposing INV-11 with a pending ledger entry (rejected: touches the index matrix and the citation-count pin and writes Invariant text that is the maintainer's); extending `test_git_security_compliance.py` (rejected: 1900+ lines and no reusable repository fixtures).
- Predictable fallout check (Step 3): module size gates do not apply to tests; no tool inventory change; no generated block references these files; pinned counts are untouched by design (REQ-004). Consumer scan: not applicable (no symbol, constant, or schema change).

## Implementation steps
1. **Phase 1: Add the regression tests**
   - [ ] Write the state-level and pipeline-level tests and confirm they pass (REQ-001; tests/mcp_servers/git/test_repository_state.py)
   - [ ] Run the one-time mutation check that the tests fail without the HEAD-destination branch, then restore it (REQ-001; tests/mcp_servers/git/test_repository_state.py)
2. **Phase 2: Record the state in the ADR and the inventory**
   - [ ] Update the MCP-005 Known Deviations bullet (REQ-002; docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md)
   - [ ] Update the MCP-005 inventory entry (REQ-003; docs/00_governance/governance_03_issue-and-uncertainty-management.md)
3. **Phase 3: Verification**
   - [ ] Run the git server suite, ruff, mypy, the checkers, and the gates; confirm no change under `scripts/` (REQ-001 to REQ-004). No deploy step: no `scripts/` or `config/` change.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/mcp_servers/git/test_repository_state.py | Unit with real temporary repositories | `uv run pytest tests/mcp_servers/git/test_repository_state.py -q` | New tests pass |
| tests/mcp_servers/git/ | Regression | `uv run pytest tests/mcp_servers/git -q` | Whole git server suite passes |
| tests/mcp_servers/git/test_repository_state.py | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` and the test file path | Clean |
| ADR-012 and governance_03 | Documentation checkers | `uv run python tools/check_known_deviation_sync.py`, `check_adr_structure.py`, `check_issue_inventory_conformance.py`, `check_adr_invariant_matrix.py`; `uv run python tools/run_validation_gates.py` | No findings; gates pass |
| Whole change | Scope guard | `git diff --stat -- scripts/ docs/10_adr/adr_01_index.md tests/test_run_cited_adr_tests.py` | Empty |

## Risks
- **Risk**: The tests depend on the host's default git branch name → **Mitigation**: derive the protected name from the repository's actual current branch.
- **Risk**: Pinning the detached HEAD denial blocks a later fix of the misleading message → **Mitigation**: the message is not asserted, only the denial; UNK-02 records the decision.
- **Risk**: The inventory entry stays open while the tests exist, which can read as inconsistent → **Mitigation**: the updated entry states that only the Invariant decision remains, following the SHARED-002 precedent.
- **Risk**: Overlap with mcpai008 in the same test directory and the same server source file → **Mitigation**: the new class is self-contained and no source change is made here.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the regression tests | Pending | — | — | |
| 2 | Record the state in the ADR and the inventory | Pending | — | — | |
| 3 | Verification | Pending | — | — | |

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
- **Source issue**: issues/20261123-104601_gov002_git-protected-head-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-110851
- **Related target files**: tests/mcp_servers/git/test_repository_state.py, docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md, docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (protected-HEAD tests); Step 2 run against a real repository | tests/mcp_servers/git/test_repository_state.py | Phase 1 | AC-1 | `uv run pytest tests/mcp_servers/git -q` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (record the decision); ADR-012 Known Deviations bullet | docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md | Phase 2 | AC-2 | `check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-003 | Issue Acceptance Criteria (inventory matches); MCP-005 entry | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 2 | AC-2 | `check_issue_inventory_conformance.py` | Confirmed by repository evidence |
| REQ-004 | Issue Constraints (no behavior change, no approval text); citation-count pin | tests/mcp_servers/git/test_repository_state.py | Phase 3 | AC-3 | `git diff --stat -- scripts/ docs/10_adr/adr_01_index.md tests/test_run_cited_adr_tests.py` | Derived from confirmed evidence |
