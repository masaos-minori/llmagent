## Goal
- Correct ADR-013 where it is stale or incomplete without changing any decision: rename the EventBus function (REQ-003: update every mention), complete Scope and Implementation References, add the verified TTL baseline note, and re-check the decision-reference claim (REQ-004: ADR-013 describes only behavior that exists).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the sections named in Procedure of `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`.
- Depends on the seq 01 document (new function name must exist) and the seq 05 document (the TTL note cites its verified behavior).

## Assumptions
- A wording, evidence, or reference edit does not reopen ADR approval (`docs/00_governance/governance_01_documentation-policy.md`); this document changes no Decision Details, Invariant, Blocking value, authority edge, Approval text, or Known Deviations text.
- Three mentions refer to the EventBus function (Current State, Decision Details 1, Implementation References); three refer to the MCP function of the same old name (Constraints, Rationale 4, the precedent bullet of Implementation References) and stay (verified in Step 3a).
- The claim that Decision Details references do not match the list was not reproduced in Step 2 (Plan UNK-08); this document re-checks it once and fixes only a reproduced mismatch.
- If a seq 05 test contradicts a draft statement of the TTL note, the note follows the test.

## Design decisions
- Describe the TTL baseline behavior in Implementation Notes, not in Decision Details, so no decision text changes.
- Name behavior and symbols only; state no config value (the TTL bounds are owned by `config/eventbus.toml`).

## Alternatives considered
- Add the TTL behavior as new Decision Details or Invariants: rejected here, it changes decisions and needs an approval record (Plan UNK-05).

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure
1. Rename `attach_auth_middleware` to `attach_request_id_middleware` in Current State, Decision Details 1, and the first Implementation References bullet; leave the three MCP-function mentions unchanged.
2. Scope: add `scripts/eventbus/admin_route.py` and `scripts/eventbus/authz_ttl.py` to Components, and `tests/eventbus/test_admin_topics_authorization.py` and `tests/eventbus/test_authz_generation_ttl.py` to Tests.
3. Implementation References: add bullets for `scripts/eventbus/admin_route.py` (`update_topics_authorization()`) and `scripts/eventbus/authz_ttl.py` (`sweep_expired_authorizations()`, `authz_sweep_loop()`); add the two test files to the Tests bullet.
4. Implementation Notes: after the existing paragraph, add the TTL baseline note (Method).
5. Re-check decision references: list every "Decision Details #N" reference in this ADR and confirm each points at the intended item; fix only a reproduced mismatch and record the outcome for the commit message.

### Method
- The TTL note states, as plain English prose, the behavior pinned by `TestRestartBaselineAudit` and the seq 05 tests: the baseline hash covers only the consumer and topic pairs, so expiries never change it; expiry entries live only in the in-force generation, so a restart publishes generation 0 with none; a pair carried over by an update keeps its previous expiry and `ttl_seconds` applies only to newly granted pairs; the sweep changes runtime state only, so a pair that the TOML baseline lists, removed and re-granted with a TTL, is removed at expiry and returns after a restart.
- Use the existing heading style and bullet format of the ADR; English only.

### Details
- Do not edit Ongoing Risks, Invariants, Decision Details wording (other than the symbol), Approval, or Known Deviations; those belong to the owner-decision items.
- If `check_docs_consistency` or `check_adr_preservation` flags only the added Implementation References entries, that is the expected additive finding; any finding on decision text means the edit went too far and MUST be undone.

## Compatibility considerations
N/A: documentation only; the ADR index and Invariant matrix rows are unchanged.

## Security considerations
N/A: documentation only; no secret values appear in the added text.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.
- `uv run python tools/check_docs_consistency.py --domain eventbus`.
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_authority.py`.
- `uv run python .github/run_cited_adr_tests.py`.

## Completion criteria
- Scope and Implementation References list `admin_route.py`, `authz_ttl.py`, `test_admin_topics_authorization.py`, and `test_authz_generation_ttl.py`.
- The EventBus function is named `attach_request_id_middleware` in the three EventBus mentions and unchanged in the MCP mentions.
- Implementation Notes states the TTL baseline behavior as pinned by tests.
- No decision text changed and every checker above passes.

## Out of Scope
- New Invariants, Ongoing Risks changes, JSONL role changes, and audit event naming (Plan Unknowns UNK-02 to UNK-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the ADR sections listed in Procedure | Completed | 20261119-100407 | 20261119-100524 | Step 2 stale check clean; ADR clean at baseline Changed: docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md. Decision-reference re-check: all 7 references resolve (UNK-08 not reproduced, no fix needed). TTL note trimmed to stay under the 32768-byte limit |
| 2 | Run the documentation and ADR checkers named in `routing.md` Tools | Completed | 20261119-100524 | 20261119-102738 | Docs checkers pass (quality, structure, content-policy strict, japanese, consistency eventbus, adr structure/reference/matrix/authority). check_adr_preservation: only expected Implementation References findings plus a Decision wording warning from the symbol rename. ADR-cited tests run once at end of batch End of unit: full suite 12898 passed 7 skipped (not integration/production_paths_allowed/repo_scan); diff-cover 100%; ADR-cited tests 52 passed; validation gates pass |

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
- **Requirement ID**: `REQ-003` (update ADR mentions of the renamed function), `REQ-004` (complete Scope and References, add the TTL note)
- **Source issue**: issues/20261117-123002_adrchk002_eventbus-authz-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-092411_adrchk002_eventbus-authz-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-094420
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`