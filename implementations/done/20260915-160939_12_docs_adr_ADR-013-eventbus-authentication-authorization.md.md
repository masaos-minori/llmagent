## Goal
Remove ADR-013's redundant file/class/config/test list from `## Implementation
Notes` once reconciled into `### Implementation References`, per `REQ-012`.

## Scope
- In scope: add `scripts/eventbus/app.py` (middleware registration) and
  `scripts/eventbus/config.py` (fail-closed validation) — both confirmed to
  exist and absent from References — plus the 2 cited test files, into
  References; delete the Notes list; insert the one-line pointer.
- Out of scope: this ADR's own pre-existing `## Known Deviations` section
  (lines 274-278) — untouched.

## Assumptions
- The one-line pointer is used verbatim.
- The 2 test file paths (`tests/eventbus/test_eventbus_auth.py`,
  `tests/eventbus/test_eventbus_config.py`) were not independently `ls`-verified
  during Plan creation (`UNK-02`) — verify them in this procedure.
- Neither `app.py` nor `config.py` is cited with a specific function symbol in
  Notes (only described by role: "middleware registration", "fail-closed
  validation") — add them to References the same way, without inventing a
  specific symbol name that Notes itself does not provide.

## Design decisions
- `app.py`/`config.py` are confirmed to exist and are genuinely absent from
  References — a straightforward addition, not a correction of a wrong entry.

## Alternatives considered
- Search for and name a specific function symbol for `app.py`/`config.py` beyond
  what Notes itself provides — rejected; inventing detail beyond what the source
  ADR text establishes risks introducing a new inaccuracy; add the file-level
  entry with its descriptive role only, matching Notes' own level of
  specificity.

## Implementation
### Target file
`docs/adr/ADR-013-eventbus-authentication-authorization.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   266-268 and References at 313-318 (this ADR's own `## Known Deviations` at
   274-278 is unaffected).
2. Re-confirm via `ls scripts/eventbus/app.py scripts/eventbus/config.py` that
   both still exist and are still absent from References.
3. Verify the 2 test files exist via `ls`; correct paths if stale.
4. Add `scripts/eventbus/app.py` (middleware registration) to References.
5. Add `scripts/eventbus/config.py` (fail-closed validation) to References.
6. Add the 2 verified test files to References.
7. Delete the Notes list (lines 266-268: Implementation files / Key symbols /
   Corresponding tests).
8. Insert: "See Related Documents > Implementation References for the current
   file/symbol list."

### Method
Use `Edit` (exact-string replacement) — one call per step 4-8.

### Details
- Do not touch this ADR's `## Known Deviations` section (274-278) at all.
- Preserve References' existing `auth.py`/`audit.py` entries and their 5 symbols
  (`verify_bearer_token()`, `require_role()`, `require_consumer_identity()`,
  `log_auth_failure()`, `log_privileged_action()`) unchanged.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change. `app.py`/`config.py`'s described roles
(middleware registration, fail-closed validation) are documentation facts, not
secrets.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-013-eventbus-authentication-authorization.md` if
validation fails.

## Validation plan
- `ls scripts/eventbus/app.py scripts/eventbus/config.py` — both must resolve.
- `ls tests/eventbus/test_eventbus_auth.py tests/eventbus/test_eventbus_config.py` — both must resolve before adding.
- Manual diff: confirm References includes `app.py`/`config.py` and both test files; confirm Notes list removed.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-013-eventbus-authentication-authorization.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-013-eventbus-authentication-authorization.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- References includes `app.py`, `config.py`, and both test files.
- `## Implementation Notes` contains only the one-line pointer plus boilerplate.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- This ADR's `## Known Deviations` section.
- Any other section of ADR-013.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-163331 | Verified both test paths exist (UNK-02 resolved); reconciled app.py/config.py+tests into References; deleted Notes list; inserted pointer |
| 2 | Add or update tests per Validation plan | Completed | 20260915-163331 | 20260915-163331 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-163331 | 20260915-163331 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 2 pre-existing unrelated findings, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-163331 | 20260915-163331 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-012 — reconcile app.py/config.py + tests, delete Notes list
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-013-eventbus-authentication-authorization.md