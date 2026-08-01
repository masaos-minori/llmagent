# Move OS-package/cmake provisioning steps out of docs/02_deployment-part1.md; keep the sqlite3 USE-flag design note

## Priority
Low

## Summary
`docs/02_deployment-part1.md` §1.1 (Gentoo package list, `emerge` commands) and §1.3 (cmake build commands) are pure OS-provisioning instructions rather than design decisions, and go stale with OS/version changes.

## Reason for Change
Provisioning-level instructions don't convey design judgment (the purpose of a design document), and are better suited to a dedicated setup/provisioning runbook that can evolve independently of the design narrative.

## Implementation Intent
Move the package-list/emerge/cmake-build instructions to a setup/provisioning runbook (create one if none exists, or identify the appropriate existing location), while explicitly preserving the one note that IS a design decision: the USE-flag requirement when Python's sqlite3 build lacks load-extension support (directly relevant to the sqlite-vec adoption decision).

## Target Files or Areas
`docs/02_deployment-part1.md` (§1.1, §1.3)

## Required Changes
- Identify or create the appropriate provisioning runbook location for the OS-package-list/emerge/cmake-build instructions.
- Move that content there, leaving a reference pointer in `part1`.
- Explicitly keep the "Python's sqlite3 lacking load-extension support requires a USE flag adjustment" note in `part1`'s main text, since it's tied to the sqlite-vec design decision, not mere provisioning.

## Acceptance Criteria
`part1` no longer contains the full package-list/emerge/cmake-build instructions inline; a reference to the provisioning runbook remains; the sqlite3 USE-flag design note is preserved in `part1`.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/02_deployment-part1.md` shortened; new or updated provisioning runbook gains this content.

## Out of Scope
Do not change the actual provisioning commands/package versions in this issue — documentation relocation only.

## AI Implementation Instruction
Search for an existing provisioning/setup runbook before creating a new one. Be careful to preserve the sqlite3 USE-flag note exactly where it currently sits in the design narrative — do not accidentally move it along with the rest of the provisioning content.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §1 (コード説明に寄りすぎている領域), §2 削除候補 item 3
- Generated at: 2026-08-02
