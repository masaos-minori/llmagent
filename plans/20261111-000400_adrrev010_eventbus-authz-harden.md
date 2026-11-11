> **PAUSED** — superseded by adrrev009 (20261111-193537). Implementation halted until adrrev009 lands; its overlapping ADR-008 scope is now owned by adrrev009.

## Goal
Correct the verified defects in ADR-013 (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`) so its Decision Details, Verification table, threat model, and risks state the EventBus authentication/authorization contract accurately, without changing any code, credential model, or governance approval.

## Priority
High

## Scope
- **In-Scope**: Document-only corrections to ADR-013 that remove internal contradictions and incorrect invariant mappings and make the ADR match the current `scripts/eventbus/` behavior. No source, test, config, or schema change. No fabrication of governance approvals.
- **Out-of-Scope**: Merging `auth_token`/`admin_token`, standardizing the no-op outcome as HTTP 422 and removing the `changed` field, rejecting a shared `consumer_id` at `load_config()`, adding a boot epoch to the generation counter, adding new ADR invariants beyond correcting the existing table, and any EventBus route-handler or configuration-loading change. Each is a maintainer decision or an undecided design choice recorded as a Non-blocking Unknown; see `Unknowns`.
- **Dependencies**:
  - **Depends on**: `issues/20261109-112504_adrrev001_eventbus-route-handlers.md` | phase all | route-handler structure and per-route authorization enforcement are owned here; this Plan documents existing behavior only and does not require it to land first (recorded as a non-blocking Unknown).
  - **Depends on**: `issues/20261109-112739_adrrev006_eventbus-future-decision.md` | phase all | owns the EventBus future-integration decision; this Plan documents the kept-EventBus contract and does not require it to land first (recorded as a non-blocking Unknown).

## Background
ADR-013 is the accepted authentication and authorization contract for the EventBus, a service that carries a security boundary (five-role model, Consumer identity binding, fail-closed config-key validation, one-generation optimistic concurrency). It was last amended 2026-11-10 (caller-model status). The issue `memo-issue.md` items H-12 and M-02, re-checked against current source on 2026-11-09, list several gaps in ADR-013: incorrect Verification-table invariant mappings, an Empty/no-op contract that contradicts the implemented behavior, a grammatically broken `load_config()` sentence, a threat model that alternates between "multi-tenant" and "single-operator", and a "proper identity store in production" sentence.

## Problem
- The Verification table maps `persistent: false` (Admin response, ADR-013 line 258) to INV-03 ("DLQ administration and privileged replay MUST require operator authorization"), and maps the admin 422 / no-op `changed: false` rows (lines 259-260) to INV-04 ("unknown/missing/mistyped config keys MUST be rejected by `load_config()`"). Neither mapping matches the behavior it lists; INV-03 and INV-04 govern unrelated concerns.
- Decision Detail #12 (line 103) states "An empty body `{}` or a body that produces no actual change is rejected with HTTP 422", yet `scripts/eventbus/admin_route.py` returns `200 changed: false` for a well-formed but unchanged body (lines 214-225) and the ADR's own Verification row 260 documents `changed: false`. The ADR contradicts both the code and itself.
- Decision Detail #6 (line 83) ends "...and a TOML authorization mapping reaches the Consumer principal through it.", a trailing clause that does not parse.
- The threat model is stated as "multi-tenant" (Alternative A, line 152) and "single-operator" (Alternative B, lines 157-158) in adjacent alternatives, and the Ongoing Risks section says production deployments "should use a proper identity store" (line 187).

## Reason for Change
ADR-013 governs a security boundary; incorrect invariant mappings leave the most security-relevant behavior (the mappings themselves) unverified, and the no-op contradiction makes the contract ambiguous. These are documentation defects in an already-accepted ADR. The EventBus is kept in service (maintainer decision 2026-11-09), so the fix is not conditional on any pending decision.

## Implementation Intent
Edit ADR-013 only, to (1) re-map the three mis-mapped Verification rows to what they actually verify, (2) reconcile Decision Detail #12 with the implemented empty-vs-no-op contract, (3) repair the broken `load_config()` sentence, and (4) standardize the threat model to single-operator and drop the identity-store sentence. Every edit preserves ADR invariants, references, test citations, Known Deviations, and Approval text. No code, config, credential model, or governance approval changes.

## Requirements
- `REQ-001`: Re-map the three incorrect Verification-table entries so each verifies what it actually tests (`persistent: false` → Decision Detail #10; the empty-body 422 and no-op `changed: false` rows → Decision Detail #12), removing the wrong INV-03/INV-04 mappings (ADR-013 lines 258-260).
- `REQ-002`: Reconcile Decision Detail #12 (line 103) with the implemented contract: an empty or malformed body is rejected with HTTP 422, while a well-formed but unchanged body returns `200 changed: false`; state this explicitly so the ADR no longer contradicts `admin_route.py` or Verification row 260.
- `REQ-003`: Repair the grammatically broken trailing clause of Decision Detail #6 (line 83) so the sentence parses and states the fail-closed `load_config()` behavior accurately.
- `REQ-004`: Standardize the threat model to single-operator by resolving the "multi-tenant"/"single-operator" alternation in the Alternatives Considered section (lines 152, 157-158).
- `REQ-005`: Remove the "proper identity store in production" sentence from Ongoing Risks (line 187).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Correct three wrong Verification-table invariant mappings (lines 258-260), reconcile Decision Detail #12 with the implemented empty-vs-no-op contract (line 103 vs `admin_route.py:214-225`), repair the broken `load_config()` sentence (Decision Detail #6, line 83), standardize the threat model to single-operator (lines 152, 157-158), and remove the "proper identity store" sentence (line 187). All edits preserve invariants, references, test citations, Known Deviations, and Approval text. | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005 | Verified by reading ADR-013 in full and `scripts/eventbus/admin_route.py` (empty body → 422 at :125-129; unchanged body → 200 `changed:false` at :214-225); the mis-mappings, no-op drift, broken sentence, and threat-model alternation are confirmed against current ADR text. | None (documentation-only) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/admin_route.py` | State the implemented empty-vs-no-op contract that ADR-013 Decision Detail #12 and Verification rows 259-260 must match (empty body → 422 at :125-129; unchanged body → 200 `changed:false` at :214-225; `expected_generation` 409 at :161-169). | REQ-002 |
| `scripts/eventbus/config.py` | Confirm the fail-closed `load_config()` key-validation behavior that the repaired Decision Detail #6 sentence must describe. | REQ-003 |
| `scripts/eventbus/auth.py` | Confirm the generation counter, control-plane credential roles, and principal map that ADR-013 describes, so corrections do not diverge from the documented contract. | REQ-001, REQ-004 |

## Acceptance Criteria
- Every Verification-table row maps to the invariant or Decision Detail it actually tests; no row maps a persistence or no-op behavior to INV-03 or INV-04 (`REQ-001`).
- Decision Detail #12 distinguishes empty/malformed body (422) from well-formed-but-unchanged body (200 `changed: false`) and no longer asserts that a no-op is rejected with 422 (`REQ-002`).
- Decision Detail #6 reads as a complete, grammatical sentence (`REQ-003`).
- The threat model is stated consistently as single-operator with no "multi-tenant" alternative (`REQ-004`).
- The "proper identity store in production" sentence is removed (`REQ-005`).
- `check_adr_preservation.py` reports no ERROR (no invariant, reference, test citation, Known Deviation, or Approval text changed); `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, and `check_docs_japanese.py` pass.

## Tests
N/A: this Plan is documentation-only and modifies no Python file under `scripts/` or `tools/`, so no unit/integration test is written and the validation-quality baseline is N/A (see `Validation plan` for the documentation checkers that gate the edit).

## Documentation Impact
ADR-013 (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`) is the sole affected document. It is the authentication/authorization contract for the EventBus domain; load it via `docs/00_index.md` "Document References by Task" under the eventbus/security area. The ADR index (`docs/10_adr/adr_01_index.md`) references ADR-013 only structurally (title, authority graph, INV-02/INV-07 matrix rows); body edits do not change the graph or cited test paths, so the index does not require regeneration (recorded in `Assumptions`).

