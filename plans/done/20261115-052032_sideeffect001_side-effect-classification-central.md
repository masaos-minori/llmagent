## Goal
Define one canonical frozen set of side-effecting tools in `shared/tool_constants.py` and have shared dispatch, HTTP transport retry suppression, and static policy validation import it, so no side-effecting shared-dispatch tool can silently bypass dedup and the contradictory routing-authority comment in `tool_constants.py` is removed.

## Priority
High

## Scope
- **In-Scope**:
  - Define `ALL_SIDE_EFFECTING_TOOLS` as one canonical frozenset covering write, delete, execute, API-write, and side-effecting index/refresh tools that route through shared `dispatch_tool()`.
  - Replace `scripts/mcp_servers/dispatch.py`'s local `_write_tools` union with the imported canonical set.
  - Replace `scripts/shared/http_transport.py`'s local `_WRITE_TOOLS` union with the imported canonical set.
  - Point `scripts/agent/tool_policy.py`'s static side-effect classification at the canonical set so risk classification, dedup, and retry suppression share one source.
  - Add exact-equality parity tests between `TOOL_LIST` entries with `is_write=True` and the canonical set, with explicit approved exceptions only.
  - Remove the contradictory routing-authority comment block in `scripts/shared/tool_constants.py` (lines 122-126) and leave the module header (lines 4-21) as the sole authority statement.
- **Out-of-Scope**:
  - Removing direct MCP routes or enforcing idempotency-key presence at the request boundary (`mcproute001`).
  - Changing retry classes, safety tiers, `is_write`, `WRITE_DANGEROUS`, or approval tiers themselves.
  - Changing which tools are read vs. write at the schema-2.0 layer beyond keeping parity with the canonical set.
  - Diagnostics or workflow recovery changes.
- **Dependencies**:
  - **Depends on**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md` | phase all | this Issue defines the canonical side-effect set that `mcproute001`'s key requirement must consume; the set must exist before that requirement can be implemented.
  - **Depends on**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` | phase all | it changes `config/mcp_dedup.toml` ownership; re-verify retry-class parity after it lands.
  - **Depends on**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md` | phase all | shares the single contradictory-comment edit in `tool_constants.py`; this Issue owns that edit so the two Plans do not both modify the file.
  - Sequencing note: `plans/20261111-110144_adrrev017_docs-history-wording.md` edits ADR-003 wording; re-verify ADR-003 text before documenting to avoid a documentation conflict.

## Background
- `Explicit in code`: `scripts/mcp_servers/dispatch.py` builds a module-level `_write_tools` union of `WRITE_TOOLS`, `DELETE_TOOLS`, `GIT_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `CICD_WRITE_TOOLS`, `GITHUB_WRITE_TOOLS`, `GITHUB_DANGEROUS_TOOLS`, `SHELL_TOOLS` (`MDQ_WRITE_TOOLS` excluded). It is the membership test for `dispatch_tool()` dedup via `_is_side_effecting()`. (checked in Step 2/3)
- `Explicit in code`: `scripts/shared/http_transport.py` rebuilds an equivalent `_WRITE_TOOLS` union ("Mirrors scripts/mcp_servers/dispatch.py's `_write_tools`") for its fail-closed failure-classification gate in `call()`. (checked in Step 2/3)
- `Explicit in code`: `scripts/agent/tool_policy.py` builds `_STATIC_SIDE_EFFECT_TOOLS` from `_ALL_WRITE_TOOLS | DELETE_TOOLS | _EXEC_TOOLS | _GITHUB_MUTATION_TOOLS`, where `_ALL_WRITE_TOOLS` includes `MDQ_WRITE_TOOLS`. This set already covers MDQ, so the three modules disagree on whether `index_paths`/`refresh_index` are side-effecting. (checked in Step 2/3)
- `Confirmed by repository evidence`: `scripts/mcp_servers/mdq/mdq_server.py` routes `index_paths` and `refresh_index` through `dispatch_tool()` (line 321), and `config/mcp_dedup.toml` marks both `retryable`. They are therefore dedup-capable side effects that the dispatch/http unions currently exclude. (checked in Step 2/3)
- `Explicit in code`: `scripts/shared/tool_constants.py` module header (lines 4-21) states the sets are "Not a routing source" and `ToolRegistry` is "drift-detection input only" / "not a fallback", while the `WEB_SEARCH_TOOLS` comment (lines 122-126) states "`ToolRegistry` is the canonical/fallback routing source". The two statements contradict. (checked in Step 2/3)

