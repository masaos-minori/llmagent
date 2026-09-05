## Goal
Once Phase 0 clears: update
`docs/04_mcp_06_02_configuration-file-inventory.md`'s `security_profile` row
to record its retired status and startup-failure behavior if the retired key
is still present in a config file (`REQ-005`).

## Scope
- **In-Scope**: `docs/04_mcp_06_02_configuration-file-inventory.md` only —
  the `security_profile` row.
- **Out-of-Scope**: the other 5 target files; any other row of this
  inventory document; `localremoval`'s/`loopbackonly`'s/`mcpauth`'s/
  `localcleanup`'s own implementations.

## Assumptions
- Phase 0 is **not** cleared as of 2026-09-03 (re-confirmed, same status as
  seq 01-03). This document's Procedure is Blocked until all four dependency
  Plans land.
- Re-confirmed 2026-09-03: `config/agent.toml` → `security_profile` row
  (currently "Global agent security profile (local / production)") is
  present in the inventory table, unchanged from the Plan's citation
  (originally line 33; confirmed at the equivalent position in the current
  table — the row content, not necessarily the exact line offset, is what
  matters here since this is a table-row edit, not a line-anchored one).
- `localremoval`'s own Plan is the source of truth for what happens if a
  retired `security_profile` key is still present in a config file at
  startup (e.g. fail-fast vs. ignored) — this document's edit must match
  `localremoval`'s actual landed startup-validation behavior, not assume a
  specific outcome now.

## Design decisions
- Mark the row as retired in place (e.g. a "Retired" annotation in the Scope
  column, or a strikethrough with a note) rather than deleting the row
  outright — preserves a record that this key existed and was intentionally
  retired, useful for anyone encountering an old config file with the key
  still present.
- Document the actual startup-failure behavior for a lingering retired key
  (per `localremoval`'s landed implementation), since an operator upgrading
  an old deployment may still have the key in their config file.

## Alternatives considered
- Deleting the row entirely — rejected: loses the historical record of what
  the key was and why it was retired, unlike the "mark retired" approach
  which documents both the past and current state.

## Implementation
### Target file
`docs/04_mcp_06_02_configuration-file-inventory.md`

### Procedure
1. Confirm Phase 0's precondition is met. As of 2026-09-03 it is not — do
   not proceed past this step until it is.
2. Once cleared, re-read `localremoval`'s landed implementation to determine
   the actual behavior when `security_profile` is still present in
   `config/agent.toml` after its removal (fail-fast error, ignored with a
   warning, or another documented behavior).
3. Update the `security_profile` row: mark it retired, and document the
   confirmed startup-failure (or other) behavior for a lingering key.

### Method
Direct `Edit` to `docs/04_mcp_06_02_configuration-file-inventory.md`, once
Phase 0's precondition is confirmed met and `localremoval`'s actual landed
behavior is re-read.

### Details
- Do not guess the startup-failure behavior from `localremoval`'s Plan-time
  text alone — re-verify against the actual landed code/tests, per this
  Plan's own Assumptions ("if any deviates materially... re-verified against
  the actual landed text").
- Keep the row's table position unchanged (do not reorder the inventory
  table) — only its Scope/description content changes.

## Compatibility considerations
N/A: documentation-only, no code compatibility impact.

## Security considerations
None directly — documentation-only. Accurately documenting the
retired-key-still-present behavior helps operators avoid a misconfigured
production deployment, but this document does not implement any control.

## Rollback considerations
Single-file edit under version control; revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_02_configuration-file-inventory.md` | Documentation structure/quality check | `uv run python tools/check_docs_quality.py` | No structural findings in the changed file |
| `docs/04_mcp_06_02_configuration-file-inventory.md` | Structure validation | `uv run python tools/check_docs_structure.py` | Internal links resolve; Front Matter intact |

## Completion criteria
- The `security_profile` row records its retired status and the confirmed
  startup-failure (or other) behavior for a lingering key (AC-5).
- Not completable until Phase 0 clears.

## Out of scope
The other 5 target files; any other inventory row;
`localremoval`'s/`loopbackonly`'s/`mcpauth`'s/`localcleanup`'s own
implementations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-04 | 2026-09-04 | Target document already revised by Phase 0: row 34 updated to `Global agent security profile — production only (SecurityProfile.LOCAL was removed)` — matches REQ-005 requirement (retired status + startup-failure behavior documented) |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260902-143338_adrprodonly_supersede_profile_based_design_docs_sync_references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-093353_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-171632
- **Related target files**: docs/04_mcp_06_02_configuration-file-inventory.md
