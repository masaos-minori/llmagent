## Goal
Consolidate security-posture handling into ADR-004 as the single normative authority and replace the posture restatements in ADR-002, ADR-003, ADR-007, and ADR-014 with references to ADR-004, and register the `security.posture-contract` decision target (primary: ADR-004) in `config/adr_authority.toml`. No code change: a subprocess MCP server whose posture gate fails exits before binding and aborts Agent startup regardless of `required` (fail-closed), and no non-required server exists.

## Priority
High

## Scope
- **In-Scope**: Consolidate the ambiguous "exclude and continue" phrasing of ADR-003 Decision Detail #16 so "not accepted" means the same as `FAILED` (abort even when `required = false`). Replace the posture restatements in ADR-002, ADR-007, and ADR-014 with a pointer to ADR-004. Register `security.posture-contract` in `config/adr_authority.toml`. Restate posture intent and failure behavior in the MCP startup-validation and Agent operations documents without copying exit-status or config values.
- **Out-of-Scope**: Making any server non-required (EventBus and Group 7 decision issue). Adding a distinct subprocess exit status or structured startup log line for posture failures (code change not warranted, see Verification). Removing non-strict branches. Fabricating ADR approval records.
- **Dependencies**:
  - **Depends on**: `plans/done/20261110-095717_adrrev006_eventbus-future-decision.md` | phase all | determines the expected outcome of a plain network outage for a non-required server; satisfied (plan Frozen in `plans/done/`) and not blocking because no code change or test is produced here.

## Background
The Agent must never continue startup unless every configured MCP server's security posture is positively confirmed valid. ADR-004 is the single authority for how a `FAILED` posture result is handled. The same rule was restated verbatim across four more ADRs (ADR-002, ADR-003, ADR-007, ADR-014), and ADR-003 #16 framed it as a static-availability "exclude and continue" decision that omits the `required = false` abort ADR-004 mandates, inviting a misread. The authority model has no registered owner for the posture contract.

## Problem
- ADR-003 #16 reads "exclude and continue" for a server whose posture is not accepted and does not carve out the ADR-004 rule that a `FAILED` posture aborts startup even when `required = false`. The two ADRs are not strictly contradictory but ADR-003 omits a mandated rule, so a reader can downgrade a safety failure to an availability warning.
- The posture contract is restated in four ADRs, so any correction must be applied five times and each restatement can drift independently.
- `config/adr_authority.toml` has no `security.posture-contract` decision target, so the authority model has no registered owner for the contract.

## Reason for Change
- Normative ADRs that contradict or omit each other are a blocking Canonical Source Conflict under the documentation policy.
- Consolidation to one authority removes the drift surface. The change is low-risk because the underlying fail-closed behavior is already correct and enforced in code (see Verification), so this is a documentation-consistency and authority-model task.

## Implementation Intent
Keep the current fail-closed behavior as-is and express it in exactly one normative place. ADR-004 already states that a `FAILED` posture aborts startup regardless of `required` and that a subprocess spawn/posture failure before binding is treated as such. Rewrite ADR-003 #16 to remove the "continue" implication and equate "not accepted" with `FAILED`. Replace the ADR-002, ADR-007, ADR-014 restatements with one-line pointers to ADR-004. Register the contract owner in `config/adr_authority.toml`. Restate intent (not values) in the operational documents.