## Problem
Side-effect classification is reconstructed locally in `dispatch.py`, `http_transport.py`, and `tool_policy.py`. A new category or tool omitted from the dispatch/http unions becomes a keyless, non-deduplicated execution path. `mdq_tools.py`'s `index_paths`/`refresh_index` are currently such a path: they dispatch through `dispatch_tool()` and are classified `retryable`, but neither union marks them side-effecting, so a duplicated keyed call executes twice. The contradictory comments in `tool_constants.py` also give opposite answers to which source routes tools.

## Reason for Change
A silent omission from the dispatch union turns a side-effecting tool into an unprotected execution path (correctness and security risk under ADR-004 fail-closed-on-writes), and the sibling MCP route issue (`mcproute001`) needs a single classification to enforce idempotency keys. The contradictory authority comment must be resolved so the module header is the only statement.

## Implementation Intent
- Define `ALL_SIDE_EFFECTING_TOOLS` as one canonical frozenset in `shared/tool_constants.py` and have dispatch, HTTP transport, and tool policy import it.
- Keep `WRITE_DANGEROUS`, retry class, approval tier, and `is_write` as separate dimensions; unify only the classification used for dedup and retry suppression.
- Cross-test the metadata so drift fails in CI rather than at runtime (parity test between `TOOL_LIST` `is_write=True` entries and the canonical set).
- Remove the contradictory comment and leave the module header as the sole authority statement.

