## Goal
- Record in ADR-004 that Decision Group 7 and INV-09 are inapplicable today (option B) until a non-required component exists, with the approval record (REQ-002: the Group 7 outcome).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one applicability note under `### Group 7` and one `Approval Record` line.
- Not in scope: the Group 7 decision text (items 18-19), INV-09 text, the verification-matrix row text, Exceptions, anything else in the ADR.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (documents 01, 02, 05, 06), then Phase 2 (documents 03, 07), then Phase 3 (document 04).

## Assumptions
- Option B (repository owner instruction of 2026-11-10) leaves Group 7 and INV-09 in force as written and adds an applicability statement only; it does not amend INV-09 (Plan Assumptions). Falsifiable by `check_adr_preservation.py` (a WARNING at most).
- Step 3a re-verification, re-run 2026-11-10 at HEAD `9a86dede9`: `### Group 7: Behavior of Non-Mandatory Components` is at line 92 (items 18-19 at lines 94-95), INV-09 at line 224, and the verification-matrix row citing INV-09 at line 255; `registry/component_mandatoriness.yaml` holds 10 entries, every one `classification: required`. The numbers recorded in the earlier pass (93, 226, 257) were two lines high because the upstream commit `b217f999b` shortened this ADR above Group 7; the anchors here are the current ones.
- Overlap with plan 003 (RAG) and plan 004 (non-strict bypass) on this ADR: different sections (Group 7 here; their Group 10 and Group 1 edits) — compatible (Plan Assumptions, re-confirmed by `check_plan_target_overlaps.py` in Step 2).
- Approval is recorded as "task-level approval decision (repository owner instruction)" per `docs/00_governance/governance_01_documentation-policy.md`, following this ADR's existing Approval Record convention; no approver name is invented.

## Design decisions
- The applicability note is a blockquote immediately under the `### Group 7` heading so the numbered decision items stay verbatim.
- The note names its own removal trigger (the first non-required classification in `registry/component_mandatoriness.yaml`), so it cannot silently go stale (Plan Risks mitigation).

## Alternatives considered
N/A: option A (re-evaluating each server's mandatoriness) was rejected in the Plan; this document implements the chosen option B.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Procedure
1. Insert an applicability blockquote after `### Group 7: Behavior of Non-Mandatory Components` (line 92): every component in `registry/component_mandatoriness.yaml` is classified `required`, so items 18-19 and INV-09 describe behavior no current configuration triggers; they remain in force as written and are inapplicable until the first component is classified non-required (an explicit owner decision per Decision Group 3 item 13); removal trigger: that first non-required classification.
2. Add one Current Decision Approval line to the ADR's `Approval Record` citing the repository owner instruction of 2026-11-10 for this applicability statement, in the existing task-level-approval wording.
3. Run `check_adr_preservation.py` and read its report; this document's edits are intended changes and INV-09 (line 224) must be unchanged.

### Method
- Edit in place; keep the ADR in English; front matter untouched.

### Details
- The note cites the registry file as the checked source; it does not restate the registry contents beyond the count-based fact.
- The verification-matrix row at line 255 (INV-09, "Confirmed (spawn path: see Exceptions)") is not edited here; its applicability note is added in document 04 (ADR index matrix).

## Compatibility considerations
- No code, configuration, or registry change (Plan Scope out-of-scope); `config/agent.toml` and `ProductionConfigValidator` are untouched.

## Security considerations
N/A: no behavior change; fail-closed and fail-fast boundaries are unchanged.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_preservation.py` (expect only the intended edits; INV-09 unchanged), `uv run python tools/check_docs_content_policy.py --strict`.

## Completion criteria
- ADR-004 carries the Group 7/INV-09 applicability statement with the 2026-11-10 repository-owner source and its removal trigger; Group 7 items 18-19 and INV-09 remain verbatim; the checkers pass.

## Out of Scope
- Registry or configuration changes; reclassification of any server; edits in `agent_08_04` (document 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` as described in Procedure | Pending | — | — | |
| 2 | Run the documentation checkers listed in Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261109-112739_adrrev006_eventbus-future-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095717_adrrev006_eventbus-future-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-135353
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