## Requirements
- `REQ-001`: ADR-003 Decision Detail #16 MUST state that a server whose posture is not accepted is excluded AND that a `FAILED` posture aborts Agent startup regardless of `required`; "not accepted" MUST mean the same as `FAILED` for this rule.
- `REQ-002`: ADR-002 MUST not restate posture handling; it MUST point to ADR-004.
- `REQ-003`: ADR-007 MUST not restate posture handling; it MUST point to ADR-004.
- `REQ-004`: ADR-014 MUST not restate posture handling; it MUST point to ADR-004.
- `REQ-005`: `config/adr_authority.toml` MUST register `security.posture-contract` with primary ADR-004 and conform to the authority schema.
- `REQ-006`: `mcp_06_09`, `agent_10_01`, and `mcp_02_02` MUST describe posture intent, failure behavior, and the unverifiable case without copying exit-status or config values.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Remove "exclude and continue" from Decision Detail #16; equate "not accepted" with `FAILED`; keep the registry-exclusion framing consistent with ADR-004. | REQ-001 | ADR-003 #16 (L86) frames posture as static-availability and omits the `required=false` abort; verified against current ADR text. | none (doc) | Verified |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Replace the posture `FAILED` abort restatement with a one-line reference to ADR-004. | REQ-002 | ADR-002 L239 restates "a `FAILED` check aborts Agent startup"; consistent with ADR-004 but redundant. | none (doc) | Verified |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Modify | Replace the posture `FAILED` abort restatement with a one-line reference to ADR-004. | REQ-003 | ADR-007 L80/L228 restates the abort and marks it "not an availability failure"; more precise than ADR-003 but redundant. | none (doc) | Verified |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Modify | Replace the posture restatement with a one-line reference to ADR-004. | REQ-004 | ADR-014 L138 restates the registry-exclusion framing. | none (doc) | Verified |
| `config/adr_authority.toml` | Modify | Add `[[authority]]` `decision_target = "security.posture-contract"`, `primary_adr = "ADR-004"`; add the owning edge if the schema models ownership. | REQ-005 | No `security.`/`posture` token exists in the current file. | none (config) | Verified |
| `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` | Modify | Restate posture intent and the unverifiable case for probed servers. | REQ-006 | Current doc describes startup validation behavior; posture contract now lives in ADR-004. | none (doc) | Verified |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | Restate posture failure behavior and the fail-closed guarantee at the operations level. | REQ-006 | Operations doc references posture handling that is now centralized in ADR-004. | none (doc) | Verified |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Modify | Restate posture handling per startup mode as a pointer to ADR-004. | REQ-006 | Current doc restates posture handling. | none (doc) | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | The single normative authority; must be read to state the correct rule that the other ADRs point to. | REQ-001..REQ-004 |
| `scripts/mcp_servers/server.py` | Evidence that `_enforce_startup_posture_gate()` exits pre-bind and fail-fast. | REQ-001 |
| `scripts/agent/startup_mcp_starter.py` | Evidence that subprocess spawn/health failures abort startup unconditionally. | REQ-001 |
| `scripts/agent/services/mcp_health.py` | Evidence for the probed (persistent/HTTP) server classification path. | REQ-001 |
| `registry/component_mandatoriness.yaml` | Evidence that every entry is `required` (no non-required server exists). | REQ-001 |

## Acceptance Criteria
- ADR-003 #16 contains no rule that conflicts with ADR-004; "not accepted" equals `FAILED` for posture. (REQ-001)
- ADR-002, ADR-007, ADR-014 contain no normative posture-failure rule; each points to ADR-004. (REQ-002..REQ-004)
- `config/adr_authority.toml` registers `security.posture-contract` with primary ADR-004 and passes `check_adr_authority.py`. (REQ-005)
- `mcp_06_09`, `agent_10_01`, `mcp_02_02` describe intent and failure behavior without copying exit-status or config values. (REQ-006)
- `check_adr_structure.py`, `check_adr_authority.py`, `check_docs_consistency.py --domain mcp`, and `check_docs_consistency.py --domain agent` pass.

## Tests
- N/A: no code change. Validation is by the documentation and authority checkers named in the Acceptance Criteria. Any doc/authority structural checker in `rules/toolchain.md` that runs on `docs/` and `config/adr_authority.toml` changes MUST pass.

## Documentation Impact
Fully documentation and authority-config. ADR-002, ADR-003, ADR-007, ADR-014, the MCP startup-validation and Agent operations documents, and `config/adr_authority.toml` change. Name targets via `docs/00_index.md` "Document References by Task": the ADRs live under the failure-handling / tool-registry / MCP domains; the operational docs live under the agent and mcp domains. ADR amendments require a maintainer approval record written by a maintainer (see Risks); this Plan fabricates none.

