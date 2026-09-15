## Goal
Add entry `16` to `docs/00_governance_04_documentation-checks.md`'s
`## Automated Checks` section documenting `tools/check_adr_structure.py`,
per `REQ-006`, matching entry 8's format.

## Scope
- In scope: one new numbered entry under `## Automated Checks`.
- Out of scope: the Governance Verification Matrix (`GV-XXX` table) — the
  source Plan does not request a new `GV-` row for this check, since it
  automates part of existing manual check 11 ("ADR Section Header
  Compliance") rather than introducing a new governance rule; re-verify this
  scoping decision against the Plan text at Step 3a before writing, and only
  add a `GV-` row if the Plan explicitly requires it.

## Assumptions
- Current max entry number under `## Automated Checks` is `15` (`### 15.
  Docs Content Policy Check`, confirmed via this pass's read of the live
  file) — so the new entry is numbered `16`.
- Entry `8`'s format (`### 8. Documentation Structure Validation
  (\`check_docs_structure.py\`)`, prose-plus-bullets, `**Usage:**` fenced
  code block) is the structural precedent, per the Plan's explicit
  instruction.

## Design decisions
- Heading: `### 16. ADR Structure Check (\`check_adr_structure.py\`)`.
- Body: one-sentence purpose statement, then a bulleted list of the two
  checks (Known Deviations heading presence — ERROR; Implementation
  Notes/References path drift — WARNING, skip-if-zero-paths rule spelled out
  since it is the check's one non-obvious behavior), then `**Usage:**` fenced
  bash block showing plain invocation and `--format json`.
- Insert immediately after entry 15 (end of the `## Automated Checks`
  section, before `## Manual Checks`) to preserve strict numeric ordering.

## Alternatives considered
- Cross-reference this new entry from manual check 11 ("ADR Section Header
  Compliance") — considered but left out of REQ-006's explicit scope (the
  Plan's REQ-006 only asks for the new entry itself); flagging this
  possible follow-up here rather than silently expanding scope.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
1. Re-verify (Step 3a) that entry 15 is still the current max entry number
   and its exact heading text is unchanged before inserting.
2. Insert the new `### 16. ...` section immediately after entry 15's content
   block, before the `## Manual Checks` heading.

### Method
`Edit` tool, anchoring on the `## Manual Checks` heading (insert immediately
before it) to avoid depending on entry 15's full body text matching
byte-for-byte.

### Details
Applied text (trimmed from the originally-drafted wording below — see
Execution Status Notes: the original wording pushed the file's total size
45 bytes past `check_docs_structure.py`'s 24576-byte limit, a genuine new
finding, not a pre-existing baseline one; this shorter wording keeps the
same two-check content while landing at 24422 bytes):
```markdown
### 16. ADR Structure Check (`check_adr_structure.py`)

Validates `docs/adr/*.md` structure:
- `## Known Deviations` heading presence (missing → Error)
- Notes vs References path drift (a `scripts/`/`tests/` path in
  Implementation Notes absent from Implementation References → Warning;
  skipped if Notes cites zero such paths)

**Usage:**
```bash
python tools/check_adr_structure.py
python tools/check_adr_structure.py --format json
```
```

## Compatibility considerations
N/A: additive documentation only; no existing entry is renumbered or
modified.

## Security considerations
N/A: documentation change only.

## Rollback considerations
Revert by removing the added section; no other document depends on entry 16
existing yet.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md` — clean.
- `uv run python tools/check_docs_structure.py docs/00_governance_04_documentation-checks.md` — clean.
- Manual read-through: entry numbering remains strictly sequential 1-16 with no gaps/duplicates.

## Completion criteria
- Entry 16 present, correctly numbered, matching entry 8's structural
  format (heading / prose+bullets / `**Usage:**` block).

## Out of scope
- Governance Verification Matrix (`GV-XXX`) row — not requested by REQ-006;
  flagged as a possible follow-up above, not actioned in this cycle.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-195209 | 20260915-195209 | Applied wording trimmed from original draft — see Details |
| 2 | Add or update tests per Validation plan | Completed | 20260915-195209 | 20260915-195209 | N/A: documentation-only change, no test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-195209 | 20260915-195209 | Documentation change — validated via `check_docs_quality.py`/`check_docs_structure.py`, not the code toolchain First pass: check_docs_structure.py flagged a genuine NEW size-limit violation (24621 > 24576 bytes; baseline pre-edit was 23977, confirmed via git stash) caused by the originally-drafted entry text — fixed by trimming wording (Step 6 fix-and-recheck, 1 attempt); re-run: 24422 bytes, all checks passed. check_docs_quality.py: clean both passes. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-195209 | 20260915-195209 | This row IS the documentation update This row IS the documentation update |

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
- **Requirement ID**: REQ-006 — document check_adr_structure.py as Automated Check entry 16
- **Source issue**: issues/done/20260914-124634_docqa05_adr-implementation-notes-lint-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-192743_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-193504
- **Related target files**: docs/00_governance_04_documentation-checks.md