## Goal
Correct the five verified defects in ADR-013 (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`) so its Verification table, Decision Details #6 and #12, threat-model wording, and Ongoing Risks state the EventBus authentication/authorization contract accurately. Documentation-only: no code, test, config, schema, or governance-approval change.

## Scope
**Release unit**: N/A: not part of a release unit

Single Plan-target row: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (REQ-001..REQ-005, Plan Phases 1-6).

## Assumptions
- Plan dependency conditions are met: adrrev010's PAUSED banner ("halted until adrrev009 lands") was resolved during Plan verification — adrrev009 landed at commit `8ab061b3c` (`plans/done/20261110-233648_adrrev009_adr008-recovery-align.md`), and both dependency issues (`20261109-112504_adrrev001`, `20261109-112739_adrrev006`) are archived in `issues/done/`. The banner was corrected in the Plan file before procedure generation.
- Overlap judgment (ADR-013 is also targeted by two paused Plans, per `check_plan_target_overlaps.py`):
  - `plans/20261111-104605_adrrev016_adr-authority-format.md` (PAUSED) adds an Implementation column to the ADR-013 Automated Tests table. Compatible: this procedure changes only `Verifies` cells (plus one row's descriptive wording), not the table shape. If adrrev016 lands first, re-anchor by text (line numbers shift) before applying the edits here.
  - `plans/20261111-110144_adrrev017_docs-history-wording.md` (PAUSED) removes the "deliberate breaking change ... (owner decision 2026-10-30)" wording from the EBAUTHGEN001 paragraph (current line 95). It labels that paragraph "Decision Detail 12 (line 95)"; numbering drift: in this Plan, "Decision Detail #12" is the Empty/no-op item at line 103. No content overlap: this procedure does not edit line 95 or the EBAUTHGEN001 note, and adrrev017 does not touch Decision #12 (line 103), Verification rows 258-260, the threat model, or line 187.
- The Decision Detail #12 correction documents already-implemented behavior (`scripts/eventbus/admin_route.py`), so it is a documentation correction, not a re-decision. Standardizing no-op to 422 instead is UNK-02 (maintainer decision, out of scope).
- `check_adr_preservation.py` compares against `HEAD`; editing Decision wording may raise a WARNING. A WARNING is acceptable per the Plan; an ERROR (invariant/reference/test-citation/Known-Deviation/Approval change) is not.

## Design decisions
- Verification re-mappings target Decision Details, not invariants, because none of INV-01..INV-07 covers runtime-only persistence or empty/no-op request semantics; the table already permits `Decision Details #N` references (existing precedent: the `load_config()` empty-`auth_token` row verifies "Decision Details #7").
- The shared-token-value rejection in Decision Detail #6 is attributed to the principal-map build (`scripts/eventbus/auth.py:144-163` duplicate-non-empty-token guard, invoked during startup publication), not to `load_config()` itself: `load_config()` performs the key-validation fail-closed (`scripts/eventbus/config.py`), while duplicate token values fail at generation build. The corrected sentence must state this accurately.
- Row 259's descriptive wording ("Empty/no-op body rejected with 422") must be narrowed to "Empty body rejected with 422": the code returns 200 `changed: false` for a no-op (row 260 already says so), and leaving the conflated wording would keep the internal contradiction REQ-001/REQ-002 exist to remove. Only `Verifies` cells plus this one description change are touched; no invariant text or test citation is edited.

## Alternatives considered
- Map rows 258-260 to new invariants — rejected: adding invariants is out of Plan scope (Plan Out-of-Scope explicitly excludes new ADR invariants).
- Change `admin_route.py` to make no-op return 422 so the old ADR text becomes true — rejected: reverses the Plan's documentation-only contract and pre-empts maintainer decision UNK-02.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (edit only).

Reference files (read-only, already verified; do not modify): `scripts/eventbus/admin_route.py`, `scripts/eventbus/config.py`, `scripts/eventbus/auth.py`.

### Procedure
Five text edits, in Plan phase order (Phases 1-5; Phase 6 is the validation pass):

1. **Phase 1 (REQ-001) — Verification table remap.** In the Automated Tests table, change only the `Verifies` cell of three rows:
   - `| Runtime-only persistence: `persistent: false` in admin response | INV-03 | Integration | Yes |` → `Verifies` becomes `Decision Details #10 (runtime-only persistence)`.
   - `| Empty/no-op body rejected with 422 | INV-04 | Integration | Yes |` → `Verifies` becomes `Decision Details #12 (empty body case)`; Test-cell wording becomes "Empty body rejected with 422" (see Design decisions).
   - `| No-op detected: `changed: false` when config unchanged | INV-04 | Integration | Yes |` → `Verifies` becomes `Decision Details #12 (no-op case)`.
   Do not touch any other row, invariant text, or test citation.
2. **Phase 2 (REQ-002) — Decision Detail #12 rewrite.** Replace item 12 (current line 103):
   - Old: `12. **Empty/no-op rejection.** An empty body `{}` or a body that produces no actual change is rejected with HTTP 422 (not reported as a successful change).`
   - New: `12. **Empty-body rejection; no-op reports unchanged.** An empty body `{}` is rejected with HTTP 422 (not reported as a successful change). A well-formed body that produces no actual change is not rejected: the request returns HTTP 200 with `changed: false`, publishes no new generation (`previous_generation` equals `new_generation`), and emits no audit record (per Decision Detail #11).`
   This matches `admin_route.py:125-129` (empty → 422) and `admin_route.py:214-225` (no-op → 200, nothing published). INV-04 and all other invariant wording stay untouched.
3. **Phase 3 (REQ-003) — Decision Detail #6 repair.** Replace the broken trailing clause of item 6 (current line 83). Keep the first sentence verbatim ("Fail-closed rejection of unknown, missing, and incorrectly-typed EventBus configuration keys in `load_config()` — implemented locally, not via `ConfigLoader`."). Replace everything after it with an accurate, grammatical statement of: (a) the duplicate-credential rejection — building the authorization principal map from a loaded config fails closed when distinct token fields share one non-empty token value (`auth.py:144-163` guard, raised at startup generation build, so the config never serves traffic), and (b) Consumer principals take their `consumer_id`/topic authorizations only from the TOML `consumer_authorization`/`topic_authorization` mappings (and admin updates built on top of them). Example shape (implementer may refine wording, must preserve these three facts and nothing new):
   `6. Fail-closed rejection of unknown, missing, and incorrectly-typed EventBus configuration keys in `load_config()` — implemented locally, not via `ConfigLoader`. The same fail-closed posture rejects duplicate credentials: building the authorization principal map fails at startup when distinct token fields share one non-empty token value, so distinct token roles never resolve to the same bearer token. Consumer principals take their `consumer_id` and topic authorizations only from the TOML `consumer_authorization`/`topic_authorization` mappings and admin updates built on top of them.`
4. **Phase 4 (REQ-004) — threat-model wording.** In Alternative A's Reason for Rejection (current line 152), replace "loopback-only binding alone is insufficient for a multi-tenant security model even on localhost" with wording consistent with the project's single-operator threat model, e.g. "loopback-only binding alone is insufficient as the security boundary even for the single-operator deployment model this project targets". Alternative B (lines 157-158, "single-operator use case") is already consistent — leave unchanged. Advantages/Disadvantages of both alternatives are retained.
5. **Phase 5 (REQ-005) — remove identity-store sentence.** In Ongoing Risks (current line 187), delete the trailing sentence so the bullet reads: `- Consumer identity binding assumes the token encodes the consumer identity.`

### Method
Direct text edits to the single ADR file with exact old-text anchors as quoted above (line numbers are from the working tree at procedure generation time; re-anchor by text if the file shifted, e.g. after a paused sibling Plan lands).

### Details
- Verified code anchors: `admin_route.py:125-129` empty body → 422; `:143-153` `expected_generation` 422 cases; `:161-169` 409 generation conflict; `:214-225` no-op → 200 `changed: false`, `previous_generation == new_generation`, `changed_count: 0`; `auth.py:144-163` duplicate-non-empty-token guard with error "share a non-empty value"; `auth.py:95-98,170-223` control-plane roles / consumer principal map.
- Verified test anchors (do not edit, cited as evidence the remapped rows actually test): `tests/eventbus/test_admin_topics_authorization.py` `TestAdminGating::test_empty_body_rejected` (empty → 422), `test_response_includes_persistent_and_changed` (persistent/changed contract), `test_response_changed_false_when_noop` (no-op → 200 `changed: false`).
- INV-03 = operator-gated DLQ/replay; INV-04 = `load_config()` key validation. Neither covers the three remapped rows — basis for REQ-001.

## Compatibility considerations
- Documentation-only change; no runtime, API, config, or test behavior change. ADR-013 body edits do not change the authority graph, area assignment, or cited test paths, so `docs/10_adr/adr_01_index.md` needs no regeneration.
- Paused sibling Plans adrrev016/adrrev017 overlap the same file with compatible, non-contradicting edits (see Assumptions); whichever lands second must re-anchor by text.

## Security considerations
No security posture change: the edits make the ADR describe the implemented fail-closed behavior (401/403/422/409 semantics, duplicate-token rejection) more accurately. No secret/token values are introduced into the document.

## Rollback considerations
Single-file documentation change: revert with `git checkout -- docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`. No data, service, or config rollback needed.

## Validation plan
Run from the repository root (Plan Validation plan):
1. `uv run python tools/check_docs_quality.py` — Pass
2. `uv run python tools/check_docs_structure.py` — Pass
3. `uv run python tools/check_docs_content_policy.py` — Pass
4. `uv run python tools/check_docs_japanese.py` — Pass
5. `uv run python tools/check_adr_preservation.py` — No ERROR vs `HEAD` (a WARNING on Decision/normative-keyword count change is acceptable; it must not flag an invariant, reference, test citation, Known Deviation, or Approval change)
6. `uv run python tools/generate_adr_authority.py --check` — no drift on `docs/10_adr/adr_01_index.md`

## Completion criteria
- Verification rows 258-260 (pre-edit numbering) map to Decision Details #10/#12 and no persistence or no-op row maps to INV-03/INV-04 (AC 1 / REQ-001).
- Decision Detail #12 distinguishes empty body (422) from well-formed-but-unchanged (200 `changed: false`) (AC 2 / REQ-002).
- Decision Detail #6 reads as a complete, grammatical sentence with the three required facts (AC 3 / REQ-003).
- Threat model is stated consistently as single-operator; no "multi-tenant" wording remains in Alternatives Considered (AC 4 / REQ-004).
- The "proper identity store in production" sentence is removed (AC 5 / REQ-005).
- All six Validation plan commands pass with the stated outcomes (AC 6).

## Out of Scope
- Merging `auth_token`/`admin_token` (UNK-01), standardizing no-op to 422 (UNK-02), shared-`consumer_id` guard in `load_config()` (UNK-03), boot epoch for generations (UNK-04) — maintainer decisions recorded in the Plan.
- Any change to `scripts/eventbus/`, tests, `config/eventbus.toml`, other docs, ADR index regeneration, ADR-013 invariants, approvals, or Known Deviations.
- adrrev016's Implementation-column work and adrrev017's EBAUTHGEN001 wording work (separate paused Plans).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the five ADR-013 text edits per Implementation > Procedure (Phases 1-5) | Pending | — | — | |
| 2 | No test changes (documentation-only Plan; tests are evidence anchors only) | N/A | — | — | Plan Tests section is N/A |
| 3 | Run the validation sequence (Validation plan; docs-only scope of `rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation beyond the target file | N/A | — | — | Target file is the only doc in scope; index needs no regeneration |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: `issues/done/20261109-112952_adrrev010_eventbus-authz-harden.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261111-000400_adrrev010_eventbus-authz-harden.md` (archived to `plans/done/` after procedure generation)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-212354
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