## Assumptions
- ADR-004 currently encodes the correct rule (posture `FAILED` aborts startup regardless of `required`) and needs no content change for this issue; it is used as the reference target.
- The `security.posture-contract` authority entry follows the existing `[[authority]]` / `decision_target` / `primary_adr` shape already present in `config/adr_authority.toml`.
- Pointing the four ADRs to ADR-004 does not remove information that is not already in ADR-004.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Exact current wording of the ADR-002, ADR-007, ADR-014 posture restatements and ADR-003 #16 at implementation time. | Read once at implementation; the plan cites the verified current state. | Read the target ADRs in `plan-to-implementation-procedure` Step 2. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Medium (ADR read by index and authority checks) | 5 | Shared (governance author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Low | 5 | Shared (governance author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Modify | Low | 2 | Shared (governance author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Modify | Low | 3 | Shared (governance author) | not applicable (rsynced) |
| `config/adr_authority.toml` | Modify | Medium (authority graph consumed by `check_adr_authority.py`) | 2 | Shared (governance author) | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` | Modify | Low | 3 | Shared | not applicable (rsynced) |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | Medium (high churn) | 21 | Shared | not applicable (rsynced) |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Modify | Low | 11 | Shared | not applicable (rsynced) |

## Design
Path B classification is driven by file count (8 modification targets), not by runtime impact: no source, test, schema, or public interface changes occur. The four analyses:

- Architecture: N/A for source import graph; the relevant dependency is the ADR authority graph (`config/adr_authority.toml` edges), not the Python import layer. Editing an ADR propagates through `check_adr_authority.py`, `check_adr_structure.py`, `check_adr_invariant_matrix.py`, and `adr-reference-scoped` pre-commit, so those gates bound the blast radius.
- Dependency graphing: the modification set is closed — exactly the four ADRs, the authority config, and the three operational docs named in the Issue. No transitive source callers exist.
- Historical: `agent_10_01` has high 30-day churn (21 commits); `mcp_02_02` (11) is moderate. Re-read these two at implementation to avoid stepping on concurrent edits.
- Operational: N/A — no ports, sockets, or database locks are touched.
- Persisted schema: N/A — no SQLite DDL or migration is touched. `config/adr_authority.toml` is configuration, not a persisted DB.

The only design choice left open is the exact authority-graph shape for `security.posture-contract` (whether the schema wants an `[[authority]]` row plus owning `adr_edge`, or a field inside an existing security section). Resolve it by reading the current `config/adr_authority.toml` schema and running `check_adr_authority.py` before committing the edit; if the schema cannot express it, record it as a follow-up rather than inventing a shape.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Consolidate ADR-003 #16**
   - [ ] Remove the "exclude and continue" implication from `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` Decision Detail #16 and equate "not accepted" with `FAILED` (REQ-001).
2. **Phase 2: Replace restatements in ADR-002, ADR-007, ADR-014 with references to ADR-004**
   - [ ] Rewrite the posture clause in `docs/10_adr/adr_02_01_002_platform-config-isolation.md` to point to ADR-004 (REQ-002).
   - [ ] Rewrite the posture clause in `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` to point to ADR-004 (REQ-003).
   - [ ] Rewrite the posture clause in `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` to point to ADR-004 (REQ-004).
3. **Phase 3: Register the authority owner**
   - [ ] Add `security.posture-contract` (primary ADR-004) to `config/adr_authority.toml` following the existing schema shape; run `check_adr_authority.py` (REQ-005).
4. **Phase 4: Restate intent in operational documents**
   - [ ] Update `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, and `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` to describe posture intent and the unverifiable case without copying values (REQ-006).
