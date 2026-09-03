## Goal
Once Phase 0 clears: update
`docs/04_mcp_06_17_local-to-production-auth-migration.md`'s Migration Steps
to match the four dependency Plans' actual landed procedures, consolidating
with (not duplicating) `localcleanup`'s `docs/02_deployment.md`
migration-procedure addition — resolving `UNK-02` (`REQ-006`).

## Scope
- **In-Scope**: `docs/04_mcp_06_17_local-to-production-auth-migration.md`
  only — its Migration Steps and Troubleshooting sections, plus the
  `UNK-02` canonical-document decision (which document is canonical, and how
  the other cross-links to it).
- **Out-of-Scope**: `docs/02_deployment.md` itself (owned by `localcleanup`'s
  own Plan/implementation-procedure — this row only decides how it
  cross-links, does not rewrite it); the other 5 target files;
  `localremoval`'s/`loopbackonly`'s/`mcpauth`'s own implementations.

## Assumptions
- Phase 0 is **not** cleared as of 2026-09-03 (re-confirmed, same status as
  seq 01-04). This document's Procedure is Blocked until all four dependency
  Plans land.
- Re-confirmed 2026-09-03:
  `docs/04_mcp_06_17_local-to-production-auth-migration.md` exists with
  "Migrating from local to production environments", Migration Steps, and
  Troubleshooting sections — this is the more specific, pre-existing
  migration document `UNK-02` identifies.
- Re-confirmed 2026-09-03: `localcleanup`'s own implementation-procedure
  document (`implementations/20260903-171040_01_docs_02_deployment.md.md`,
  generated this session) added a "Production-Only Migration Procedure"
  section to `docs/02_deployment.md` — per this Plan's `UNK-02`, that
  addition was made without discovering this file's existing, more specific
  content. `localcleanup`'s own implementation-procedure document is itself
  still Pending (not yet executed) as of 2026-09-03, so `docs/02_deployment.md`
  does not yet actually contain that section — the consolidation decision
  below must be re-verified once `localcleanup`'s row actually executes,
  since its exact section title/content is not final until then.

## Design decisions
- Resolve `UNK-02` by designating `04_mcp_06_17_local-to-production-auth-migration.md`
  as the canonical migration-procedure document (it is more specific — this
  Plan's Background finds it dedicated to exactly this migration, with
  Migration Steps and Troubleshooting sections already structured for it)
  and making `docs/02_deployment.md`'s section a short summary that
  cross-links to it, rather than the reverse — avoids the
  `docs/00_governance_04_documentation-checks.md` `GV-011` duplicated-
  canonical-source concern the source Plan's Design section raises.
- Update Migration Steps to reference the four dependency Plans' actual
  landed procedures (not their Plan-time text), consistent with this Plan's
  repeated re-verification requirement.

## Alternatives considered
- Keeping both `docs/02_deployment.md` and `04_mcp_06_17` as independent,
  full migration procedures — rejected: this is exactly the "duplicated
  canonical source" problem `GV-011` flags; a reader following one document
  could miss updates only made to the other.
- Making `04_mcp_06_17` the summary and `docs/02_deployment.md` the
  canonical document (reverse of Design decision) — rejected: `04_mcp_06_17`
  is the more specific, purpose-built document for this exact migration;
  `docs/02_deployment.md` is a general deployment guide that should
  reference specialized procedures, not own them.

## Implementation
### Target file
`docs/04_mcp_06_17_local-to-production-auth-migration.md`

### Procedure
1. Confirm Phase 0's precondition is met. As of 2026-09-03 it is not — do
   not proceed past this step until it is.
2. Once cleared, re-read `docs/02_deployment.md`'s actual landed
   "Production-Only Migration Procedure" section (from `localcleanup`'s
   execution) and this file's existing Migration Steps/Troubleshooting
   content in full.
3. Update this file's Migration Steps to match the four dependency Plans'
   actual landed procedures (backup, bind-address/auth-token migration,
   strict-validation verification, full restart, post-restart verification,
   conditional deletion — cross-checking against `docs/02_deployment.md`'s
   own version for consistency, not duplication).
