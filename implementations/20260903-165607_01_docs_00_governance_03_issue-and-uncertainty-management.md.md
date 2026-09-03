## Goal
Verify (`REQ-001`) that `RAG-006` and `RAG-007` — the Known Issue entries
`ragcontract` (`REQ-012`) and `ragfreshness` (`REQ-010`) plan to add to this file's
Part 1, once those two Plans are implemented — do not duplicate each other or an
existing entry; and conditionally register (`REQ-004`) the artifact-versioning
(`artifact_type`/`created_by`/`source_file`/`chunk_type` contract) Needs
Confirmation question in this file's Active Items list, but only if it remains
unresolved after `ragcontract` lands.

## Scope
- **In-Scope**: this file only —
  `docs/00_governance_03_issue-and-uncertainty-management.md`'s Part 1 (Known
  Issues) `RAG-*` entries duplication check, and its "Needs Confirmation
  Inventory" Active Items registration.
- **Out-of-Scope**: authoring `RAG-006`/`RAG-007` themselves (owned by
  `ragcontract`'s and `ragfreshness`'s own implementation-procedure documents, not
  this one); resolving the artifact-versioning design question itself (only
  registering the question, if still unresolved); the `ToolRegistry`
  misclassification check (`REQ-003`) and the canonical Migration History location
  check (`REQ-005`) — both are reference/verification-only checks with no
  modification target of their own (see source Plan's Requirement Traceability),
  tracked at the Plan level, not owned by this document; source-code changes.

## Assumptions
- `ragcontract` (`plans/done/20260903-085152_plan.md`) and `ragfreshness`
  (`plans/done/20260903-085718_plan.md`) will land `RAG-006` and `RAG-007`
  respectively in this file's Part 1 substantially as their own (already
  corrected) Plan documents specify — re-verify against the actual landed text,
  not assumed, before finalizing (per the source Plan's `UNK-02`).
- Neither `ragcontract` nor `ragfreshness` has been implemented as of 2026-09-03 —
  their generated implementation-procedure documents remain pending under
  `implementations/`, not yet archived to `implementations/done/` (confirmed via
  directory listing) — so this document's Procedure below begins with a
  precondition check and cannot complete the actual duplication check until both
  land.
- `toolroutedoc` (`plans/done/20260903-090104_plan.md`) is fully implemented; its
  `REQ-006` was found Obsolete during its own `plan-to-implementation-procedure`
  phase — no MCP-area Known Issue entry exists or will exist, so the source Plan's
  `REQ-002` (originally a duplication check against that entry) requires no action
  in this document.

## Design decisions
- Treat `ragcontract`'s and `ragfreshness`'s own Plan documents as the source of
  truth for what `RAG-006`/`RAG-007` should say — this document only checks for
  duplication/consolidation once they land, it does not re-derive or restate their
  content.
- Consolidate only if genuine topical duplication is found — do not merge two
  legitimately distinct entries merely because they share the `RAG-*` prefix.

## Alternatives considered
- Executing this verification immediately, without waiting for `ragcontract`/
  `ragfreshness` to land — rejected: `RAG-006`/`RAG-007` do not exist yet
  (confirmed via `grep -n "^#### RAG-"` on 2026-09-03, only `RAG-003`/`RAG-004`/
  `RAG-005` present); there is nothing yet to check for duplication.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Confirm the source Plan's Phase 1 precondition: `ragcontract` and
   `ragfreshness` have each been fully implemented (all of their generated
   implementation-procedure documents archived under `implementations/done/`, not
   merely their Plan moved to `plans/done/`). As of 2026-09-03 this is not yet the
   case for either — do not proceed past this step until it is.
2. Once the precondition is met, re-read this file's Part 1 in full for the
   landed `RAG-006` and `RAG-007` entries.
3. Compare their `Title`/`Summary` text against each other and against the
   existing `RAG-003`/`RAG-004`/`RAG-005` entries (and any other entry landed in
   the meantime) for topical duplication.
4. If a duplicate is found, consolidate into a single entry, preserving the more
   complete/accurate content and updating any cross-references elsewhere in the
   document.
5. Re-check whether the artifact-versioning contract remains unresolved after
   `ragcontract` lands (`scripts/rag/ingestion/pipeline_utils.py`'s `ChunkJsonRaw`
   comment plus `ragcontract`'s own landed documentation). If still unresolved,
   register a new entry in this file's "Needs Confirmation Inventory" Active Items
   list (next available `NC-*` ID — `NC-033` as of 2026-09-03, re-checked for
   collision immediately before insertion), following the existing 15-field Entry
   Template.

### Method
Manual read-and-compare via `Read`/`grep` (no automated dedup tool exists for this
document); a direct `Edit` is made only if consolidation or NC registration is
actually needed once the precondition is met.

### Details
- Duplication check keys on entry `Title`/`Summary` text overlap, not ID
  proximity — two entries can be ID-adjacent (`RAG-006`, `RAG-007`) without being
  duplicates.
- NC registration must follow the document's existing 15-field template
  (ID/Source File/Section/Line Number/Question/Evidence/Impact/Required
  Action/Status/Assigned To/Last Reviewed/Priority/Related NC/Resolution
  Target/Blocking) and its own Lifecycle rule (`Status` is `open`/`investigating`/
  `deferred` only — no `resolved` value exists; a resolved item is removed from
  Active Items entirely, not marked resolved in place).
- Current Active Items run `NC-021` through `NC-032` (confirmed 2026-09-03 via
  `grep -n "^#### NC-"`); a new entry would be `NC-033`, re-checked for collision
  immediately before insertion in case another unrelated NC entry lands first.
- `RAG-006`/`RAG-007` do not exist yet as of 2026-09-03 — this Procedure's steps
  2-5 cannot be completed until `ragcontract` and `ragfreshness` are implemented
  (see Assumptions); step 1's precondition check can and should be re-run each
  time this document's execution is attempted.

## Compatibility considerations
N/A: documentation-only, no code compatibility impact. No other document links to
`RAG-006`/`RAG-007` by anchor yet, since neither entry exists.

## Security considerations
None — documentation-only governance bookkeeping; no code, credentials, or
access-control content is affected.

## Rollback considerations
Single-file edit under version control; revert via `git revert` if a
consolidation or NC registration proves wrong. No other file depends on this
file's `RAG-*`/`NC-*` entry structure beyond `tools/check_needs_confirmation_inventory.py`
and `tools/check_known_deviation_sync.py`'s own generic format checks.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Needs Confirmation inventory check | `uv run python tools/check_needs_confirmation_inventory.py` | Any new NC entry is correctly registered per the document's own inventory rules |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Known-deviation cross-check | `uv run python tools/check_known_deviation_sync.py` | No dangling or mismatched Known Issue references introduced |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Manual duplication check | `grep -n "^#### RAG-"`, then compare `RAG-006`/`RAG-007` titles against each other and existing entries | No topic appears as more than one entry |

## Completion criteria
- Step 1's precondition (`ragcontract` and `ragfreshness` both fully implemented,
  archived under `implementations/done/`) is confirmed met before any further
  action in this document is taken.
- `RAG-006` and `RAG-007` (once landed) do not duplicate each other or an existing
  entry — consolidated into one entry if they did.
- The artifact-versioning contract question is either registered as a new NC
  entry or confirmed genuinely resolved by `ragcontract`'s landed documentation —
  not left undocumented either way (`AC-2`).
- `check_needs_confirmation_inventory.py` and `check_known_deviation_sync.py`
  report no new errors.

## Out of scope
`REQ-002` (Obsolete — no MCP-area entry exists or will exist to check); `REQ-003`
(`ToolRegistry` misclassification check — reference-only, no modification target,
already re-confirmed clean as of 2026-09-03 at the Plan level); `REQ-005`
(canonical Migration History location check — reference-only, spans 3 different
files, none of which is this one); any edit to `ragcontract`'s or `ragfreshness`'s
own implementation-procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Precondition not met: `ragcontract`/`ragfreshness` implementation-procedure documents remain pending under `implementations/`, not yet archived to `implementations/done/`, as of 2026-09-03 |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Blocked | — | — | Cannot meaningfully run until step 1's precondition is met — `RAG-006`/`RAG-007` do not exist yet to validate |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No other documentation in scope for this row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `ragcontract` (`plans/done/20260903-085152_plan.md`) and `ragfreshness` (`plans/done/20260903-085718_plan.md`) have not yet been implemented — their generated implementation-procedure documents remain pending under `implementations/`, not archived to `implementations/done/` | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (verify RAG-006/RAG-007 non-duplication), REQ-004 (conditional artifact-versioning NC registration)
- **Source issue**: issues/done/20260902-143331_compathistory_consolidate_compat_removal_history_and_issue_states.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-090552_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-165607
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
