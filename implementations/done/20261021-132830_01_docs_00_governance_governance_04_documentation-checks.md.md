## Goal
Align the Verification Matrix `Follow-up` column with the "Follow-up Work Needed" section for GV-009, GV-010, GV-011, and GV-017 in `docs/00_governance/governance_04_documentation-checks.md`, per the owner's per-rule decision recorded under REQ-001, so the document no longer contradicts itself.

## Scope
- Modify only the `Follow-up` cell of the GV-009, GV-010, GV-011, GV-017 matrix rows (lines 325, 326, 327, 333) and the matching entries in the "Follow-up Work Needed" section (lines 341-353) of `docs/00_governance/governance_04_documentation-checks.md`.
- Do not change any rule's Gate, Timing, Status, Method, or Tool/Review column, and do not touch any other rule.

## Assumptions
- The owner's per-rule intent (intended / not intended) for GV-009, GV-010, GV-011, GV-017 is recorded before this change executes (Plan REQ-001); this procedure documents both branches so either can be applied once decided.
- The matrix stays the single source for gate, blocking, and timing facts; only the Follow-up column and the section are aligned.
- Wording stays in the present tense per the Current-Specification-Only Policy (`docs/00_governance/governance_01_documentation-policy.md`).

## Design decisions
- Change only the `Follow-up` cell and its matching section bullet per rule; leave the matrix's gate/timing/status columns untouched so the verification contract's hard facts are unchanged.
- Document both branches here (intended → concrete follow-up; not intended → manual/warning-only + remove section item) because the owner decision gates which branch executes.

## Alternatives considered
- Editing the "Follow-up Work Needed" section only and leaving the matrix: rejected, the matrix is the canonical contract location and must mirror the section.
- Inferring the owner's intent and selecting one branch: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Confirm the owner's per-rule decision for GV-009, GV-010, GV-011, GV-017 is recorded (REQ-001). If absent, stop and report; do not infer intent.
2. Apply exactly one branch per rule:
   - **Intended**: set a concrete, actionable Follow-up in the matrix cell and keep a concrete item in the "Follow-up Work Needed" section. For GV-011, name the extension scope (which `stale_patterns` canonical-document-reference patterns must cover).
   - **Not intended**: set the matrix Follow-up cell to a manual/warning-only-by-design value and remove that rule's item from the "Follow-up Work Needed" section.
3. Leave every other column (Gate, Timing, Status, Method, Tool/Review) and every other rule unchanged.
4. Run the documentation checks in the Validation plan.

### Method
- Locate the four matrix rows by Rule ID: GV-009 (L325), GV-010 (L326), GV-011 (L327), GV-017 (L333); each currently reads `... Existing | None`.
- Locate the "Follow-up Work Needed" section (L341-353) and its numbered items for GV-009/GV-010, GV-011, GV-017.
- Edit the four Follow-up cells and the matching section bullets to match the recorded decision; do not renumber or restructure the surrounding matrix.

### Details
- **GV-009 / GV-010** (duplicate canonical specification / multiple primary canonical sources): if intended, the follow-up is "automate conflict detection for unregistered prose across documents; registered claims already checked by GV-019"; state the concrete automation scope. If not intended, record as manual review by design and drop from the section.
- **GV-011** (references to non-existent canonical documents): if intended, name the exact `stale_patterns` custom-rule patterns to add for canonical document references (resolve UNK-02) in both the matrix cell and the section; if not intended, record as warning-only by design and drop from the section.
- **GV-017** (removed-name reintroduction in current specifications): if intended, state the plan to promote `--check-removed-names` to default-on following `check_compat_shims.py`'s "report-only until compliant" convention; if not intended, record as opt-in/by-design and drop from the section.
- Keep present-tense wording throughout (Current-Specification-Only Policy).

## Compatibility considerations
- Downstream plans reference `governance_04` as the verification contract; aligning the Follow-up column and section keeps the contract self-consistent and does not alter any gate, timing, or fact.

## Security considerations
N/A: documentation-only alignment of a governance matrix and section; no code, secrets, or access changes.

## Rollback considerations
N/A: revert the commit that edits `governance_04_documentation-checks.md`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Structural quality | `uv run python tools/check_docs_quality.py` | Pass |
| `docs/00_governance/governance_04_documentation-checks.md` | Structure (front matter, headings, related docs) | `uv run python tools/check_docs_structure.py docs/00_governance/governance_04_documentation-checks.md` | Pass |
| `docs/00_governance/governance_04_documentation-checks.md` | Content policy (no implementation detail) | `uv run python tools/check_docs_content_policy.py` | Pass |
| Manual | Matrix `Follow-up` column matches "Follow-up Work Needed" section for GV-009/GV-010/GV-011/GV-017 | Manual review | Rows agree |

## Completion criteria
- The `Follow-up` cells for GV-009, GV-010, GV-011, GV-017 agree with their matching "Follow-up Work Needed" section items.
- Any kept-open item is concrete enough to start (GV-011 names the `stale_patterns` extension scope).
- `check_docs_quality.py`, `check_docs_structure.py`, and `check_docs_content_policy.py` pass for the edited file.
- No gate, timing, status, method, or tool column changed; no other rule touched.

## Out of Scope
- Implementing any automation or `stale_patterns` extension (filed separately under REQ-003 when a rule is decided "intended").
- Enabling `--check-removed-names` by default, or changing any rule's gate, timing, or blocking status.
- GV-016 CI wiring and the compression policy for `governance_01`/`governance_04`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Align the GV-009/GV-010/GV-011/GV-017 matrix `Follow-up` column with the "Follow-up Work Needed" section per the recorded owner decision | Pending | — | — | Branch selected by owner decision (REQ-001) |
| 2 | Run the documentation checks in the Validation plan | Pending | — | — | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner per-rule intent (intended/not intended) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` — align the matrix `Follow-up` column and the "Follow-up Work Needed" section for GV-009/GV-010/GV-011/GV-017
- **Source issue**: `issues/20261021-100252_gov004fu_decide-the-governance_04-follow-up-work-items-for-gv-009-gv-010-gv-011-gv-017.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-121656_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-132830
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
