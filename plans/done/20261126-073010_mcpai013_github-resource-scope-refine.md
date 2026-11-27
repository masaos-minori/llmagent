## Goal
- Refine GitHub resource scopes for provably independent resources: branch scope for branch and file writes, issue scope for issue and comment writes, pull request scope for PR writes, with repository scope kept for operations that affect shared repository state, and the conflict predicate extended so repository scope still conflicts with every finer scope.

## Priority
Low

## Scope
- **In-Scope**: GitHub write-tool metadata declarations in `scripts/mcp_servers/github/tools_file.py`, `tools_issues.py`, `tools_pull_requests.py`; the scope-kind vocabulary and conflict predicate in `scripts/shared/resource_scope.py`; `RESOURCE_KEY_KIND_VALUES` in `scripts/shared/tool_metadata.py`; scheduler tests; the cross-scope-conflict documentation note in `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`.
- **Out-of-Scope**: any correctness or authorization change; read-tool scope declarations (reads do not enter the conflict graph per `mcp_03_01:167`, so they are left at `github_repo`); `scripts/agent/tool_scheduler.py` (Step 2: the scheduler consumes the predicate unchanged — recorded as a reference row); the MDQ database scope work (mdqmcp008, open issue, reuses the already-defined convention).
- **Dependencies**: mcpai002 and mcpai010 are closed (mcpai010's plan is frozen in this batch); mcpai011 is closed. Keep last per the Issue.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 13). Step 2 verification against current source: the scope key naming convention `<kind>:<identity>` is already defined in `scripts/shared/resource_scope.py` (`resolve_resource_scopes()` docstring, line 81: `f"{tool.resource_scope_kind}:{normalized_value}"`), so the Issue's Required-Changes item 2 is a confirm-and-document requirement, not a new definition; mdqmcp008 remains open and reuses it. `_scopes_conflict()` (line 117) conflicts on exact equality plus `filesystem:` ancestor/descendant only — repository scope does not currently conflict with a finer scope of a different kind, so the ancestor semantics must be added for the composed GitHub kinds. `RESOURCE_KEY_KIND_VALUES` is `{path, branch, repo, non_escalating}` (`scripts/shared/tool_metadata.py:62-64`); `issue` and `pull_request` key kinds do not exist and are added here. All GitHub write tools currently declare `github_repo` scope (`tools_file.py:58-59` shared tail). Write tools: file — `github_create_or_update_file`, `github_push_files`, `github_delete_file`; issues — `github_create_issue` (line 115), `github_add_issue_comment` (line 150); PRs — `github_create_pull_request` (117), `github_update_pull_request` (150), `github_merge_pull_request` (166). The archived related work `issues/done/20261027-104324_mcpcompat003_align-legacy-resource-scope.md` is confirmed present.

## Problem
Repository-level scopes serialize unrelated writes within one repository and reduce throughput. This is not a correctness defect. The independence of finer scopes against the GitHub API's server-side behavior was an open question; per the owner decision of 20261126 this Plan proceeds with stated independence arguments per tool group and tests that lock them.

## Reason for Change
Throughput only; premature refinement could weaken safety, so it follows the security and idempotency work.

## Implementation Intent
Improve concurrency without weakening read/write conflict protection or repository-wide invariants; keep repository scope for operations that affect shared repository state; document cross-scope conflicts.

## Design decisions (Path B)
- **Independence arguments** (owner decision, 20261126; each group gets a stated argument and a test, per the Issue's AI Implementation Instruction):
  - Branch/file writes: two writes to different branches of the same repository touch disjoint refs on the GitHub server side; no shared mutable state is affected by the API call itself. Scope: `github_branch:<owner>/<repo>/<branch>`.
  - Issue/comment writes: an issue and its comments are a self-contained resource; writes to different issues cannot interleave on shared state. Scope: `github_issue:<owner>/<repo>/<issue>`.
  - Pull request writes: a PR is a self-contained resource for update; scope `github_pull_request:<owner>/<repo>/<pr>`.
  - Kept at repository scope: `github_merge_pull_request` (merge mutates the target branch — shared repository state), `github_create_issue` and `github_create_pull_request` (owner decision 20261126, Step 3a: their request models have no `issue_number`/`pull_request_number`, so the resource identity does not exist at call time and `validate_tool_schema_v2()` would reject the key as not in `inputSchema.properties`, `resource_scope.py:157-161`), and every operation whose scope keys do not resolve. Correction 20261126 (Step 3a): the fail-closed fallback is the synthetic `global:write` scope (`resource_scope.py:62`), which is stricter than repo scope, not repo scope; the Plan previously stated the fallback "keeps repo scope". A file-write call that omits `branch` therefore lands on `global:write`, not on `github_repo:` — no safety weakening, but the wording is corrected here.
- **Conflict predicate extension**: composed GitHub kinds gain ancestor semantics — `github_repo:<owner>/<repo>` conflicts with any `github_branch:`/`github_issue:`/`github_pull_request:` scope whose identity begins with `<owner>/<repo>/` (AC-3). Implemented in `_scopes_conflict()` alongside the existing `filesystem:` ancestor rule; the scheduler is unchanged because it consumes the predicate as a black box.
- **Key-kind vocabulary**: add `issue` and `pull_request` to `ResourceKeyKind` and `RESOURCE_KEY_KIND_VALUES` (`tool_metadata.py:61-64`); `branch` already exists. `tests/shared/test_tool_metadata.py:51-52` pins the set by exact equality, so that test is a target row (amended 20261126, class `scope`, owner-approved). Identity normalization reuses the existing composed-kind separator handling — the three finer GitHub kinds must be added to `_COMPOSED_KIND_SEPARATORS` (`resource_scope.py:66-69`), otherwise `resolve_resource_scopes()` emits one scope string per key instead of the single composed `github_branch:<owner>/<repo>/<branch>` string the Design decisions state; they must not be added to `_FILESYSTEM_LIKE_KINDS` (identities are not paths).
- **Convention**: the `<kind>:<identity>` convention is confirmed as already defined; the documentation note records it and the cross-scope conflict rule.

## Requirements
- `REQ-001`: Branch scope for branch and file writes, issue scope for issue and comment writes, pull request scope for PR writes, with the stated independence argument recorded per group; repository scope kept where shared repository state is affected (merge, unresolved-branch pushes).
- `REQ-002`: Repository-wide scopes conflict with all relevant finer scopes (ancestor semantics in the conflict predicate).
- `REQ-003`: Same-resource writes and read/write conflicts remain sequential; independent resources run concurrently.
- `REQ-004`: The `<kind>:<identity>` naming convention is confirmed (already defined) and documented with the cross-scope conflict rule.
- `REQ-005`: Existing repository-level safety is not weakened; each finer scope has a test, and a scope that cannot be proven independent stays at repository scope.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261126; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).
Amended 2026-11-26 (scope): added tests/shared/test_tool_metadata.py — Update the exact-equality pin of RESOURCE_KEY_KIND_VALUES to include the new key kinds
Amended 2026-11-27 (scope, owner-approved): added `tests/agent/test_tool_approval_risk.py` and
`tests/agent/test_tool_approval_preflight.py` — pins invalidated by the REQ-001 branch-kind
declarations (a declared branch key on a high-risk branch escalates risk to HIGH).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/resource_scope.py` | Modify | Add `github_branch`, `github_issue`, `github_pull_request` to `_KNOWN_SCOPE_KINDS` and to `_COMPOSED_KIND_SEPARATORS` (separator `/`); add ancestor semantics so a `github_repo:` scope conflicts with finer GitHub scopes of the same repository | REQ-002, AC-3 | `_KNOWN_SCOPE_KINDS` at lines 41-52 lacks the finer kinds; `_COMPOSED_KIND_SEPARATORS` at lines 66-69 has only `github_repo` and `cicd_workflow`; `_scopes_conflict()` at line 117 conflicts on exact equality and `filesystem:` ancestry only (re-verified 20261126, Step 3a) | `tests/shared/test_resource_scope.py` | Verified |
| `scripts/shared/tool_metadata.py` | Modify | Add `issue` and `pull_request` to `ResourceKeyKind` and `RESOURCE_KEY_KIND_VALUES` | REQ-001 | `ResourceKeyKind` and `RESOURCE_KEY_KIND_VALUES` at lines 61-64 are `{path, branch, repo, non_escalating}` (re-verified 20261126, Step 3a) | `tests/shared/test_tool_metadata.py` (target row, amended 20261126) | Verified |
| `scripts/mcp_servers/github/tools_file.py` | Modify | Declare branch scope for the three file write tools (branch key resolves to `github_branch:<owner>/<repo>/<branch>`); read tool keeps `github_repo` — the shared tail is used by all 4 entries including the read tool, so the write entries need their own tail constant | REQ-001, AC-2 | Shared github_repo tail at lines 56-60 used by all 4 entries; write entries at lines 81, 97, 114 (re-verified 20261126, Step 3a) | `tests/mcp_servers/github/test_github_tool_schema.py` (not yet created — created by the mcpai010 procedure `implementations/20261126-205430_03_tests_mcp_servers_github_test_github_tool_schema.py.md`), `tests/shared/test_resource_scope.py` | Verified |
| `scripts/mcp_servers/github/tools_issues.py` | Modify | Declare issue scope for `github_add_issue_comment` only; `github_create_issue` keeps `github_repo` (its request model has no `issue_number`, so the resource identity does not exist at call time — owner decision 20261126); read and search entries unchanged | REQ-001, AC-2, REQ-005 | Shared github_repo tail is used by the read entries too (90, 106, 122), so the write entries need their own tail constant; write entries at 109 and 142, tails spread at 122 and 156 (re-verified 20261126, Step 3a) | `tests/shared/test_resource_scope.py` | Verified |
| `scripts/mcp_servers/github/tools_pull_requests.py` | Modify | Declare pull request scope for `github_update_pull_request` only; `github_create_pull_request` keeps `github_repo` (no `pull_request_number` in its request model — owner decision 20261126); `github_merge_pull_request` keeps `github_repo` (shared repository state per the independence argument) | REQ-001, AC-1, AC-2 | Shared github_repo tail is used by the read entries too (92, 108), so the write entries need their own tail constant; write entries at 111, 144, 160, tails spread at 124, 157, 173 (re-verified 20261126, Step 3a) | `tests/shared/test_resource_scope.py` | Verified |
| `tests/shared/test_resource_scope.py` | Modify | Add tests: finer-kind resolution, repository-versus-finer ancestor conflict, non-conflict between independent resources, fail-closed fallback unchanged | REQ-002, REQ-003, REQ-005, AC-2, AC-3 | Existing file covers `github_repo` composition (line 86) and `filesystem:` ancestry (line 40) only (checked in Step 2) | itself | Verified |
| `tests/agent/test_tool_scheduler.py` | Modify | Add conflict-graph tests: same branch write/write, same issue comment, same PR update/merge serialization; independent branches and issues concurrent; repository-wide operation conflicts with finer scopes | REQ-003, REQ-005, AC-1, AC-2, AC-3 | `TestResourceScopeGrouping` at line 157 groups by exact scope overlap only (checked in Step 2) | itself | Verified |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Modify | Document cross-scope conflicts (boundaries and constraints) and the confirmed `<kind>:<identity>` convention | REQ-004, AC-4 | Scheduler section at lines 108-167 describes the conflict graph without cross-kind ancestor rules (the predicate bullet is line 116; re-verified 20261126, Step 3a) | `uv run python tools/check_docs_quality.py` | Verified |
| `tests/shared/test_tool_metadata.py` | Modify | Update the exact-equality pin of RESOURCE_KEY_KIND_VALUES to include the new key kinds | REQ-001 / AC-2 | tests/shared/test_tool_metadata.py:51-52 pins RESOURCE_KEY_KIND_VALUES by exact equality (re-verified 20261126, Step 3a) | itself | Verified |
| `tests/agent/test_tool_approval_risk.py` | Modify | Update the REQ-008 pin that asserted no shipped github tool declares a branch-kind key: the three file write tools now declare `branch`, so the test pins the declared key set and the high-risk-branch escalation | REQ-001, AC-5 | `test_github_tools_have_no_declared_branch_keys` at line 225 asserted no `branch` kind in `resource_scope_keys`; `_escalate_for_github_branch()` (`scripts/agent/tool_policy.py:346`) reads the declared branch keys; `tests/agent/_config_test_defaults.py:141` defaults `approval_high_risk_branches` to `["main"]` (re-verified 20261127) | itself | Verified |
| `tests/agent/test_tool_approval_preflight.py` | Modify | Update the `github_push_files` dry-run pin: with a declared `branch` key the default high-risk branch `main` escalates risk to HIGH, which requires the full word "yes", so the test uses a non-high-risk branch | REQ-001, AC-5 | `test_github_tool_triggers_dry_run` at line 705 supplied `branch="main"` with a patched "y" answer; HIGH requires "yes" in `_prompt_user_approval()` (`scripts/agent/tool_approval.py`) (re-verified 20261127) | itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories, glob
patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/tool_scheduler.py` | The conflict-graph consumer (`_scopes_conflict`, line 37; synthetic `global:write` scope, line 49); Step 2 confirms it needs no change — recorded as a reference row per the Issue's Target Areas | REQ-003 |
| `tests/agent/test_tool_scheduler_comprehensive.py` | Existing scheduler coverage that must keep passing with the predicate change | REQ-003 |
| `tests/agent/test_tool_scheduler_serialization.py` | Existing serialization coverage that must keep passing | REQ-005 |
| `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md` | The open issue that reuses the `<kind>:<identity>` convention; the documentation note must not contradict it | REQ-004 |

## Acceptance Criteria
- AC-1: Same-resource writes and read/write conflicts remain sequential (REQ-003, REQ-005).
- AC-2: Independent resources (different branches, issues, PRs) can run concurrently (REQ-001, REQ-003).
- AC-3: Repository-wide operations conflict with all relevant finer scopes (REQ-002).
- AC-4: The cross-scope conflict rule and the confirmed convention are documented (REQ-004).
- AC-5: Existing repository-level safety is not weakened; every finer scope carries a stated independence argument and a test (REQ-005).

## Tests
- Same branch write/write, same issue comment, same pull request update/merge serialization; independent branches or issues concurrent; repository-wide operation conflicts with finer scopes (REQ-003, REQ-005, AC-1, AC-2, AC-3).
- Approval pins for the declared branch key: the shipped github tools that declare a branch-kind key are the three file write tools, and a high-risk branch value escalates them to HIGH while a tool with no branch key is not escalated (REQ-001, AC-5; `tests/agent/test_tool_approval_risk.py`) — amendment 2026-11-27.
- Run ruff, mypy, and the full test suite per `rules/toolchain.md`; import-linter must keep the `shared-is-leaf` contract (the `shared` module must not import `agent` or `mcp_servers`).
- Docs gate on the changed file: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`.

## Documentation Impact
Yes. `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` records cross-scope conflicts (boundaries and constraints) and the confirmed `<kind>:<identity>` convention. The file is also a mcpai012 target row; judged compatible — this Plan adds the cross-scope rule, mcpai012 performs the final sweep afterward (execution order: mcpai013 runs after mcpai012 per the Issue's "Keep last").

## Assumptions
- Owner decision recorded on 20261126 for this cycle: proceed with stated independence arguments per tool group; if an argument cannot be held for a specific tool, that tool stays at repository scope and the plan reports it rather than refining.
- The independence arguments in Design decisions are the stated arguments required by the Issue's AI Implementation Instruction; they are recorded per group and locked by tests.
- Read tools are not conflict-graph participants (`mcp_03_01:167`: conflict grouping applies where at least one call is `is_write=True`), so their scope declarations are not changed.
- The convention is already defined; REQ-004 is confirmation plus documentation, not a new definition.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any finer scope can be proven independent for the GitHub API's server-side behavior | Per-group independence argument plus a locking test | Owner decision 20261126: proceed with the stated arguments in Design decisions; a group whose argument fails during implementation is left at repository scope and reported | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/resource_scope.py` | Modify | Medium (conflict predicate consumed by the scheduler and all servers' scope declarations) | 2 | Medium (4 author variants in `scripts/shared/resource_scope.py` + `scripts/agent/tool_scheduler.py` history) | not applicable (rsynced) |
| `scripts/shared/tool_metadata.py` | Modify | Medium (schema validator accepts the widened key-kind set) | 1 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/github/tools_file.py` | Modify | Low (metadata tail shared by 4 entries; schema-consistency test pins it) | 3 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/github/tools_issues.py` | Modify | Low | 3 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/github/tools_pull_requests.py` | Modify | Low | 3 | High (single author) | not applicable (rsynced) |
| `tests/shared/test_resource_scope.py` | Modify | Low | 3 | High (single author) | not applicable (tests not deployed) |
| `tests/agent/test_tool_scheduler.py` | Modify | Low | 1 | Medium (same 4-variant history as the scheduler) | not applicable (tests not deployed) |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Modify | Medium (shared with mcpai012, judged compatible) | 7 | High (single author) | not applicable (docs not deployed) |
| `tests/shared/test_tool_metadata.py` | Modify | Not assessed (amendment 2026-11-26) | N/A | N/A | Not assessed (amendment 2026-11-26) |
| `tests/agent/test_tool_approval_risk.py` | Modify | Not assessed (amendment 2026-11-27) | N/A | N/A | Not assessed (amendment 2026-11-27) |
| `tests/agent/test_tool_approval_preflight.py` | Modify | Not assessed (amendment 2026-11-27) | N/A | N/A | Not assessed (amendment 2026-11-27) |

## Design
- **Predicate, not scheduler**: the change is confined to `_scopes_conflict()` — composed GitHub kinds gain ancestor semantics keyed on `<owner>/<repo>`; the scheduler's grouping, the synthetic `global:write` scope, and the fail-closed fallback are untouched, so existing safety properties hold by construction (REQ-005).
- **Declared-order scope strings**: finer scopes resolve from the existing `resource_scope_keys` mechanism (`resolve_resource_scopes()` builds `kind:value` from declared keys present in args); the new key kinds `issue` and `pull_request` plug into the same path, and a write whose keys do not resolve keeps the fail-closed fallback scope.
- **Predictable fallout**: no target crosses the 24576 B module-size gate (largest: `tests/agent/test_tool_scheduler.py` 22949 B). Pinned counts: `RESOURCE_KEY_KIND_VALUES` is pinned by the schema validator tests; the shared metadata tails in the three tools files are pinned by `tests/mcp_servers/github/test_github_tool_schema.py` (mcpai010's target row). No tool is added or removed, so `tools/TOOL_DESCRIPTIONS.md` is not affected. No generated-reference domain is touched. Consumer scan for `_scopes_conflict` (Step 3, recorded per `workflow-edge.md`): `scripts/agent/tool_scheduler.py` — reference row; `tests/shared/test_resource_scope.py` — target row; `tests/agent/test_tool_scheduler_serialization.py` — reference row; `tests/mcp_servers/test_tool_schema_contract.py`, `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_tool_routing_validation.py` — `not affected: they execute the module but pin no scope-kind or key-kind set; the change only adds conflicts and vocabulary values` (reference rows).
- **Validation quality baseline**: `radon cc -s` on `scripts/shared/resource_scope.py` — `_scopes_conflict` is grade A (3); adding the GitHub ancestor branch keeps it under B. Import-linter contracts currently 6/6 kept. Full toolchain sequence per `rules/toolchain.md`; diff-cover ≥ 90% on changed lines.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table.

1. **Phase 1: Conflict predicate and vocabulary tests first**
   - [ ] Write the predicate tests first: finer-kind resolution, repository-versus-finer ancestor conflict, independent-resource non-conflict, unchanged fail-closed fallback (REQ-002, REQ-003, REQ-005, AC-2, AC-3; `tests/shared/test_resource_scope.py`)
   - [ ] Add the finer scope kinds and the GitHub ancestor rule (REQ-002, AC-3; `scripts/shared/resource_scope.py`)
   - [ ] Add `issue` and `pull_request` to `RESOURCE_KEY_KIND_VALUES` (REQ-001; `scripts/shared/tool_metadata.py`)
   - [ ] Modify (REQ-001; `tests/shared/test_tool_metadata.py`) — amendment 2026-11-26
2. **Phase 2: Tool metadata declarations**
   - [ ] Declare branch scope for the file write tools, issue scope for the comment write tool, pull request scope for the PR update write tool; keep `github_repo` for the create tools (no resource identity exists at call time — owner decision 20261126), for merge, and for unresolved-branch pushes (REQ-001, AC-2, AC-5; `scripts/mcp_servers/github/tools_file.py`, `scripts/mcp_servers/github/tools_issues.py`, `scripts/mcp_servers/github/tools_pull_requests.py`)
3. **Phase 3: Scheduler conflict-graph tests**
   - [ ] Write the serialization and concurrency tests: same branch write/write, same issue comment, same PR update/merge, independent branches and issues concurrent, repository-wide operation conflicts with finer scopes (REQ-003, REQ-005, AC-1, AC-2, AC-3; `tests/agent/test_tool_scheduler.py`)
4. **Phase 4: Documentation and validation**
   - [ ] Document cross-scope conflicts and the confirmed convention (REQ-004, AC-4; `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`)
   - [ ] Run the full validation sequence (`rules/toolchain.md`: format → lint → type → arch → security → test → coverage) and the docs gates (REQ-001..REQ-005)

### Release units
N/A: no release unit — each phase can be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/resource_scope.py` | Unit | `uv run pytest tests/shared/test_resource_scope.py -v` | Ancestor conflict for repository-versus-finer; independent resources non-conflicting |
| `scripts/shared/tool_metadata.py` | Unit (schema validator) | `uv run pytest tests/shared/test_resource_scope.py -v` | New key kinds accepted by `validate_tool_schema_v2()` |
| `scripts/mcp_servers/github/tools_file.py`, `tools_issues.py`, `tools_pull_requests.py` | Unit (declared metadata resolves to the intended scope strings) | `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/github/test_github_tool_schema.py -v` | Write tools resolve to `github_branch:`/`github_issue:`/`github_pull_request:`; merge stays `github_repo:` |
| `scripts/agent/tool_scheduler.py` (consumer, unmodified) | Unit | `uv run pytest tests/agent/test_tool_scheduler.py tests/agent/test_tool_scheduler_comprehensive.py tests/agent/test_tool_scheduler_serialization.py -v` | Same-resource writes sequential; independent resources concurrent |
| All Python targets | Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings; shared-is-leaf kept |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Documentation consistency | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain mcp` | No findings |

## Risks
- **Risk**: a stated independence argument fails against actual GitHub server-side behavior (e.g., cross-branch effects through default-branch protection or merge queues) → **Mitigation**: per the Issue's instruction, a group whose argument cannot be proven stays at repository scope and is reported; the plan closes as not applicable for that group rather than weakening safety.
- **Risk**: the ancestor-rule change alters conflict results for existing `github_repo` pins → **Mitigation**: the change only adds conflicts (never removes one), so existing serialization behavior is preserved monotonically; the pinned tests are target rows.
- **Risk**: schema-consistency tests pin the shared metadata tails byte-for-byte (`tools_file.py:25-29` comment) → **Mitigation**: the tests are updated in the same phase as the declarations (mcpai010's schema test is already a frozen target row of the sibling plan).
- **Risk**: overlap with mcpai012 on `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` → **Mitigation**: judged compatible (this Plan adds the cross-scope rule; mcpai012 sweeps afterward), recorded in Documentation Impact.
- **Risk**: `Bus Factor` is medium on the scheduler/predicate pair → **Mitigation**: keep each phase independently revertable and land tests before implementation.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Conflict predicate and vocabulary tests first | Completed | 20261126-235205 | 20261127-001200 | — Procedures 01, 02, 06 executed (06 after 01 in seq order, so test-first ordering could not be observed). 8 new tests in tests/shared/test_resource_scope.py; RESOURCE_KEY_KIND_VALUES widened and pinned by tests/shared/test_tool_metadata.py. |
| 2 | Tool metadata declarations | Completed | 20261126-235716 | 20261127-000618 | — Procedures 03, 04, 05 executed: branch tail for the three file write tools, issue tail for github_add_issue_comment, PR tail for github_update_pull_request; create/merge and read entries keep github_repo. |
| 3 | Scheduler conflict-graph tests | Completed | 20261127-000949 | 20261127-000949 | — Procedure 07 executed: 8 conflict-graph tests in tests/agent/test_tool_scheduler.py; reference scheduler tests unchanged. |
| 4 | Documentation and validation | Completed | 20261127-001310 | 20261127-091945 | — Procedure 08 executed (docs checkers pass). End-of-batch full suite: 15925 passed / 5 skipped. diff-cover on changed scripts/ lines: 100%. Amendment 2026-11-27 (class scope, owner-approved): two approval pins invalidated by the branch-key declaration were updated - tests/agent/test_tool_approval_risk.py and tests/agent/test_tool_approval_preflight.py (procedures 10, 11). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at Plan creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261126-215042_01_scripts_shared_resource_scope.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-215042_02_scripts_shared_tool_metadata.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-215042_03_scripts_mcp_servers_github_tools_file.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-215042_04_scripts_mcp_servers_github_tools_issues.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-215042_05_scripts_mcp_servers_github_tools_pull_requests.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-215042_06_tests_shared_test_resource_scope.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-215042_07_tests_agent_test_tool_scheduler.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-215042_08_docs_22_mcp_mcp_03_01_dispatch-and-routing.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261127-091945_10_tests_agent_test_tool_approval_risk.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261127-091945_11_tests_agent_test_tool_approval_preflight.py.md` | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140520_mcpai013_github-resource-scope-refine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-073010
- **Related target files**: `scripts/shared/resource_scope.py`, `scripts/shared/tool_metadata.py`, `scripts/mcp_servers/github/tools_file.py`, `scripts/mcp_servers/github/tools_issues.py`, `scripts/mcp_servers/github/tools_pull_requests.py`, `tests/shared/test_resource_scope.py`, `tests/agent/test_tool_scheduler.py`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, `tests/shared/test_tool_metadata.py`, `tests/agent/test_tool_approval_risk.py`, `tests/agent/test_tool_approval_preflight.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes item 1; independence arguments (owner decision 20261126) | `scripts/mcp_servers/github/tools_file.py`, `tools_issues.py`, `tools_pull_requests.py`, `scripts/shared/tool_metadata.py` | Phase 1, Phase 2 | AC-2, AC-5 | `tests/shared/test_resource_scope.py` | Confirmed by repository evidence + owner decision |
| REQ-002 | Required Changes item 1 (cross-scope conflicts); `resource_scope.py:117` | `scripts/shared/resource_scope.py` | Phase 1 | AC-3 | `tests/shared/test_resource_scope.py` | Confirmed by repository evidence |
| REQ-003 | Acceptance Criteria 1-2; `tool_scheduler.py:37` consumer | `tests/agent/test_tool_scheduler.py` | Phase 3 | AC-1, AC-2 | itself | Confirmed by repository evidence |
| REQ-004 | Required Changes item 2; `resource_scope.py:81` convention already defined | `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Phase 4 | AC-4 | docs checkers | Confirmed by repository evidence |
| REQ-005 | Constraints; fail-closed fallback in `resource_scope.py` | `tests/shared/test_resource_scope.py`, `tests/agent/test_tool_scheduler.py` | Phase 1, Phase 3 | AC-5 | itself | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-26: Update the exact-equality pin of RESOURCE_KEY_KIND_VALUES to include the new key kinds | tests/shared/test_tool_metadata.py | Phase 1 | AC-2 | itself | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-27: update the REQ-008 pin that assumed no github tool declares a branch-kind key; the file write tools now declare one | tests/agent/test_tool_approval_risk.py | Phase 2 | AC-5 | itself | Confirmed by repository evidence + owner decision 20261127 |
| REQ-001 | Amendment 2026-11-27: update the dry-run approval pin invalidated by the HIGH escalation on a high-risk branch | tests/agent/test_tool_approval_preflight.py | Phase 2 | AC-5 | itself | Confirmed by repository evidence + owner decision 20261127 |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261126-215042 -->