## Requirements
- `REQ-001`: `shared/tool_constants.py` defines `ALL_SIDE_EFFECTING_TOOLS` as one canonical frozenset covering every tool that routes through shared `dispatch_tool()` and has a write/delete/execute/API-write/index-refresh side effect.
- `REQ-002`: `dispatch.py` derives its side-effect membership test (`_is_side_effecting`) from the imported canonical set instead of a local union.
- `REQ-003`: `http_transport.py` derives its fail-closed write gate (`_WRITE_TOOLS`) from the imported canonical set instead of a local union.
- `REQ-004`: `tool_policy.py` derives its static side-effect classification from the canonical set so risk classification, dedup, and retry suppression agree on which tools are side-effecting.
- `REQ-005`: A parity test asserts exact equality between `TOOL_LIST` entries with `is_write=True` and `ALL_SIDE_EFFECTING_TOOLS`, allowing only explicitly named approved exceptions, so a future omission fails in CI.
- `REQ-006`: The contradictory routing-authority comment in `tool_constants.py` is removed and the module header is the only authority statement.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified`; `issue-to-plan` Step 8's Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/tool_constants.py` | Modify | Define `ALL_SIDE_EFFECTING_TOOLS` as the single canonical frozenset and delete the contradictory routing-authority comment block (lines 122-126), leaving the module header (lines 4-21) as the sole authority. | REQ-001, REQ-006 | `ALL_SIDE_EFFECTING_TOOLS` does not exist anywhere (`rg ALL_SIDE_EFFECTING scripts/ tests/` → none); module header lines 4-21 vs. comment lines 122-126 contradict; `MDQ_WRITE_TOOLS` defined line 94 | `tests/mcp_servers/test_tool_schema_contract.py` | Verified |
| `scripts/mcp_servers/dispatch.py` | Modify | Replace the local `_write_tools` union (lines 45-54) with the imported canonical set so `_is_side_effecting()` covers MDQ index/refresh tools. | REQ-002 | `_write_tools` union lines 45-54 excludes `MDQ_WRITE_TOOLS`; `_is_side_effecting()` line 158-160 drives dedup | `tests/mcp_servers/test_mcp_dispatch.py` | Verified |
| `scripts/shared/http_transport.py` | Modify | Replace the local `_WRITE_TOOLS` union (lines 36-45) with the imported canonical set for the fail-closed write gate. | REQ-003 | `_WRITE_TOOLS` union lines 36-45 mirrors dispatch and excludes MDQ; used at lines 246 and 304 | `tests/mcp_servers/` transport tests | Verified |
| `scripts/agent/tool_policy.py` | Modify | Point `_STATIC_SIDE_EFFECT_TOOLS` (lines 78-84) at the imported canonical set so risk classification, dedup, and retry suppression share one source without changing membership. | REQ-004 | `_ALL_WRITE_TOOLS` line 78-80 includes `MDQ_WRITE_TOOLS`; `_STATIC_SIDE_EFFECT_TOOLS` line 82-84 equals the canonical union today | `tests/agent/` tool_policy tests | Verified |
| `tests/mcp_servers/test_tool_schema_contract.py` | Modify | Add an exact-equality parity assertion between `TOOL_LIST` `is_write=True` entries and `ALL_SIDE_EFFECTING_TOOLS`, with explicit approved exceptions only. | REQ-005 | Existing `test_tool_name_coverage_matches_tool_constants()` iterates every `TOOL_LIST` module (lines 51-58); no existing equality check against a side-effect set | `tests/mcp_servers/test_tool_schema_contract.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/mdq/mdq_server.py` | Confirm `index_paths`/`refresh_index` route through `dispatch_tool()` (line 321) so the MDQ classification decision is evidence-based. | REQ-001 |
| `config/mcp_dedup.toml` | Confirm `index_paths`/`refresh_index` are `retryable` (lines 42-43), i.e. dedup-capable side effects. | REQ-001 |
| `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md` | Record that `mcproute001` consumes the canonical set for its key requirement; establishes the sequencing dependency. | REQ-001, Scope |
| `plans/20261115-050235_rtregistry001_runtime-registry-sole-authority.md` | Confirm `rtregistry001` treats `tool_constants.py` as read-only and assigns the contradictory-comment edit to this Issue (avoids a frozen-plan overlap). | REQ-006, Scope |

## Acceptance Criteria
- `AC-001`: `ALL_SIDE_EFFECTING_TOOLS` exists in `shared/tool_constants.py` and is the single source for dispatch, HTTP transport, and tool policy. (`REQ-001`)
- `AC-002`: `dispatch.py` no longer defines a local `_write_tools` union; `index_paths`/`refresh_index` are covered by dedup. (`REQ-002`)
- `AC-003`: `http_transport.py` no longer defines a local `_WRITE_TOOLS` union; its fail-closed write gate uses the canonical set. (`REQ-003`)
- `AC-004`: `tool_policy.py` static side-effect classification derives from the canonical set with unchanged membership. (`REQ-004`)
- `AC-005`: A CI parity test fails if any `TOOL_LIST` `is_write=True` tool is missing from, or any canonical member is absent from, the tool lists, except explicitly named approved exceptions. (`REQ-005`)
- `AC-006`: The contradictory routing-authority comment is removed; the module header is the only authority statement. (`REQ-006`)

## Tests
- Exact-equality parity test across all MCP servers' `TOOL_LIST`, the canonical set, and `config/mcp_dedup.toml` retry classes, each referencing `REQ-005`. (`REQ-005`)
- Unit tests for dispatch dedup on each category including MDQ `index_paths`/`refresh_index`, confirming a keyed duplicate is served rather than re-executed. (`REQ-002`, `REQ-005`)
- Transport test confirming a write-failure on an MDQ tool is classified fail-closed after the set change. (`REQ-003`)
- tool_policy test confirming `classify_operation_type` and `check_write_classification` still classify `index_paths`/`refresh_index` as side-effecting after pointing at the canonical set. (`REQ-004`)

