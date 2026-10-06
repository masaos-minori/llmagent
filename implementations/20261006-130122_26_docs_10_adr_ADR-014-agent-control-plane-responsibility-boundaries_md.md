## Goal

Migrate `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` per the target
ADR structure: remove the body `## Related Documents` block, promote `Related ADRs` and
`Implementation References` to top-level `## ` sections before `## Completion Checklist`,
drop the `Specifications`/`Operations`/`Known Issues` subsections (their targets are in
`related:` / `## Known Deviations`), keep context-bearing links as prose where needed, and
tidy headings/blank lines/file endings. Report links moved to `related:` and invalid links
removed (REQ-002, REQ-004 / AC-2, AC-4).

## Scope

- **In-Scope**: `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` only.
  And its link-set baseline (compare before/after so no still-needed link is lost, AC-2).
- **Out-of-Scope**: the other 19 ADRs; the rule/tool/test changes (separate rows).

## Assumptions

- The recommended target structure (UNK-01) is adopted.
- `rel001` has landed (prerequisite for the whole plan).

## Design decisions

- Remove the entire `## Related Documents` heading + subsection body.
- Promote the old `### Related ADRs` bullets to a new top-level `## Related ADRs`; promote
  the old `### Implementation References` bullets to a new top-level `## Implementation
  References`.
- Drop `### Specifications`, `### Operations` (its value is `None`), `### Known Issues`.
- **`### Known Issues` is NOT sole-cited.** Its only body link
  (`issues/done/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md`) also
  appears in `## Known Deviations` (line 208, struck-through but present). Per UNK-03 / AC-4,
  an ID that lives in more than one place must NOT be moved out of `## Known Deviations`; so
  drop the `### Known Issues` subsection without relocating its citation. Re-run
  `tools/check_known_deviation_sync.py` before and after to confirm the same findings (AC-4).
- Fold any remaining context phrase into `## Implementation Notes` or the relevant section as
  ordinary prose — only where the phrase adds information (UNK-02).
- Keep `## Known Deviations` (with its Known Issue IDs) untouched.
- Update the stale "See Related Documents > Implementation References" prose (line 200) to
  point at the new top-level `## Implementation References` (the old section name is being
  removed).

## Alternatives considered

- Moving every block link wholesale into `related:` — rejected: the plan forbids bulk moves
  (Constraints); each body-only link is judged individually (UNK-02).
- Moving the `### Known Issues` issue-file path into `## Known Deviations` — rejected: it is
  already cited there (line 208); moving it would duplicate the reference (AC-4).
- Keeping the subsections as `### ` — rejected: the standard header list promotes them to
  top-level `## ` (UNK-01).

## Implementation

### Target file

`docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`

### Procedure

1. **Baseline link set.** Record every link in the block (lines 237-267): markdown
   `[text](path)` and fenced `` `path` `` references, plus the `related:` front-matter entry.
   Save this for the before/after comparison (AC-2).
2. **Link triage.** For each block link not present in `related:`, judge necessity: move to
   `related:` if still needed, delete if invalid/obsolete, or register Needs Confirmation if
   unjudgeable. Do not move links wholesale (Constraints).
3. **Confirm the Known Issues citation is not sole-cited.** Verify
   `issues/done/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md` also
   appears in `## Known Deviations` (line 208). Run
   `tools/check_known_deviation_sync.py` once as a before-baseline (AC-4).
4. **Remove the block.** Delete the `## Related Documents` heading (line 237) and its
   subsection body through the end of `### Implementation References` (line 266), just before
   `## Completion Checklist` (line 268).
5. **Promote `## Related ADRs`.** Insert a top-level `## Related ADRs` section (before
   `## Completion Checklist`) carrying the one ADR-to-ADR link formerly under
   `### Related ADRs` (line 241: ADR-001).
6. **Promote `## Implementation References`.** Insert a top-level `## Implementation
   References` section carrying the scripts/tests references formerly under
   `### Implementation References` (lines 258-266).
7. **Drop `### Specifications` / `### Operations` / `### Known Issues`.** `### Operations` is
   `None`; `### Known Issues`'s single citation is already in `## Known Deviations` (do not
   relocate it, AC-4); fold any still-needed context phrase into prose (UNK-02); otherwise
   omit.
8. **Tidy.** Update the "See Related Documents > Implementation References" prose (line 200)
   to the new top-level `## Implementation References`; ensure exactly one blank line between
   the promoted sections and surrounding headings; ensure the file ends with a single
   trailing newline. Re-run `tools/check_known_deviation_sync.py` and confirm it reports the
   same findings as step 3 (AC-4).

### Method

- Read `ADR-014` lines 235-269 (block + surrounding).
- Apply steps 1-8.
- Confirm no `## Related Documents` (or any `Related Documents`) heading remains at any
  level.

### Details

- Block layout (current): `## Related Documents`(237) → `### Related ADRs`(239),
  `### Specifications`(243), `### Operations`(248), `### Known Issues`(252),
  `### Implementation References`(256); `## Completion Checklist`(268).
- `## Implementation Notes`(196) and `## Known Deviations`(206) are outside the block; leave
  them. `## Known Deviations` line 208 already cites the `### Known Issues` issue-file path.

## Compatibility considerations

- After migration this ADR must still pass `tools/check_docs_structure.py` (no body
  `Related Documents` at any level) and `tools/check_adr_structure.py` (reads the new
  top-level `## Implementation References`; `## Known Deviations` presence intact).
- `check_known_deviation_sync.py` must report the same findings before and after (AC-4).
- `adr-index.md`'s dependency graph is unrelated; leave it.

## Security considerations

N/A: documentation restructuring only.

## Rollback considerations

Revert this file to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `ADR-014` | Link-set comparison | Diff block links vs `related:` before/after | No still-needed link removed |
| `ADR-014` | Known-Issue sync | Run `check_known_deviation_sync.py` before/after | Same findings both runs (AC-4) |
| `ADR-014` | Structure | Read removed-block region + grep `Related Documents` | No body `Related Documents` at any level; `## Related ADRs`/`## Implementation References` present as top-level |
| Repo | Integration | `uv run python tools/check_docs_structure.py`, `check_adr_structure.py`, `check_known_deviation_sync.py` | Pass |

## Completion criteria

- The body `## Related Documents` block is removed.
- `## Related ADRs` and `## Implementation References` exist as top-level sections before
  `## Completion Checklist`.
- The `### Known Issues` issue-file path is left in `## Known Deviations` (not duplicated, not
  hidden) — same `check_known_deviation_sync.py` findings before and after (AC-4).
- No still-needed link was lost (per-ADR diff); links moved to `related:` and invalid links
  removed are reported.
- The repo passes its own structure checks.

## Out of scope

- The other 19 ADRs; rule/tool/test changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-002 / AC-2 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: doc-only migration |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | check_docs_structure.py + check_adr_structure.py + check_known_deviation_sync.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-004` — migrate this ADR (block removed, sections promoted, no link lost, AC-2) and keep `check_known_deviation_sync.py` findings stable while dropping the `### Known Issues` subsection (AC-4)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`
