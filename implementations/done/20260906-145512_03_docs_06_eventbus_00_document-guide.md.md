## Goal
Confirm (this row is likely already satisfied by concurrent work — see Assumptions)
that "Canonical Source Rule" no longer states unconditionally that code should be
trusted over documentation, aligning it with the new resolution sequence (REQ-009).

## Scope
- In scope: the "## Canonical Source Rule" section only (currently lines 39-41).
- Out of scope: any other section of this document (e.g. "## Known Issues / Deferred
  Items" immediately following it).

## Assumptions
- **Already satisfied as of this cycle (2026-09-06) — verify, do not blindly
  re-implement**: direct read found "## Canonical Source Rule" (lines 39-41) no
  longer contains the Plan's cited text ("The canonical source for behavior is the
  source code..., trust the code and update the documentation"). It now reads: "See
  [EventBus runtime-behavior](../config/documentation_canonical_sources.toml#eventbuscore-behavior)
  and [EventBus persistence-schema](../config/documentation_canonical_sources.toml#eventbuspersistence-schema)
  in the Canonical Source Registry." — this is a concurrent session's migration to
  `config/documentation_canonical_sources.toml` (the machine-readable Canonical
  Source Registry, `M-01-04` — explicitly Out-of-Scope for this Plan per its own
  Scope section), which happens to also satisfy REQ-009's requirement (no
  unconditional "trust the code" statement remains) as a side effect.

## Design decisions
- Do not revert or duplicate this concurrent change — it already satisfies REQ-009's
  actual requirement (remove the unconditional code-trust statement), even though it
  arrived via a different mechanism (registry reference) than this Plan's own
  Design section anticipated (a reference to "the new resolution sequence"). A
  registry-file reference and a resolution-sequence reference both equally satisfy
  "no longer states unconditionally that code should be trusted over documentation."

## Alternatives considered
- Additionally add a resolution-sequence cross-reference alongside the existing
  registry link, since this Plan's Design section originally envisioned that
  specific wording: considered, but not required — REQ-009's actual acceptance
  criterion (AC-9: no unconditional universal-ranking restatement remains) is already
  met; adding a second cross-reference would be additive polish, not a requirement.

## Implementation
### Target file
`docs/06_eventbus_00_document-guide.md`

### Procedure
1. Re-read "## Canonical Source Rule" immediately before considering this row —
   if it still reads as confirmed this cycle (registry-reference wording, no
   unconditional code-trust statement), report this row `Not applicable — already
   satisfied by prior concurrent work (M-01-04 registry migration)` and make no
   edit.
2. If a future re-read finds the unconditional statement has somehow returned (e.g.
   a conflicting concurrent edit), reapply the fix: replace it with a reference to
   `docs/00_governance_01_documentation-policy.md`'s claim-type/decision-target
   resolution mechanism (matching seq 01/02's approach), or confirm the registry
   reference remains — either satisfies REQ-009.

### Method
Confirmed this cycle (2026-09-06) via direct read: lines 39-41 already reference
`config/documentation_canonical_sources.toml`, not the unconditional "trust the
code" statement the Plan's authoring-time snapshot (2026-09-05) cited. `rg -i "trust
the code" docs/06_eventbus_00_document-guide.md` returns no match.

### Details
No change needed under current repository state.

## Compatibility considerations
N/A: no edit expected; if one is made, documentation-only.

## Security considerations
N/A.

## Rollback considerations
N/A: no edit expected under current state.

## Validation plan
- `rg -i "trust the code" docs/06_eventbus_00_document-guide.md` — confirm no match
  (already passing this cycle).
- `uv run python tools/check_docs_quality.py docs/06_eventbus_00_document-guide.md`
  (baseline check only, no change expected to cause a new finding).

## Completion criteria
- "## Canonical Source Rule" does not state unconditionally that code should be
  trusted over documentation — already true as of this cycle; re-confirm at
  implementation time.

## Out of scope
- `config/documentation_canonical_sources.toml` itself — `M-01-04`'s scope, not this
  Plan's.
- `docs/00_governance_01_documentation-policy.md` — tracked in seq 01.
- `docs/00_governance_04_documentation-checks.md` — tracked in seq 02.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Likely `N/A` — already satisfied, see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20260903-103025_m0102_replace-universal-source-ranking-with-target-based-resolution.md
- **Source plan**: plans/20260905-164741_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-145512
- **Related target files**: docs/06_eventbus_00_document-guide.md