## Documentation Impact
The Plan updates MCP dispatch and tool-safety documents under `docs/22_mcp/` to state the single side-effect classification source and its relation to the other dimensions (intent, boundaries, Needs Confirmation items). The specific target doc is identified via `docs/00_index.md`'s "Document References by Task" table during `plan-to-implementation-procedure`; it is not hardcoded here because doc filenames change as docs are split. No tools or counts are listed in the doc (`skills/DESIGN.md` Docs content policy). Driven by `REQ-001`/`REQ-006`.

## Assumptions
- `ALL_SIDE_EFFECTING_TOOLS` equals the union `WRITE_TOOLS | DELETE_TOOLS | GIT_WRITE_TOOLS | RAG_WRITE_TOOLS | CICD_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS | SHELL_TOOLS | MDQ_WRITE_TOOLS`, which today equals `tool_policy.py`'s `_STATIC_SIDE_EFFECT_TOOLS` (verified: `_EXEC_TOOLS == {"shell_run"}` ⊆ `SHELL_TOOLS`; `_GITHUB_MUTATION_TOOLS == GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS`). Pointing `tool_policy.py` at the canonical set is therefore behavior-preserving. (Step 2/3)
- `index_paths`/`refresh_index` are side-effecting for dedup because they route through `dispatch_tool()` (`mdq_server.py:321`) and are `retryable` in `config/mcp_dedup.toml`; including them closes a real dedup gap, consistent with `tool_policy.py` already classifying them as writes. (Step 2/3)
- `http_transport.py`'s expanded fail-closed gate now covering MDQ writes aligns with ADR-004 (fail-closed on writes) and with the existing static classification. (Step 2/3)
- The `tool_constants.py` contradictory-comment edit is owned solely by this Issue; `rtregistry001` reads the file only. (Step 2/3)
- `deploy.sh` rsyncs `scripts/` wholesale, so Python changes need no `deploy.sh` update.

## Unknowns
None. The Issue's two open items were resolved by repository evidence and are recorded as findings above, not as live unknowns:
- MDQ classification (`index_paths`/`refresh_index`): resolved — they route through `dispatch_tool()` and are `retryable`, so they belong in the canonical set. (Step 2/3)
- The HTTP transport module identity and its write-set definition: resolved — it is `scripts/shared/http_transport.py`, whose `_WRITE_TOOLS` mirrors `dispatch.py`. (Step 2/3)

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/tool_constants.py` | Modify | Medium — imported by dispatch, transport, tool_registry, tool_policy | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/dispatch.py` | Modify | Medium — shared dispatch entry used by every MCP server | N/A | N/A | not applicable (rsynced) |
| `scripts/shared/http_transport.py` | Modify | Medium — per-request fail-closed gate | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/tool_policy.py` | Modify | Medium — approval/audit classification path | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/test_tool_schema_contract.py` | Modify | Low — test-only | N/A | N/A | not applicable (rsynced) |

## Design
Path B: affects four source files plus a test file, modifies a shared constant consumed across modules, and changes runtime dedup behavior. Four analyses below.

