## Goal
Once Phase 0 clears (`localremoval`, `loopbackonly`, `mcpauth`,
`localcleanup` all implemented): revise ADR-004 in place per the 2026-09-03
architecture-owner sign-off (`REQ-002`, `UNK-01` resolved — no new
superseding ADR is created), and update its `Known Deviations` section to
reflect the completed implementation (`REQ-008`).

## Scope
- **In-Scope**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
  only — the in-place revision (Decision Group 1 and related sections) and
  the `Known Deviations` update.
- **Out-of-Scope**: creating a new superseding ADR (explicitly resolved
  against, per architecture-owner sign-off); the other 5 target files;
  `localremoval`'s/`loopbackonly`'s/`mcpauth`'s/`localcleanup`'s own
  implementations.

## Assumptions
- Phase 0 is **not** cleared as of 2026-09-03 (re-confirmed): `localremoval`
  (`plans/20260903-091417_plan.md`), `loopbackonly`
  (`plans/20260903-091921_plan.md`), and `mcpauth`
  (`plans/20260903-092407_plan.md`) remain under `plans/`; `localcleanup`
  (`plans/done/20260903-092746_plan.md`) reached `plans/done/` this session
  but its own implementation-procedure document remains unexecuted. This
  document's entire Procedure is therefore Blocked until all four land.
- Re-confirmed 2026-09-03: ADR-004's `Decision Group 1` heading is now at
  line 53 (not the Plan's originally-cited `48-51` — line numbers shifted
  due to unrelated intervening edits; content unchanged) and its `Known
  Deviations` section is at line 461, with the
  `ADR-004-D1-profile-config-model-still-present` entry at line 463 (not the
  originally-cited `449-455`) — corrected in the source Plan during this
  cycle's revalidation.
- The architecture-owner sign-off (`UNK-01`, resolved 2026-09-03) directs
  revising ADR-004 in place, consistent with `localremoval`'s own sign-off —
  this document's Procedure follows that direction; it does not re-litigate
  supersede-vs-revise.

## Design decisions
- Revise in place per ADR-004's own governance guidance ("Accepted後に現在の
  判断を変更する場合は、本ADR本文を直接更新する") — add a dated revision note
  within the ADR itself rather than creating a separate superseded document,
  per the architecture-owner sign-off.
- Update `Known Deviations` to reflect the *completed* implementation only
  once Phase 0 actually clears — do not mark deviations resolved
  preemptively based on the dependency Plans' own text.

## Alternatives considered
- Creating ADR-013 (or similar) as a new superseding ADR — rejected per the
  2026-09-03 architecture-owner sign-off (`UNK-01` resolved against this
  option).

## Implementation
### Target file
`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure
1. Confirm Phase 0's precondition is met (all four dependency Plans
   implemented, archived under `implementations/done/`, not merely
   `plans/done/`). As of 2026-09-03 this is not the case — do not proceed
   past this step until it is.
2. Once cleared, revise `Decision Group 1` (currently: single common
   failure-handling policy across all environments, `security_profile`
   distinguishing Local/Production) to describe the final,
   Local-mode-removed, Production-only state, per `localremoval`'s,
   `loopbackonly`'s, and `mcpauth`'s actual landed text.
3. Add a dated revision note within the ADR body recording this change and
   citing the architecture-owner sign-off date (2026-09-03) and the four
   dependency Plans by path.
4. Update the `Known Deviations` section: mark
   `ADR-004-D1-profile-config-model-still-present` resolved if the
   dependency Plans' landed implementation actually removes the
   `security_profile`-based classification branch; add or resolve the
   `ProductionConfigValidator` severity-downgrade deviation this Plan's seq
   01 row (REQ-001) records, once `localremoval`'s `REQ-004` lands.

### Method
Direct `Edit` to `docs/adr/ADR-004-environment-failure-handling-policy.md`,
once Phase 0's precondition is confirmed met.

### Details
- Re-read the four dependency Plans' actual landed documentation (not their
  Plan-time text) before revising, per the source Plan's Assumptions
  ("if any deviates materially, this Plan's Implementation steps for the
  affected Requirement must be re-verified against the actual landed text").
- Preserve ADR-004's existing structure (Context, Decision, Implementation
  Notes, Known Deviations) — this is a revision, not a rewrite.
- Cross-check against this Plan's seq 01 row (`docs/adr-index.md`)'s ADR-004
  row/dependency-graph update — both rows must describe the same final
  state.

## Compatibility considerations
N/A: documentation-only, no code compatibility impact. `docs/00_security_01`,
`04_mcp_06_17`, and `adr-index.md` all reference ADR-004 — coordinate this
edit with seq 01/03/05's own updates in the same Phase-0-cleared cycle.

## Security considerations
None directly — documentation-only ADR revision. The ADR itself governs
security-relevant failure-handling policy, so accuracy matters, but this
document does not implement any security control.

## Rollback considerations
Single-file edit under version control; revert via `git revert` if needed.
ADR-004 is referenced by `docs/00_security_01`, `04_mcp_06_17`, and
`adr-index.md` — a revert here should be coordinated with those files if
already edited in the same cycle.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-004-environment-failure-handling-policy.md` | Documentation structure/quality check | `uv run python tools/check_docs_quality.py` | No structural findings in the changed file |
| `docs/adr/ADR-004-environment-failure-handling-policy.md` | Structure validation | `uv run python tools/check_docs_structure.py` | Internal links resolve; Front Matter intact |
| Repository-wide | Manual repository search | Search for retired profile keys/wording per source Issue Testing Expectations | No active document describes Local mode as supported |

## Completion criteria
- ADR-004 is revised in place (not superseded); decision history is
  preserved via a dated revision note (AC-2).
- `Known Deviations` reflects the completed implementation state (AC-8).
- Not completable until Phase 0 clears.

## Out of scope
Creating a new superseding ADR; the other 5 target files;
`localremoval`'s/`loopbackonly`'s/`mcpauth`'s/`localcleanup`'s own
implementations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Phase 0 not cleared as of 2026-09-03 — see Assumptions |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Blocked | — | — | Cannot meaningfully run until Phase 0 clears |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document's own target file is the documentation being updated; no separate doc row applies |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Phase 0 not cleared: `localremoval`, `loopbackonly`, `mcpauth` remain under `plans/`; `localcleanup` is in `plans/done/` but its own implementation-procedure document is unexecuted | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-008
- **Source issue**: issues/done/20260902-143338_adrprodonly_supersede_profile_based_design_docs_sync_references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-093353_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-171632
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md