4. Add a note at the top of `docs/02_deployment.md`'s corresponding section
   (coordinate with `localcleanup`'s already-landed content — this is an
   edit to the cross-link only, not a rewrite of that section) pointing to
   this file as the canonical, detailed procedure — this Plan's own target
   scope for this row is `04_mcp_06_17` only, so if `docs/02_deployment.md`
   itself needs the reciprocal cross-link edited, flag it as requiring the
   corresponding `localcleanup`-lineage document to be updated, per this
   workflow's additional-target-file-discovery rule if it is not already
   covered by an existing target row.

### Method
Direct `Edit` to `docs/04_mcp_06_17_local-to-production-auth-migration.md`,
once Phase 0's precondition is confirmed met and `docs/02_deployment.md`'s
actual landed content is re-read.

### Details
- Re-verify `docs/02_deployment.md`'s actual section title and content
  before writing any cross-reference to it — `localcleanup`'s
  implementation-procedure document (as generated) proposes "Production-Only
  Migration Procedure" as the heading, but this may change during that row's
  own execution.
- If reconciling requires editing `docs/02_deployment.md` itself (not just
  this file), that is a change to a file outside this row's own Target file
  — per `skills/plan-to-implementation-procedure/workflow.md` Step 3, this
  would be an additional-target-file discovery requiring the Plan to be
  amended, UNLESS `docs/02_deployment.md` is already a target of a sibling
  Plan (`localcleanup`) whose own implementation-procedure document can be
  the one edited instead — prefer amending `localcleanup`'s document over
  stopping this cycle, since it already owns that file.

## Compatibility considerations
N/A: documentation-only, no code compatibility impact. Coordinate with
`localcleanup`'s `docs/02_deployment.md` addition so the two documents stay
consistent (per `UNK-02`).

## Security considerations
None directly — documentation-only migration-procedure content. Accuracy
matters for anyone executing an actual production migration, but this
document does not implement any control.

## Rollback considerations
Single-file edit under version control; revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_17_local-to-production-auth-migration.md` | Documentation structure/quality check | `uv run python tools/check_docs_quality.py` | No structural findings in the changed file |
| `docs/04_mcp_06_17_local-to-production-auth-migration.md` | Structure validation | `uv run python tools/check_docs_structure.py` | Internal links resolve; Front Matter intact |
| `docs/04_mcp_06_17_...md`, `docs/02_deployment.md` | Manual cross-check | Manual review resolving `UNK-02` | Exactly one canonical migration-procedure document, with the other cross-linking to it |

## Completion criteria
- `04_mcp_06_17`'s Migration Steps match the four dependency Plans' actual
  landed procedures (AC-6).
- `04_mcp_06_17` and `docs/02_deployment.md` are consolidated (one
  canonical, one cross-linking), not independently duplicated (AC-6,
  `UNK-02` resolved).
- Not completable until Phase 0 clears.

## Out of scope
`docs/02_deployment.md`'s own content (owned by `localcleanup`'s lineage);
the other 5 target files; `localremoval`'s/`loopbackonly`'s/`mcpauth`'s own
implementations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Phase 0 not cleared as of 2026-09-03; also depends on `localcleanup`'s own implementation-procedure document (seq 01 of that Plan) having executed first |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Blocked | — | — | Cannot meaningfully run until Phase 0 clears |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document's own target file is the documentation being updated; no separate doc row applies |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Phase 0 not cleared: `localremoval`, `loopbackonly`, `mcpauth` remain under `plans/`; `localcleanup` is in `plans/done/` but its own implementation-procedure document (`implementations/20260903-171040_01_docs_02_deployment.md.md`) is unexecuted | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20260902-143338_adrprodonly_supersede_profile_based_design_docs_sync_references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-093353_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-171632
- **Related target files**: docs/04_mcp_06_17_local-to-production-auth-migration.md