- **Architecture.** `shared/tool_constants.py` already owns the category frozensets as seed data. `dispatch.py` and `http_transport.py` each rebuild a write union locally; `tool_policy.py` builds `_STATIC_SIDE_EFFECT_TOOLS` from the same categories. The change promotes one union of those categories — `ALL_SIDE_EFFECTING_TOOLS` — to the single source and makes the three consumers import it. Import direction is unchanged: consumers under `scripts/` import from `shared/`, satisfying the import layer contract.
- **Dependency graphing.** `ALL_SIDE_EFFECTING_TOOLS` is imported by `dispatch.py`, `http_transport.py`, and `tool_policy.py`. Its membership must equal the union of every category that routes through `dispatch_tool()`. Because `tool_policy.py`'s current `_STATIC_SIDE_EFFECT_TOOLS` already equals that union (`_EXEC_TOOLS == {"shell_run"}` ⊆ `SHELL_TOOLS`; `_GITHUB_MUTATION_TOOLS == GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS`), delegating `tool_policy.py` to the canonical set is behavior-preserving rather than a membership change.
- **Historical analysis.** `dispatch.py` and `http_transport.py` write sets have diverged from `tool_policy.py` by omitting `MDQ_WRITE_TOOLS`; the divergence is the defect, not churn. No historical rework is expected beyond the unification.
- **Operational dependency.** `mcproute001` consumes the canonical set for its idempotency-key requirement; the set must exist before that requirement is implemented. `rtregistry001` reads `tool_constants.py` only and assigns the contradictory-comment edit to this Issue, so the two Plans do not both modify the file. `adrrev008` changes `config/mcp_dedup.toml` ownership; re-verify retry-class parity after it lands.

**Design decisions:**
- **Canonical set membership.** Include `MDQ_WRITE_TOOLS` (`index_paths`, `refresh_index`). They route through `dispatch_tool()` and are `retryable` in `config/mcp_dedup.toml`, so excluding them from the dedup union is the current defect. Decision grounded in Step 2/3 evidence.
- **Scope of unification.** Unify only the classification used for dedup and retry suppression. Keep `is_write`, retry class, approval tier, and `WRITE_DANGEROUS` as separate dimensions; `tool_policy.py` keeps its operation-type tiers but reads side-effect membership from the canonical set.
- **Parity test location.** Add the exact-equality assertion to the existing `tests/mcp_servers/test_tool_schema_contract.py`, which already iterates every `TOOL_LIST` module, rather than a new file.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Define the canonical set and remove the contradictory comment**
   - [ ] Add `ALL_SIDE_EFFECTING_TOOLS` to `scripts/shared/tool_constants.py` as the union of all side-effecting categories, with a docstring pointing to the module header as the sole authority. (`REQ-001`)
   - [ ] Delete the contradictory routing-authority comment block (lines 122-126) so the module header is the only authority statement. (`REQ-006`)
2. **Phase 2: Wire the consumers to the canonical set**
   - [ ] Replace the local `_write_tools` union in `scripts/mcp_servers/dispatch.py` with the imported `ALL_SIDE_EFFECTING_TOOLS`. (`REQ-002`)
   - [ ] Replace the local `_WRITE_TOOLS` union in `scripts/shared/http_transport.py` with the imported `ALL_SIDE_EFFECTING_TOOLS`. (`REQ-003`)
   - [ ] Point `scripts/agent/tool_policy.py`'s `_STATIC_SIDE_EFFECT_TOOLS` at the imported canonical set, preserving membership. (`REQ-004`)
