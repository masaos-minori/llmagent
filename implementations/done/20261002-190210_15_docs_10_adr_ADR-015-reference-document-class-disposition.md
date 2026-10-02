# Implementation Procedure: Fix stale governance paths in docs/10_adr/ADR-015-reference-document-class-disposition.md

## Goal

Replace stale `docs/governance_0N_*` path references in `docs/10_adr/ADR-015-reference-document-class-disposition.md` with actual existing paths under `docs/00_governance/governance_0N_*`.

## Scope

- Modify only `docs/10_adr/ADR-015-reference-document-class-disposition.md`.
- In-Scope: Replace stale paths on lines 30, 62, and 141.
- Out-of-Scope: Changing any other content in the file.

## Assumptions

- The correct path is `docs/00_governance/governance_01_documentation-policy.md` (confirmed by filesystem inspection).

## Design decisions

- **Approach**: Direct string replacement — replace `docs/governance_01_documentation-policy.md` with `docs/00_governance/governance_01_documentation-policy.md` on lines 30, 62, and 141.

## Alternatives considered

None — direct replacement is the only sensible approach for stale paths.

## Implementation

### Target file

`docs/10_adr/ADR-015-reference-document-class-disposition.md`

### Procedure

Replace the stale path strings on lines 30, 62, and 141 with the correct paths.

### Method

Edit `docs/10_adr/ADR-015-reference-document-class-disposition.md`:

**Line 30:** Change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`

**Line 62:** Change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`

**Line 141:** Change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`

### Details

Line 30 currently reads:
```
`docs/governance_01_documentation-policy.md`'s Document Classification defines a "Reference" class (API/command/configuration reference material), but a proposed documentation-slimming policy's mechanical-content removal criteria conflict with hand-written Reference documents by design — their entire content is exactly the kind of code-derivable listing the policy wants removed. This ADR recommends treating Reference-class documents as generated artifacts (Option B), produced from source code via `tools/generate_reference_table.py`, rather than retiring the class or accepting continued drift.
```

Change to:
```
`docs/00_governance/governance_01_documentation-policy.md`'s Document Classification defines a "Reference" class (API/command/configuration reference material), but a proposed documentation-slimming policy's mechanical-content removal criteria conflict with hand-written Reference documents by design — their entire content is exactly the kind of code-derivable listing the policy wants removed. This ADR recommends treating Reference-class documents as generated artifacts (Option B), produced from source code via `tools/generate_reference_table.py`, rather than retiring the class or accepting continued drift.
```

Line 62 currently reads:
```
Applies to any `docs/*.md` document classified `class: Reference` per `docs/governance_01_documentation-policy.md`'s Document Classification, once tooling exists to generate its content.
```

Change to:
```
Applies to any `docs/*.md` document classified `class: Reference` per `docs/00_governance/governance_01_documentation-policy.md`'s Document Classification, once tooling exists to generate its content.
```

Line 141 currently reads:
```
This ADR reached `Accepted` via a Named Approval Record per the ADR Acceptance Evidence Standard (`docs/governance_01_documentation-policy.md`) — not the task-level fallback path.
```

Change to:
```
This ADR reached `Accepted` via a Named Approval Record per the ADR Acceptance Evidence Standard (`docs/00_governance/governance_01_documentation-policy.md`) — not the task-level fallback path.
```

Only the path strings change; surrounding text is preserved.

## Compatibility considerations

- The corrected paths resolve to existing files (`docs/00_governance/governance_01_documentation-policy.md`).

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path strings if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-015-reference-document-class-disposition.md` | Path resolution | `grep -rnE "docs/governance_0[0-4]_" docs/10_adr/ADR-015-reference-document-class-disposition.md` | No matches |
| `docs/10_adr/ADR-015-reference-document-class-disposition.md` | File existence | `test -f docs/00_governance/governance_01_documentation-policy.md` | File exists |

## Completion criteria

- All `docs/governance_0N_*` paths on lines 30, 62, and 141 of `ADR-015-reference-document-class-disposition.md` resolve to existing files.
- No remaining `docs/governance_0N_*` patterns in `ADR-015-reference-document-class-disposition.md`.

## Out of scope

- Other stale paths in `ADR-015-reference-document-class-disposition.md` (if any).
- Changes to other files.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-003 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test needed for path string fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-003 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No documentation update needed |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