## Assumptions
- The verified defects are confined to ADR-013. The issue's other doc targets (`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_01_index.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`) were inspected during verification and found not to require modification; they are therefore out of scope, not Reference Files.
- The ADR index does not need regeneration after these body edits: the authority graph (`ADR-013 → ADR-002, ADR-006`), the area assignment, and the cited test paths (`tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/eventbus/test_eventbus_auth.py`) are unchanged, so `generate_adr_authority.py --check` should report no drift.
- Overlap with sibling Plans in this batch is compatible: this Plan touches only ADR-013; adrrev007 targets `agent_10_01` (posture fail-closed ops) and adrrev008/adrrev009 target ADR-008 in sections distinct from ADR-013. No file appears in more than one frozen Plan.
- Correcting Decision Detail #12 to match the code is a documentation correction, not a new decision: the code already returns `200 changed: false` for an unchanged body, so the ADR is made truthful rather than re-decided. Whether to instead standardize no-op as 422 by changing the code is a maintainer decision (UNK-02), deferred.
- `check_adr_preservation.py` compares against `HEAD`; edits that change a Decision, Failure Policy, or normative-keyword count raise a WARNING, not an ERROR. The Detail #12 correction is expected to touch a Decision's wording, so a WARNING is possible and acceptable if it does not also alter an invariant, reference, test citation, Known Deviation, or Approval text.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Merge `auth_token` and `admin_token` into one control-plane credential. Both exist with identical `_CONTROL_PLANE_ROLES` ({OPERATOR, MONITORING, ADMIN}) and `admin_token` holds no Consumer role, so they are functionally redundant (`auth.py:96-98,174-223`). Merging removes a config key (breaking config load, per the issue's Constraint) and has blast radius across config/tests/docs. | No maintainer ruling on whether redundancy justifies a config-breaking merge. | Maintainer decision; record outcome in ADR-013 Consequences if adopted. Not implemented here. | False |
| UNK-02 | Standardize the no-op outcome as HTTP 422 and remove the `changed` response field. The code correctly distinguishes empty/malformed body (422) from well-formed-but-unchanged body (200 `changed: false`); standardizing to 422 would discard that distinction and risk regression. | No maintainer ruling on whether the empty-vs-no-op distinction is worth keeping. | Maintainer decision; if adopted, requires code + test + doc changes beyond this Plan's scope. Not implemented here. | False |
| UNK-03 | Reject at `load_config()` any configuration granting one `consumer_id` to more than one principal. Neither `load_config()` nor `EventBusConfig.__post_init__` currently rejects such a grant (only the token-value check in `_build_principal_map()` exists); a genuine gap. Defensible under the single-operator threat model, but a behavioral/code change. | No maintainer ruling on whether to add the guard. | Maintainer decision; if adopted, requires a code change beyond this Plan's scope. Not implemented here. | False |
| UNK-04 | Form of a boot epoch (or hash of the baseline) added to the authorization generation to reject stale post-restart generations with 409. After restart the baseline reloads as generation 0 and runtime overrides are never persisted, so a stale `expected_generation` operates on the freshly-reloaded baseline every observer sees; the vulnerability is theoretical, and the issue lists the epoch form as undecided. | No decided design choice (separate field vs hash of baseline). | Design choice left open; record resolution in ADR-013 Restart semantics if adopted. Not implemented here. | False |
| UNK-05 | Open dependency `issues/20261109-112504_adrrev001_eventbus-route-handlers.md` (EventBus route handlers, per-route authorization enforcement). This Plan documents existing behavior only and does not require adrrev001 to land first. | adrrev001 is still open in `issues/`. | Recorded as non-blocking; adrrev001's path is the Resolution Path. | False |
| UNK-06 | Open dependency `issues/20261109-112739_adrrev006_eventbus-future-decision.md` (EventBus future-integration decision). This Plan documents the kept-EventBus contract and does not require adrrev006 to land first. | adrrev006 is still open in `issues/`. | Recorded as non-blocking; adrrev006's path is the Resolution Path. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Low | N/A | N/A | Low: documentation-only edit; no deploy step required |