3. **Phase 3: Parity tests and verification**
   - [ ] Add the exact-equality parity test between `TOOL_LIST` `is_write=True` entries and `ALL_SIDE_EFFECTING_TOOLS` (explicit approved exceptions only) to `tests/mcp_servers/test_tool_schema_contract.py`. (`REQ-005`)
   - [ ] Add a dispatch dedup unit test covering MDQ `index_paths`/`refresh_index` serving a keyed duplicate. (`REQ-002`, `REQ-005`)
   - [ ] Run validation (Phase 3) and hand off deployment. (`REQ-001`-`REQ-006`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/tool_constants.py` | Unit: `ALL_SIDE_EFFECTING_TOOLS` contains exactly the expected members; MDQ included. | `pytest tests/mcp_servers/test_tool_schema_contract.py` | parity test passes; no unexpected symmetric difference |
| `scripts/mcp_servers/dispatch.py` | Integration: keyed MDQ call is deduplicated, not re-executed. | `pytest tests/mcp_servers/test_mcp_dispatch.py` | dedup serves duplicate; no new failures |
| `scripts/shared/http_transport.py` | Unit: MDQ write failure is fail-closed. | `pytest tests/mcp_servers/` transport tests | gate classifies MDQ write as fail-closed |
| `scripts/agent/tool_policy.py` | Unit: classification membership unchanged after delegation. | `pytest tests/agent/` tool_policy tests | `classify_operation_type`/`check_write_classification` unchanged |
| Whole change | Static: mypy, ruff, import layer. | `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run ruff check scripts/`, `PYTHONPATH=scripts uv run lint-imports` | all pass |

## Risks
- **Risk**: Expanding `http_transport.py`'s fail-closed gate to MDQ writes changes behavior for a previously-uncovered tool. → **Mitigation**: the expansion matches ADR-004 fail-closed-on-writes and `tool_policy.py`'s existing static classification; a transport unit test asserts the new behavior before merge.
- **Risk**: Divergence between the canonical set and `tool_policy.py`'s current membership introduces an unintended classification change. → **Mitigation**: verified in Step 2/3 that the two unions are equal today; the tool_policy unit test locks membership.
- **Risk**: Frozen-plan overlap on `scripts/shared/tool_constants.py` with `mcproute001`/`rtregistry001`. → **Mitigation**: `rtregistry001` reads the file only and assigns the comment edit to this Issue; `mcproute001` consumes the set rather than editing it (recorded in Dependencies/Assumptions); confirmed via `check_plan_target_overlaps.py`.
- **Risk**: Removing the comment while another Plan expects its wording. → **Mitigation**: `rtregistry001` explicitly stops citing the comment and defers the edit; re-verify before documenting.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define the canonical set and remove the contradictory comment | Completed | — | 20261115 | Procedures 01-04 executed and archived 20261115; targeted tests green; ruff/mypy/lint-imports clean |
| 2 | Wire dispatch, http_transport, and tool_policy to the canonical set | Completed | — | 20261115 | Procedures 01-04 executed and archived 20261115; targeted tests green; ruff/mypy/lint-imports clean |
| 3 | Parity tests and verification | Completed | — | 20261115 | Procedures 01-04 executed and archived 20261115; targeted tests green; ruff/mypy/lint-imports clean |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261115-192353_01_scripts_shared_tool_constants.py.md` | 1, 3 | Procedure | Completed | — | — |
| `implementations/20261115-192353_02_scripts_mcp_servers_dispatch.py.md` | 2, 3 | Procedure | Completed | — | — |
| `implementations/20261115-192353_03_scripts_shared_http_transport.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261115-192353_04_scripts_agent_tool_policy.py.md` | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-052032
- **Related target files**: `scripts/shared/tool_constants.py`, `scripts/mcp_servers/dispatch.py`, `scripts/shared/http_transport.py`, `scripts/agent/tool_policy.py`, `tests/mcp_servers/test_tool_schema_contract.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; Target Files or Areas | `scripts/shared/tool_constants.py` | Phase 1 | AC-001 | parity test (`test_tool_schema_contract.py`) | Confirmed by repository evidence |
| REQ-002 | Required Changes; Acceptance Criteria | `scripts/mcp_servers/dispatch.py` | Phase 2 | AC-002 | dispatch dedup test (`test_mcp_dispatch.py`) | Confirmed by repository evidence |
| REQ-003 | Required Changes; Acceptance Criteria | `scripts/shared/http_transport.py` | Phase 2 | AC-003 | transport fail-closed test | Confirmed by repository evidence |
| REQ-004 | Implementation Intent; Required Changes | `scripts/agent/tool_policy.py` | Phase 2 | AC-004 | tool_policy classification test | Confirmed by repository evidence |
| REQ-005 | Testing Expectations | `tests/mcp_servers/test_tool_schema_contract.py` | Phase 3 | AC-005 | parity test | Confirmed by repository evidence |
| REQ-006 | Required Changes; Out of Scope | `scripts/shared/tool_constants.py` | Phase 1 | AC-006 | import-layer + structure check | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-192353 -->