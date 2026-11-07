## Goal

Remove the "proposed"/"pending"/"not accepted" framing from the "Plan Amendment Approval
Classes" section in `rules/workflow-lifecycle.md` (REQ-001 / AC-001) so the two classes
(fallout = MAY amend + report afterward; scope = approval first) state the standing,
owner-decided policy instead of a proposal awaiting acceptance.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The owner has decided both amendment classes (recorded in the source issue's owner
  decision); this edit records the decided text, it does not decide policy.
- The two-class definition and the surrounding freeze-criteria validation rules are correct
  and stay unchanged; only the "proposed" framing is removed.
- `tools/amend_plan.py` already encodes both classes (`CLASSES = ("fallout", "scope")`) and
  leaves the allow/deny decision to the caller, so the tool needs no change; `--help`
  agrees with the documented classes (REQ-003 / AC-003).

## Design decisions
- Remove only the "proposed" framing: the heading suffix, the `Status: proposed` sentence,
  and the closing "While the policy is not accepted" paragraph.
- Keep the two-class definition and the `tools/amend_plan.py` mechanics sentence verbatim.

## Alternatives considered
- Rewriting the section into active voice with new prose: unnecessary; dropping the proposal
  language yields the decided policy with the smallest, least error-prone edit.

## Implementation
### Target file
`rules/workflow-lifecycle.md`

### Procedure
In the "Plan Amendment Approval Classes" section (currently lines 133-147), make three
edits: drop the `(proposed)` heading suffix, delete the `Status: proposed` sentence, and
delete the closing "While the policy is not accepted" paragraph.

### Method
Edit the section in place; do not touch the two-class definition or any other section.

### Details
1. Heading (line 133):
   Before: `### Plan Amendment Approval Classes (proposed)`
   After:  `### Plan Amendment Approval Classes`
2. Delete the sentence spanning lines 135-138:
   `Status: proposed, pending the owner's decision (Plan UNK-01); it has no effect until the owner accepts it.`
   Keep the immediately following sentence that begins `The amendment itself is made with \`tools/amend_plan.py\`...`.
3. Delete the closing paragraph (lines 146-147):
   `While the policy is not accepted, every amendment follows the second class (approval first).`
4. Keep the two-class definition (fallout MAY amend + report afterward; scope MUST obtain
   approval first) verbatim.

## Compatibility considerations
N/A: a rule prose edit; no tool behavior, config, or API changes. The recorded policy
already reflects current practice.

## Security considerations
N/A: no security-relevant change; a policy-documentation wording update.

## Rollback considerations
N/A: revert the commit that makes this edit.

## Validation plan
- Run `uv run python tools/check_skills_references.py` to confirm every backtick-quoted
  `rules/`/`skills/` reference still resolves after the edit.
- Run `uv run python tools/check_skills_heading_cycles.py` to confirm no cross-file heading
  cycle was introduced.
- Run `uv run python tools/amend_plan.py --help` to confirm `--class` is still
  `fallout|scope` (REQ-003 / AC-003).

## Completion criteria
- `rules/workflow-lifecycle.md` no longer carries the "(proposed)" heading, the
  `Status: proposed` line, or the "While the policy is not accepted" line; both amendment
  classes are stated as the active policy.

## Out of Scope
- Changing the release-unit batch mode or the Plan Freeze criteria.
- Any behavioral change to `tools/amend_plan.py`.
- Editing documents beyond `rules/workflow-lifecycle.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the "(proposed)" framing from the amendment classes in `rules/workflow-lifecycle.md` (REQ-001) | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A: docs-only, no tests | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: this document is the documentation change | — | — | |

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
- **Requirement ID**: `REQ-001` — record the fallout-vs-scope amendment classes as decided policy
- **Source issue**: `issues/20261106-123524_ownerdec001_amendment-policy-and-batch-test-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-175321_ownerdec001_amendment-policy-and-batch-test-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-180725
- **Related target files**: `rules/workflow-lifecycle.md`
