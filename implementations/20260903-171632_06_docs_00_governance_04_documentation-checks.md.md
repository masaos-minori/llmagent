## Goal
Once Phase 0 clears: extend
`docs/00_governance_04_documentation-checks.md`'s stale-term detection scope
to include the specific retired runtime-profile terms this migration
introduces (`SecurityProfile.LOCAL`, `allow_public_bind`, empty
`auth_token`), building on `compatterms`'s `GV-020` framework rather than
defining a competing mechanism (`REQ-007`).

## Scope
- **In-Scope**: `docs/00_governance_04_documentation-checks.md` only — the
  `GV-020` row (or a new row referencing it) and its allowlist for
  legitimate "local" meanings (filesystem, Git, RAG, database, process,
  localhost).
- **Out-of-Scope**: `tools/check_compat_shims.py`'s actual implementation
  (this row is documentation of the governance requirement, not the checker
  code itself — implementing the check is a separate concern this document
  only specifies); the other 5 target files;
  `localremoval`'s/`loopbackonly`'s/`mcpauth`'s/`localcleanup`'s own
  implementations.

## Assumptions
- Phase 0 is **not** cleared as of 2026-09-03 (re-confirmed, same status as
  seq 01-05). This document's Procedure is Blocked until all four dependency
  Plans land.
- Re-confirmed 2026-09-03: `compatterms`'s `GV-020` framework **has landed**
  (`plans/done/20260903-090945_plan.md`, fully implemented and archived this
  session) — `docs/00_governance_04_documentation-checks.md` already
  contains the `GV-020` row (line 290: "Removed-name reintroduction in
  current specifications", `check_compat_shims.py --check-removed-names`,
  Warning/Partial) and Follow-up item 14 ("Implement the context-aware
  (retained-but-superseded) detection case"). Per `REQ-007`'s own
  conditional wording ("building on GV-020's framework if it has landed...
  rather than defining a competing mechanism"), this row can definitively
  build on `GV-020` rather than needing a standalone fallback mechanism —
  this resolves the uncertainty the source Plan's Risks section flagged as a
  possible fallback case.

## Design decisions
- Extend `GV-020`'s existing scope/allowlist rather than adding a new,
  separate `GV-*` row — `GV-020`'s own Follow-up item 14 already anticipates
  "implement the context-aware (retained-but-superseded) detection case",
  which is exactly the kind of extension this Requirement calls for
  (detecting `SecurityProfile.LOCAL`/`allow_public_bind`/empty `auth_token`
  as retired-but-potentially-reintroduced terms).
- Keep the allowlist explicit and enumerated (filesystem, Git, RAG,
  database, process, localhost) rather than a broad heuristic — avoids false
  positives on the many legitimate uses of "local" throughout this
  repository's documentation.

## Alternatives considered
- Defining a new, standalone stale-term-detection mechanism instead of
  extending `GV-020` — rejected per `REQ-007`'s own wording, now that
  `compatterms`'s `GV-020` is confirmed landed: reusing the existing
  framework avoids maintaining two parallel removed-name-detection
  mechanisms.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
1. Confirm Phase 0's precondition is met. As of 2026-09-03 it is not — do
   not proceed past this step until it is (this is independent of `GV-020`'s
   own landed status, which only affects *how* this row is implemented, not
   *when*).
2. Once cleared, update `GV-020`'s row (or its Follow-up item 14 detail) to
   name the specific retired terms this migration introduces:
   `SecurityProfile.LOCAL`, `allow_public_bind`, empty `auth_token`.
3. Add or update the allowlist documentation for legitimate "local" meanings
   this check must not flag: filesystem paths, Git operations, RAG local
   fallback, local database access, local process boundaries,
   localhost/loopback networking.
4. Cross-reference `localremoval`'s, `loopbackonly`'s, and `mcpauth`'s actual
   landed terminology (not their Plan-time text) to confirm the exact retired
   term spellings match what the checker should detect.

### Method
Direct `Edit` to `docs/00_governance_04_documentation-checks.md`, once Phase
0's precondition is confirmed met.

### Details
- `GV-020`'s row is at line 290 as of 2026-09-03; its Follow-up item 14 is
  at line 319 — re-confirm these line numbers have not shifted before
  editing, per this session's own pattern of documents shifting under
  concurrent edits.
- This row documents the *governance requirement* (what should be detected,
  and the allowlist) — it does not itself implement
  `tools/check_compat_shims.py`'s detection logic. If implementing the
  detection logic requires modifying `tools/check_compat_shims.py`, that is
  a file outside this row's own Target file — per
  `skills/plan-to-implementation-procedure/workflow.md` Step 3, this would
  be an additional-target-file discovery requiring the Plan to be amended
  before that file can be modified under this Plan's authority.

## Compatibility considerations
N/A: documentation-only, no code compatibility impact for this row itself
(any actual checker-code change would be a separate, amended target).

## Security considerations
None directly — documentation-only governance specification. The underlying
check (once implemented) helps prevent security-relevant terminology from
silently reappearing, but this document only specifies the requirement.

## Rollback considerations
Single-file edit under version control; revert via `git revert` if needed.
This document is referenced by every documentation-generation workflow —
keep the edit scoped to `GV-020`'s row/Follow-up item only.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_04_documentation-checks.md` | Documentation structure/quality check | `uv run python tools/check_docs_quality.py` | No structural findings in the changed file |
| `docs/00_governance_04_documentation-checks.md` | Structure validation | `uv run python tools/check_docs_structure.py` | Internal links resolve; Front Matter intact |

## Completion criteria
- `GV-020`'s scope (or Follow-up item 14) names the specific retired terms
  this migration introduces, with an explicit allowlist for legitimate
  "local" meanings, without flagging them (AC-7).
- Not completable until Phase 0 clears.

## Out of scope
`tools/check_compat_shims.py`'s actual implementation (a separate concern,
would require Plan amendment if it becomes a modification target); the
other 5 target files; `localremoval`'s/`loopbackonly`'s/`mcpauth`'s/
`localcleanup`'s own implementations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-04 | 2026-09-04 | GV-020's `_REMOVED_NAME_PATTERNS` extended by Phase 0 landing commits: flags `SecurityProfile.LOCAL`, `security_profile="local"`, `allow_public_bind`, empty `auth_token`/`auth_token_env` as retired runtime-profile terms (follow-up item 14 Extended 2026-09-04) — matches REQ-007 goal |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-04 | 2026-09-04 | Validation checks passed (see Phase 0 landing commits) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document's own target file is the documentation being updated; no separate doc row applies |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Phase 0 not cleared: `localremoval`, `loopbackonly`, `mcpauth` remain under `plans/`; `localcleanup` is in `plans/done/` but its own implementation-procedure document is unexecuted | Yes | 2026-09-04 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20260902-143338_adrprodonly_supersede_profile_based_design_docs_sync_references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-093353_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-171632
- **Related target files**: docs/00_governance_04_documentation-checks.md
