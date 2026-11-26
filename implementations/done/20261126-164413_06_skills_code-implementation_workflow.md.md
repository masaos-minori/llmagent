## Goal
- Add the Step 4 rule of `skills/code-implementation/workflow.md` for a full-suite run whose only failures are baselined, without growing the file past its size ceiling (REQ-005; Plan D-5, D-6).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new bullet in Step 4 and six wording tightenings in the same step that offset its size. Out of scope: any other step, `rules/toolchain.md`, and `tools/check_skill_size_baseline.txt`.

## Assumptions
- Verified in Step 3a: Step 4 has no branch for a known unrelated failure, requires a passing full-suite run, and ends in Rollback on Failure at the Attempt Limit; the "Never Turn a Failure Green" rule of `skills/python-test-and-fix/SKILL.md` forbids skip, xfail, and widened deselect, so the rule restates only the prohibition.
- The file is 42118 B, exactly its ceiling in `tools/check_skill_size_baseline.txt`; the new bullet is about 289 B and the tightenings save about 294 B (measured), a net of about -5 B.
- Plan UNK-03 (whether a baselined-only run satisfies the pass requirement and `rules/toolchain.md` completion checklist) is decided in the Plan by D-5 and is confirmed by the owner approving it; this document applies D-5 and does not edit `rules/toolchain.md`.

## Design decisions
- The rule sits right after the bullet that defines the full-suite run, so it reads as part of that run. It limits itself to baselined ids with a tracking issue and keeps the no-hiding prohibition.

## Alternatives considered
- Put the text in `skills/code-implementation/workflow-edge.md`: not a Plan target row, so out of scope.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Record `wc -c skills/code-implementation/workflow.md` (42118 expected).
2. Apply these tightenings in Step 4 (exact old text to new text; line breaks as in the file):
   - delete the line `  The documentation-only case above runs no full suite at all.`;
   - ` — this is a second,` + newline + `  independent run, scoped strictly to the conflict-detected case.` becomes ` (a second run, for this case only).`;
   - `(where the earlier file is not yet archived and the` + newline + `  end-of-batch run covers it)` becomes `(inside one, the end-of-batch run covers it)`;
   - `Run it after targeted tests pass and confirmed to` + newline + `  have collected at least one test, using` becomes `Run it after the targeted tests pass (at least one collected), using`;
   - `no test run applies: the 0-collected rule, the targeted run,` + newline + `  the once-per-cycle full-suite run, and the coverage gate (recorded `N/A`) are skipped. Run` becomes `no test run applies (the coverage gate is recorded `N/A`). Run` (the file wraps the first line differently: copy the exact text);
   - `Fixing and` + newline + `  re-running after a failure is subject to the same Attempt Limit (3 attempts) and Failure Log` + newline + `  as targeted tests;` becomes `A fix and` + newline + `  re-run after a failure follow the Attempt Limit (3) and Failure Log of targeted tests;`.
3. Insert, as a new bullet directly after the full-suite-run bullet (before the bullet that starts "Run the test commands the procedure's"): `- A full run whose only failures are baselined (each entry names an issue) counts as no new failure: run it with `--junitxml=<path>`, then `uv run python tools/compare_test_baseline.py <path>` (exit 0). Note the known count and issue in Notes; MUST NOT skip, xfail, or deselect a failure.`
4. Run `wc -c` again: the size MUST be at most 42118. If larger, tighten another repeated phrase inside Step 4 without changing a rule, or stop and report (do not raise the ceiling).

### Method
- Edit with exact strings copied from the file; no rule is removed (each tightening drops repeated or redundant wording only), and the Attempt Limit, Rollback on Failure, and single-full-run rules keep their meaning.

### Details
- Re-read Step 4 once after the edit to confirm the rules are intact and the new bullet is not inside another bullet.

## Compatibility considerations
- The workflow is loaded by every implementation cycle: the added rule applies only when a baseline entry exists, and the baseline ships empty, so current behavior is unchanged until the owner adds an entry.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py` (no new violation, file at most 42118 B); the pre-commit hook "Check skills/rules/prompts file references resolve" on commit; the documentation-only checkers of `rules/tool-gates.md` for `skills/**/*.md`.

## Completion criteria
- The bullet exists after the full-suite-run bullet, the six tightenings are applied, no rule of Step 4 changed meaning, and the size check passes with the file at most 42118 B.

## Out of Scope
- The tool (procedure 01), its description (procedure 04), the tool-gates row (procedure 05), and `rules/toolchain.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-171205 | 20261126-171205 | wfeff002: full suite 15737 passed, 4 failed (3 pre-existing tests/mcp_servers/git; 1 eventbus flake, passes alone and on the clean tree) |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` "When to run which tool" | Completed | 20261126-171205 | 20261126-171205 | wfeff002: full suite 15737 passed, 4 failed (3 pre-existing tests/mcp_servers/git; 1 eventbus flake, passes alone and on the clean tree) |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261126-151437_wfeff002_test-failure-baseline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-161137_wfeff002_test-failure-baseline.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-164413
- **Related target files**: `skills/code-implementation/workflow.md`