5. **Phase 5: Deployment & Verification**
   - [ ] Run `check_adr_structure.py`, `check_adr_authority.py`, `check_docs_consistency.py --domain mcp`, `check_docs_consistency.py --domain agent`, and the ADR-index/authority CI gates; confirm no ADR invariant or Known Deviation regressed (all REQs).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `config/adr_authority.toml` | Authority-schema consistency | `uv run python tools/check_adr_authority.py` | No `DUP_PRIMARY`/`DANGLING_ADR`/`AUTHORITY_CYCLE`/`ASSUMPTION_DRIFT`; `security.posture-contract` resolves to ADR-004 |
| ADR-002/003/007/014 | Structural + invariant preservation | `uv run python tools/check_adr_structure.py`, `check_adr_preservation.py` | No invariant/reference/Known Deviation text changed outside intent; #16 edit is a permitted wording change |
| All edited docs | Cross-domain claim consistency | `uv run python tools/check_docs_consistency.py --domain mcp`, `--domain agent` | Pass |
| All edited docs | Japanese-text policy | `uv run python tools/check_docs_japanese.py` | Pass (English only) |

## Risks
- **Risk**: ADR content edits trip `check_adr_preservation.py` (ERROR when an invariant, reference, test citation, Known Deviations, or Approval text changed) because the tool measures any body change. → **Mitigation**: scope each ADR edit to the single posture clause, keep all other text byte-identical, and re-run `check_adr_preservation.py` against `HEAD` before committing; treat a finding as scope creep to remove.
- **Risk**: The authority-config edit introduces a `DANGLING_ADR` or `DUP_PRIMARY` finding. → **Mitigation**: model the entry on an existing `[[authority]]` row and run `check_adr_authority.py` before commit.
- **Risk**: ADR amendments require a maintainer approval record. → **Mitigation**: the implementation writes the approval record; this Plan records the requirement and fabricates none.
- **Risk**: `agent_10_01` high churn (21 commits/30d) risks stepping on concurrent doc edits. → **Mitigation**: re-read the file at implementation and re-run the doc checkers.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Consolidate ADR-003 #16 | In Progress | — | — |  |
| 2 | Replace ADR-002/007/014 restatements with references to ADR-004 | In Progress | — | — |  |
| 3 | Register `security.posture-contract` in `config/adr_authority.toml` | In Progress | — | — |  |
| 4 | Restate posture intent in `mcp_06_09`, `agent_10_01`, `mcp_02_02` | In Progress | — | — |  |
| 5 | Run documentation and authority checkers | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|---------|
| `implementations/20261111-065828_01_docs_10_adr_adr_02_02_003_agent-runtime-tool-registry-routing-authority.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261111-065828_02_docs_10_adr_adr_02_01_002_platform-config-isolation.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261111-065828_03_docs_10_adr_adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261111-065828_04_docs_10_adr_adr_02_02_014_agent-control-plane-responsibility-boundaries.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261111-065828_05_config_adr_authority.toml.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261111-065828_06_docs_22_mcp_mcp_06_09_startup-validation-behavior-tool_definitions_strict.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261111-065828_07_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261111-065828_08_docs_22_mcp_mcp_02_02_startup-modes-and-health.md.md` | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261109-112814_adrrev007_posture-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261110-225014
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`, `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `config/adr_authority.toml`, `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / Acceptance Criteria; ADR-003 #16 omits the `required=false` abort (verified, prior adversarial run, current source unchanged) | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | 1 | ADR-003 no conflicting rule | Doc checker `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; ADR-002 L239 restatement | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | 2 | References ADR-004 | `check_docs_consistency.py --domain overview` | Confirmed by repository evidence |
| REQ-003 | Required Changes; ADR-007 L80/L228 restatement | `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | 2 | References ADR-004 | `check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-004 | Required Changes; ADR-014 L138 restatement | `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | 2 | References ADR-004 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-005 | Required Changes; no `security.` token in `config/adr_authority.toml` | `config/adr_authority.toml` | 3 | Registers ADR-004 primary | `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes / Documentation Impact | `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | 4 | Intent-only description | `check_docs_consistency.py`, `check_docs_japanese.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261111-065828 -->