## Design
Classification: **Path A** (small task). Rationale per `skills/issue-to-plan/SKILL.md` Routing: affects 1 file, no public/runtime interface change, no database schema change. Path A analysis depth applies (direct verification only); architecture/dependency/historical/operational analysis is skipped.

Scope rationale: The issue enumerates six Required Changes. Adversarial verification against current source found that only the four categories of ADR-013 documentation defect are real, verifiable, and fixable by editing the ADR. The other four (credential merge, no-op standardization, shared-`consumer_id` guard, boot epoch) are either config-breaking/regression-risk changes or undecided design choices with no maintainer ruling; each is recorded as a Non-blocking Unknown, not implemented. This keeps the Plan within the Path A ≤3-file bound and avoids fabricating governance approvals.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands (for example a `NOT NULL` column added before its write path):

1. **Phase 1: Correct the Verification table** (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, REQ-001)
   - [ ] Re-map line 258 (`persistent: false`) from INV-03 to what it verifies (Decision Detail #10, runtime-only persistence).
   - [ ] Re-map lines 259-260 (empty-body 422, no-op `changed: false`) from INV-04 to Decision Detail #12.
   - [ ] Confirm no other Verification row was mis-mapped while editing.
2. **Phase 2: Reconcile the Empty/no-op contract** (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, REQ-002)
   - [ ] Rewrite Decision Detail #12 (line 103) to state empty/malformed body → 422 and well-formed-but-unchanged body → 200 `changed: false`, matching `scripts/eventbus/admin_route.py:125-129,214-225` and Verification row 260.
   - [ ] Ensure the rewrite does not alter INV-04 or any other invariant wording.
3. **Phase 3: Repair the broken `load_config()` sentence** (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, REQ-003)
   - [ ] Rewrite the trailing clause of Decision Detail #6 (line 83) so it parses and states the fail-closed key-validation plus shared-token-value rejection accurately.
4. **Phase 4: Standardize the threat model** (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, REQ-004)
   - [ ] Resolve the "multi-tenant"/"single-operator" alternation in Alternatives Considered (lines 152, 157-158) to single-operator.
5. **Phase 5: Remove the identity-store sentence** (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, REQ-005)
   - [ ] Delete the "proper identity store in production" sentence from Ongoing Risks (line 187).
6. **Phase 6: Deployment & Verification** (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
   - [ ] Run the documentation checkers in the Validation plan; confirm `check_adr_preservation.py` reports no ERROR against `HEAD`.
   - [ ] Confirm the ADR index still passes `generate_adr_authority.py --check` (no graph/test-path drift).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Documentation structure/quality | `uv run python tools/check_docs_quality.py` | Pass |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Documentation structure (size, front matter, related-doc coverage, links) | `uv run python tools/check_docs_structure.py` | Pass |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Documentation content policy (no implementation-detail warnings) | `uv run python tools/check_docs_content_policy.py` | Pass |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | No Japanese text remains | `uv run python tools/check_docs_japanese.py` | Pass |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | ADR preservation (invariants/references/test citations/Known Deviations/Approval unchanged vs `HEAD`) | `uv run python tools/check_adr_preservation.py` | No ERROR (a WARNING on Decision/normative-keyword count change is acceptable) |
| `docs/10_adr/adr_01_index.md` | ADR authority graph drift after ADR-013 body edits | `uv run python tools/generate_adr_authority.py --check` | No drift |

## Risks
- **Risk**: Editing Decision Detail #12 to match the code may be read as changing an accepted decision rather than correcting a documentation error. → **Mitigation**: The edit makes the ADR describe the already-implemented behavior (200 `changed: false`); it does not introduce new behavior. Recorded as a correction, and the alternative (standardize to 422 via code) is deferred as UNK-02.
- **Risk**: `check_adr_preservation.py` may raise a WARNING because a Decision's wording changes. → **Mitigation**: A WARNING is non-blocking; verify it does not also flag an invariant, reference, test citation, Known Deviation, or Approval change.
- **Risk**: Re-mapping Verification rows could accidentally alter an invariant's meaning or a cited test. → **Mitigation**: Only the `Verifies` cell of the three rows is changed; invariant text and test citations are untouched; confirmed by `check_adr_preservation.py` and `generate_adr_authority.py --check`.
- **Risk**: Standardizing the threat model could remove a legitimately recorded alternative. → **Mitigation**: Only the "multi-tenant"/"single-operator" wording in the Alternatives Considered section is reconciled to single-operator; both alternatives and their advantages/disadvantages are retained, only the inconsistent threat-model label is unified.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the Verification table (REQ-001) | Pending | — | — | |
| 2 | Reconcile the Empty/no-op contract (REQ-002) | Pending | — | — | |
| 3 | Repair the broken `load_config()` sentence (REQ-003) | Pending | — | — | |
| 4 | Standardize the threat model (REQ-004) | Pending | — | — | |
| 5 | Remove the identity-store sentence (REQ-005) | Pending | — | — | |
| 6 | Deployment & Verification | Pending | — | — | |

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
- **Source issue**: `issues/20261109-112952_adrrev010_eventbus-authz-harden.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-000400
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Adversarial Verification: Verification-table mis-mappings (lines 258-260 map to INV-03/INV-04) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 1 | AC 1 | `check_adr_preservation.py`, `generate_adr_authority.py --check` | Confirmed by repository evidence |
| REQ-002 | Adversarial Verification: no-op drift (Decision Detail #12 line 103 vs `admin_route.py:214-225` and row 260) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 2 | AC 2 | `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-003 | Adversarial Verification: broken `load_config()` sentence (Decision Detail #6 line 83) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 3 | AC 3 | `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-004 | Adversarial Verification: threat-model alternation (lines 152, 157-158) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 4 | AC 4 | `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-005 | Adversarial Verification: "proper identity store" sentence (line 187) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 5 | AC 5 | `check_docs_quality.py` | Confirmed by repository evidence |
